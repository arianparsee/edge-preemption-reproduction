import math

import pytest

from edge_reproduction.models.enums import EventType
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.events import SimulationEvent


def test_event_serializes_required_audit_fields() -> None:
    event = SimulationEvent(
        sequence=0,
        time=1,
        event_type=EventType.ACCEPTED,
        task_id="task-a",
        server_id="server-1",
        resources_before=ResourceVector(10.0, 10.0, 10.0, 10.0),
        resources_after=ResourceVector(4.0, 6.0, 8.0, 8.0),
        utility=10.0,
        earned_utility=0.0,
        price=9.0,
        reason="scripted_fit_admission",
    )

    serialized = event.as_dict()

    assert serialized["event_type"] == "accepted"
    assert serialized["resources_after"] == {
        "storage": 4.0,
        "computation": 6.0,
        "upload": 8.0,
        "download": 8.0,
    }
    assert serialized["price"] == 9.0


def test_event_rejects_non_finite_price() -> None:
    with pytest.raises(ValueError, match="finite"):
        SimulationEvent(
            sequence=0,
            time=0,
            event_type=EventType.REJECTED,
            task_id="task-a",
            server_id=None,
            resources_before=None,
            resources_after=None,
            utility=10.0,
            earned_utility=0.0,
            price=math.inf,
            reason="invalid_test",
        )
