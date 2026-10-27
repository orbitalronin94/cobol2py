#!/usr/bin/env python3
"""Run a deterministic 500-program differential sweep over the X-COBOL archive.

The source archive is an external input and is never copied into the repository.
Run only in Dockerfile.external, with networking disabled and the checkout read-only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, signal, subprocess, tempfile, zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ARCHIVE_MD5 = "cbd974caed72b0836777dc2305928ed3"
ARCHIVE_URL = "https://zenodo.org/records/14269462/files/COBOL_Files.zip?download=1"
SOURCE_EXTENSIONS = {".cbl", ".cob", ".cobol"}
MAX_SOURCE_BYTES = 1_000_000

def run_process(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    """Run one untrusted program in its own process group and kill it on timeout."""
    try:
        process = subprocess.Popen(command, cwd=str(cwd), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", start_new_session=True,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(cwd),
                 "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                 "PYTHONDONTWRITEBYTECODE": "1"})
    except OSError as error:
        return {"launched": False, "returncode": None, "stdout": "", "stderr": str(error), "timeout": False}
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return {"launched": True, "returncode": process.returncode, "stdout": stdout,
                "stderr": stderr, "timeout": False}
    except subprocess.TimeoutExpired:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        stdout, stderr = process.communicate()
        return {"launched": True, "returncode": process.returncode, "stdout": stdout or "",
                "stderr": stderr or "", "timeout": True}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

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
    parser.add_argument("--compile-timeout", type=int, default=8)
    parser.add_argument("--run-timeout", type=int, default=3)
    parser.add_argument("--translator-timeout", type=int, default=20)
    args = parser.parse_args()
    if args.target < 1: parser.error("--target must be positive")
    translator = args.translator.resolve()
    if not translator.is_file(): parser.error(f"translator not found: {translator}")
    args.output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1, "dataset": "X-COBOL: A Dataset of Open-Source COBOL repositories, v2",
        "dataset_url": "https://zenodo.org/records/14269462", "archive_md5_expected": ARCHIVE_MD5,
        "archive_md5_verified": False,
        "selection": "Deterministic SHA-256 ordering of unique source contents; retain sources that compile and whose GnuCOBOL reference process terminates within timeout.",
        "pass_definition": "Exact stdout and process return-code match against a compiled GnuCOBOL executable.",
        "target": args.target, "source_files_discovered": 0, "unique_source_contents": 0,
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
        for content_hash, source in ordered:
            if report["tested"] >= args.target: break
            report["screened"] += 1
            relative = source.relative_to(extracted_root).as_posix()
            result: dict[str, Any] = {"id": case_id(relative, content_hash), "source": relative,
                "source_sha256": content_hash, "reference_compile": "pending", "status": "excluded", "reason": None}
            with tempfile.TemporaryDirectory(dir=temp_root, prefix="case-") as case_dir:
                work = Path(case_dir)
                executable = work / "reference"
                compiled = run_process(["cobc", "-x", "-I", str(source.parent), "-o", str(executable), str(source)],
                                       work, args.compile_timeout)
                if not compiled["launched"] or compiled["timeout"] or compiled["returncode"] != 0:
                    report["reference_compile_failures"] += 1
                    result["reference_compile"] = "failed"
                    result["reason"] = "compile timeout" if compiled["timeout"] else (
                        compiled["stderr"] or "compiler did not produce an executable")[-400:]
                    continue
                result["reference_compile"] = "passed"
                reference = run_process([str(executable)], work, args.run_timeout)
                if not reference["launched"] or reference["timeout"]:
                    report["reference_runtime_exclusions"] += 1
                    result["reason"] = "reference execution timed out or could not launch"
                    continue
                translated = run_process(["python3", "-I", str(translator), str(source), "--format", "auto"],
                                         work, args.translator_timeout)
                if not translated["launched"] or translated["timeout"] or translated["returncode"] != 0:
                    result.update({"status": "failed", "reason": "translator timeout" if translated["timeout"] else
                        (translated["stderr"] or f"translator exited {translated['returncode']}")[-400:]})
                else:
                    generated = work / "translated.py"
                    generated.write_text(translated["stdout"], encoding="utf-8")
                    try: compile(translated["stdout"], str(generated), "exec")
                    except SyntaxError as error:
                        result.update({"status": "failed", "reason": f"generated Python syntax error: {error.msg}"})
                    else:
                        candidate = run_process(["python3", "-I", str(generated)], work, args.translator_timeout)
                        result["candidate_returncode"] = candidate["returncode"]
                        result["reference_returncode"] = reference["returncode"]
                        result["stdout_match"] = candidate["stdout"] == reference["stdout"]
                        result["returncode_match"] = candidate["returncode"] == reference["returncode"]
                        if candidate["launched"] and not candidate["timeout"] and result["stdout_match"] and result["returncode_match"]:
                            result.update({"status": "passed", "reason": None})
                        else:
                            result.update({"status": "failed", "reason": "translated program timed out" if candidate["timeout"]
                                else "stdout or return code differs from GnuCOBOL"})
                report["results"].append(result)
                report["tested"] += 1
                if result["status"] == "passed": report["passed"] += 1
                else: report["failed"] += 1
    report["target_reached"] = report["tested"] == args.target
    report["pass_rate_percent"] = round(100 * report["passed"] / report["tested"], 2) if report["tested"] else 0.0
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
        f"- Translator mismatches/errors: **{report['failed']}**", f"- Target reached: **{report['target_reached']}**", "",
        "## Per-program results", "", "| Case | Archive path | Status | Detail |", "|---|---|---|---|"]
    for item in report["results"]:
        detail = (item.get("reason") or "Exact stdout and return-code match").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['id']} | {item['source']} | {item['status'].upper()} | {detail} |")
    lines.extend(["", "See the JSON artifact for source hashes, return codes, and exact match flags.", ""])
    (args.output / "external-corpus-report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:18]))
    if not report["target_reached"]:
        print(f"Could only find {report['tested']} runnable standalone sources; required {args.target}.")
        return 2
    return 0 if report["failed"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
