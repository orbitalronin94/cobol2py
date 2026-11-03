# H1 — Safe Python emission

Proposal-only draft. Evidence: 39 generated Python syntax errors in the latest 500-case failure report. Hypothesis: unsupported or partially parsed COBOL tokens reach the emitter and create invalid Python.

Implementation: trace generated syntax diagnostics to parser/emitter boundaries; emit explicit comments/diagnostics for unsupported fragments; preserve valid block structure and source locations. Do not apply blanket regex rewrites.

Tests: minimized fixtures for each confirmed syntax family, Python compile checks, and exact GnuCOBOL differential tests.

Gate: unchanged fixed 500-case sample (`skip=500`), baseline 250/500, minimum 251/500, complete tests, checksum verified, exact candidate SHA. No score improvement is claimed by this draft.