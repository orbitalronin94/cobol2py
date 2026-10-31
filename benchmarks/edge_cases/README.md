# COBOL edge-case corpus

50 standalone COBOL programs targeting arithmetic precedence, decimal semantics, group moves/REDEFINES, strings, and control flow.

The best documented original-corpus baseline is **480/1,000 (48.00%)**: primary 244/500, holdout 236/500 (PR #177; root README). The adjacent manifest records the corpus, not successful compilation. Compile with GnuCOBOL and capture reference stdout/exit status before scoring.

Keep the original 500 + 500 score separate from the 50-case edge corpus. Do not mix denominators or compare a 1,050-case score directly with the 1,000-case baseline. This branch does not claim the monolithic refactor or the `Maquinas` canary has been executed.
