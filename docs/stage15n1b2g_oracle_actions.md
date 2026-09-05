# Stage 15-N.1B.2-G-R — GitHub Oracle retain branches

Status: approved diagnostic technical proposal.

This workflow performs one deterministic factual bootstrap for workload seed
`541501192080118187`, policy DK-P, and the ASSUMP-046 initial-population repair.
The factual run exists only to materialize 28 restorable pre-commit checkpoints.
It must exactly match the checksum-pinned ASSUMP-046 comparator before any Oracle
job can start.

Four locally completed Oracle branches, sequences 0 through 3, are represented by
a sanitized checksum-gated reuse fixture. They are not recomputed. The initial
matrix therefore contains sequences 4 through 27: 24 logical branches with two
exact replays per branch, or 48 suffix executions. A later manual resume may name
a prior run ID; only checksum-valid prior branch artifacts are removed from the
matrix.

The diagnostic intervention occurs after natural selection and before atomic
commit. It retains factual victims and rejects the transaction's factual incoming
tasks. It does not rerun the GA, choose replacement victims or subsets, reseed, or
add random draws. Every branch is independent, so Oracle deltas are explicitly
non-additive.

Raw checkpoints and factual task-level evidence are confined to the temporary
bootstrap artifact with seven-day retention. Branch and final artifacts contain
only sanitized aggregates and have fourteen-day retention. The final scientific
summary is emitted only at completeness 28/28.

This work does not alter the official pipeline or the paper method. Figure 6
remains not reproduced.
