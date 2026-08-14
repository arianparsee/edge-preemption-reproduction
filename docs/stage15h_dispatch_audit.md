# Stage 15-H — pre-dispatch audit

## Scientific scope

- Status: user-approved **[آزمون کمکی]** 30-workload validation.
- Variants: initialization-only repair (ASSUMP-045) and offspring-only repair
  (ASSUMP-046), independently applied to DK-R and DK-P.
- Fixed penalty, combined repair, parameter tuning and baseline recomputation are
  excluded.
- The official Pipeline DK implementation and the Stage 13-J/13-K and Stage
  14-A Figure-6 artifacts are not overwritten. Figure 6 remains **not
  reproduced**.

## Reuse gate before dispatch

- Stage 13-J/13-K run `31644121025`: 120/120 baseline pairs and 30/30 workloads
  passed the existing stable-artifact audit. Exact result/workload SHA-256 values
  are pinned in `configs/experiments/stage15h_baseline_reuse_manifest.json`.
- Stage 15-D.1 run `31716969817`: the four seed-one repair artifacts match the
  committed reuse fixture and the new pinned manifest byte-for-byte.
- Stage 15-E run `31729227438`: 16/16 new repair artifacts plus the four reused
  Stage-15D.1 pairs reconstruct the previously validated 20/20 matrix. Exact
  hashes, workload seeds, policy seeds, variants and artifact patterns are
  pinned in `configs/experiments/stage15h_repair_reuse_manifest.json`.
- No policy, simulator or workload was executed during this reuse audit.

## Planned cloud execution

- New logical pairs: `25 workloads × 2 repairs × 2 DK policies = 100`.
- Each logical pair performs two exact same-seed replays inside one job.
- Matrix policy: `max-parallel: 8`, `fail-fast: false`, 180-minute per-pair
  timeout and 14-day independent artifacts.
- Resume accepts a prior run ID and includes only pairs that pass the public
  schema, scientific flags and checksum validation. Missing/invalid pairs alone
  remain in the matrix.
- Baseline pairs are downloaded from pinned repository run `31644121025` and
  are never executed again.
- The final `if: always()` job refuses partial aggregation; an incomplete matrix
  produces only a completeness report.

## RNG boundary

Option A remains unchanged. Exact replay equality, initial policy-seed state,
final RNG state, primitive counts and call shape are required within each
variant. Historical Stage-13 baselines did not record full RNG/call-shape data;
therefore no unsupported variant-versus-baseline RNG equality claim is made.
This limitation is emitted explicitly in every pair and final report.

## Local validation

- Targeted unit/static suite: 21 passed.
- Ruff: passed.
- Mypy for new executable support scripts: passed.
- Fresh matrix construction: exactly 100 unique approved pairs.
- Partial-finalization guard: designed to emit `incomplete_not_aggregated` and
  fail before any partial mean is produced.

## Public-release audit

Publishable scope is limited to:

- the Stage-15H GitHub Actions workflow and dispatch sentinel;
- runner, reuse verifier, resume planner, public-pair validator and finalizer;
- two pinned non-sensitive checksum/config manifests;
- unit tests and this audit/traceability update.

Excluded from publication: source PDFs, raw workloads, task traces,
chromosomes, downloaded artifacts, archives, credentials, tokens, `.env`
files, local paths and environment metadata. The pre-existing user change in
`.gitignore` and inaccessible local pytest directories are deliberately not
staged.
