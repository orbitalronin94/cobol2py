# 30-seed failure-directed repair tournament

**Status: blocked — the 30 candidate refs exist, but none is currently a valid candidate against current main.**

## Main baseline and remeasurement

- Historical main reference: **257/500 (51.4%)**, [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592), translator SHA `393b6f5d98eb0a0f2f1af41eb5d937e6bb274d28`.
- Later main remeasurement: **258/500 (51.6%)**, [run 42272058313](https://github.com/orbitalronin94/cobol2py/actions/runs/42272058313), frozen SHA `3485bbd36daee6c3c2319d204bf33fddac6a32a4`.
- These two reports use the same 500 case IDs, X-COBOL v2 archive MD5 `cbd974caed72b0836777dc2305928ed3`, `skip=500`, `target=500`, and exact stdout-byte plus process-return-code comparison. Both samples are complete and checksum-verified.
- The only changed case is `exec84-2-03eae98697`: translator timeout at 20.003376s in the 257 report, versus a completed translation at 19.109681s in the 258 report. This is timeout-boundary variance, not evidence of a translator improvement. Keep **257/500 as the historical reference** and **258/500 as a separate main remeasurement**; do not collapse them into a new record.
- The **258/500 in run 42266714599 is an experimental-branch result**, not a main baseline.
- Main SHA audited on 2026-11-10: `c80f7f2252e0637fde3a987f7991cbc6bdd98b5e`. Compared with the frozen 30-seed baseline SHA `3485bbd36daee6c3c2319d204bf33fddac6a32a4`, main is two commits ahead. The changed files are the tournament workflow, manifest/README/test, and experiment protocol; no translator implementation file changed. The 258 remeasurement therefore remains the latest direct measurement of the unchanged translator implementation, subject to the single timeout variance above.

## Existing 16-candidate tournament — do not duplicate

[Run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592) contains a complete main holdout report (257/500) and **15 complete candidate holdout reports**, all using the same 500 case IDs. The run concluded `failure`; the `unstring-pointer` candidate's test job failed. No candidate passed the zero-regression gate.

- Candidate holdout scores ranged from **246/500 to 252/500**.
- Best score: `experiment-massive-16/open-mixed-modes-verified`, **252/500**, with 4 new passes but **9 regressions**.
- Its new-pass IDs were `exec84-2-03eae98697`, `rl105a-3725db9cec`, `rock-paper-scissors-ad6321acf1`, and `sq206a-3536dcf7c2`.
- Its regression IDs were `cep001-1f7cf0de31`, `ic233a-4698d35ce6`, `nc134a-58dbc1f548`, `nc134a-ff40dc4c31`, `nc135a-a977eda638`, `nc243a-04e83cd675`, `pnota-ac81563c54`, `progr2-ff3935a6eb`, and `smp001-ccd7110609`.

The 16-candidate artifacts already cover several adjacent hypotheses (file OPEN modes, sequential READ/WRITE/REWRITE, INSPECT REPLACING, STRING/UNSTRING, date/time ACCEPT, and arithmetic reference modification). Treat these as historical evidence, not as promotion-ready candidates; avoid rerunning the same stale snapshots.

## Audit of the 30-seed tournament

- [PR #349](https://github.com/orbitalronin94/cobol2py/pull/349) and [PR #350](https://github.com/orbitalronin94/cobol2py/pull/350) are merged. [PR #351](https://github.com/orbitalronin94/cobol2py/pull/351), merged 2026-11-10, hardened the 30-seed workflow and recorded the branch audit.
- The current workflow `.github/workflows/failure-directed-30-seed-tournament.yml` is manual-dispatch only. It freezes main and candidate SHAs, requires candidate ancestry, translator and test changes, runs the full 500-case holdout, and ranks by case ID with a strict zero-regression/+1 gate. It never promotes automatically.
- All **30 candidate branch refs exist**, but all 30 compare as **diverged** from audited main SHA `c80f7f2252e0637fde3a987f7991cbc6bdd98b5e`. Seeds 11–15 additionally have no translator implementation change and no test change relative to current main. Other branches are also stale; several sampled histories do not implement their declared manifest hypotheses.
- The manifest readiness flag is therefore `blocked`. The workflow deliberately exits before matrix execution while readiness is blocked. Do not dispatch it until all branches have been rebuilt from current main, with one isolated implementation hypothesis, a minimal reproducer/regression test, and a passing full suite.
- The previous attempt, [run 42272058313](https://github.com/orbitalronin94/cobol2py/actions/runs/42272058313), was **cancelled**. Its frozen-main baseline completed at 258/500, but only 9 candidate holdout reports were available (seeds 1–8 and 16). The best reported score was 236/500 with 5 gains and 27 regressions; no candidate was eligible. The other seeds failed, were cancelled, or lacked valid reports.
- The later [manifest validation run 42815007670](https://github.com/orbitalronin94/cobol2py/actions/runs/42815007670) and [main tests run 42815007686](https://github.com/orbitalronin94/cobol2py/actions/runs/42815007686) succeeded. These are validation/test runs, **not** a completed 30-seed tournament.
- [PR #352](https://github.com/orbitalronin94/cobol2py/pull/352) is an open documentation-only modernization strategy PR; it does not provide candidate benchmark evidence.

## Next work

1. Rebuild each of the 30 candidate branches on the current main SHA; do not merge stale branch snapshots.
2. Audit that each branch implements its exact manifest hypothesis and includes a minimal reproducer plus a regression test. In particular, seeds 11–15 currently lack translator/test changes.
3. Reuse the existing 16-candidate artifacts for overlapping file, STRING/UNSTRING, INSPECT and arithmetic hypotheses rather than creating duplicate experiments.
4. Investigate the malformed generated condition line `if filler_17['numeric_1'] == > (than == 0):` as a **hypothesis** for a condition-operator parser defect. Recover the exact source and make a minimal failing reproducer before changing the translator; the generated line alone is not a proven root cause.
5. Dispatch the 30-seed workflow only after readiness becomes `ready`. Re-run the full holdout against the then-current main SHA before any promotion. No winner, PR, merge, or benchmark-record update is currently justified.
