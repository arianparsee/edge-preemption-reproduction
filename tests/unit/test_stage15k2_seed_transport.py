import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/stage15k2-five-seed-r2-repair.yml"
APPROVED_SEEDS = (
    "2074092324964443463",
    "2218754797665862270",
    "2997476077322633071",
    "3782887846963969634",
)


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _matrix_seed_block(text: str) -> str:
    return text.split("        workload_seed:\n", 1)[1].split("        policy:\n", 1)[0]


def test_matrix_seeds_are_exact_quoted_decimal_strings_in_approved_order() -> None:
    block = _matrix_seed_block(_workflow_text())
    seeds = tuple(re.findall(r'^\s+- "([^"]+)"\s*$', block, flags=re.MULTILINE))

    assert seeds == APPROVED_SEEDS
    assert all(re.fullmatch(r"[0-9]{19}", seed) for seed in seeds)
    assert all(seed == str(int(seed, 10)) for seed in seeds)
    assert "E+18" not in block
    assert "." not in block


def test_workflow_transports_seed_through_one_quoted_environment_variable() -> None:
    text = _workflow_text()

    assert 'WORKLOAD_SEED_DECIMAL: "${{ matrix.workload_seed }}"' in text
    assert '--workload-seed "$WORKLOAD_SEED_DECIMAL"' in text
    assert 'seed = os.environ["WORKLOAD_SEED_DECIMAL"]' in text
    assert 'str(int(seed_string, 10)) != seed_string' in text
    assert 're.fullmatch(r"[0-9]{19}", seed_string)' in text


def test_workflow_scope_remains_four_seeds_two_policies_and_two_replays() -> None:
    text = _workflow_text()
    block = _matrix_seed_block(text)

    assert len(re.findall(r'^\s+- "[0-9]{19}"\s*$', block, flags=re.MULTILINE)) == 4
    assert text.count("pipeline_double_knapsack_retention") >= 1
    assert text.count("pipeline_double_knapsack_preemption") >= 1
    assert "Run two exact replays; baseline and seed one are not executed" in text
    assert "run-id: 33663692202" in text
    assert "max-parallel: 8" in text
    assert "fail-fast: false" in text
