"""Typed experiment configuration with unresolved-decision gating."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models._validation import (
    ensure_identifier,
    ensure_positive_integer,
    ensure_unique,
)
from edge_reproduction.models.enums import ProcessingMode


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """Minimal typed configuration shared by future experiment runners.

    The two-round auction is explicit in Section III, so ``auction_rounds`` must
    be two. The paper does not report a random seed; ``None`` therefore remains a
    representable unresolved value. Any scientific decision still awaiting user
    approval is named in ``unresolved_decisions`` and blocks execution through
    :meth:`ensure_resolved`.
    """

    experiment_id: str
    method: str
    processing_mode: ProcessingMode
    horizon_slots: int
    random_seed: int | None = None
    auction_rounds: int = 2
    unresolved_decisions: tuple[str, ...] = field(default_factory=tuple)
    parameters: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier("experiment_id", self.experiment_id)
        ensure_identifier("method", self.method)
        if not isinstance(self.processing_mode, ProcessingMode):
            raise TypeError("processing_mode must be a ProcessingMode")
        ensure_positive_integer("horizon_slots", self.horizon_slots)
        if self.random_seed is not None and (
            isinstance(self.random_seed, bool) or not isinstance(self.random_seed, int)
        ):
            raise TypeError("random_seed must be an integer or None")
        if self.auction_rounds != 2:
            raise ValueError("the paper's auction has exactly two rounds")

        unresolved = tuple(self.unresolved_decisions)
        for decision_id in unresolved:
            ensure_identifier("unresolved decision_id", decision_id)
        ensure_unique("unresolved_decisions", unresolved)

        parameters = dict(self.parameters)
        provenance = dict(self.provenance)
        for key in parameters:
            ensure_identifier("parameter key", key)
        for key, value in provenance.items():
            ensure_identifier("provenance key", key)
            ensure_identifier("provenance value", value)

        object.__setattr__(self, "unresolved_decisions", unresolved)
        object.__setattr__(self, "parameters", MappingProxyType(parameters))
        object.__setattr__(self, "provenance", MappingProxyType(provenance))

    def ensure_resolved(self) -> None:
        """Block an execution that would silently choose scientific assumptions."""

        if self.unresolved_decisions:
            joined = ", ".join(self.unresolved_decisions)
            raise UnresolvedDecisionError(f"unresolved reproduction decisions: {joined}")
