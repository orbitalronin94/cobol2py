#!/usr/bin/env python3
"""Audit the vendored MIT-100 inventory and report dependency/compile blockers.

This is deliberately an audit, not a translator pass-rate benchmark. A COBOL
unit blocked by missing copybooks or platform dependencies must not be counted
as a translator failure.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmarks" / "mit-100"
MANIFEST = CORPUS / "manifest.json"
COPY_RE = re.compile(r"^\s*COPY\s+([A-Z0-9_-]+)(?:\.[A-Z0-9_-]+)?", re.I | re.M)
ID_RE = re.compile(r"PROGRAM-ID\s*\.\s*([A-Z0-9_-]+)", re.I)
CALL_RE = re.compile(r"\bCALL\s+(?:['\"]([A-Z0-9_-]+)['\"]|([A-Z0-9_-]+))", re.I)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write JSON report")
    parser.add_argument("--markdown", dest="markdown_path", help="write Markdown report")
    parser.add_argument("--compile", action="store_true",
                        help="attempt GnuCOBOL syntax checks where copybooks are resolved")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    sources = sorted({entry["path"] for entry in entries})
    copybook_roots = [CORPUS / "copybooks", CORPUS / "source"]
    report = {
        "corpus": manifest.get("corpus", "MIT-100"),
        "manifest_entries": len(entries),
        "unique_program_ids": len({e.get("program_id") for e in entries}),
        "source_file_count": len(sources),
        "gnucobol_available": shutil.which("cobc") is not None,
        "compile_requested": args.compile,
        "files": [],
        "copybooks": {"referenced": [], "resolved": [], "missing": []},
        "summary": {},
    }
    all_copybooks: set[str] = set()
    for relative in sources:
        path = ROOT / relative
        content = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        copies = sorted(set(COPY_RE.findall(content)))
        all_copybooks.update(name.upper() for name in copies)
        ids = ID_RE.findall(content)
        calls = sorted({(a or b).upper() for a, b in CALL_RE.findall(content)})
        missing = []
        for name in copies:
            candidates = []
            for root in copybook_roots:
                candidates.extend([root / name, root / f"{name}.CPY", root / f"{name}.cpy"])
            if not any(candidate.is_file() for candidate in candidates):
                missing.append(name.upper())

        item = {
            "path": relative,
            "exists": path.is_file(),
            "program_ids_found": ids,
            "copybooks": copies,
            "missing_copybooks": sorted(set(missing)),
            "static_call_targets": calls,
            "compile_status": "NOT_REQUESTED",
            "compile_output": "",
        }
        if not path.is_file():
            item["compile_status"] = "MISSING_SOURCE"
        elif args.compile:
            if not report["gnucobol_available"]:
                item["compile_status"] = "BLOCKED_NO_GNUCOBOL"
            elif missing:
                item["compile_status"] = "BLOCKED_MISSING_COPYBOOKS"
            else:
                command = ["cobc", "-fsyntax-only", "-free", "-I", str(CORPUS / "copybooks"), str(path)]
                result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
                item["compile_status"] = "SYNTAX_OK" if result.returncode == 0 else "COMPILE_ERROR"
                item["compile_output"] = (result.stdout + result.stderr)[-4000:]
        report["files"].append(item)

    report["copybooks"]["referenced"] = sorted(all_copybooks)
    for name in report["copybooks"]["referenced"]:
        candidates = []
        for root in copybook_roots:
            candidates.extend([root / name, root / f"{name}.CPY", root / f"{name}.cpy"])
        (report["copybooks"]["resolved"] if any(p.is_file() for p in candidates)
         else report["copybooks"]["missing"]).append(name)

    statuses = Counter(item["compile_status"] for item in report["files"])
    report["summary"] = {
        "source_files": len(sources),
        "program_ids_in_manifest": report["manifest_entries"],
        "unique_program_ids": report["unique_program_ids"],
        "unique_copybooks_referenced": len(report["copybooks"]["referenced"]),
        "copybooks_resolved": len(report["copybooks"]["resolved"]),
        "copybooks_missing": len(report["copybooks"]["missing"]),
        "file_status_counts": dict(sorted(statuses.items())),
    }

    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_path:
        (ROOT / args.json_path).write_text(json_text, encoding="utf-8")
    else:
        print(json_text)

    lines = [
        "# MIT-100 dependency and compilation audit",
        "",
        f"- Manifest entries: **{report['manifest_entries']}**",
        f"- Unique program IDs: **{report['unique_program_ids']}**",
        f"- Distinct source files: **{len(sources)}**",
        f"- Unique copybooks referenced: **{len(report['copybooks']['referenced'])}**",
        f"- Copybooks resolved inside the vendored corpus: **{len(report['copybooks']['resolved'])}**",
        f"- Copybooks missing from the vendored corpus: **{len(report['copybooks']['missing'])}**",
        f"- GnuCOBOL available: **{report['gnucobol_available']}**",
        "",
        "## Per-file status",
        "",
        "| Source file | Program IDs | Missing copybooks | Compile status |",
        "|---|---:|---:|---|",
    ]
    for item in report["files"]:
        lines.append(
            f"| `{item['path']}` | {len(item['program_ids_found'])} | "
            f"{len(item['missing_copybooks'])} | {item['compile_status']} |"
        )
    lines += ["", "## Missing copybooks", ""]
    lines += [f"- `{name}`" for name in report["copybooks"]["missing"]] or ["None"]
    lines += [
        "",
        "This report is a source/dependency audit, not a translator correctness score.",
        "Files blocked by missing copybooks or platform services are not counted as translator failures.",
        "",
    ]
    markdown = "\n".join(lines)
    if args.markdown_path:
        (ROOT / args.markdown_path).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
