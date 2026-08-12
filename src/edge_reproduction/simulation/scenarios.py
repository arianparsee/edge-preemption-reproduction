"""Small deterministic scenarios used to verify the base simulator by hand."""

from edge_reproduction.algorithms.pricing import fit_price
from edge_reproduction.models.config import ExperimentConfig
from edge_reproduction.models.enums import ProcessingMode, ScriptedAction
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.engine import SimulationCommand
from edge_reproduction.simulation.state import SimulationState


def stage_nine_smoke_scenario() -> tuple[
    SimulationState, tuple[SimulationCommand, ...], ExperimentConfig
]:
    """Return the manually auditable two-server/four-task Stage-9 scenario.

    Values are normalized technical test units, not experimental parameters
    attributed to the paper. Decisions are scripted so no Stage-10 algorithm,
    tie-breaking rule or unresolved preemption price is smuggled into the engine.
    """

    tasks = {
        "task-a": Task("task-a", 0, 4, 10.0, ResourceVector(6.0, 4.0, 2.0, 2.0), 1.0),
        "task-b": Task("task-b", 0, 2, 8.0, ResourceVector(5.0, 5.0, 5.0, 5.0), 1.0),
        "task-c": Task("task-c", 1, 2, 30.0, ResourceVector(7.0, 5.0, 2.0, 2.0), 1.0),
        "task-d": Task("task-d", 0, 1, 12.0, ResourceVector(4.0, 4.0, 4.0, 4.0), 1.0),
    }
    servers = {
        "server-1": Server("server-1", ResourceVector(10.0, 10.0, 10.0, 10.0)),
        "server-2": Server("server-2", ResourceVector(4.0, 4.0, 4.0, 4.0)),
    }
    state = SimulationState(0, tasks, servers)
    commands = (
        SimulationCommand(0, 0, ScriptedAction.ARRIVE, "task-a", "arrival_slot_reached"),
        SimulationCommand(0, 1, ScriptedAction.ARRIVE, "task-b", "arrival_slot_reached"),
        SimulationCommand(0, 2, ScriptedAction.ARRIVE, "task-d", "arrival_slot_reached"),
        SimulationCommand(
            0,
            3,
            ScriptedAction.ACCEPT,
            "task-a",
            "scripted_fit_admission",
            server_id="server-1",
            price=fit_price(tasks["task-a"].utility),
        ),
        SimulationCommand(
            0,
            4,
            ScriptedAction.ACCEPT,
            "task-d",
            "scripted_fit_admission",
            server_id="server-2",
            price=fit_price(tasks["task-d"].utility),
        ),
        SimulationCommand(
            0,
            5,
            ScriptedAction.REJECT,
            "task-b",
            "no_residual_fit_on_any_server",
        ),
        SimulationCommand(1, 0, ScriptedAction.ARRIVE, "task-c", "arrival_slot_reached"),
        SimulationCommand(
            1,
            1,
            ScriptedAction.PREEMPT_AND_ACCEPT,
            "task-c",
            "scripted_preemption_for_smoke_verification",
            server_id="server-1",
            victim_task_ids=("task-a",),
        ),
        SimulationCommand(
            3,
            0,
            ScriptedAction.COMPLETE,
            "task-c",
            "completed_exactly_at_inclusive_deadline",
        ),
    )
    config = ExperimentConfig(
        experiment_id="stage9-smoke",
        method="scripted-smoke",
        processing_mode=ProcessingMode.PIPELINE,
        horizon_slots=4,
        random_seed=20240809,
        parameters={
            "server_count": 2,
            "task_count": 4,
            "deadline_boundary": "inclusive",
            "assignment_flow_semantics": "selected_server_only",
        },
        provenance={
            "server_count": "technical_smoke_fixture",
            "task_count": "technical_smoke_fixture",
            "deadline_boundary": "approved_assumption_ASSUMP-001",
            "assignment_flow_semantics": "approved_assumption_ASSUMP-002",
        },
    )
    return state, commands, config
