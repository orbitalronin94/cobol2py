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

On pull requests that change the translator or benchmark, the iterative evaluation workflow runs only the fixed second half (`skip=500`, `target=500`) to reduce compute cost. The policy and its limitations are documented in [HOLDOUT_ONLY_EVALUATION_POLICY.md](../docs/HOLDOUT_ONLY_EVALUATION_POLICY.md). The `external-cobol-corpus` and `external-python-benchmark` workflows both run only this second half during iterative evaluation. The workflow downloads an external archive and runs programs from third-party repositories.

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
4. The historical primary sample tested the first 500 eligible programs. The fixed evaluation corpus skips those first 500 eligible programs and tests the next 500, using the same eligibility rules. The iterative candidate workflow now runs only this second half.
5. Count only standalone files that compile with the installed GnuCOBOL and whose reference run terminates within the timeout toward the requested sample size.
6. A tested program passes only when translated Python has **exactly the same stdout and process return code** as the GnuCOBOL executable.

The report separately records how many files were discovered, screened, rejected by reference compilation, excluded because the reference timed out, and actually compared. If fewer than 500 executable standalone sources can be selected, the run fails as incomplete rather than presenting a smaller sample as 500.

## Interpretation limits

- This is a deterministic sample from X-COBOL, not a representative random sample of all COBOL installations or dialects.
- Standalone compilation and execution filters out copybook-only files, modules, programs requiring external transactions/databases, and programs that need input or files not supplied by the harness.
- No stdin is supplied; programs requiring interactive input may be excluded by timeout or may behave differently from production.
- Exact stdout and exit status do not establish file side-effect equivalence, numeric behavior for all inputs, performance, security, or business correctness.
- The 500-program score must be reported alongside the screened/excluded counts and the corpus revision. Do not combine it with the existing curated fixture score into one headline percentage.
- Because the same fixed 500 programs are observed repeatedly while candidates are tuned, this score is not an untouched holdout estimate of generalization. Describe it as a fixed evaluation corpus and state the risk of overfitting.

## Output

The iterative Python workflow uploads `external-corpus-report.json` and `external-corpus-report.md` for the fixed evaluation corpus with 90-day retention. Historical workflows may still produce separate primary and second-half artifacts. It never uploads the source archive or extracted source files. The workflow's success status means the requested sample was measured successfully; it does **not** mean every translated program passed. Candidate mismatches are counted in the report so we can establish the baseline. The run fails only if it cannot reach the requested sample size or the benchmark infrastructure fails.
