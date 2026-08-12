# Edge-computing preemption paper reproduction

This repository is a staged scientific reproduction of:

> *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*, arXiv:2403.15665v2 (2024).

The implementation is intentionally incomplete while the paper is reconstructed stage by stage. Scientific assumptions that are not explicit in the paper must be approved and recorded before they are used.

Current implementation status: **Stage 13-B — deterministic auxiliary experiment
harness implemented and smoke-tested; all official arXiv v2 experiment
specifications remain non-executable**.

Stage 13-A does not run a paper experiment. It records that none of the 12
official experiment families is currently executable without missing scientific
inputs or implementation dependencies. Figs.3-20 are covered exactly once in:

```text
configs/experiments/
```

See `docs/experiment_protocol.md` for the readiness matrix. Missing seeds,
repeats, horizons and aggregation rules remain `null`; they are never replaced
by hidden defaults. The safe next engineering step is an auxiliary experiment
harness and smoke run around the existing single-auction four-policy regression.

The Stage-13B harness now provides that auxiliary path. Run or safely resume its
one registered smoke experiment with:

```powershell
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json --resume
```

Raw results are isolated below `results/raw/stage13b`; the aggregate execution
index is below `results/aggregated/stage13b`. Resume verifies hashes and never
overwrites a mismatching artifact. The recorded metric is active utility after
one auction, not completed Utility from the paper.

Stage 12-A audits the Southampton/Iridis trace. The paper source bundle contains
only raster trace figures, not raw records or a schema. Exact dates, column mapping,
compute units, upload/output handling and priority mapping remain unavailable, so
real-trace preprocessing is intentionally blocked pending source data or an approved
surrogate scope.

Stage 12-B keeps the official arXiv PNGs, visible-pixel digitization, future
generated surrogate rows and future experiment results in separate directories.
The storage and computation plots are pixel-identical below their titles, so no
independent computation distribution is inferred. Run the digitization audit with:

```powershell
.\.venv\Scripts\python.exe scripts\digitize_southampton_histograms.py
```

The resulting components and diagnostic overlays are technical QA artifacts, not
raw trace records, histogram bins or a numerical reproduction of paper results.

Stage 12-C generates a deliberately limited four-column surrogate from visible
pixel areas. It omits computation, arrivals, Utility and network fields, and is
not compatible with the paper algorithm input. Generate it with:

```powershell
.\.venv\Scripts\python.exe scripts\generate_southampton_surrogate.py --config configs\southampton_surrogate_stage12c_auxiliary.json
```

Generated rows are isolated below `data/processed/surrogates`, diagnostics below
`results/aggregated/stage12c`, and qualitative PNG/SVG comparisons below
`figures/diagnostics/stage12c`. The configured seed is auxiliary and was not tuned
to resemble the paper plots.

Stage 10-B implements the two-round KnapsackGreedy Retention control flow with
approved assumptions ASSUMP-001..009. The Round-1 knapsack is injected through a
selector contract because arXiv v2 does not report the complete pyeasyga settings;
the exhaustive selector shipped here is an auxiliary small-test tool, not the paper GA.

Stage 10-C adds KnapsackGreedy Preemption with an ASSUMP-010 fixed victim snapshot,
frozen Round-2 victim times, single-victim atomic replacement, and current-round
protection for autoFit and direct admissions.

Stage 10-G adds the official Pipeline DK-R path backed by pinned pyeasyga 0.3.1.
Its approved reproducibility configuration is population 200, tournament 20,
50 generations and a mandatory caller seed. Every GA and workload-level pricing
setting is emitted in result metadata. The included exhaustive selector is used
only as an auxiliary oracle for hand-sized tests; Batch DK-R remains blocked
because no valid success-count pricing formula is available.

Run the configured hand example with:

```powershell
.\.venv\Scripts\python.exe scripts\run_stage_ten_g_pipeline_dkr_example.py
```

Stage 10-I adds Pipeline DK-P under approved ASSUMP-016..019: a total-capacity
combined-pool Round-2 knapsack, literal score ordering, atomic repacking, zero-to-many
preemptions and no fabricated Round-2 economic price. Run its configured example with:

```powershell
.\.venv\Scripts\python.exe scripts\run_stage_ten_i_pipeline_dkp_example.py
```

Stage 10-J runs KG-R, KG-P, Pipeline DK-R and Pipeline DK-P independently on one
shared regression scenario. Its after-auction active-utility metric and the Exact
selector used by KG are auxiliary controls, not reported paper results. Run it with:

```powershell
.\.venv\Scripts\python.exe scripts\run_stage_ten_j_four_policy_regression.py
```

Stage 11-A audits the executable meaning of the Normal and Bimodal distribution
tables. Stage 11-B implements the approved missing mechanics with NumPy PCG64,
mandatory seeds, named child streams, rejection sampling, exact Bimodal quotas,
deterministic CSV/JSON artifacts and PNG/SVG diagnostic plots. The supplied
102-slot configs are explicitly auxiliary envelopes, not paper-reported horizons.

Generate both auxiliary diagnostic datasets with:

```powershell
.\.venv\Scripts\python.exe scripts\generate_synthetic.py --config configs\synthetic_normal_stage11b_auxiliary.json
.\.venv\Scripts\python.exe scripts\generate_synthetic.py --config configs\synthetic_bimodal_stage11b_auxiliary.json
```

Generated data are written below `data/processed/synthetic`, statistical summaries
below `results/aggregated/stage11b`, and diagnostic plots below
`figures/diagnostics/stage11b`. These artifacts validate the generator; they are
not numerical results or figures reported by the paper.
