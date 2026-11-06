# Seven hypotheses for a major external-equivalence gain

Status: research and experiment design; no translator behavior is changed by this document.

Baseline: `main` at `d13c0a3eca572b53f5503b4bf0dc9c3e97dcc8dd`, after PR #345.
Latest verified paired result available when this plan was prepared: 255/500 primary and 255/500 holdout (51.0% each). These are the iterative X-COBOL v2 samples; the holdout has been used during development and is not an untouched statistical holdout.

## Objective

Find a small set of semantic changes with a large net effect on the fixed external 500+500 corpus. The objective is not to maximize syntax coverage in the abstract. It is to recover complete, currently failing programs while preserving every currently passing case.

This is deliberately a seven-hypothesis research portfolio, not a claim that all seven changes are already implemented or that any percentage gain is guaranteed.

## Translator findings that motivate the hypotheses

The current translator is concentrated in `cobol2py.py`:

- `CobolVar` stores one `depending_on`, one primary `indexed_by` plus a list of index names, and one ascending key. It does not yet represent all table dimensions, active lengths, and key clauses as a complete semantic model.
- `build_tree()` and `translate_nodes()` handle several structured statements, but EVALUATE emission currently translates one subject and iterates individual WHEN branches.
- `translate_statement()` contains targeted handlers for arithmetic, STRING, UNSTRING, INSPECT, and file I/O. Unsupported statements can fall through to a comment such as `# COBOL no traducido`, which is not an executable equivalent.
- `parse_file_specs()` models a limited set of SELECT/FD metadata; there is no general multi-program CALL/LINKAGE execution model.
- `OCCURS DEPENDING ON` is explicitly diagnosed as unsupported for active-length semantics; storage is currently allocated to the maximum occurrence count.
- The expression translator has a broad intrinsic-function rewrite pipeline, but arithmetic receiver semantics, rounding, and size-error handling are not universally equivalent to COBOL.

## Seven hypotheses

### H1 — SORT and MERGE as record-processing operations

**Gap:** There is no dedicated SORT or MERGE implementation in the current statement translator.

**Hypothesis:** A bounded implementation of common file/table SORT and MERGE forms can recover complete programs, especially when they sort records using one or more keys.

**Scope to investigate:** `SORT`, `MERGE`, `USING`, `GIVING`, `INPUT PROCEDURE`, `OUTPUT PROCEDURE`, `RELEASE`, `RETURN`, ascending/descending keys, and sort collating behavior.

**Semantic traps:** Do not replace every SORT with Python `sorted()`. Input/output procedures have side effects; records can be released and returned incrementally; duplicate-key order and collating sequence matter.

**Candidate tests:** in-memory table sort; file sort; multiple keys; descending key; input/output procedure; empty input; duplicate keys.

**Existing tracker:** issue #123 covers SORT with INPUT/OUTPUT PROCEDURE. Reuse or update it rather than creating duplicate work.

### H2 — CALL, parameter passing, and LINKAGE SECTION

**Gap:** No general CALL statement implementation was found in the statement translator, and the program model has no general subprogram invocation/parameter-binding layer.

**Hypothesis:** Supporting static CALL and common parameter-passing forms can turn otherwise incomplete multi-program test cases into runnable translations.

**Scope to investigate:** literal and identifier program names; `USING`; `BY REFERENCE`; `BY CONTENT`; `BY VALUE`; `RETURNING`; `ENTRY`; LINKAGE SECTION declarations; nested calls and return codes.

**Semantic traps:** REFERENCE must preserve aliasing; CONTENT must isolate the passed value; VALUE follows platform/compiler conventions; storage lifetime and nested calls must be explicit. Never silently emulate unsupported dynamic loading.

**Candidate tests:** mutate a caller field by reference; prove CONTENT does not mutate caller storage; return a scalar; nested call; missing subprogram diagnostic; parameter count/type mismatch.

### H3 — EVALUATE ALSO with positional multidimensional matching

**Gap:** The current EVALUATE emitter evaluates a single subject and handles WHEN branches one at a time. It does not model multiple subject/object positions as a tuple.

**Hypothesis:** Correct positional EVALUATE ALSO support can recover decision-table programs with limited changes to the existing control-flow representation.

**Scope to investigate:** multiple ALSO subjects; multiple ALSO objects; `ANY`; `WHEN OTHER`; ranges and relational selection objects; mixed numeric/alphanumeric subjects.

**Semantic traps:** Every WHEN object must match its corresponding subject position. ANY is a wildcard for one position, not for the whole tuple. Evaluate each subject once, preserving COBOL's selection semantics.

**Candidate tests:** two and three subjects; ANY in first/middle/final position; mixed literals and identifiers; THRU ranges; WHEN OTHER; no-match behavior.

**Existing tracker:** issue #122. Keep its acceptance criteria aligned with this plan.

### H4 — SEARCH (serial) and complete table-index semantics

**Gap:** SEARCH ALL exists only for a restricted indexed-table shape. A complete serial SEARCH path and richer index/key metadata are missing.

**Hypothesis:** Extending table metadata and implementing serial SEARCH can unlock a wider family of table-processing programs than adding isolated statement aliases.

**Scope to investigate:** `SEARCH`; `WHEN`; `AT END`; index initialization and advancement; nested OCCURS dimensions; multiple INDEXED BY names; ascending/descending keys; qualified key references.

**Semantic traps:** COBOL indexes are not ordinary one-based numeric subscripts. SEARCH ALL requires sorted data and a valid key condition; do not use binary search when those preconditions are not established. Preserve the distinction between an index and a subscript.

**Candidate tests:** first/middle/last hit; no hit; AT END; nested table; multiple indexes; SEARCH ALL precondition failures; key qualification.

### H5 — OCCURS DEPENDING ON active length

**Gap:** The translator currently allocates maximum storage and emits `OCCURS_DEPENDING_ON_UNSUPPORTED` because active-length semantics are not implemented.

**Hypothesis:** Representing active length explicitly and enforcing it at every relevant operation can recover variable-length table and record programs.

**Scope to investigate:** initial active length; changes to the depending item; reference modification; MOVE/INITIALIZE; SEARCH; file record layouts; nested and group OCCURS DEPENDING ON.

**Semantic traps:** Maximum allocated capacity is not the same as active occurrence count. Access beyond active length, initialization, group moves, and serialization must follow COBOL rules. Do not globally truncate arrays based on one stale counter.

**Candidate tests:** zero/minimum/maximum active count; counter changes after population; nested variable-length group; out-of-range access; interactions with REDEFINES and file records.

### H6 — Token-aware COPY REPLACING and REPLACE preprocessing

**Gap:** COPY expansion exists, but replacement handling is bounded and uses textual substitution. There is no complete scoped REPLACE directive implementation.

**Hypothesis:** A token-aware preprocessor will correctly expand a wider range of real copybooks and avoid substitutions inside literals or unrelated identifiers.

**Scope to investigate:** pseudo-text delimiters; word replacement; partial-word replacement; continuation lines; nested COPY; REPLACING LEADING/TRAILING; REPLACE OFF and scope boundaries.

**Semantic traps:** Replacement is not arbitrary global string replacement. Respect token boundaries, literals, comments, pseudo-text, and the compiler's replacement scope.

**Candidate tests:** identifier replacement; PIC clause replacement; quoted literal containing the old token; nested copybook; repeated replacement; REPLACE OFF; fixed-format continuation.

**Existing tracker:** issue #96 covers pseudo-text COPY REPLACING. Expand that issue rather than creating a duplicate.

**Benchmark caveat:** This may improve real-world source compatibility more than the current external score. If the benchmark filters programs that fail GnuCOBOL compilation or omits their copybooks, some COPY improvements will not change the measured denominator.

### H7 — COBOL arithmetic result semantics: ROUNDED and SIZE ERROR

**Gap:** Arithmetic verbs are recognized, but the implementation does not guarantee full COBOL receiving-field, rounding, and size-error semantics. Existing diagnostics already flag partial numeric PIC semantics.

**Hypothesis:** Centralizing arithmetic result conversion by receiving PIC and adding explicit ON SIZE ERROR behavior can recover complete numeric programs and fix cascading output mismatches.

**Scope to investigate:** ADD/SUBTRACT/MULTIPLY/DIVIDE/COMPUTE; GIVING; REMAINDER; ROUNDED; ON SIZE ERROR; NOT ON SIZE ERROR; signed and scaled PIC; truncation and decimal precision.

**Semantic traps:** Python float is not a universal substitute for COBOL decimal arithmetic. Rounding mode, intermediate precision, receiver truncation, sign, implied decimal, and size-error conditions must be derived from the receiving item and compiler semantics.

**Candidate tests:** positive/negative ties; scale reduction; overflow/underflow; signed receiver; multiple receivers; remainder; ON and NOT ON SIZE ERROR; arithmetic with intermediate expressions.

**Related evidence:** PR #344 identified NIST arithmetic cases that still failed because the complete programs also use ON SIZE ERROR and/or ROUNDED. Its narrow literal-dividend change did not establish a casewise gain against the historical holdout baseline.

## Prioritization

The order below balances likely score impact, implementation cost, and the ability to isolate semantics. It is a research order, not a prediction of percentage gain.

1. H3 EVALUATE ALSO — bounded parser/emitter change and direct tests.
2. H4 SEARCH and table-index semantics — likely reusable across multiple programs.
3. H7 arithmetic result semantics — high leverage, but requires exact decimal behavior.
4. H1 SORT/MERGE — currently absent, but procedure semantics make it larger.
5. H5 OCCURS DEPENDING ON — requires a coherent active-length model.
6. H2 CALL/LINKAGE — potentially high impact, but requires cross-program runtime design.
7. H6 COPY/REPLACE — high practical value; benchmark impact depends on corpus packaging.

## Experimental protocol

### Phase 0 — Freeze and census

- Record the exact base SHA and current baseline reports.
- Download the pinned X-COBOL v2 archive used by the existing workflow.
- Build a read-only census of the 1,000 fixed cases. For each hypothesis, report matching case IDs, source evidence, whether the baseline failed, and whether the source actually reaches the translator.
- Do not change corpus selection, filters, denominator, expected outputs, timeouts, or benchmark runner.
- Distinguish syntactic presence from a demonstrated root cause. A statement appearing in a failing source does not prove it caused the mismatch.

### Phase 1 — Isolated candidates

- Implement each hypothesis on an isolated candidate branch or commit.
- Add focused unit tests and differential fixtures against GnuCOBOL.
- Run the full unit suite and Python compilation.
- Measure the exact same primary and holdout IDs, with the same archive checksum and runner configuration.
- Store SHA, report JSON, source case IDs, and per-case outcomes for every candidate.

### Phase 2 — Select and combine

- Compare each candidate against the same-run main baseline, not a historical score from another run.
- Report improved, regressed, and unchanged IDs separately for primary and holdout.
- Reject any candidate with unexplained regressions or incomplete evidence.
- Combine only candidates that show independent gains; re-run the complete suite and paired benchmark after combination to detect interactions.

### Phase 3 — Promotion gate

A combined candidate is eligible for merge only when:

- All unit tests and compilation checks pass.
- Both 500-case samples are complete and checksum-verified.
- The tested SHA equals the PR head SHA.
- Every score is computed from the fixed 500 IDs per sample.
- There are zero casewise regressions against the same-run main baseline.
- Net gains are attributable to translator behavior, not corpus, timeout, filtering, or evaluator changes.
- The report includes every changed prediction and the exact source/semantic reason.

## Explicit non-goals

- No change to benchmark corpus, selection, filtering, expected outputs, or denominator.
- No relaxing exact-match requirements.
- No replacing unsupported semantics with comments or silent approximations.
- No promotion based only on aggregate score.
- No merge based on a single historical comparison.
- No claim that these hypotheses guarantee a 75% score.

## Existing work to avoid duplicating

At preparation time, open work already covers several neighboring areas, including STRING/UNSTRING/INSPECT, file I/O, ACCEPT/DISPLAY, reference modification, and the narrow DIVIDE literal case. Before implementation, re-check open PRs and rebase or extend their work where scopes overlap. In particular, do not duplicate #329–#343 or treat #344 as an arithmetic-semantics implementation.

## References

- IBM Enterprise COBOL Language Reference: https://www.ibm.com/docs/en/cobol-zos/6.4.0
- IBM SORT statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-sort-statement
- IBM MERGE statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-merge-statement
- IBM CALL statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-call-statement
- IBM EVALUATE statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-evaluate-statement
- IBM SEARCH statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-search-statement
- IBM COPY statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-copy-statement
- IBM REPLACE statement: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=statements-replace-statement
- IBM arithmetic result assignment: https://www.ibm.com/docs/en/cobol-zos/6.4.0?topic=items-assigning-arithmetic-results
