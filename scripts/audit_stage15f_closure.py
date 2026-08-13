"""Read-only audit of the Stage 15-F Figure-6 diagnostic closure."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EVALUATION_FIGURES = set(range(3, 21))


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matches_stage14a_manifest(path: Path, expected: str) -> tuple[bool, str]:
    """Match exact bytes, except the legacy Markdown CRLF pre-commit digest."""

    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == expected:
        return True, "exact_bytes"
    if path.suffix == ".md":
        normalized_crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if hashlib.sha256(normalized_crlf).hexdigest() == expected:
            return True, "legacy_markdown_crlf_digest"
    return False, "mismatch"


def audit(project_root: Path) -> dict[str, object]:
    """Verify closure claims without importing or executing simulator code."""

    registry = _object(project_root / "configs/experiments/registry_arxiv_v2.json")
    specs = [
        _object(project_root / "configs/experiments" / str(entry["file"]))
        for entry in registry["specifications"]
    ]
    figures = [int(figure) for spec in specs for figure in spec["target_figures"]]
    if set(figures) != EVALUATION_FIGURES or len(figures) != len(set(figures)):
        raise ValueError("evaluation figures 3-20 are not covered exactly once")
    allowed_statuses = {"blocked", "auxiliary_only_official_blocked"}
    if any(spec["execution_status"] not in allowed_statuses for spec in specs):
        raise ValueError("an unevaluated official experiment is unexpectedly runnable")

    manifest_path = project_root / "results/aggregated/stage14a/stage14a_manifest.json"
    manifest = _object(manifest_path)
    if (
        manifest.get("reproduction_status") != "not_reproduced"
        or manifest.get("validated_pairs") != 120
        or manifest.get("validated_workloads") != 30
        or manifest.get("policy_or_workload_reexecution") is not False
    ):
        raise ValueError("Stage 14-A Figure-6 registration changed unexpectedly")
    stage14a_hash_modes: dict[str, str] = {}
    for item in manifest["inventory"]:
        path = project_root / str(item["path"])
        if not path.is_file():
            raise ValueError(f"Stage 14-A artifact is missing: {item['path']}")
        matched, mode = _matches_stage14a_manifest(path, str(item["sha256"]))
        if not matched:
            raise ValueError(f"Stage 14-A artifact hash changed: {item['path']}")
        stage14a_hash_modes[str(item["path"])] = mode

    closure = (
        project_root / "docs/stage15f_figure6_diagnostic_closure.md"
    ).read_text(encoding="utf-8")
    reproduction = (project_root / "docs/reproduction_report.md").read_text(
        encoding="utf-8"
    )
    assumptions = (project_root / "docs/assumptions.md").read_text(encoding="utf-8")
    required_closure_phrases = (
        "بازتولید نشد",
        "feasibility ضعیف chromosomeهای GA",
        "initialization repair",
        "offspring repair",
        "5/5 seed",
        "R1-DIAG-AUX",
        "کد رسمی نویسندگان",
    )
    if any(phrase not in closure for phrase in required_closure_phrases):
        raise ValueError("Stage 15-F closure omits a required scientific boundary")
    if "Figure 6 | 120/120 اجرا کامل؛ نتیجه «بازتولید نشد»" not in reproduction:
        raise ValueError("reproduction report does not preserve Figure-6 status")
    no_new_assumption = "introduces\n" + "  **no new scientific assumption**"
    if no_new_assumption not in assumptions:
        raise ValueError("assumptions file does not record the no-new-assumption boundary")

    r1 = next(spec for spec in specs if spec["experiment_id"] == "R1-DIAG")
    if r1["execution_status"] != "blocked" or r1["target_figures"] != [3, 4, 5]:
        raise ValueError("R1-DIAG official boundary changed unexpectedly")
    return {
        "schema_version": "stage15f-closure-audit-v1",
        "status": "passed",
        "simulator_executed": False,
        "figure6_reproduction_status": "not_reproduced",
        "stage14a_inventory_files_verified": len(manifest["inventory"]),
        "stage14a_hash_modes": stage14a_hash_modes,
        "evaluation_figures_audited": 18,
        "official_experiments_unblocked": 0,
        "closest_unblocked_paper_figure": "Fig1_conceptual_epoch_job_set",
        "closest_auxiliary_evaluation_target": "R1-DIAG-AUX_near_Fig3",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.project_root.resolve())
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
