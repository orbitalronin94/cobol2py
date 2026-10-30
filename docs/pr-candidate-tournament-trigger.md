# PR candidate tournament trigger

This marker starts the second X-COBOL v2 equivalence tournament.

Frozen base: `c2a4dd60edff66429d41d90a44f52d6f3f85ec6a` (latest main, including PR #66 workflow only).

Historical best: 414/1,000 exact matches (197/500 primary + 217/500 holdout).

Candidates are measured as isolated translator/test/browser patches applied to this frozen base:
- PR #58 — fixed-format split data names
- PR #59 — INSPECT TALLYING BEFORE INITIAL
- PR #60 — screen-only ACCEPT clauses
- PR #62 — INSPECT REPLACING CHARACTERS
- PR #63 — ACCEPT FROM date/time

The workflow also reruns the unmodified main baseline. No candidate is automatically merged; scorecards and failure diagnostics are retained for manual review.

Workflow correction merged in PR #68: each PR's own tests run at its source SHA; only translator and browser implementation files are transplanted onto the current-main baseline. This commit re-triggers the corrected tournament.
