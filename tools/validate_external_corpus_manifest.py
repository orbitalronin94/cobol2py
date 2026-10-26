#!/usr/bin/env python3
"""Validate provenance metadata for the external COBOL candidate ledger."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "external-corpus" / "candidates.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def validate(manifest: dict) -> list[str]:
    errors: list[str] = []
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["entries must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_sources: set[tuple[str, str, str]] = set()
    required = (
        "id", "project", "program_id", "repository", "source_path",
        "source_url", "source_commit", "source_blob_sha", "source_lines",
        "license_spdx", "license_path", "license_evidence", "compile_status",
        "runtime_status",
    )
    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in required:
            if not entry.get(field):
                errors.append(f"{label}.{field} is required")
        entry_id = entry.get("id")
        if entry_id:
            if entry_id in seen_ids:
                errors.append(f"duplicate id: {entry_id}")
            seen_ids.add(entry_id)

        commit = entry.get("source_commit", "")
        blob_sha = entry.get("source_blob_sha", "")
        if commit and not SHA_RE.fullmatch(commit):
            errors.append(f"{label}.source_commit must be a 40-character lowercase SHA")
        if blob_sha and not SHA_RE.fullmatch(blob_sha):
            errors.append(f"{label}.source_blob_sha must be a 40-character lowercase SHA")
        lines = entry.get("source_lines")
        if not isinstance(lines, int) or isinstance(lines, bool) or lines <= 0:
            errors.append(f"{label}.source_lines must be a positive integer")
        url = entry.get("source_url", "")
        if commit and commit not in url:
            errors.append(f"{label}.source_url must pin source_commit")
        if url and not url.startswith("https://github.com/"):
            errors.append(f"{label}.source_url must use HTTPS GitHub URL")
        identity = (entry.get("repository", ""), commit, entry.get("source_path", ""))
        if all(identity):
            if identity in seen_sources:
                errors.append(f"duplicate source identity: {identity}")
            seen_sources.add(identity)

        if entry.get("compile_status") not in {
            "NOT_RUN", "BLOCKED", "COMPILE_OK", "COMPILE_ERROR"
        }:
            errors.append(f"{label}.compile_status is not a recognized classification")
        if entry.get("runtime_status") not in {
            "NOT_RUN", "BLOCKED", "MATCH", "MISMATCH", "ERROR"
        }:
            errors.append(f"{label}.runtime_status is not a recognized classification")
        if entry.get("vendored") is True and not entry.get("license_evidence"):
            errors.append(f"{label} needs license evidence before vendoring")
    return errors


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = validate(manifest)
    print(
        f"External COBOL candidates: {len(manifest.get('entries', []))}; "
        f"validation errors: {len(errors)}"
    )
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("Metadata is structurally valid; this does not imply compilation or equivalence.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
