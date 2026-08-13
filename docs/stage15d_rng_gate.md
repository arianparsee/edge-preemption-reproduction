# Stage 15-D — RNG protective-gate audit

## Outcome

ASSUMP-044 through ASSUMP-047 are approved only as `[فرض آزمون کمکی]`.
The required pre-implementation audit proved that the full temporal execution
has a data- and outcome-dependent random-call path. The user approved Option A
on 2026-08-13; implementation may proceed under its fixed-shape and exact-replay
controls.

No scientific assumption, algorithm, seed or approved configuration was
changed. The valid Stage-15C baseline was not recomputed.

## Direct source evidence

1. In audited pyeasyga 0.3.1, `create_individual` calls
   `random.randint(0, 1)` once for every gene. Therefore initialization consumes
   `population_size * candidate_count` calls for each real GA invocation
   (`pyeasyga.py`, lines 65–77 and 121–129).
2. Crossover and mutation use conditional random paths: every parent pair draws
   the crossover and mutation thresholds, but `random.randrange` is called only
   when the corresponding condition succeeds (`pyeasyga.py`, lines 146–179).
3. The project adapter bypasses pyeasyga for zero or one candidate and invokes
   the GA only for two or more candidates
   (`src/edge_reproduction/algorithms/genetic_knapsack.py`, lines 270–334).
4. Candidate count and GA invocation count are not fixed by population and
   generations. In the temporal engine, accepted/rejected outcomes determine
   later `WAITING_RETRY` eligibility (`temporal_engine.py`, lines 328–375 and
   406–436).
5. DK-R Round 2 contains the tasks that chose that server, while DK-P Round 2
   contains `current + returning`; both pools therefore depend on earlier
   counterfactual outcomes (`double_knapsack_retention.py`, lines 406–444;
   `double_knapsack_preemption.py`, lines 254–275 and 381–420).

Consequently, a single-factor repair can consume no random number itself and
still legitimately change a later candidate pool, the number/length of GA
calls, the aggregate primitive counts and the final RNG state. Fixed
`population_size`, `generations` and pyeasyga operators do not make the complete
temporal call graph fixed.

## Stage-15C evidence retained without recomputation

The stable Stage-15C artifact records different realized selector shapes even
between the two official DK policies on the same workload:

| Baseline | Round-1 GA calls / candidates | Round-2 GA calls / candidates | Final RNG SHA-256 |
| --- | ---: | ---: | --- |
| DK-R | 856 / 54,264 | 111 / 6,783 | `f7a55555888e9230bf357bdc1a800c22f1c5e834a6f097fd91cc6f1e2d3ae958` |
| DK-P | 864 / 54,184 | 128 / 7,005 | `9c25351125ea2a5cd335d22f864c0eb6f549ed5d923f5ba1ad12ceecf1ab932c` |

The artifact records initial/final RNG-state hashes and GA-level call counts,
but it does not contain per-primitive random-call counts. Recomputing the
baseline merely to add those counters is outside the approved scope.

## Conflict

Two requested properties cannot both hold for the genuine temporal
counterfactual:

- allow the variant to change selection, admission, retry, expiration,
  preemption and completion; and
- require its aggregate primitive counts and final RNG state to equal the
  Stage-15C baseline.

Padding random draws, freezing later pools or reseeding each invocation would
change the stochastic experiment and is not authorized.

## Decision options

### Option A — approved: fixed-shape RNG control plus full-run determinism

- Prove on isolated identical candidate sequences that every variant adds zero
  draws and ends in exactly the same RNG state as the baseline selector.
- In each full temporal variant, record primitive counts and final RNG state,
  but permit baseline differences only when the observed GA call-shape
  (invocation count/candidate lengths) has diverged.
- Run each variant twice with the same seed and require exact equality of its
  primitive counts, final RNG state and scientific result.
- Fail fast for any unexplained count/state difference or any difference while
  call-shape remains identical.

This preserves the intended six genuine temporal counterfactual pairs.

### Option B — deferred and not executed: selector-only replay with frozen Stage-15C call shape

Replay the baseline candidate pools outside the temporal simulator. Exact RNG
equality can then be required, but the experiment cannot validly report effects
on retry, expiration, preemption, completion or completed Utility.

### Option C — keyed RNG per auction invocation

Derive an independent RNG stream for every auction/round/server key. This would
decouple later calls, but changes the approved stochastic architecture and is
therefore not recommended without a new explicit assumption.

## Current status

- Variant code: implementation in progress under approved Option A.
- Local fixed-shape and small-policy tests: required before dispatch.
- GitHub workflow: not created or dispatched.
- New pairs: `0/6`.
- Stage-15C baseline: unchanged and preserved.
- Blocking decision: resolved; Option A approved on 2026-08-13.
