# MIT-100 COBOL corpus

This directory vendors a pinned snapshot of **100 distinct COBOL `PROGRAM-ID` units** from CobolCraft, a substantial COBOL Minecraft server implementing world persistence, packet handling, command dispatch, registries, physics, loot tables, player/world state and related features.

- Source project: https://github.com/meyfa/CobolCraft
- Audited snapshot used for this import: https://github.com/billybillymc/masquerade-cobol/tree/685c484124ffeb1f6a06447c54ed55ea152ec13b/test-codebases/cobolcraft
- Snapshot commit: `685c484124ffeb1f6a06447c54ed55ea152ec13b`
- License: MIT; the source project's own `LICENSE` is preserved in this directory.
- Inventory: [manifest.json](manifest.json) lists exactly 100 unique program IDs, the vendored file path, upstream source blob SHA, line count, commit and source URL.

## Important scope note

The 100 entries are distinct COBOL program units, not 100 independent applications. Several `PROGRAM-ID` units share a source file and call into shared copybooks, registries and runtime structures. The corpus deliberately retains that real-world modular context instead of pretending each unit is standalone. Some units are helper routines; complexity comes from the broader system and its cross-module behavior, so the manifest is a reproducible source inventory rather than a claim that every individual unit is large.

## Validation status

- [x] Exactly 100 distinct `PROGRAM-ID` values in the manifest.
- [x] Source files copied from one pinned snapshot; original MIT license included.
- [x] Source blob SHA and line count recorded per source file in the manifest.
- [x] Added `tools/audit_mit100.py` to inventory source files, list `COPY` dependencies and static `CALL` targets, and emit JSON/Markdown reports.
- [ ] Dependency/copybook closure completed.
- [ ] GnuCOBOL compilation executed in a pinned environment and results reviewed.
- [ ] Translator output and runtime behavior differentially compared.

Run the current static/dependency audit with:

```bash
python tools/validate_mit100_manifest.py
python tools/audit_mit100.py --json mit100-audit.json --markdown mit100-audit.md
```

When GnuCOBOL is installed, add `--compile` to attempt syntax checks for source files whose copybooks are present in the vendored corpus. The report distinguishes missing-copybook blockers from syntax errors; it does not run a behavioral differential test.

**No compilation or equivalence pass rate is claimed.** Missing copybooks/platform requirements must be reported as blocked, not counted as translator failures.

## Attribution

Copyright (c) 2024–2025 Fabian Meyer. The original MIT license is included at [LICENSE](LICENSE). The imported snapshot came through the pinned Masquerade repository revision listed above.
