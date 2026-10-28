# External corpus benchmark (500 real-world COBOL sources)

The repository's checked-in regression manifest is intentionally curated. This optional
benchmark adds an independent, larger corpus without copying third-party source code into
this repository.

## Source

- **Dataset:** [X-COBOL v2 — A Dataset of Open-Source COBOL repositories](https://zenodo.org/records/14269462)
- **Published scope:** 5,195 COBOL files from 168 repositories.
- **Archive:** `COBOL_Files.zip`, downloaded at run time and checked against the published archive MD5 recorded in `run_external_corpus.py`.
- **Source files:** only extracted into temporary storage; reports retain relative archive paths and SHA-256 hashes, not the source text.

Open-source availability of a dataset does not automatically grant the same license to every file it contains. Treat the corpus as evaluation-only, check individual upstream licenses before reuse or redistribution, and do not commit the downloaded archive or extracted files.

## Run it

On pull requests that change the translator or benchmark, the workflow runs two samples in parallel. You can also launch **Actions → external-cobol-corpus → Run workflow** and keep the target at `500`. The workflow downloads an external archive and runs programs from third-party repositories.

The job builds a small Docker image with Python and GnuCOBOL, then runs the test process with:
- network disabled;
- the checkout mounted read-only;
- Linux capabilities dropped and privilege escalation disabled;
- memory, CPU, process-count, and per-process timeout limits;
- no GitHub token or application secrets passed into the test container.

This is a defense-in-depth sandbox, not a claim that arbitrary code execution is risk-free. Review the workflow and source-provenance policy before enabling it in any fork or environment with secrets.

## Selection and scoring

1. Verify the downloaded archive checksum before extracting it.
2. Extract only safe, ordinary ZIP entries and consider `.cbl`, `.cob`, and `.cobol` files up to 1 MB.
3. Deduplicate identical source contents and order candidates deterministically by SHA-256.
4. The primary sample tests the first 500 eligible programs in that order. The disjoint holdout skips those first 500 eligible programs, then tests the next 500, using the same eligibility rules.
5. Count only standalone files that compile with the installed GnuCOBOL and whose reference run terminates within the timeout toward the requested sample size.
6. A tested program passes only when translated Python has **exactly the same stdout and process return code** as the GnuCOBOL executable.

The report separately records how many files were discovered, screened, rejected by reference compilation, excluded because the reference timed out, and actually compared. If fewer than 500 executable standalone sources can be selected, the run fails as incomplete rather than presenting a smaller sample as 500.

## Latest confirmed measurement

The latest fully completed 500 + 500 run is [workflow #40760502862](https://github.com/orbitalronin94/cobol2py/actions/runs/40760502862), measured at commit `0f8817709d3baaaecc7b15c022e6ea7ab96f2542`.

| Sample | Exact matches | Accuracy |
|---|---:|---:|
| Primary (first 500 eligible programs) | 173/500 | 34.60% |
| Disjoint holdout (next 500 eligible programs) | 196/500 | 39.20% |
| Combined (both samples) | 369/1,000 | 36.90% |

The immediately preceding complete run, [workflow #40757950854](https://github.com/orbitalronin94/cobol2py/actions/runs/40757950854), scored 162/500 primary and 184/500 holdout (346/1,000 combined, 34.60%). The measured gain is **23 additional exact matches, or +2.30 percentage points combined**: +11 in primary and +12 in holdout. Compared with [workflow #40753902144](https://github.com/orbitalronin94/cobol2py/actions/runs/40753902144) at 344/1,000 (34.40%), the increase is **25 exact matches (+2.50 percentage points)**. Against the earlier 291/1,000 (29.10%) reference, the increase is 78 exact matches (+7.80 percentage points).

**Commit caveat:** newer development revisions have not yet been validated by a completed external run. Workflow [#40761767797](https://github.com/orbitalronin94/cobol2py/actions/runs/40761767797) is still in progress on commit `e62d8873c48157a2abed7e468894e380e310307f`, which is not the current branch head. Do not attribute 36.90% to later commits until both samples complete for the relevant SHA. A green workflow means the benchmark executed successfully; it does not mean all translated programs matched.

## Interpretation limits

- This is a deterministic sample from X-COBOL, not a representative random sample of all COBOL installations or dialects.
- Standalone compilation and execution filters out copybook-only files, modules, programs requiring external transactions/databases, and programs that need input or files not supplied by the harness.
- No stdin is supplied; programs requiring interactive input may be excluded by timeout or may behave differently from production.
- Exact stdout and exit status do not establish file side-effect equivalence, numeric behavior for all inputs, performance, security, or business correctness.
- The 500-program score must be reported alongside the screened/excluded counts and the corpus revision. Do not combine it with the existing curated fixture score into one headline percentage.

## Output

The workflow uploads a separate `external-corpus-report.json` and `external-corpus-report.md` artifact for each sample (primary and holdout) with 90-day retention. It never uploads the source archive or extracted source files. The workflow's success status means the requested sample was measured successfully; it does **not** mean every translated program passed. Candidate mismatches are counted in the report so we can establish the baseline. The run fails only if it cannot reach the requested sample size or the benchmark infrastructure fails.
