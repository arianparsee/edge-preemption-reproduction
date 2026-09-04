# Stage 15-M.1B publication and security audit

This Stage adds only the isolated proposed-method module, fixture-based tests,
one bounded workflow, a runner/validator, sanitized aggregate comparator
evidence and documentation.

The committed ASSUMP-054 comparator fixture is derived from the validated
artifact of Run `33872440661` and pins its artifact ZIP and pilot JSON SHA-256.
It contains no task identifier, raw edge, chromosome, workload, trace, local
path or environment metadata.

The workflow has `contents: read`, uses no secret, pins every Action to a full
commit SHA, runs one DK-P logical pair with two replays, and retains only the
sanitized aggregate result, validation report and checksum manifest for 14
days. It does not execute baseline, ASSUMP-046 repair-only or ASSUMP-054.

The official DK-P module, official Figure-6 result, workload seeds, GA settings,
pricing, lifecycle, pipeline and previously validated results are unchanged.

## Pre-publication gates

- 57 direct and related regression tests: passed.
- Ruff over the complete repository: passed.
- mypy over `src` and `scripts`: 120 source files, passed.
- workflow scope, full-SHA Action pins, one-job/two-replay contract, no baseline
  execution, bounded retention and absence of secrets: passed by static tests.
- `git diff --check`: passed.
- The sanitized ASSUMP-054 fixture was compared field-by-field with the stable
  checksum-verified Run `33872440661` pilot artifact: all identity, outcome,
  replay and Figure-6 fields matched.
- Secret signatures, credentials, personal paths and `.env` references in the
  publication set: none found.
- Largest changed publication file is the pre-existing traceability document;
  no raw result, PDF, archive or binary artifact is included.

## Publication set

- `.github/workflows/stage15m1b-one-auction-cooldown.yml`
- `docs/assumptions.md`
- `docs/stage15m1b_plan.md`
- `docs/stage15m1b_security_audit.md`
- `outputs/traceability_matrix_arxiv_v2.md`
- `scripts/run_stage15m1b_pilot.py`
- `scripts/validate_stage15m1b_public.py`
- `src/edge_reproduction/diagnostics/ga_instrumentation.py`
- `src/edge_reproduction/modified_methods/one_auction_cooldown_dkp.py`
- `tests/fixtures/stage15m1_assump054_reuse.json`
- `tests/unit/test_stage15m1b_contracts.py`
- `tests/unit/test_stage15m1b_cooldown.py`
