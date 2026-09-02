# Reproduction assumptions ledger

This ledger records only assumptions explicitly approved by the user. Technical
test fixtures are documented separately and are not attributed to the paper.

## Source-governance rule

- Baseline source: arXiv:2403.15665v2 (2024).
- The final IEEE 2025 version may be used only as
  `[منبع تکمیلی خارج از مبنای v2]` to analyze ambiguity.
- Any fact taken from the 2025 version must be recorded separately with its
  version and must not be attributed to arXiv v2 without an explicit label.
- Approved: 2026-08-10.

## ASSUMP-001 — Inclusive deadline boundary

- Status: approved
- Approved: 2026-08-09
- Evidence gap: arXiv v2 does not fully specify event ordering at the numerical endpoint.
- Approved interpretation: a task completing at `arrival_slot + deadline_slots` meets its deadline.
- Closest paper evidence: equation (11) uses `d_{j,d} <= d_j`.
- Scope: simulator deadline checks and earned-utility decisions.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-002 — Selected-server evaluation for equations (2)-(6)

- Status: approved
- Approved: 2026-08-09
- Evidence gap: the printed `forall i` quantifier makes nonzero flow incompatible with an unselected server.
- Approved interpretation: flow upper-bound and completion equalities are evaluated for the selected server only.
- Closest paper evidence: equation (19) assigns a task to at most one server and the prose repeatedly refers to the chosen server.
- Scope: mathematical validation, exact-model construction and simulator checks.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-003 — Normalized four-resource congestion

- Status: approved
- Approved: 2026-08-10
- Evidence gap: the prose and Algorithm 1 do not jointly provide an executable,
  bounded definition of `congestion(job, residual_resources)`.
- Approved interpretation: for storage, computation, upload and download, compute
  `min(demand_k / residual_k, 1)` and take the arithmetic mean of the four shares.
- Zero cases: a zero demand contributes zero; a positive demand with zero residual
  contributes one.
- Algorithm-1 pricing: `congestionFactor = 0.025 * (1 - congestion)`.
- Feasibility guard: a task larger than the server's total capacity enters the
  impossible branch before congestion is evaluated.
- Scope: Algorithm 1 Round-1 pricing only; the still-unspecified numerical price
  in the impossible branch is not supplied by this assumption.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-004 — Inclusive five-percent preemption threshold

- Status: approved
- Approved: 2026-08-10
- Evidence gap: the prose and printed Algorithm 2 place the factor `1.05` on
  different sides of the comparison.
- Approved interpretation: `new_ratio >= 1.05 * victim_ratio`, where
  `new_ratio = new_job.utility / new_job.deadline` and
  `victim_ratio = victim.utility / victim.time_remaining`.
- Boundary: exact equality at five percent is eligible.
- Scope: KnapsackGreedy Preemption.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-005 — At most one KnapsackGreedy victim

- Status: approved
- Approved: 2026-08-10
- Evidence gap: the Algorithm-2 loop could preempt multiple current tasks although
  the prose describes one victim.
- Approved interpretation: current tasks are examined in ascending
  `utility / time_remaining` order; the first task satisfying ASSUMP-004 and
  component-wise `new_job.space <= victim.space + residual_resources` is the
  sole victim for that incoming task.
- Scope: KnapsackGreedy Preemption only; this is explicitly not generalized to
  Double Knapsack Preemption.
- Remaining gap: tie-breaking between equal victim ratios is not defined by this
  assumption or arXiv v2.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-006 — Break and atomic single-victim replacement

- Status: approved
- Approved: 2026-08-10
- Evidence gap: Algorithm 2 omits a `break` after `Preempt` and `Add`.
- Approved interpretation: after the first successful preemption and admission,
  victim examination stops immediately.
- Atomicity: victim release and incoming allocation form one transaction; failure
  leaves resource accounting, allocations and task states unchanged.
- Scope: KnapsackGreedy Preemption.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-007 — Impossible-task sentinel price

- Status: approved
- Approved: 2026-08-10
- Evidence gap: arXiv v2, Section V-A1, page 6 states only that a task which can
  never fit receives a price greater than its utility.
- Approved interpretation: if at least one demand component exceeds total server
  capacity, set `price = math.nextafter(utility, math.inf)`.
- Meaning: the value is a branch sentinel, not an economic price.
- Failure behavior: if the result is not finite, fail fast and do not invent a
  fallback value.
- Scope: Round-1 server bid for an impossible task.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-008 — Strict empirical percentile

- Status: approved
- Approved: 2026-08-10
- Baseline evidence: arXiv v2, Section V-A1, page 6 describes the percentile as
  how a requesting task compares with current jobs by `utility/time_remaining`,
  but does not define empty sets or exact ties.
- Supplementary evidence: `[منبع تکمیلی خارج از مبنای v2]` final IEEE 2025
  version describes Percentile as the share of current jobs that the new task is
  better than.
- Approved interpretation: for a nonempty current-job set,
  `count(current_ratio < new_ratio) / count(all_current_ratios)`.
- Empty set: percentile is zero.
- Exact ties: equal ratios do not contribute to the numerator.
- Scope: Algorithm-1 Round-1 pricing.
- Provenance label: `[فرض بازتولید]`; the empty-set and tie behavior remain assumptions.

## ASSUMP-009 — KnapsackGreedy Retention Round 2

- Status: approved
- Approved: 2026-08-10
- Evidence gap: arXiv v2 states that non-preemptive Round 1 is unchanged but does
  not print an independent Round-2 Retention algorithm.
- Approved interpretation:
  1. admit all returning tasks carrying this server's `autoFit` mark;
  2. remove those tasks from the remaining set;
  3. inspect remaining tasks by descending `utility/time_remaining`;
  4. admit a task only if it fits the current four-dimensional residual vector;
  5. update residual resources immediately after every admission;
  6. reject a non-fitting task for the current Round 2 and continue;
  7. perform no preemption.
- Tie behavior: fail fast on equal sorting ratios; do not apply a hidden tie-break.
- Retry behavior: future-round retry remains unspecified and outside this assumption.
- Scope: KnapsackGreedy Retention only.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-010 — Fixed pre-Round-2 victim snapshot for KnapsackGreedy Preemption

- Status: approved
- Approved: 2026-08-10
- Evidence gap: arXiv v2 prose refers to currently-running jobs, while Algorithm 2
  does not state whether `s.jobs` is a snapshot or a live collection.
- Approved interpretation: immediately before admitting any current-round
  returning task, capture a fixed snapshot of tasks already active on the server
  from earlier rounds. Only this snapshot can supply victims during that Round 2.
- Membership rules:
  1. current-round `autoFit` admissions never enter the victim pool;
  2. other current-round direct admissions never enter the victim pool;
  3. snapshot membership remains fixed until that Round 2 ends;
  4. a snapshot member already preempted is skipped thereafter;
  5. newly admitted tasks are protected only in the current Round 2 and become
     ordinary running tasks in future time rounds.
- Ordering: snapshot tasks are ordered ascending by `utility/time_remaining`.
- Time semantics: each victim's `time_remaining` is captured at Round-2 start and
  remains constant because simulation time does not advance inside the auction.
- Ties: equal victim ratios fail fast; no hidden tie-break is applied.
- Preemption limit: ASSUMP-005 and ASSUMP-006 still restrict each incoming task to
  the first eligible single victim and stop immediately after success.
- Scope: KnapsackGreedy Preemption only; it does not apply to Double Knapsack.
- Difference from the earlier proposal: the core snapshot choice is unchanged,
  but this approved text additionally fixes membership, frozen time, removal,
  current-round protection and method scope.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-011 — Pipeline Double Knapsack pricing feasibility branch

- Status: approved
- Approved: 2026-08-10
- Evidence gap: reference [4], Algorithm 1, uses `Under threshold` and an
  arbitrary positive `beta` without defining the threshold or an executable
  value; arXiv v2 does not restate this branch.
- Approved interpretation:
  1. scope is Pipeline Double Knapsack Retention only;
  2. use the Case-3 pricing family from direct reference [4] with `alpha=0.1`;
  3. `Under threshold` means that the task is feasible by itself on the server's
     total four-dimensional capacity;
  4. an infeasible task receives
     `price = math.nextafter(utility, math.inf)`;
  5. the sentinel is not an economic price and a non-finite result fails fast.
- Relationship to ASSUMP-007: this explicitly extends its impossible-task
  sentinel semantics to Pipeline DK-R; it does not silently broaden ASSUMP-007.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-012 — Four-resource violation and workload-level scaling factor

- Status: approved
- Approved: 2026-08-10
- Evidence gap: direct reference [4], equation (11), has one bandwidth dimension,
  while arXiv v2 separates upload and download; neither source fixes an executable
  scaling factor for all v2 workloads.
- Approved interpretation:
  1. extend equation (11) to Storage, Computation, Upload and Download;
  2. for each dimension, use the new task's demand plus the aggregate demand of
     the proposed knapsack subset in the numerator and total server capacity in
     the denominator;
  3. compute `violation = 1 + f * sum(four_resource_ratios)`;
  4. compute `f = mean_utility - 1.1 * std_utility` exactly once from the complete
     workload before any auction and keep it fixed for that workload;
  5. for empirical data, calculate mean and standard deviation from the complete
     processed experiment workload, not from a per-round pool;
  6. record `f`, the utility statistics and calculation scope in experiment
     metadata;
  7. fail fast when `f` is non-finite or non-positive.
- Sensitivity analysis: later evaluate `f` independently under the label
  `[آزمون کمکی]`; it must not be presented as an original-paper result.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-013 — Official Pipeline DK-R genetic algorithm

- Status: conditionally approved
- Approved conditionally: 2026-08-10
- Approved requirements:
  1. the official Pipeline DK-R path uses a stochastic GA with 50 generations;
  2. before coding, audit direct pyeasyga reference [28] and extract the documented
     library version and settings for population, selection, crossover, mutation
     and elitism;
  3. record every GA setting and random seed in configuration and result metadata;
  4. if any required setting cannot be extracted, propose it as a new
     `[فرض بازتولید]` and obtain user approval before use;
  5. an Exact Solver is only `[ابزار کمکی]` for test-time feasibility and objective
     checks and must never be presented as the official paper implementation.
- Activation condition: this assumption cannot authorize implementation until
  the reference-[28] audit is complete and all required settings are sourced or
  separately approved.
- Scope: official Pipeline Double Knapsack Retention GA only.
- Provenance label: `[فرض بازتولید]` for the 50-generation choice and any later
  explicitly approved unsourced setting; source-derived defaults retain their
  direct-source provenance.
- Reference-[28] audit result (2026-08-10):
  - the 2016 reference aligns with pyeasyga release/documentation `0.3.1`;
  - documented defaults are population 50, crossover probability 0.8, mutation
    probability 0.2, elitism enabled and maximisation enabled;
  - source defaults are tournament selection with tournament size
    `population_size // 10`, one-point crossover, one-random-bit mutation and a
    random binary initial chromosome;
  - the official multidimensional-knapsack example overrides only population
    size to 200 and assigns fitness zero to infeasible chromosomes;
  - the paper does not identify whether it used the generic population default
    50 or the multidimensional example's value 200;
  - activation condition was satisfied by approval of ASSUMP-015 on 2026-08-10.
- Seed handling: pyeasyga uses Python's module-level `random` generator and has no
  constructor seed. The implementation must require an explicit caller seed and
  record it; it must not invent a hidden paper seed. Example/test seeds are
  `[آزمون کمکی]`, not claimed paper settings.

## ASSUMP-014 — Seeded tie handling for Pipeline DK-R

- Status: approved
- Approved: 2026-08-10
- Evidence gap: arXiv v2 and direct references [1] and [4] do not state a general
  tie rule. The worked v2 example on page 7 randomly selects one of two equal fit
  prices but does not define the distribution or seed.
- Approved interpretation:
  1. choose uniformly with a seeded RNG among servers sharing the lowest
     acceptable bid;
  2. canonicalize the GA input task order by task ID before stochastic execution;
  3. leave internal equal-fitness behavior to the audited GA library and record
     its seed and configuration;
  4. the auxiliary Exact Solver fails fast on multiple equal optima unless a test
     explicitly compares the full set of optimal solutions.
- Scope: Pipeline Double Knapsack Retention only.
- Provenance label: `[فرض بازتولید]`.

## ASSUMP-015 — Official Pipeline DK-R population configuration

- Status: approved
- Approved: 2026-08-10
- Evidence gap: pyeasyga 0.3.1 has a generic population default of 50, while its
  official multidimensional-knapsack example explicitly increases population to
  200. The paper and direct references [1] and [4] do not identify which value
  was used.
- Approved official configuration:
  1. `population_size = 200`;
  2. `tournament_size = 20`, derived from the audited pyeasyga behavior
     `population_size // 10`;
  3. `generations = 50` under ASSUMP-013;
  4. seed is a required input and has no hidden default;
  5. population size, tournament size, generations, seed and every GA setting
     are recorded in configuration and per-run result metadata;
  6. all other operators and settings come from audited pyeasyga 0.3.1 and their
     provenance is recorded explicitly.
- Sensitivity-only alternative: population 50 and tournament size 5 may be used
  only in an independent `[آزمون کمکی]` and must not be represented as the
  official paper configuration.
- Exact Solver: remains `[ابزار کمکی]` for test-time feasibility and objective
  comparison only; it is not the official GA path.
- Scope: official Pipeline Double Knapsack Retention only.
- Provenance label: `[فرض بازتولید]`.
- Implementation status (2026-08-10): implemented in
  `PyeasygaConfig`, `PyeasygaUtilityKnapsackSelector` and
  `PipelineDoubleKnapsackRetentionPolicy`. The official config rejects
  population 50, requires an explicit seed at construction, and serializes the
  complete GA/pricing configuration into each result's metadata.
- Verification status: unit, integration and fixed-seed repeatability tests pass;
  the Exact Solver is invoked only by tests and the hand-example report under
  the explicit `[ابزار کمکی]` label.

## Deferred decision — Batch Double Knapsack Retention

- Status: blocked by user decision
- Decided: 2026-08-10
- Reason: the success-count pricing formula is absent from available sources.
- Rule: do not invent a numerical Batch DK-R pricing formula. Keep Batch DK-R
  blocked until official code or another citable source supplies it.
- This is a scope/status decision, not a reproduction assumption.

## Approved assumptions — Pipeline Double Knapsack Preemption

The following assumptions were identified in the Stage-10H source audit and
approved exactly as proposed by the user on 2026-08-10.

### ASSUMP-016 — Atomic combined-pool Round-2 repacking

- Status: approved.
- Approved: 2026-08-10.
- Evidence gap: arXiv v2 Section V-B, PDF p.8 says to run a knapsack on total
  capacity over current plus returning jobs and then check individual jobs for
  fit by descending score, but does not define the mutable resource state used
  during that pass.
- Approved interpretation:
  1. snapshot active current jobs at Round-2 start;
  2. form one pool from that snapshot and this server's returning jobs;
  3. run the utility-maximizing knapsack on total server capacity;
  4. plan placement from an initially empty total-capacity residual vector in
     descending score order, updating the planned residual after every fit;
  5. a fitting current job is retained with its original allocation start; a
     fitting returning job is newly admitted;
  6. a non-fitting current job is preempted; a non-fitting returning job is
     rejected for this round;
  7. commit the complete plan atomically so an intermediate release/allocation
     failure cannot partially mutate the state.
- Scope: Pipeline DK-P only. It does not use the fixed single-victim snapshot of
  ASSUMP-010 and permits any number of current jobs to be preempted, as v2 states.
- Provenance label: `[فرض بازتولید]`.
- Implementation status (2026-08-10): implemented by planning against an empty
  total-capacity vector and committing releases/admissions only on a state snapshot.

### ASSUMP-017 — Literal score ordering and unresolved ties

- Status: approved.
- Approved: 2026-08-10.
- Evidence gap: v2 gives numerical scores `1000 + ratio` and `1 + ratio` and says
  knapsack members have first priority, but does not constrain the ratio domain
  or specify equal-score ordering.
- Approved interpretation:
  1. freeze `time_remaining` at Round-2 start and calculate
     `ratio = utility / time_remaining` for both current and returning jobs;
  2. calculate the two numerical scores literally as printed;
  3. sort by descending numerical score;
  4. fail fast on exact score ties rather than applying an unreported tie-break;
  5. fail fast if an out-of-knapsack score reaches or exceeds an in-knapsack
     score, because that contradicts the accompanying first-priority prose.
- Alternative not recommended: replace the printed score with an implicit
  lexicographic `(membership, ratio)` key. This enforces the prose but changes
  the explicit numerical definition.
- Provenance label: `[فرض بازتولید]`.
- Implementation status (2026-08-10): implemented with explicit equal-score and
  cross-tier-conflict tests; neither case receives a hidden fallback.

### ASSUMP-018 — Extend the audited DK genetic configuration to DK-P Round 2

- Status: approved.
- Approved: 2026-08-10.
- Evidence gap: v2 states that only Double Knapsack Round 2 changes but does not
  separately report its GA implementation or seed settings.
- Approved interpretation:
  1. keep the existing Pipeline DK-R Round 1 and ASSUMP-011/012/014/015 behavior;
  2. run the DK-P combined-pool Round-2 knapsack with the same audited
     pyeasyga 0.3.1 configuration: population 200, tournament 20, generations 50,
     crossover 0.8, mutation 0.2, elitism enabled and utility-maximizing fitness;
  3. use one mandatory seeded RNG stream for the complete auction and record all
     settings in result metadata;
  4. keep Exact Solver use auxiliary and test-only.
- Rationale: this is the narrowest extension of “only Round 2 must be changed,”
  but ASSUMP-013/015 were previously scoped only to Pipeline DK-R.
- Provenance label: `[فرض بازتولید]`.
- Implementation status (2026-08-10): implemented through one
  `PyeasygaUtilityKnapsackSelector` instance whose private seeded stream spans
  all servers and both rounds of the auction.

### ASSUMP-019 — Do not fabricate a DK-P Round-2 economic price

- Status: approved.
- Approved: 2026-08-10.
- Evidence gap: v2 Section V-B defines membership, score and allocation but no
  Round-2 price. Reference [4] prices only jobs accepted into its second
  knapsack, whereas DK-P may also accept a non-member during its gap-filling
  fit pass.
- Approved interpretation: record knapsack membership, score and final decision
  for every combined-pool job, but do not invent a numerical Round-2 economic
  price. A DK-P result therefore exposes an empty/absent final-price mapping
  unless a source-supported formula is later found.
- Alternatives:
  1. apply reference-[4] pricing only to knapsack members, leaving other accepted
     jobs without prices (mixed and incomplete semantics);
  2. apply it to all accepted jobs (unsupported extrapolation).
- Recommended option: explicit omission, because Round-2 price no longer affects
  server choice or the allocation outcome and fabricating one would reduce
  source fidelity.
- Provenance label: `[فرض بازتولید]`.
- Implementation status (2026-08-10): the DK-P result has no final-price mapping;
  its Round-2 `AuctionRound` intentionally has zero bids and metadata records the
  source-driven omission.

## Proposed assumptions — synthetic generators

ASSUMP-020 through ASSUMP-027 were identified by the Stage-11A audit and approved
exactly as proposed by the user on 2026-08-11. Full wording and alternatives are
recorded in `outputs/stage_eleven_a_synthetic_generator_gap_audit.md`.

### ASSUMP-020 — NumPy PCG64 with mandatory seed and named child streams

- Status: approved.
- Approved: 2026-08-11.
- Scope: Synthetic Normal and Synthetic Bimodal generation.
- No seed default may be presented as the paper seed.

### ASSUMP-021 — Independent marginal distributions

- Status: approved.
- Approved: 2026-08-11.
- Scope: independence across entities and all sampled fields.

### ASSUMP-022 — Rejection sampling and nearest-half-up integers

- Status: approved.
- Approved: 2026-08-11.
- Continuous physical quantities must be finite and positive; deadline must be
  at least one, and arrival count may be zero.

### ASSUMP-023 — Literal experimental-table units

- Status: approved.
- Approved: 2026-08-11.
- Use MB/MFlops/MB-per-second/slot exactly as printed in Tables I-II, with no
  hidden MB-to-GB conversion.

### ASSUMP-024 — Explicit workload envelope and inherited Bimodal arrivals

- Status: approved.
- Approved: 2026-08-11.
- Arrival/drain slots remain mandatory user config, while Bimodal reuses the
  Normal `N(14,4)` arrivals only under this assumption.

### ASSUMP-025 — Exact Bimodal quota with divisibility guard

- Status: approved.
- Approved: 2026-08-11.
- Require total jobs divisible by ten, allocate exact 90/10 labels, and shuffle
  them using a separate seeded stream.

### ASSUMP-026 — Allocation-layer-only synthetic records

- Status: approved.
- Approved: 2026-08-11.
- Do not fabricate output size or Normal high/low labels; do not represent the
  generated records as a complete pipeline/batch workload.

### ASSUMP-027 — Stable one-based generated identifiers

- Status: approved.
- Approved: 2026-08-11.
- Use zero-padded server/job identifiers in stable arrival/generation order.

### Implementation and verification status for ASSUMP-020 through ASSUMP-027

- Implemented: 2026-08-11 in `edge_reproduction.datasets.synthetic`,
  `edge_reproduction.datasets.artifacts`, `edge_reproduction.datasets.diagnostics`
  and `scripts/generate_synthetic.py`.
- Configuration status: `seed`, `arrival_slots`, `drain_slots` and all envelope
  fields are explicit JSON inputs; neither supplied auxiliary config is represented
  as the paper's unreported experiment horizon.
- Metadata status: NumPy version, PCG64, root seed, named child-stream order,
  distribution parameters, literal units, rounding rules, rejected-draw counts,
  omissions and exact Bimodal proportions are serialized per dataset.
- Verification status: unit/integration tests, moment diagnostics, exact 90/10
  mixture validation and a 22-file byte-for-byte rerun comparison pass.
- Scientific boundary: output size `s'_j` is not generated and these records are
  allocation-layer inputs only under ASSUMP-026.

## Southampton trace decision and surrogate assumptions

### Scope decision — real trace remains blocked

- Status: approved by the user on 2026-08-11.
- The official Southampton preprocessing path remains blocked because the raw
  trace and schema are unavailable.
- An approximate histogram surrogate is authorized only for technical testing
  and qualitative reproduction. It is not real trace data or a numerical
  reproduction of paper results.
- Published images, digitized geometry, generated surrogate rows and experiment
  results must be stored separately. Parameter tuning to make outputs resemble
  the paper plots is prohibited.

### ASSUMP-028 — visible-pixel-area empirical support

- Status: approved on 2026-08-12; implemented in Stage 12-C.
- Normalize connected-component `pixel_count` within each priority/resource,
  select a component with that weight, then draw uniformly between its digitized
  visible x bounds.
- Scope: approximate raster surrogate only; hidden/occluded mass is not inferred.

### ASSUMP-029 — explicit balanced diagnostic sample count

- Status: approved on 2026-08-12; implemented in Stage 12-C.
- Use an explicit `records_per_priority=10000`, yielding equal diagnostic counts
  for Low, Medium and High without claiming the trace's unknown class mix.

### ASSUMP-030 — conditionally independent visible marginals

- Status: approved on 2026-08-12; implemented in Stage 12-C.
- Sample storage and deadline independently conditional on priority; do not claim
  reconstruction of their unknown joint dependence.

### ASSUMP-031 — limited surrogate schema and omitted computation

- Status: approved on 2026-08-12; implemented in Stage 12-C.
- Generate only `surrogate_id`, `priority`, `storage_gb` and `deadline_hours`.
  Omit computation, arrival, Utility, bandwidth and output size. The artifact is
  therefore not an executable paper-workload input.
- Rationale: storage and computation rasters are identical below the title and
  the computation axis says Gigabytes, contradicting the MFlops system model.

### ASSUMP-032 — mandatory PCG64 seed without visual tuning

- Status: approved on 2026-08-12; implemented in Stage 12-C.
- Reuse the reproducibility policy of ASSUMP-020 with a mandatory seed and named
  independent streams, recording all settings in metadata. Never select a seed
  or parameter by similarity to the paper figure.

### Implementation and verification status for ASSUMP-028 through ASSUMP-032

- Implemented on 2026-08-12 in
  `edge_reproduction.datasets.southampton_surrogate`, its artifact/diagnostic
  modules and `scripts/generate_southampton_surrogate.py`.
- The auxiliary config explicitly records seed `20240812` and 10,000 records per
  priority. The seed is a technical reproducibility value, not a paper seed, and
  was not selected through visual or numerical fitting.
- Output records contain only `surrogate_id`, `priority`, `storage_gb` and
  `deadline_hours`; metadata explicitly sets `algorithm_input_compatible=false`.
- Twelve PCG64 child streams separate component selection from within-component
  sampling for each resource/priority pair.
- Published image, digitized geometry, generated records, aggregated diagnostic
  and figure paths remain separated.
- Six statistical checks target only the approved visible-area sampling law.
  Passing them does not validate or reconstruct the unavailable raw trace.

## Approved reproduction assumptions — Stage 13-D PIPE-NORMAL temporal engine

ASSUMP-033 through ASSUMP-041 were approved by the user on 2026-08-12 with the
final wording below. Every item is a `[فرض بازتولید]`; none is an explicit arXiv
v2 setting. The reproduction baseline remains the 2024 arXiv v2 paper.

Correction note: the prior `Selected model is at capacity` message was a service
availability interruption and is unrelated to paper-server capacity, `K_j`,
`C_i` or ASSUMP-036. None of these assumptions is inferred from that message.

### ASSUMP-033 — Repetitions, seeds and aggregation

- Status: approved `[فرض بازتولید]`.
- `repeat_count = 30`.
- `root_seed = 20240812`; this is only a technical reproduction seed and is not
  a paper seed.
- Create thirty independent seeds from `root_seed` with NumPy `SeedSequence`.
- Materialize the final sorted seed list in config before execution and record it
  in metadata.
- No hidden seed default is permitted.
- Generate one workload per seed and share that same workload across all four
  policies.
- Give each policy an independent named RNG stream.
- Preserve each raw `(seed, policy)` result separately.
- Aggregate the primary metric by arithmetic mean over the thirty runs.
- Report standard deviation and confidence interval only as `[آزمون کمکی]`.
- Never select a seed or repeat count to make results resemble a paper figure.

### ASSUMP-034 — Horizon and drain

- Status: approved `[فرض بازتولید]`.
- For the principal PIPE-NORMAL run under this assumption,
  `arrival_slots = 100`.
- This is a reproduction assumption, not an explicit paper value.
- Generate arrivals only in slots 0 through 99.
- After workload generation compute:
  `last_arrival_slot = arrival_slots - 1`,
  `configured_last_slot = max(task.absolute_deadline_slot)`, and
  `drain_slots = configured_last_slot - last_arrival_slot`.
- Record `drain_policy = "through_maximum_inclusive_absolute_deadline"` in
  config.
- Record the realized `drain_slots` in every run's metadata.
- Generate no new task after the last arrival slot.
- Early temporal termination is allowed if all tasks become terminal sooner;
  otherwise run through `configured_last_slot`.
- After the inclusive deadline opportunity, every incomplete task must become
  terminal. A nonterminal task after `configured_last_slot` is an invariant
  failure and must fail fast.
- Stage-11B values 102/0 remain auxiliary only. Horizons from references [1] and
  [4] must not be attributed to v2.
- Horizon sensitivity at 50 and 200 slots is allowed later only as an
  `[آزمون کمکی]`.
- This specializes ASSUMP-024 for temporal PIPE-NORMAL: the arrival envelope is
  explicit, while drain is deterministically derived from workload deadlines and
  recorded.

### ASSUMP-035 — Event order within each epoch

- Status: approved `[فرض بازتولید]`.
- Apply this order in each epoch:
  1. active allocations accepted in earlier slots progress by one slot;
  2. record completions and release their resources;
  3. after the inclusive-boundary completion opportunity, expire incomplete jobs
     that have passed their deadline;
  4. register arrivals for the current epoch;
  5. arrivals in epoch `e` may bid only from epoch `e+1`;
  6. eligible jobs execute the two-round auction;
  7. commit the Round-2 decision atomically;
  8. jobs accepted in epoch `e` become active at the start of epoch `e+1`.
- Auction execution advances no simulation time in PIPE-NORMAL. Auction-time
  experiments remain a separate blocked scope.

### ASSUMP-036 — Total computation to per-slot demand

- Status: approved `[فرض بازتولید]`, amended by the approved Option A below.
- `K_j` is total computation and must not be compared directly with `C_i` for
  admission.
- For admission at auction epoch `e`, compute
  `service_slots = absolute_deadline_slot - e`.
- If `service_slots <= 0`, the job is inadmissible.
- The initially approved denominator `service_slots` is superseded for executable
  Stage 13-D by **ASSUMP-036-A (approved Option A, 2026-08-12)**:
  `compute_eligible_slots = service_slots - 1`; positive computation is
  inadmissible when `compute_eligible_slots <= 0`; otherwise reserve
  `compute_per_slot = remaining_computation / compute_eligible_slots`.
- Use the admission vector `(s_j, compute_per_slot, b_u,j, b_d,j)`.
- On retry, recompute from remaining computation and remaining opportunity.
- An active allocation keeps its admitted rate through completion or preemption;
  a hidden rate increase is prohibited.
- Record one-slot normalization for Table-I capacities in metadata.
- Do not present this rule as the paper's printed formula because the minimum-
  resource formula is absent from v2.
- In addition to four-dimensional fit, run a deterministic isolated dry-run of
  ASSUMP-038 from `e+1` through the inclusive deadline. Admission feasibility
  requires that this dry-run complete upload, computation and download under the
  fixed reservations and proportional precedence constraints.

### ASSUMP-037 — Output size

- Status: approved `[فرض بازتولید]`.
- Only for temporal Synthetic Normal set `output_size_mb = storage_mb`, hence
  `s'_j = s_j`.
- Record provenance as `reproduction_assumption_input_equals_output`.
- Do not modify Stage-11B artifacts.
- Do not invent an independent distribution or another fixed ratio. Other ratios
  are permitted later only as an `[آزمون کمکی]`.

### ASSUMP-038 — Pipeline progress

- Status: approved `[فرض بازتولید]`, amended by the approved Option A below.
- Keep cumulative `uploaded`, `computed` and `downloaded` for every active
  allocation.
- The first active slot begins upload only; computation may begin from the second
  active slot; download may begin from the third active slot.
- After pipeline fill, upload, computation and download may all progress in the
  same slot.
- Within a slot use the order upload → computation → download.
- Same-slot progress may satisfy cumulative constraints in that slot, subject to
  the eligibility lags above.
- Always enforce `computed / K_j <= uploaded / s_j` and
  `downloaded / s'_j <= computed / K_j`.
- Limit each update by its reservation, remaining work and proportional
  precedence.
- Conservatively reserve full `s_j` from activation.
- **ASSUMP-038-A (approved Option A, 2026-08-12):** release resources atomically
  after completion, preemption **or expiration**. Expiration deactivates the
  allocation, releases every reserved dimension and earns zero Utility.
- Record completion only after upload, computation and download are complete.
- Set and record `numerical_tolerance = 1e-9`; never tune it to alter outcomes or
  fit paper results.
- Add boundary tests for upload, computation and download beginning in three
  successive active slots.

### ASSUMP-039 — Retry and preemption

- Status: approved `[فرض بازتولید]`.
- Round-2 rejection is not immediately terminal; move the job to
  `WAITING_RETRY`.
- Retry at most once in each bidding epoch and only while completion before the
  deadline remains feasible.
- Record retry count and every rejection reason.
- Mark the job `EXPIRED` when completion is no longer feasible.
- `PREEMPTED` is terminal for that task instance; it earns zero Utility and does
  not retry.
- Never create a hidden replacement task instance for a preempted job.

### ASSUMP-040 — Final metrics

- Status: approved `[فرض بازتولید]`.
- `completed_utility` is the sum of Utility for tasks COMPLETED by their inclusive
  deadline.
- `rejected_utility` is the Utility sum of every task ID not completed at the end,
  including never admitted, expired and preempted tasks.
- Count every task ID at most once in `rejected_utility`.
- A temporary rejection that later completes contributes nothing to final
  rejected Utility.
- `ever_preempted_utility` and `ever_preempted_jobs` are independent deduplicated
  overlays.
- Preempted is not a third partition beside Completed and Rejected; because
  preemption is terminal, ever-preempted is a subset of rejected.
- Store raw auction-rejection count separately from terminal rejected jobs.
- Test these invariants:
  `completed_task_ids ∩ rejected_task_ids = ∅`,
  `completed_task_ids ∪ rejected_task_ids = all_generated_task_ids`, and
  `ever_preempted_task_ids ⊆ rejected_task_ids`.

### ASSUMP-041 — KG Round-1 GA

- Status: approved `[فرض بازتولید]`.
- Use `pyeasyga = 0.3.1`, `population_size = 200`, `tournament_size = 20`,
  `generations = 30`, `crossover_probability = 0.8`,
  `mutation_probability = 0.2`, `elitism = true` and `maximisation = true`.
- Use tournament selection, one-point crossover, one-random-bit mutation and
  random binary initialization as audited for that library version.
- Require an input seed.
- Sort tasks by `task_id` before passing them to the GA.
- Record every setting and seed in config and metadata.
- Population 200 remains a reproduction assumption; generations 30 comes from
  `g≈30` in arXiv v2.
- Exact Solver is only an `[ابزار کمکی]` for tests.
- Do not change the approved Pipeline DK-R/DK-P settings 200/20/50.

### Remaining blocked decision — Normal high/low thresholds

- Status: blocked; no numerical assumption approved or proposed.
- v2 does not define the threshold or label-generation rule for Figs.7-8 and 10.
  Do not infer it from bar heights or tune it to the published raster.

## Approved assumption — Stage 13-E full-run GA feasibility guard

### ASSUMP-042 — Feasibility-preserving zero-fitness tie repair

- Status: **approved `[فرض بازتولید]` on 2026-08-12**.
- Scope: both audited pyeasyga adapters used by KG and Pipeline DK in temporal
  full-workload runs.
- Evidence: the official pyeasyga multidimensional-knapsack example assigns
  fitness zero to infeasible chromosomes. The empty chromosome is feasible and
  also has fitness zero. pyeasyga 0.3.1 ranks only by fitness and has no
  feasibility preference for this tie.
- Observed failure: the Stage-13E three-arrival-slot Normal pilot generated 47
  tasks. At epoch 1, 20 tasks passed canonical pipeline feasibility and were
  individually feasible on `server-001`, yet KG-R's first GA returned an
  infeasible best chromosome with fitness zero. The existing selector correctly
  failed fast.
- Approved rule: after pyeasyga finishes, if and only if its best chromosome is
  infeasible **and** its reported fitness equals the configured infeasible
  fitness zero, replace the returned subset with the all-zero chromosome. The
  all-zero chromosome is feasible and has exactly the same fitness.
- If the returned infeasible chromosome has nonzero fitness, fail fast.
- Do not rerun the GA, change the seed, use Exact Solver, add items greedily,
  mutate the chromosome or create a numerical penalty.
- Record `ga.zero_fitness_feasibility_repairs` in every raw run and include the
  aggregate count in metadata.
- The existing one-gene pyeasyga compatibility path remains a separate
  `[پیشنهاد فنی]` and is unchanged.
- Provenance label: `[فرض بازتولید]`. This is not an explicit arXiv-v2 or
  pyeasyga setting.

## Proposed assumption — Stage 13-E KG client price ties

### ASSUMP-043 — Seeded uniform KG client choice on equal minimum prices

- Status: **approved and implemented `[فرض بازتولید]` on 2026-08-12**.
- Scope: client-side server choice shared by KnapsackGreedy Retention and
  KnapsackGreedy Preemption only. It does not change Pipeline DK, GA-fitness,
  returning-job ordering or victim-ordering ties.
- Evidence gap: arXiv v2 Section III says that the client chooses the cheapest
  server but gives no general tie rule. Its worked Fig. 4 example on PDF page 7
  randomly chooses one of two servers offering the same fit price. The example
  does not state a distribution or seed.
- Trigger observed after implementing ASSUMP-042: on the fixed Stage-13E pilot,
  KG-P reached epoch 11 with job `job-000032`; servers `server-003` and
  `server-007` both offered the exact minimum price `44.13898074910724`, below
  utility `49.04331194345249`. The existing fail-fast guard stopped the run.
- Approved rule (option A):
  1. preserve rejection when the minimum bid exceeds Utility;
  2. preserve the unique-minimum choice without consuming tie RNG state;
  3. for two or more exactly equal acceptable minimum prices, sort the tied
     server IDs and choose uniformly among them;
  4. use the same mandatory named per-policy seeded RNG stream already spanning
     that KG policy's GA and auction decisions; do not create or reseed a stream;
  5. record `client.equal_minimum_price_ties` in every raw run;
  6. do not generalize this rule to equal utility/time ratios, victim ratios,
     DK-P Round-2 scores or GA chromosomes.
- Option B: select the lexicographically first tied server. This is deterministic
  but has less support from the random choice shown in the v2 example.
- Option C: retain fail-fast. This avoids a new assumption but blocks the
  four-policy PIPE-NORMAL experiment on the fixed pilot.
- User decision: option A approved on 2026-08-12.
- Provenance: `[فرض بازتولید]`; never report it as an explicit v2 setting.
- Implementation status: KG-R and KG-P obtain the resolver only from the
  audited selector's existing policy RNG stream. Exact/auxiliary selectors keep
  fail-fast unless a resolver is passed explicitly. Unique minima do not call
  the resolver. Runtime metadata records `client.equal_minimum_price_ties`.
- Verification: the fixed Stage-13F pilot resolved exactly one KG-P client tie;
  all four policies completed. Unit/integration tests cover canonical input,
  fixed-seed replay, counter behavior, legacy fail-fast and metadata.

## Approved auxiliary counterfactual assumptions — Stage 15-D

The following decisions are not paper settings. They were approved by the user
on 2026-08-13 only as `[فرض آزمون کمکی]`. Their full scientific rationale,
controls and stop conditions are documented in
`docs/stage15d_counterfactual_design.md`.

### ASSUMP-044 — Counterfactual scope and execution order

- Status: **approved `[فرض آزمون کمکی]` on 2026-08-13**.
- Use only the first materialized ASSUMP-033 workload seed
  `541501192080118187` initially.
- Reuse the valid Stage-15C baseline without recomputation.
- Execute one factor at a time for DK-R and DK-P in this order: fixed penalty,
  initial-population-only repair, offspring-only repair.
- Do not execute a 30-workload extension without separate approval.
- Never present these runs as the paper method or Figure-6 reproduction.

### ASSUMP-045 — Fixed infeasible-fitness penalty

- Status: **approved `[فرض آزمون کمکی]` on 2026-08-13**.
- Change only infeasible chromosome fitness from `0.0` to exactly `-1.0`.
- Keep feasible fitness equal to Utility sum and empty chromosome fitness zero.
- Require all target-workload utilities to be finite and non-negative; otherwise
  fail fast instead of inventing another penalty.
- Preserve ASSUMP-042 as a final guard and record any remaining invocation.

### ASSUMP-046 — Initial-population-only feasibility repair

- Status: **approved `[فرض آزمون کمکی]` on 2026-08-13**.
- Draw each initial chromosome with exactly the original `n` calls to
  `random.randint(0,1)`.
- If infeasible, deterministically clear selected bits from the end of canonical
  task-id order toward the start until feasible; allow the empty chromosome.
- Consume no extra random draw and do not repair offspring.
- Record repaired initial chromosomes and removed bits.

### ASSUMP-047 — Offspring-only feasibility repair

- Status: **approved `[فرض آزمون کمکی]` on 2026-08-13**.
- Keep initial population, fitness and selection identical to baseline.
- After crossover and mutation, but before fitness evaluation, deterministically
  clear selected bits from the end of canonical task-id order until feasible.
- Consume no extra random draw, allow the empty chromosome and do not repair the
  copied elite.
- Record repaired offspring and removed bits.

### Approved protective RNG gate for ASSUMP-044 through ASSUMP-047

- Every variant must add zero random draws.
- Compare the call count of every random primitive and the final RNG state with
  the valid Stage-15C baseline; any difference is fail-fast unless source-code
  evidence first establishes a data-dependent library call path.
- A different chromosome, fitness ranking, selected subset or counterfactual
  outcome is not by itself an RNG error.
- Each variant remains independent and single-factor; no combined variant,
  parameter tuning, Figure-6 overwrite or 30-workload extension is authorized.
- The Stage-15C baseline must be reused without recomputation.
- Source audit performed before implementation found a data-dependent full-run
  RNG call path. The user approved Option A on 2026-08-13: require exact RNG
  equality for identical selector call shapes and exact same-variant replay;
  permit a full-run baseline difference only when recorded zero/single/multi,
  GA-call, candidate-pool or uniform-choice shape differences explain it.
- Padding draws, per-call reseeding, artificial candidate-pool freezing and
  lifecycle changes remain forbidden. Option B remains an unexecuted possible
  future diagnostic. See `docs/stage15d_rng_gate.md`.

## Stage 15-F — diagnostic closure decisions

- Status: user-approved closure decision on 2026-08-13; this section introduces
  **no new scientific assumption**.
- Do not rerun any workload, baseline, repair or policy for the Figure-6
  diagnostic closure.
- Preserve the official Pipeline-DK implementation and every Stage-14A Figure-6
  artifact unchanged. Figure 6 remains **not reproduced**.
- Treat initialization repair and offspring repair only as `[فرض آزمون کمکی]`;
  they are not the paper method and are not accepted changes to the official
  pipeline.
- The stable positive effect observed for both repairs across five seeds is
  diagnostic evidence only. Do not extend it to 30 workloads or combine the
  repairs without separate approval.
- Record weak GA-chromosome feasibility in the current reconstruction as the
  leading suspect, not as a proven defect in the paper. Final attribution
  remains `[نامشخص]` until author code, actual repair, chromosome encoding and
  full GA details become available.
- The closest technically runnable next target is an auxiliary Round-1
  diagnostic near Fig.3. It must not be called a paper-figure reproduction
  unless the original seed, workload and job-ID mapping are recovered.

## Stage 15-G — Figure 1 graphical reconstruction boundaries

- Status: user-approved Option A on 2026-08-14; **no new scientific or
  numerical reproduction assumption** is introduced.
- `[نامشخص]` The paper does not define a quantitative meaning for the number
  of arrival dots, the number of the continuation epoch, or processing-arrow
  duration. The reconstruction does not infer any of these values.
- `[پیشنهاد فنی]` Canvas size, coordinates, DejaVu Sans typography, line width,
  blue/red epoch accents and the white text backing are readability choices
  with no algorithmic meaning.
- No client/server entity, upload/download path, preemption path, internal
  Round-1/Round-2 structure or numeric workload value may be added to Figure 1
  because these are not visible components of the source figure.
- The output is a structural/conceptual scientific reconstruction, not a
  pixel-level copy and not an experimental result. Figure 6 remains unchanged
  and not reproduced.

## Stage 15-H — 30-workload auxiliary repair validation closure

- Status: user-approved 30-workload extension completed on 2026-08-21; this
  section introduces **no new paper or reproduction assumption**.
- Initialization-only repair (ASSUMP-046) and offspring-only repair
  (ASSUMP-047) remained independent, single-factor `[فرض آزمون کمکی]` variants.
- All 120 logical repair pairs were validated: 100 new pairs from Run
  `32474360245` and 20 checksum-pinned reused pairs. All same-variant replays and
  within-variant Option-A RNG gates passed.
- Historical Stage-13 baselines did not record the full RNG/call-shape state;
  therefore variant-versus-baseline RNG equality remains `[نامشخص]` and is not
  claimed.
- Both repairs increased completed Utility for DK-R and DK-P in 30/30 paired
  workloads. This is diagnostic evidence only and neither repair is accepted as
  the paper method or as a change to the official Pipeline-DK implementation.
- The official Stage-14A Figure-6 artifacts remain unchanged and Figure 6
  remains **not reproduced**.
- The only failed job in source Run `32474360245` was post-processing: the
  downloaded Stage-13J aggregate stored `raw_run_metrics.csv` below
  `stage13k_independent_verification`, while the workflow expected a stale
  `stage13j` path. This is a technical artifact-layout defect with no scientific
  relationship to workload capacity, resource capacity, seeds or algorithms.
- Stage 15-I may correct this path and re-run aggregation only. It must not
  execute a workload, policy, baseline or repair pair.
- Run `32829531291` confirmed that the first path correction and all 120 repair
  downloads were valid, but exposed a second technical packaging defect: the
  derived Stage-15A `per_run_lifecycle.csv` was intentionally gitignored and
  therefore absent on the clean GitHub runner. No scientific or RNG gate ran
  incorrectly and no policy result was recomputed.
- The approved Stage-15I recovery re-derives that one lifecycle table from the
  immutable 120 Stage-13J baseline `result.json` artifacts. Every input result,
  workload hash, policy seed and workload-policy identity is checked against
  `stage15h_baseline_reuse_manifest.json`; the derived CSV must equal the pinned
  Stage-15A SHA-256
  `fac98f37a6faf23bdb91387498ed11008611adef29b383d24f1c866f8504610a`.
- This derivation is aggregation/diagnostic processing only. It does not invoke
  the simulator, any policy, GA, workload generator, baseline or repair.
- Stage-15I Run `32831698843` completed successfully: lifecycle recovery,
  120/120 repair completeness, 120/120 baseline reuse, replay gates, final CSVs,
  plots and delivery checksums all passed. This closes the technical recovery
  and adds no scientific assumption.

## Stage 15-K — proposed and unapproved strictness-audit assumptions

**Status:** ASSUMP-048 and ASSUMP-049 were approved by the user on 2026-09-02
strictly as `[فرض آزمون کمکی]` for Stage 15-K.1. ASSUMP-050 through ASSUMP-053
remain `[پیشنهادشده و تأییدنشده]`, inactive and forbidden without separate
approval. None is a paper setting or an official Pipeline-DK change. The
official Pipeline DK and Figure-6 result remain unchanged.

### ASSUMP-048 — protected single-seed pilot protocol

- Status: approved `[فرض آزمون کمکی]` for Stage 15-K.1 only.

- Use only the first materialized ASSUMP-033 workload seed and DK-R/DK-P.
- Reuse the valid baseline; run each logical variant twice with identical
  workload/policy seeds.
- Require exact replay equality for outcomes, Utility, task partitions, funnel,
  config, invariants and the approved Option-A RNG gate.
- Keep variants independent and single-factor; forbid tuning, combined changes,
  padding draws and reseeding.

### ASSUMP-049 — Round-2-only initialization feasibility repair

- Status: approved `[فرض آزمون کمکی]` for Stage 15-K.1 only.

- Generate Round-2 initial chromosomes with the same draw count and canonical
  task-ID order.
- Deterministically clear selected bits from the canonical tail until feasible.
- Do not change Round 1, fitness, crossover, mutation, pricing, server choice,
  lifecycle or ASSUMP-042; add no random draw and combine no repair.

### ASSUMP-050 — Round-2-only offspring feasibility repair

- Status: `[پیشنهادشده و تأییدنشده]`; inactive.

- In Round 2 only, after crossover/mutation and before fitness, make infeasible
  offspring feasible by deterministic canonical-tail bit deletion.
- Keep the initial population and Round 1 unchanged; preserve the random-call
  structure and do not combine this variant with ASSUMP-049.

### ASSUMP-051 — remove only the isolated full-pipeline admission dry-run gate

- Status: `[پیشنهادشده و تأییدنشده]`; inactive.

- Preserve canonical resource-vector construction and current
  `compute_per_slot`, but do not let the isolated full-pipeline dry-run alone
  exclude a task before Round 1.
- Preserve actual capacity checks, runtime pipeline, inclusive deadline,
  numerical tolerance and invariants; never increase an active allocation rate.

### ASSUMP-052 — same-epoch bidding alternative

- Status: `[پیشنهادشده و تأییدنشده]`; inactive.

- Allow an epoch-`e` arrival to bid in epoch `e`, while accepted allocation
  still activates in epoch `e+1`; preserve all other event ordering.
- This option has high divergence risk because the Section-III example shows
  arrival in epoch 2, bidding in epoch 3 and processing in epoch 4.

### ASSUMP-053 — reduced pipeline-stage lag alternative

- Status: `[پیشنهادشده و تأییدنشده]`; inactive.

- Allow computation in the first active slot and download in the second while
  preserving proportional precedence and capacities.
- Any corresponding `compute_per_slot` change must be a separate preregistered
  variant; do not combine with ASSUMP-051 or ASSUMP-052.
- This option has high divergence risk relative to constraints (23), (25) and
  (27), and is not recommended for the first pilot.
