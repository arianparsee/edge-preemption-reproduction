# Stage 15-M.1 — proposed DK-P No-Cascading pilot

Status: approved `[روش اصلاح‌شده پیشنهادی]`; not the paper method and not a
replacement for the official reproduction pipeline.

## Fixed scope

- Workload seed: `541501192080118187` (first materialized ASSUMP-033 seed).
- Policy lineage: Pipeline DK-P with ASSUMP-046 initial-population repair.
- New factor: ASSUMP-054 only.
- New execution: one logical pair, two exact replays.
- Baseline and repair-only comparator execution: forbidden; sanitized,
  checksum-pinned evidence is reused.
- Figure 6: unchanged, `بازتولید نشد`.

## Dependency closure

All execution dependencies are present on `origin/main=04446d1`:

- official DK-P configuration and score construction;
- ASSUMP-046 counterfactual selector;
- non-interventional GA and auction-funnel instrumentation;
- materialized PIPE-NORMAL config and deterministic workload generator;
- sanitized Stage 13-H baseline and Stage 15-D.1 repair-only reuse fixtures.

No Stage 15-H/15-I recovery code and no Stage 15-K.3 task-level observer is
required. The proposed method lives under `modified_methods` and imports the
official helpers without changing their source.

## Comparator provenance

The runner pins both the repository fixture SHA-256 and the original validated
source-artifact SHA-256. It checks workload seed/hash, policy seed, policy,
replay status and expected outcomes before starting either new replay. The
comparators are never reconstructed from a chart, log line or filename.

## Decision rule

The pilot is scientifically successful only if every replay/RNG/invariant gate
passes and, relative to ASSUMP-046 alone, completed Utility rises, rejected
Utility falls, completion/admission improves, preemptions fall below 29,
direct chain depth is at most one, at least one protected admission completes,
and pre-admission infeasibility remains unchanged.

An unsuccessful or ambiguous result remains a valid controlled result but does
not authorize Stage 15-M.2.
