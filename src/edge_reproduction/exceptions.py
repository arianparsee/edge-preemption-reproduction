"""Project-specific exceptions with explicit reproduction semantics."""


class ReproductionError(Exception):
    """Base class for errors that should be reported as reproduction failures."""


class UnresolvedDecisionError(ReproductionError):
    """Raised when execution would require an unapproved reproduction assumption."""


class StateValidationError(ReproductionError):
    """Raised when a simulation snapshot has structurally inconsistent records."""
