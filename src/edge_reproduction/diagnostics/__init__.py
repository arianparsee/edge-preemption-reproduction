"""Non-scientific diagnostic observers used by controlled reproduction audits."""

from edge_reproduction.diagnostics.dk_funnel import (
    InstrumentedDKPolicy,
    lifecycle_funnel,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    GAInstrumentationSummary,
    InstrumentedKnapsackSelector,
)

__all__ = [
    "GAInstrumentationSummary",
    "InstrumentedDKPolicy",
    "InstrumentedKnapsackSelector",
    "lifecycle_funnel",
]
