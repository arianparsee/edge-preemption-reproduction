# Stage 15-H.1 pre-dispatch security audit

Date: 2026-08-21
Scope: technical recovery of failed Stage 15-H Run 31847136180

Stage 15-H.3 update: replace expired Stage 15-D.1/15-E sources with the
validated consolidated reuse artifact from Run 31847136180.

## Scientific boundary

- No workload, policy, seed, GA setting, repair rule, lifecycle rule, or aggregation rule changed.
- The only instrumentation change permits the already-requested `stage15h` diagnostic label.
- The artifact change adds complete REST pagination and safe ZIP extraction for pinned GitHub run artifacts.
- The consolidated 20-pair reuse ZIP is hard-pinned to SHA-256 `302b6b88083d51c84bd14abbf7415466b91b81f48bd32d120f19188080a4bc8b` before extraction.
- No baseline or successful repair pair is recomputed by the local validation.

## Local validation

- Targeted unit tests: 13 passed.
- Ruff: passed.
- mypy: passed for all changed Python source files.
- Fresh matrix: 100 unique logical pairs across batch IDs 1 through 5.
- ZIP traversal rejection, second-page artifact discovery, exact-name selection, and fixed prefix/suffix selection are covered by tests.

## Publication inventory

Only the following sanitized paths are approved for this commit:

- `.github/workflows/stage15h-thirty-workload-repairs.yml`
- `scripts/download_github_run_artifacts.py`
- `scripts/prepare_stage15h_matrix.py`
- `src/edge_reproduction/diagnostics/ga_instrumentation.py`
- `tests/unit/test_download_github_run_artifacts.py`
- `tests/unit/test_stage15b_ga_instrumentation.py`
- `tests/unit/test_stage15h_support.py`
- `docs/stage15h1_security_audit.md`

The pre-existing `.gitignore` modification and local pytest directories are excluded.

## Security result

- No credential, token value, `.env` content, source PDF, raw workload, task trace, chromosome, archive, or large artifact is included.
- The workflow refers only to GitHub's ephemeral built-in `${{ github.token }}` under `actions: read`; it introduces no secret.
- All third-party Actions remain pinned to full commit SHAs.
- The downloader restricts requests to the pinned repository/run, does not record the token, validates an available GitHub digest, rejects traversal and symbolic links, and permits at most one transient retry per job invocation.
- Artifact retention remains 14 days and repository permissions remain `contents: read` plus `actions: read`.
