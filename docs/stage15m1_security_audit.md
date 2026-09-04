# Stage 15-M.1 publication and security audit

This document is completed before dispatch. The allowed publication surface is
limited to source code for the proposed method, fixture-based tests, a bounded
workflow and explanatory documentation.

Prohibited material:

- secrets, tokens, credentials and `.env` files;
- personal filesystem paths and sensitive environment metadata;
- source-paper PDFs, archives and large artifacts;
- raw baseline/workload files, task identifiers, detailed traces, raw
  preemption edges and chromosomes;
- overwritten official results or a changed Figure-6 classification.

The GitHub artifact contains only aggregate counters, hashed scientific
fingerprints, validation status and checksums. It has a 14-day retention limit.
The workflow uses `contents: read`, SHA-pinned official actions and no secret.

## Pre-publication result

- Clean base: `origin/main` at `04446d1ada50fa0c16190fb1aaa707b15f1eb620`.
- Official algorithm, simulation, workload/config, seed and result files changed:
  none.
- Comparator fixture changes: none; both existing fixtures are consumed
  read-only and their repository/source SHA-256 values are pinned by the runner.
- Direct and related tests: 42 passed.
- Full repository suite: 351 passed and 13 pre-existing/environment-dependent
  tests failed because ignored Southampton/Stage-14A artifacts are absent and
  old Stage-13J contract tests no longer match the already-approved workflow.
  None of those failures touches Stage 15-M.1.
- Ruff: passed.
- Mypy for all `src` plus Stage-15M runner, validator and tests: passed (64
  source files). The broader historical `tests` tree retains 14 unrelated
  pre-existing typing findings and was not modified.
- `git diff --check`: passed.
- Official paper/workload execution performed locally: none.
