# Stage 15-M.1B — one-auction cooldown DK-P pilot

Status: approved `[فرض روش اصلاح‌شده پیشنهادی — آزمون کمکی]`. It is not the
paper method and does not modify the official reproduction pipeline.

## Scope

- ASSUMP-046 is the only base repair.
- ASSUMP-055 is applied after unchanged GA selection and score planning.
- Policy: DK-P only.
- Workload seed: `541501192080118187`.
- One logical pair and two exact replays.
- Baseline, ASSUMP-046 repair-only and failed permanent ASSUMP-054 evidence are
  checksum-pinned and reuse-only.
- No five- or thirty-workload execution is permitted.
- Figure 6 remains `بازتولید نشد`.

## Guard boundary

The first Round-2 evaluation after activation is non-redundant because the
temporal engine activates and progresses prior allocations before the next
auction, and DK-P rebuilds its current pool from active allocations at every
server evaluation. A cooldown is consumed after exactly that one evaluation.

Selection is run once. If the already-planned victim set contains a cooldown
task, the whole server transaction is aborted without an alternative victim,
second GA call, replacement subset or partial commit. All returning tasks in
that server batch follow the existing retry/expiration lifecycle.

## Primary decision gate

Relative to ASSUMP-046 alone:

- Completed Utility must be at least `9541.426964770584`;
- Rejected Utility must be at most `74460.00877807708`;
- Preempted jobs must be fewer than `29`;
- replay, RNG Option-A, fingerprints and invariants must pass;
- Round 1 and pre-admission infeasibility must remain unchanged.

A lower Completed Utility is failure even if Preemption or the
completion/admission ratio improves. Failure ends the No-Cascading path and
does not authorize Stage 15-M.1C.
