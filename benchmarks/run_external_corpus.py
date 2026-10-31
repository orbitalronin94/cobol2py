#!/usr/bin/env python3
"""Run a deterministic 500-program differential sweep over the X-COBOL archive.

The source archive is an external input and is never copied into the repository.
Run only in Dockerfile.external, with networking disabled and the checkout read-only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, signal, subprocess, tempfile, threading, zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Optional
import sys

# Docker invokes Python with -I (isolated mode), which omits the checkout root
# from sys.path. Add the mounted, read-only repository explicitly so the
# optional repair module remains importable in the benchmark container.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ronin.compiler_guided_repair import repair_python_source

# Bound captured output from untrusted corpus programs. Reader threads keep
# draining pipes after the limit so children cannot block on a full pipe.
MAX_CAPTURE_BYTES = 1_000_000

ARCHIVE_MD5 = "cbd974caed72b0836777dc2305928ed3"
ARCHIVE_URL = "https://zenodo.org/records/14269462/files/COBOL_Files.zip?download=1"
SOURCE_EXTENSIONS = {".cbl", ".cob", ".cobol"}
MAX_SOURCE_BYTES = 1_000_000

def run_process(command: list[str], cwd: Path, timeout: int, stdout_path: Optional[Path] = None, stderr_path: Optional[Path] = None) -> dict[str, Any]:
    """Run one untrusted program in its own process group with bounded output capture."""
    try:
        process = subprocess.Popen(command, cwd=str(cwd), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False,
            start_new_session=True,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(cwd),
                 "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                 "PYTHONDONTWRITEBYTECODE": "1"})
    except OSError as error:
        # Keep the diagnostic file contract even when the child never starts.
        # Downstream byte-diff code can then safely compare an empty stream.
        for output_path in (stdout_path, stderr_path):
            if output_path is not None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(b"")
        return {"launched": False, "returncode": None, "stdout": "", "stderr": str(error),
                "timeout": False, "stdout_truncated": False, "stderr_truncated": False,
                "stdout_sha256": hashlib.sha256(b"").hexdigest(), "stdout_length": 0}

    stdout_capture = bytearray()
    stderr_capture = bytearray()
    stdout_overflow = [False]
    stderr_overflow = [False]
    stdout_digest = hashlib.sha256()
    stdout_length = [0]

    def drain(
        stream: Any,
        capture: bytearray,
        overflow: list[bool],
        digest: Any = None,
        total_length: Optional[list[int]] = None,
        output_path: Optional[Path] = None,
    ) -> None:
        output_handle = output_path.open("wb") if output_path else None
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                if output_handle is not None:
                    output_handle.write(chunk)
                if digest is not None:
                    digest.update(chunk)
                if total_length is not None:
                    total_length[0] += len(chunk)
                remaining = MAX_CAPTURE_BYTES - len(capture)
                if remaining > 0:
                    capture.extend(chunk[:remaining])
                if len(chunk) > max(remaining, 0):
                    overflow[0] = True
        finally:
            stream.close()
            if output_handle is not None:
                output_handle.close()

    readers = [
        threading.Thread(
            target=drain,
            args=(process.stdout, stdout_capture, stdout_overflow, stdout_digest, stdout_length, stdout_path),
            daemon=True,
        ),
        threading.Thread(
            target=drain,
            args=(process.stderr, stderr_capture, stderr_overflow, None, None, stderr_path),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    for reader in readers:
        reader.join(timeout=2)

    return {
        "launched": True,
        "returncode": process.returncode,
        "stdout": stdout_capture.decode("utf-8", errors="replace"),
        "stderr": stderr_capture.decode("utf-8", errors="replace"),
        "timeout": timed_out,
        "stdout_truncated": stdout_overflow[0],
        "stderr_truncated": stderr_overflow[0],
        # Hash and byte length cover the complete stream, including discarded
        # diagnostic bytes, so large output is still compared exactly.
        "stdout_sha256": stdout_digest.hexdigest(),
        "stdout_length": stdout_length[0],
    }


def stdout_matches(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    """Compare complete stdout streams without retaining unbounded output."""
    return (
        candidate.get("stdout_length") == reference.get("stdout_length")
        and candidate.get("stdout_sha256") == reference.get("stdout_sha256")
    )

def first_byte_difference(left_path: Path, right_path: Path) -> Optional[int]:
    """Return the first differing byte offset, or None when the complete files match."""
    offset = 0
    with left_path.open("rb") as left, right_path.open("rb") as right:
        while True:
            left_chunk = left.read(65536)
            right_chunk = right.read(65536)
            if left_chunk != right_chunk:
                for index, (a, b) in enumerate(zip(left_chunk, right_chunk)):
                    if a != b:
                        return offset + index
                return offset + min(len(left_chunk), len(right_chunk))
            if not left_chunk:
                return None
            offset += len(left_chunk)

def candidate_error_context(stderr: str, generated_source: str) -> dict[str, Any]:
    """Return a sanitized generated-code location without exposing string contents."""
    frames = re.findall(r'translated\.py["\']?, line (\d+)', stderr)
    if not frames:
        return {}
    line_number = int(frames[-1])
    generated_lines = generated_source.splitlines()
    context: dict[str, Any] = {"candidate_error_line_number": line_number}
    if 1 <= line_number <= len(generated_lines):
        line = generated_lines[line_number - 1].strip()
        # Runtime diagnostics may be published as artifacts; mask all literals
        # so source-derived display text from the external corpus is not exposed.
        line = re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "<literal>", line)
        context["candidate_error_line"] = line[:160].replace("|", "\\|")
    return context


def sanitize_exception_message(message: str) -> str:
    """Keep actionable runtime diagnostics while masking arbitrary quoted data."""
    safe_type_names = {
        "str", "int", "float", "bool", "bytes", "list", "dict", "tuple",
        "set", "frozenset", "NoneType", "complex", "range", "slice",
    }

    def mask_quoted(match: re.Match[str]) -> str:
        value = match.group(2)
        if value in safe_type_names:
            return match.group(0)
        return "<quoted>"

    return re.sub(r"""(['"])(.*?)\1""", mask_quoted, message)[:240]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

def preserve_exclusion_diagnostics(
    output_root: Path, case_root: Path, source: Path,
    result: dict[str, Any], compiled: dict[str, Any],
) -> None:
    """Persist source and reference-process evidence for an excluded case."""
    diagnostic_dir = output_root / "diagnostics" / result["id"]
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, diagnostic_dir / ("source" + source.suffix.lower()))
    for artifact_name in (
        "reference-compile.stdout.bin", "reference-compile.stderr.bin",
        "reference.stdout.bin", "reference.stderr.bin",
    ):
        artifact = case_root / artifact_name
        if artifact.is_file():
            shutil.copy2(artifact, diagnostic_dir / artifact_name)
    metadata = {
        "case": result,
        "reference_compile_returncode": compiled.get("returncode"),
        "reference_compile_launched": compiled.get("launched"),
        "reference_compile_timeout": compiled.get("timeout"),
        "reference_launched": result.get("reference_launched"),
        "reference_timeout": result.get("reference_timeout"),
        "reference_returncode": result.get("reference_returncode"),
        "stdin": "DEVNULL; interactive input is not currently supplied.",
        "classification": "reference exclusion; not counted as a translator failure or in the tested denominator",
    }
    (diagnostic_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

def extract_archive(archive: Path, destination: Path) -> list[Path]:
    """Verify the published checksum and extract only safe ordinary ZIP files."""
    md5 = hashlib.md5()
    with archive.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): md5.update(block)
    if md5.hexdigest().lower() != ARCHIVE_MD5:
        raise ValueError(f"X-COBOL archive MD5 mismatch: expected {ARCHIVE_MD5}, got {md5.hexdigest()}")
    destination.mkdir(parents=True, exist_ok=True)
    extracted, root = [], destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            if info.is_dir(): continue
            relative = PurePosixPath(info.filename)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts: continue
            mode = (info.external_attr >> 16) & 0xFFFF
            if mode and (mode & 0o170000) not in (0, 0o100000): continue
            target = (destination / Path(*relative.parts)).resolve()
            if not target.is_relative_to(root): continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(info) as source, target.open("wb") as output: shutil.copyfileobj(source, output)
            if target.suffix.lower() in SOURCE_EXTENSIONS:
                try: size = target.stat().st_size
                except OSError: continue
                if 0 < size <= MAX_SOURCE_BYTES: extracted.append(target)
    return extracted

def case_id(relative: str, digest: str) -> str:
    stem = "".join(c.lower() if c.isalnum() else "-" for c in Path(relative).stem).strip("-")
    stem = "-".join(x for x in stem.split("-") if x)[:32] or "program"
    return f"{stem}-{digest[:10]}"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--translator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--skip", type=int, default=0, help="Skip this many eligible programs before testing the sample")
    parser.add_argument("--compile-timeout", type=int, default=8)
    parser.add_argument("--run-timeout", type=int, default=3)
    parser.add_argument("--translator-timeout", type=int, default=20)
    parser.add_argument("--diagnostics", action="store_true", help="Preserve complete per-case stdout/stderr byte streams and source/generated code for failed cases")
    args = parser.parse_args()
    if args.target < 1: parser.error("--target must be positive")
    if args.skip < 0: parser.error("--skip must be non-negative")
    translator = args.translator.resolve()
    if not translator.is_file(): parser.error(f"translator not found: {translator}")
    args.output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1, "dataset": "X-COBOL: A Dataset of Open-Source COBOL repositories, v2",
        "dataset_url": "https://zenodo.org/records/14269462", "archive_md5_expected": ARCHIVE_MD5,
        "archive_md5_verified": False,
        "selection": "Deterministic SHA-256 ordering of unique source contents; skip the first --skip sources that compile and terminate under GnuCOBOL, then test the next --target eligible sources.",
        "pass_definition": "Exact stdout and process return-code match against a compiled GnuCOBOL executable.",
        "target": args.target, "skip": args.skip, "eligible_skipped": 0, "source_files_discovered": 0, "unique_source_contents": 0,
        "screened": 0, "reference_compile_failures": 0, "reference_runtime_exclusions": 0,
        "tested": 0, "passed": 0, "failed": 0, "results": []}
    with tempfile.TemporaryDirectory(prefix="x-cobol-benchmark-") as temp:
        temp_root = Path(temp)
        extracted_root = temp_root / "source"
        sources = extract_archive(args.archive.resolve(), extracted_root)
        report["archive_md5_verified"] = True
        report["source_files_discovered"] = len(sources)
        unique: dict[str, Path] = {}
        for source in sources: unique.setdefault(sha256_file(source), source)
        report["unique_source_contents"] = len(unique)
        ordered = sorted(unique.items(), key=lambda pair: hashlib.sha256(
            (pair[1].relative_to(extracted_root).as_posix() + "\0" + pair[0]).encode("utf-8")).hexdigest())
        eligible_seen = 0
        for content_hash, source in ordered:
            if report["tested"] >= args.target: break
            report["screened"] += 1
            relative = source.relative_to(extracted_root).as_posix()
            result: dict[str, Any] = {"id": case_id(relative, content_hash), "source": relative,
                "source_sha256": content_hash, "reference_compile": "pending", "status": "excluded", "reason": None}
            # Flush a compact case marker so a killed isolated process can be
            # localized from Actions logs without publishing corpus source text.
            print(f"CASE START screened={report['screened']} id={result['id']}", flush=True)
            with tempfile.TemporaryDirectory(dir=temp_root, prefix="case-") as case_dir:
                case_root = Path(case_dir)
                reference_work = case_root / "reference-work"
                candidate_work = case_root / "candidate-work"
                reference_work.mkdir()
                candidate_work.mkdir()
                executable = reference_work / "reference"
                compiled = run_process(["cobc", "-x", "-I", str(source.parent), "-o", str(executable), str(source)],
                                       reference_work, args.compile_timeout,
                                       case_root / "reference-compile.stdout.bin" if args.diagnostics else None,
                                       case_root / "reference-compile.stderr.bin" if args.diagnostics else None)
                if not compiled["launched"] or compiled["timeout"] or compiled["returncode"] != 0:
                    report["reference_compile_failures"] += 1
                    result["reference_compile"] = "failed"
                    result["reference_compile_launched"] = compiled["launched"]
                    result["reference_compile_timeout"] = compiled["timeout"]
                    result["reason"] = "compile timeout" if compiled["timeout"] else (
                        compiled["stderr"] or "compiler did not produce an executable")[-400:]
                    if args.diagnostics:
                        preserve_exclusion_diagnostics(args.output, case_root, source, result, compiled)
                    continue
                result["reference_compile"] = "passed"
                reference = run_process([str(executable)], reference_work, args.run_timeout,
                                        case_root / "reference.stdout.bin" if args.diagnostics else None,
                                        case_root / "reference.stderr.bin" if args.diagnostics else None)
                if not reference["launched"] or reference["timeout"]:
                    report["reference_runtime_exclusions"] += 1
                    result["reason"] = "reference execution timed out or could not launch"
                    result["reference_launched"] = reference["launched"]
                    result["reference_timeout"] = reference["timeout"]
                    result["reference_returncode"] = reference.get("returncode")
                    if args.diagnostics:
                        preserve_exclusion_diagnostics(args.output, case_root, source, result, compiled)
                    continue
                if eligible_seen < args.skip:
                    eligible_seen += 1
                    report["eligible_skipped"] = eligible_seen
                    continue
                eligible_seen += 1
                translated = run_process(["python3", "-I", str(translator), str(source), "--format", "auto"],
                                         candidate_work, args.translator_timeout,
                                         case_root / "translator.stdout.bin" if args.diagnostics else None,
                                         case_root / "translator.stderr.bin" if args.diagnostics else None)
                result["translator_launched"] = translated["launched"]
                result["translator_timeout"] = translated["timeout"]
                result["translator_stdout_truncated"] = translated["stdout_truncated"]
                if (not translated["launched"] or translated["timeout"] or translated["stdout_truncated"]
                        or translated["returncode"] != 0):
                    reason = ("translator timeout" if translated["timeout"] else
                        "translator output exceeded capture limit" if translated.get("stdout_truncated") else
                        (translated["stderr"] or f"translator exited {translated['returncode']}")[-400:])
                    result.update({"status": "failed", "reason": reason})
                else:
                    generated = candidate_work / "translated.py"
                    # First isolated stage: compiler-guided syntax repair only.
                    # SMT and symbolic repair remain opt-in until tied to source
                    # spans and validated without changing the corpus.
                    compiler_repair = repair_python_source(translated["stdout"], max_iterations=2)
                    candidate_source = compiler_repair.source if compiler_repair.compiled else translated["stdout"]
                    result["compiler_repair_applied"] = candidate_source != translated["stdout"]
                    result["compiler_repair_status"] = compiler_repair.status
                    result["compiler_repair_iterations"] = compiler_repair.iterations
                    generated.write_text(candidate_source, encoding="utf-8")
                    try: compile(candidate_source, str(generated), "exec")
                    except SyntaxError as error:
                        generated_lines = translated["stdout"].splitlines()
                        offending_line = generated_lines[error.lineno - 1].strip() if error.lineno and error.lineno <= len(generated_lines) else ""
                        # Keep only a short generated-code excerpt for diagnosis; never publish source corpus text.
                        excerpt = offending_line[:160].replace("|", "\\|")
                        diagnostic = f"generated Python syntax error at line {error.lineno}, column {error.offset}: {error.msg}"
                        if excerpt:
                            diagnostic += f"; generated line: {excerpt}"
                        result.update({"status": "failed", "reason": diagnostic})
                    else:
                        candidate = run_process(["python3", "-I", str(generated)], candidate_work, args.translator_timeout,
                                               case_root / "candidate.stdout.bin" if args.diagnostics else None,
                                               case_root / "candidate.stderr.bin" if args.diagnostics else None)
                        result["candidate_launched"] = candidate["launched"]
                        result["candidate_timeout"] = candidate["timeout"]
                        result["candidate_returncode"] = candidate["returncode"]
                        result["reference_returncode"] = reference["returncode"]
                        result["stdout_match"] = stdout_matches(candidate, reference)
                        result["returncode_match"] = candidate["returncode"] == reference["returncode"]
                        # Store bounded diagnostics rather than program output. Compare
                        # the complete streams by digest + byte length even when the
                        # retained prefixes exceed the capture limit.
                        candidate_stdout = candidate["stdout"]
                        reference_stdout = reference["stdout"]
                        result["candidate_stdout_length"] = candidate["stdout_length"]
                        result["reference_stdout_length"] = reference["stdout_length"]
                        result["candidate_stdout_sha256"] = candidate["stdout_sha256"]
                        result["reference_stdout_sha256"] = reference["stdout_sha256"]
                        if args.diagnostics and not result["stdout_match"]:
                            result["stdout_first_difference_byte"] = first_byte_difference(
                                case_root / "candidate.stdout.bin", case_root / "reference.stdout.bin")
                        result["candidate_stdout_truncated"] = candidate["stdout_truncated"]
                        result["reference_stdout_truncated"] = reference["stdout_truncated"]
                        if not result["stdout_match"]:
                            result["stdout_first_difference"] = next(
                                (index for index, (left, right) in enumerate(zip(candidate_stdout, reference_stdout))
                                 if left != right),
                                min(len(candidate_stdout), len(reference_stdout)),
                            )
                        stderr_lines = [line.strip() for line in candidate["stderr"].splitlines() if line.strip()]
                        if stderr_lines:
                            result.update(candidate_error_context(candidate["stderr"], translated["stdout"]))
                            tail = stderr_lines[-1]
                            exception_type = tail.split(":", 1)[0].split()[-1]
                            if exception_type and exception_type[0].isupper() and exception_type.replace("_", "").isalnum():
                                result["candidate_exception_type"] = exception_type
                                if ":" in tail:
                                    result["candidate_exception_message"] = sanitize_exception_message(tail.split(":", 1)[1].strip())
                            if exception_type == "NameError":
                                # Import locally as a defensive guard in isolated benchmark runners.
                                import re as _re
                                missing = _re.search(r"name ['\"]([^'\"]+)['\"] is not defined", tail)
                                if missing:
                                    result["candidate_missing_name"] = missing.group(1)[:100]
                        if (candidate["launched"] and not candidate["timeout"]
                                and result["stdout_match"] and result["returncode_match"]):
                            result.update({"status": "passed", "reason": None})
                        else:
                            reason = ("translated program could not launch" if not candidate["launched"]
                                else "translated program timed out" if candidate["timeout"]
                                else "stdout or return code differs from GnuCOBOL")
                            result.update({"status": "failed", "reason": reason})
                if args.diagnostics and result.get("status") == "failed":
                    diagnostic_dir = args.output / "diagnostics" / result["id"]
                    diagnostic_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, diagnostic_dir / ("source" + source.suffix.lower()))
                    generated_file = candidate_work / "translated.py"
                    if generated_file.is_file():
                        shutil.copy2(generated_file, diagnostic_dir / "translated.py")
                    for artifact_name in ("reference-compile.stdout.bin", "reference-compile.stderr.bin",
                                          "reference.stdout.bin", "reference.stderr.bin",
                                          "translator.stdout.bin", "translator.stderr.bin",
                                          "candidate.stdout.bin", "candidate.stderr.bin"):
                        artifact = case_root / artifact_name
                        if artifact.is_file():
                            shutil.copy2(artifact, diagnostic_dir / artifact_name)
                    metadata = {"case": result, "reference_compile_returncode": compiled.get("returncode"),
                                "reference_compile_launched": compiled.get("launched"),
                                "reference_compile_timeout": compiled.get("timeout"),
                                "reference_launched": reference.get("launched"),
                                "reference_timeout": reference.get("timeout"),
                                "reference_returncode": reference.get("returncode"),
                                "candidate_launched": result.get("candidate_launched"),
                                "candidate_timeout": result.get("candidate_timeout"),
                                "candidate_returncode": result.get("candidate_returncode"),
                                "translator_launched": translated.get("launched"),
                                "translator_timeout": translated.get("timeout"),
                                "translator_returncode": translated.get("returncode"),
                                "stdin": "DEVNULL; interactive input is not currently supplied.",
                                "comparison": "Complete stdout byte streams are retained; exact score uses SHA-256, byte length, and return code."}
                    (diagnostic_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                report["results"].append(result)
                report["tested"] += 1
                if result["status"] == "passed": report["passed"] += 1
                else: report["failed"] += 1
    report["sample_complete"] = report["tested"] == args.target
    report["pass_rate_percent"] = round(100 * report["passed"] / report["tested"], 2) if report["tested"] else 0.0
    report["equivalence_threshold_percent"] = 75.0
    report["equivalence_gate_reached"] = report["sample_complete"] and report["pass_rate_percent"] >= report["equivalence_threshold_percent"]
    report["source_code_republished"] = False
    report["notes"] = [
        "Only source files that compile and terminate under GnuCOBOL are included in the tested denominator.",
        "Compile failures and reference timeouts are reported separately, not counted as translator failures.",
        "This is a deterministic sample of standalone executable programs, not a measure of all COBOL dialects.",
        "Only hashes, relative archive paths, and results are reported; third-party source files are not copied into the repository.",
        "Run only in the isolated container with networking disabled and repository mounted read-only."]
    (args.output / "external-corpus-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# External COBOL corpus differential benchmark", "",
        f"- Dataset: [X-COBOL v2]({report['dataset_url']})",
        f"- Archive checksum verified: **{report['archive_md5_verified']}**",
        f"- Source files discovered: **{report['source_files_discovered']}**; unique contents: **{report['unique_source_contents']}**",
        f"- Candidates screened: **{report['screened']}**",
        f"- Reference compile failures: **{report['reference_compile_failures']}**",
        f"- Reference runtime exclusions: **{report['reference_runtime_exclusions']}**",
        f"- Differentially tested: **{report['tested']}/{report['target']}**",
        f"- Exact matches: **{report['passed']}/{report['tested']} ({report['pass_rate_percent']:.2f}%)**",
        f"- Translator mismatches/errors: **{report['failed']}**", f"- Sample complete: **{report['sample_complete']}**",
        f"- 75% exact-equivalence gate reached: **{report['equivalence_gate_reached']}**", "",
        "## Per-program results", "", "| Case | Archive path | Status | Detail |", "|---|---|---|---|"]
    for item in report["results"]:
        detail = (item.get("reason") or "Exact stdout and return-code match").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['id']} | {item['source']} | {item['status'].upper()} | {detail} |")
    # Aggregate failure families so a benchmark run points directly to the next fixes.
    failure_reasons = [item.get("reason") or "" for item in report["results"] if item["status"] != "passed"]
    syntax_errors = [reason for reason in failure_reasons if reason.startswith("generated Python syntax error")]
    runtime_mismatches = sum(reason == "stdout or return code differs from GnuCOBOL" for reason in failure_reasons)
    exception_counts: dict[str, int] = {}
    for item in report["results"]:
        exception_type = item.get("candidate_exception_type")
        if exception_type:
            exception_counts[exception_type] = exception_counts.get(exception_type, 0) + 1
    lines.extend(["", "## Failure summary", "",
        f"- Generated Python syntax errors: **{len(syntax_errors)}**",
        f"- Runtime/output mismatches: **{runtime_mismatches}**",
        f"- Other translator errors/timeouts: **{len(failure_reasons) - len(syntax_errors) - runtime_mismatches}**",
        "", "### Most frequent runtime exception classes", ""])
    for exception_type, count in sorted(exception_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:12]:
        lines.append(f"- **{count}** — {exception_type}")
    lines.extend(["", "### Most frequent syntax diagnostics", ""])
    diagnostic_counts: dict[str, int] = {}
    for reason in syntax_errors:
        message = reason.split("; generated line:", 1)[0]
        diagnostic_counts[message] = diagnostic_counts.get(message, 0) + 1
    for message, count in sorted(diagnostic_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:12]:
        lines.append(f"- **{count}** — {message}")

    # Repeated offending lines often reveal one shared translator bug even when
    # Python's syntax-error message differs by line/column. These short excerpts
    # are already included per case in the JSON artifact; aggregate them here to
    # make the next repair batch easier to prioritize.
    generated_line_counts: dict[str, int] = {}
    for reason in syntax_errors:
        if "; generated line:" not in reason:
            continue
        generated_line = reason.split("; generated line:", 1)[1].strip()
        generated_line_counts[generated_line] = generated_line_counts.get(generated_line, 0) + 1
    lines.extend(["", "### Most frequent generated Python lines", ""])
    for generated_line, count in sorted(
        generated_line_counts.items(), key=lambda pair: (-pair[1], pair[0])
    )[:15]:
        safe_line = generated_line.replace("|", "\\|").replace("\n", " ")
        lines.append(f"- **{count}** — `{safe_line}`")

    lines.extend(["", "See the JSON artifact for source hashes, return codes, exact match flags, and short generated-line diagnostics.", ""])
    (args.output / "external-corpus-report.md").write_text("\n".join(lines), encoding="utf-8")
    summary_start = lines.index("## Failure summary")
    print("\n".join(lines[:18] + [""] + lines[summary_start:]))
    if not report["sample_complete"]:
        print(f"Could only find {report['tested']} runnable standalone sources; required {args.target}.")
        return 2
    # This is a baseline measurement, not a regression gate: a non-100% score
    # is the result we want to measure and inspect, not a broken benchmark run.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
