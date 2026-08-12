# Experiment protocol registry - arXiv v2 baseline

Status date: 2026-08-12  
Baseline: arXiv:2403.15665v2 (2024)

## Scientific boundary

The files in `configs/experiments` are non-executable specifications. They map
paper experiments to current inputs, metrics, implementation dependencies and
unresolved decisions. They never fill an unreported seed, repeat count, horizon,
aggregation rule or solver setting with a hidden default.

Figures 1-2 are conceptual system diagrams, not experiment outputs. The registry
covers every evaluation figure, Figs. 3-20, exactly once. Tables I-II are source
parameters for the already implemented synthetic generators.

## Experiment readiness matrix

| Experiment | Paper target | Workload | Methods | Current status | Primary blocker |
| --- | --- | --- | --- | --- | --- |
| OPT-25 | textual solver result | [1] synthetic instance | Gurobi | blocked | exact instance, solver and implementation absent |
| OPT-18 | textual optimum comparison | [1] synthetic instance | Gurobi + four policies | blocked | exact instance and temporal simulator absent |
| OPT-10 | textual small comparison | subset of OPT-18 | four policies | blocked | identity of ten jobs absent |
| R1-DIAG | Figs.3-5 | Normal pipeline | KG-P | blocked | paper run seed/instance and official KG GA absent |
| PIPE-NORMAL | Figs.6-8 | Synthetic Normal | four policies | blocked | temporal execution, `s'_j`, run control and class thresholds |
| PIPE-NORMAL-TIME | Figs.9-10 | Normal + auction time | four policies | blocked | PIPE-NORMAL blockers plus clock/slot semantics |
| BATCH-NORMAL | Fig.11 | Synthetic Normal | DK-R, KG-P, KG-R | blocked | Batch DK-R price and batch simulator absent |
| BATCH-NORMAL-TIME | Fig.12 | Normal + auction time | same three | blocked | batch and auction-time blockers |
| BATCH-BIMODAL | Figs.13-15 | Synthetic Bimodal | same three | blocked | Batch DK-R and batch simulator absent |
| TRACE-DIAG | Figs.16-18 | Southampton | none | official blocked; auxiliary only | raw trace/schema absent |
| TRACE-BASE | Fig.19 | Southampton | KG-P, KG-R | blocked | raw trace and executable batch workload absent |
| TRACE-CAP-2H | Fig.20 | capped Southampton | DK-R, KG-P, KG-R | blocked | trace, Batch DK-R and time semantics absent |

No paper experiment is currently classified as executable. This is not a test
failure; it is the result of enforcing the approved no-hidden-assumption policy.

## Specification contract

Each independent JSON specification records:

| Field | Meaning |
| --- | --- |
| `source_location` | exact v2 section/pages/figures |
| `processing_mode` / `workload` | paper experiment family |
| `methods` | methods actually shown or compared in that experiment |
| `target_figures` | output figures covered by this config |
| `metrics` | requested paper metrics, not yet fabricated outputs |
| `paper_explicit` | only values stated or directly derived from v2 |
| `run_control` | seed/repeats/horizon/drain/aggregation; missing values remain `null` |
| `unresolved_decisions` | scientific choices requiring source or user approval |
| `implementation_gaps` | code/data/solver dependencies not yet present |
| `execution_status` | `blocked` or `auxiliary_only_official_blocked` |
| `auxiliary_capability` | narrower technical work already possible |

The existing `ExperimentConfig.ensure_resolved()` remains the runtime guard. The
Stage-13A JSON files are intentionally not parsed into executable configs.

## Current reusable capabilities

| Capability | State | Scientific use in Stage 13 |
| --- | --- | --- |
| Normal/Bimodal generator | implemented, deterministic | input generation only; horizon is auxiliary |
| KG-R/KG-P | one-auction policy implemented | control-flow tests; official KG GA still absent |
| Pipeline DK-R/DK-P | one-auction policy implemented | pyeasyga path and small regression only |
| Four-policy common regression | implemented | valid Stage-13 smoke candidate, not paper result |
| Scripted temporal simulator | implemented | manual commands only; policies not integrated |
| Pipeline progress equations | validators implemented | no scheduler/progress engine and `s'_j` missing |
| Batch DK-R | blocked | Batch figures cannot run |
| Gurobi oracle | absent by user decision | OPT experiments cannot run |
| Southampton official preprocessing | blocked | raw trace experiments cannot run |
| Southampton visible surrogate | implemented | qualitative data QA only; not algorithm input |

## Unresolved decision groups

### Synthetic run control

- paper seeds and repeat count;
- arrival horizon and drain/termination policy;
- aggregation across runs;
- exact paper instance for Figs.3-10.

The existing 102-slot/seed-20240811 generator config may be reused only as an
explicitly auxiliary smoke input. It must not silently become the paper protocol.

### Temporal semantics

- generated output size `s'_j`;
- automated allocation-to-progress mapping;
- client choice to retry after a rejected auction;
- state of a preempted job in later auctions;
- terminal rejection versus deadline expiry;
- intra-epoch ordering around bidding, processing and deadline checks.

The paper explicitly says a rejected client *may* resubmit, but gives no client
policy. It also illustrates arrival at epoch `e`, bidding at `e+1` and processing
at `e+2`; this does not resolve all event-order boundaries.

### Metric semantics

- Normal-workload high/low Utility thresholds;
- whether final rejected totals include expired or preempted jobs;
- overlap rules beyond the explicit `ever preempted at least once` definition;
- averaging/error bars, which are absent from v2.

### Auction-time experiments

- synthetic slot duration in seconds;
- whether per-server auction durations run serially, in parallel, or are directly
  deducted from remaining deadlines;
- how fractional seconds map to slot-level progress.

### Permanently source-blocked paths

- OPT instance rows and Gurobi execution environment;
- Batch DK-R success-count pricing;
- Southampton raw trace/schema/mapping.

These paths should remain blocked rather than be repaired with numerical guesses.

## Safe next implementation step

Stage 13-B can implement a generic experiment-orchestration harness around the
existing four-policy single-auction regression, including config loading,
unresolved-decision gating, isolated raw outputs and deterministic reruns. That
would be an `[آزمون کمکی]`, not execution of Figs.3-20.

Running PIPE-NORMAL or any later paper experiment requires a separate approval
of the relevant scientific decisions above. Building the harness does not.

## Stage 13-B auxiliary harness status

Implemented on 2026-08-12:

- `scripts/run_experiment.py` runs one explicitly resolved auxiliary config;
- `scripts/run_all_experiments.py` runs a bounded registry sequentially;
- Stage-13A paper specifications fail fast with `UnresolvedDecisionError`;
- existing run directories are never overwritten;
- `--resume` validates config/result hashes and skips only a matching complete run;
- a corrupt or incomplete prior run is rejected rather than repaired silently;
- raw `result.json`, provenance `manifest.json` and an aggregated registry index
  are written to separate directories;
- environment metadata records Python, platform, NumPy and pyeasyga versions;
- nondeterministic wall time is deliberately omitted from scientific artifacts.

The only registered execution is
`stage13b-four-policy-single-auction-smoke`. It reuses the small Stage-10J
scenario and produces the metric `active_utility_after_auction`, which is not
completed Utility from the paper.

```powershell
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json --resume
```

This harness makes no Stage-13A paper specification executable. The readiness
matrix above remains unchanged: zero official experiments are runnable.

## Stage 13-C temporal and capacity audit status

Stage 13-C completed a source-only audit before building a multi-epoch
PIPE-NORMAL engine. The earlier service message `Selected model is at capacity`
was only a model-service availability interruption; it was unrelated to this
project, server capacity, `K_j`, `C_i` or ASSUMP-036.

As a separate scientific design gap for future temporal execution, job `K_j` is
total computation while server `C_i` is a per-slot capacity. The current
Stage-11B conversion is intentionally allocation-layer-only and is not presently
failing; it simply must not be promoted to a temporal completion model without
an approved total-to-per-slot rule.

ASSUMP-033 through ASSUMP-041 were approved by the user on 2026-08-12 as
`[فرض بازتولید]`; none is an explicit arXiv-v2 setting. The two Stage-13D
consistency conflicts were resolved by approved Option A: computation demand is
divided by `service_slots-1` and checked by an isolated pipeline dry-run, while
expiration atomically releases resources. The proof and decision trail are in
`outputs/stage_thirteen_d_consistency_blocker.md`.

The multi-epoch engine, pipeline progress, retry/preemption lifecycle, final
aggregator and four-policy connection were implemented and verified by a small
two-task smoke. This smoke is not a paper result. Its report is
`outputs/stage_thirteen_d_temporal_pipe_normal_smoke.md`.

Normal high/low thresholds remain separately blocked; no value was inferred
from the published bar heights. The 100-slot × 30-run execution and Figure 6
remain outside Stage 13-D.
