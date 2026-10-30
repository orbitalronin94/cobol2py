# PR candidate tournament trigger

Final corrected run against main `c0b318955967cf8cfd80ff13ee25107f0a5b6daf`.

Historical best: 414/1,000 (197/500 primary + 217/500 holdout).

Candidate PRs: #58 fixed-format split data names; #59 INSPECT TALLYING BEFORE INITIAL; #60 screen-only ACCEPT; #62 INSPECT REPLACING CHARACTERS; #63 ACCEPT FROM date/time.

The workflow validates each PR's own regression suite, applies only its translator/browser source delta to this main SHA, runs integrated tests, and executes exact primary + holdout samples. It compares exact IDs against a same-run main baseline and keeps all diagnostics. No candidate auto-merges.
