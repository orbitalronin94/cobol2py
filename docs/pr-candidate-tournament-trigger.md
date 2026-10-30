# PR candidate tournament trigger

Start the corrected X-COBOL v2 candidate tournament against main at `462835451959dc25d93f7f73d565f45088744a86`.

Historical best: 414/1,000 exact matches (197/500 primary + 217/500 holdout).

Candidates: PR #58 fixed-format split data names; PR #59 INSPECT TALLYING BEFORE INITIAL; PR #60 screen-only ACCEPT clauses; PR #62 INSPECT REPLACING CHARACTERS; PR #63 ACCEPT FROM date/time.

Each PR's tests run at its own source SHA. Its translator/browser implementation patch is separately applied to the frozen main SHA, where the full unit suite and both exact 500-case samples run. The same-run main baseline is included. The workflow reports per-ID gains/regressions and preserves all diagnostics. No automatic merge.
