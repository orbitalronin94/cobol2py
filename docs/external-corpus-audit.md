# External COBOL corpus: source audit (work in progress)

Audit date: 2026-10-26. This is a **candidate ledger, not the final 100-program corpus**. No entry below is marked compile-validated or semantically equivalent. Sources remain upstream; this repository does not copy or redistribute them yet.

## Inclusion gates

1. Pin an immutable upstream commit and source path.
2. Verify the repository license and check whether individual files are third-party material.
3. Record source blob SHA, line count, dependencies/copybooks, compiler mode and execution fixtures.
4. Normalize line endings/trailing whitespace for a duplicate check, while retaining the original blob SHA.
5. Compile with a pinned GnuCOBOL version; classify compile failures separately from platform/dependency-blocked cases.
6. Compare translated Python syntax, stdout, stderr/return code and generated side effects when a deterministic fixture exists.
7. Count a program as an independent case only after content and provenance deduplication.

## Candidate source ledger

| Candidate | License checked | Pinned upstream commit | Source path | Lines | Source blob SHA | Current assessment |
|---|---|---|---|---:|---|---|
| COBOL Legacy Ledger — VALIDATE | MIT in repository LICENSE | `4ec2a1fd9a569fa694c384a6a06201f0045904b2` | [VALIDATE.cob](https://github.com/albertdobmeyer/cobol-legacy-ledger/blob/4ec2a1fd9a569fa694c384a6a06201f0045904b2/COBOL-BANKING/src/VALIDATE.cob) | 219 | `ed75f1c17253860ff5f3f59480c68a3a29369485` | Candidate; dependencies and runtime fixture pending |
| Banco-en-COBOL — BANCO | AGPL-3.0 in repository LICENSE | `7ea14ed7512e77cae43c0b837884f7bc76beec90` | [banco.cob](https://github.com/Mel-Roses/Banco-en-COBOL/blob/7ea14ed7512e77cae43c0b837884f7bc76beec90/banco.cob) | 1,583 | `9318ff8a94b597e7c54ace97540de8185809dbc1` | Candidate; AGPL attribution/license obligations and Linux reproducibility to be handled |
| Payroll Management System — PAYROLL | MIT in repository LICENSE | `433ea0074b4a90466136d41963b29abae69c4cfe` | [payroll.cbl](https://github.com/JAGADISHSUNILPEDNEKAR/Payroll_Management_System/blob/433ea0074b4a90466136d41963b29abae69c4cfe/payroll.cbl) | 639 | `586401b76eac3fa26d684eec56f0e57efa0b4c88` | Candidate; data files and execution fixture pending |
| Enterprise Financial Transaction Processor — TXNVAL00 | MIT in repository LICENSE | `5b328496120afbbc3e1bcadf60421598c19db2ea` | [TXNVAL00.cbl](https://github.com/ItsSNOWMOBILE/cobol-enterprise-txn-processor/blob/5b328496120afbbc3e1bcadf60421598c19db2ea/src/programs/TXNVAL00.cbl) | 812 | `5fb7579a856181f7a15cb8063c3f4885f86c3b35` | Strong batch candidate; pipeline copybooks and fixtures need to be assessed as a system |
| IBM StockTrader Cash Account — CASH00 | Apache-2.0 in repository LICENSE | `c35db0d1f283367109bcd5dfadd76560cf53b2dc` | [CASH00.cbl](https://github.com/IBMStockTrader/cash-account-cobol/blob/c35db0d1f283367109bcd5dfadd76560cf53b2dc/COBOL/CASH00.cbl) | 270 | `9c04a8d1db4673102fe0095fed8a63a96ac37b9d` | Likely not standalone GnuCOBOL: contains embedded SQL/CICS-oriented constructs; classify as dependency/platform-blocked unless a supported harness exists |
| COBOL Cashier — BANKLED | MIT in repository LICENSE | `3eb401ee417b01ee28d8e560b3c4330e3c4eccaa` | [BANKLED.cob](https://github.com/bitoiu/cobol-cashier/blob/3eb401ee417b01ee28d8e560b3c4330e3c4eccaa/src/BANKLED.cob) | 653 | `c69d3f839725a811f175ea066572bc3ea6a0ebd2` | Candidate; indexed-file/copybook setup and test fixtures pending |

## Important limitations

- These are six source candidates, not six proven independent benchmark cases. A source project may contain multiple programs that form one inseparable pipeline; the manifest must represent dependencies and suite membership.
- Line count is a triage signal, not a complexity score. We must inspect data divisions, control flow, file I/O, SQL/CICS/JCL, copybooks and actual business logic.
- License checks currently establish the license file present at the pinned repository revision; they do not independently prove authorship of every line. Check provenance notices before inclusion.
- GnuCOBOL availability alone does not make CICS/DB2/VSAM programs directly runnable. The benchmark must report such cases as blocked/non-evaluable, not as translator failures.
- No GnuCOBOL compile or differential run has been performed for these entries yet. Do not report pass rates from this candidate ledger.

## Reproducible compiler environment

Use a container/CI job with a pinned GnuCOBOL release and record `cobc --version`, OS image digest, compiler flags and environment variables in each report. GnuCOBOL is available through Ubuntu packages and supports executable builds with `cobc -x`; see the [GnuCOBOL FAQ](https://gnucobol.sourceforge.io/faq/) and [Ubuntu package listing](https://packages.ubuntu.com/gnucobol).

## Next gates

- [ ] Find and license-check enough additional source projects to exceed 100 *unique* cases before pruning.
- [ ] Pin and record every source revision, blob hash, license identifier and attribution.
- [ ] Resolve copybooks and multi-program dependencies without flattening away suite relationships.
- [ ] Add a script that compiles, runs, translates and compares each evaluable case in an isolated temporary directory.
- [ ] Publish counts for unique candidates, license-approved cases, compiled cases, executable fixtures, differential matches and blocked cases.
