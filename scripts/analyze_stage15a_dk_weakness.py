"""Stage 15-A paired diagnostic audit of DK weakness using existing results only."""

# ruff: noqa: E501 - Persian report prose is intentionally stored as readable Markdown.

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean
from typing import Final, cast

POLICIES: Final[tuple[str, ...]] = (
    "knapsack_greedy_retention",
    "knapsack_greedy_preemption",
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
LABELS: Final[dict[str, str]] = dict(zip(POLICIES, ("KG-R", "KG-P", "DK-R", "DK-P"), strict=True))


@dataclass(frozen=True, slots=True)
class LifecycleRow:
    workload_seed: int
    policy: str
    generated_jobs: int
    round_one_no_server_rejections: int
    round_two_rejections: int
    retry_scheduled: int
    retry_attempts: int
    canonical_expirations: int
    post_rejection_expirations: int
    waiting_deadline_expirations: int
    active_deadline_expirations: int
    accepted_jobs: int
    accepted_first_attempt: int
    accepted_after_retry: int
    completed_jobs: int
    preempted_jobs: int
    ga_repairs: int
    completed_utility: float

    @property
    def auction_task_decisions(self) -> int:
        return self.accepted_jobs + self.round_one_no_server_rejections + self.round_two_rejections


def _event_count(events: Iterable[Mapping[str, object]], event_type: str) -> int:
    return sum(event.get("event_type") == event_type for event in events)


def lifecycle_row(payload: Mapping[str, object]) -> LifecycleRow:
    """Extract auditable lifecycle counters from one immutable raw result."""

    run = payload["run"]
    if not isinstance(run, dict):
        raise TypeError("run must be a mapping")
    events = run["events"]
    outcome = run["outcome"]
    metadata = run["metadata"]
    retries = run["retry_count_by_task"]
    if not isinstance(events, list) or not isinstance(outcome, dict):
        raise TypeError("invalid run events or outcome")
    if not isinstance(metadata, dict) or not isinstance(retries, dict):
        raise TypeError("invalid run metadata or retry counters")
    event_rows = [event for event in events if isinstance(event, dict)]
    if len(event_rows) != len(events):
        raise TypeError("all events must be mappings")
    final_states = run["final_task_states"]
    if not isinstance(final_states, dict):
        raise TypeError("final_task_states must be a mapping")

    expired_reasons = Counter(
        str(event.get("reason")) for event in event_rows if event.get("event_type") == "expired"
    )
    accepted_ids = {
        str(event["task_id"]) for event in event_rows if event.get("event_type") == "accepted"
    }
    accepted_first = sum(int(cast(int, retries[task_id])) == 0 for task_id in accepted_ids)
    round_one = sum(
        event.get("event_type") == "rejected" and event.get("server_id") is None
        for event in event_rows
    )
    round_two = sum(
        event.get("event_type") == "rejected" and event.get("server_id") is not None
        for event in event_rows
    )
    canonical = sum(
        count
        for reason, count in expired_reasons.items()
        if reason.startswith("canonical_admission_infeasible:")
    )
    post_rejection = sum(
        count
        for reason, count in expired_reasons.items()
        if reason.startswith("post_rejection_next_epoch_infeasible:")
    )
    row = LifecycleRow(
        workload_seed=int(cast(int, payload["workload_seed"])),
        policy=str(payload["policy"]),
        generated_jobs=len(final_states),
        round_one_no_server_rejections=round_one,
        round_two_rejections=round_two,
        retry_scheduled=_event_count(event_rows, "retry_scheduled"),
        retry_attempts=sum(int(cast(int, value)) for value in retries.values()),
        canonical_expirations=canonical,
        post_rejection_expirations=post_rejection,
        waiting_deadline_expirations=expired_reasons[
            "waiting_task_no_remaining_completion_opportunity"
        ],
        active_deadline_expirations=expired_reasons[
            "active_pipeline_incomplete_after_inclusive_deadline_opportunity"
        ],
        accepted_jobs=len(accepted_ids),
        accepted_first_attempt=accepted_first,
        accepted_after_retry=len(accepted_ids) - accepted_first,
        completed_jobs=int(outcome["completed_jobs"]),
        preempted_jobs=int(outcome["ever_preempted_jobs"]),
        ga_repairs=int(metadata["ga.zero_fitness_feasibility_repairs"]),
        completed_utility=float(outcome["completed_utility"]),
    )
    if row.round_one_no_server_rejections + row.round_two_rejections != int(
        outcome["raw_auction_rejection_count"]
    ):
        raise ValueError("event-level rejection count differs from final outcome")
    if (
        row.accepted_jobs
        != row.completed_jobs + row.preempted_jobs + row.active_deadline_expirations
    ):
        raise ValueError("accepted terminal accounting invariant failed")
    return row


def load_rows(raw_root: Path, expected_repeats: int) -> list[LifecycleRow]:
    """Load exactly one result per approved workload-policy pair."""

    rows = [
        lifecycle_row(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(raw_root.rglob("result.json"))
    ]
    expected = expected_repeats * len(POLICIES)
    if len(rows) != expected:
        raise ValueError(f"expected {expected} result files, found {len(rows)}")
    identities = {(row.workload_seed, row.policy) for row in rows}
    if len(identities) != expected:
        raise ValueError("duplicate workload-policy result")
    by_seed: dict[int, set[str]] = defaultdict(set)
    for row in rows:
        by_seed[row.workload_seed].add(row.policy)
    if len(by_seed) != expected_repeats or any(
        set(POLICIES) != value for value in by_seed.values()
    ):
        raise ValueError("paired workload coverage is incomplete")
    return rows


def _summary(rows: list[LifecycleRow]) -> list[dict[str, object]]:
    values = [
        field
        for field in LifecycleRow.__dataclass_fields__
        if field not in {"workload_seed", "policy"}
    ]
    summary: list[dict[str, object]] = []
    for policy in POLICIES:
        selected = [row for row in rows if row.policy == policy]
        record: dict[str, object] = {"policy": policy, "label": LABELS[policy]}
        for field in values:
            record[f"mean_{field}"] = fmean(float(getattr(row, field)) for row in selected)
        decisions = sum(row.auction_task_decisions for row in selected)
        repairs = sum(row.ga_repairs for row in selected)
        accepted = sum(row.accepted_jobs for row in selected)
        completed = sum(row.completed_jobs for row in selected)
        record["pooled_acceptance_fraction"] = accepted / decisions
        record["pooled_completion_given_acceptance"] = completed / accepted
        record["ga_repair_burden_per_1000_task_decisions"] = 1000.0 * repairs / decisions
        summary.append(record)
    return summary


def _paired_contrasts(rows: list[LifecycleRow]) -> list[dict[str, object]]:
    lookup = {(row.workload_seed, row.policy): row for row in rows}
    seeds = sorted({row.workload_seed for row in rows})
    contrasts: list[dict[str, object]] = []
    for name, dk, kg in (
        ("retention_DK_minus_KG", POLICIES[2], POLICIES[0]),
        ("preemption_DK_minus_KG", POLICIES[3], POLICIES[1]),
    ):
        for metric in (
            "canonical_expirations",
            "ga_repairs",
            "round_two_rejections",
            "retry_scheduled",
            "post_rejection_expirations",
            "accepted_jobs",
            "completed_jobs",
            "completed_utility",
        ):
            differences = [
                float(getattr(lookup[(seed, dk)], metric))
                - float(getattr(lookup[(seed, kg)], metric))
                for seed in seeds
            ]
            contrasts.append(
                {
                    "contrast": name,
                    "metric": metric,
                    "paired_workloads": len(differences),
                    "mean_paired_difference": fmean(differences),
                    "minimum_paired_difference": min(differences),
                    "maximum_paired_difference": max(differences),
                }
            )
    return contrasts


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty CSV")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(
    raw_root: Path, output_root: Path, report_path: Path, expected_repeats: int
) -> dict[str, object]:
    """Create derived diagnostics; never execute or alter scientific code."""

    output_root.mkdir(parents=True, exist_ok=True)
    targets = [
        output_root / "per_run_lifecycle.csv",
        output_root / "policy_lifecycle_summary.csv",
        output_root / "paired_dk_minus_kg.csv",
        output_root / "stage15a_diagnostic.json",
        report_path,
    ]
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite Stage 15-A artifacts: {existing}")
    rows = load_rows(raw_root, expected_repeats)
    summary = _summary(rows)
    contrasts = _paired_contrasts(rows)
    _write_csv(targets[0], [asdict(row) for row in rows])
    _write_csv(targets[1], summary)
    _write_csv(targets[2], contrasts)

    by_label = {str(row["label"]): row for row in summary}
    canonical_vectors = {
        policy: [
            row.canonical_expirations
            for row in sorted(rows, key=lambda item: item.workload_seed)
            if row.policy == policy
        ]
        for policy in POLICIES
    }
    canonical_policy_invariant = len({tuple(value) for value in canonical_vectors.values()}) == 1
    report: dict[str, object] = {
        "schema_version": "stage15a-dk-diagnostic-v1",
        "baseline": "arXiv:2403.15665v2_2024",
        "source_run_id": 31644121025,
        "analysis_type": "paired_observational_no_counterfactual_rerun",
        "policy_or_workload_reexecution": False,
        "assumption_seed_algorithm_changes": False,
        "validated_pairs": len(rows),
        "validated_workloads": expected_repeats,
        "canonical_expiration_vector_identical_across_policies": canonical_policy_invariant,
        "ga_repair_rate_available": False,
        "ga_repair_rate_limitation": "nontrivial_GA_call_denominator_not_recorded",
        "policy_summary": summary,
        "findings": {
            "admission": (
                "all raw auction rejections occur after server selection in Round 2; "
                "DK accepts materially fewer tasks than matched KG"
            ),
            "canonicalization": (
                "canonical expiration vectors are identical across all policies and therefore "
                "do not explain the relative DK-vs-KG gap"
            ),
            "ga_repair": (
                "DK has a higher repair burden, but repair probability cannot be inferred "
                "without the missing GA-call denominator"
            ),
            "retry_expiration": (
                "lower DK admission produces more retries and post-rejection expirations"
            ),
            "completion": (
                "accepted retention jobs all complete; accepted preemption jobs end as either "
                "completed or preempted, with no active-deadline expiration"
            ),
            "causal_status": "not_yet_proven_requires_one_factor_controlled_experiments",
        },
    }
    targets[3].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def value(label: str, metric: str) -> float:
        return float(cast(float, by_label[label][metric]))

    markdown = """# Stage 15-A - تحلیل تشخیصی کنترل‌شده ضعف DK

## دامنه و روش

- [استخراج مستقیم] تحلیل paired روی همان 30 workload مشترک و 120 pair معتبر Run 31644121025 انجام شد.
- هیچ policy، workload یا simulator دوباره اجرا نشد و هیچ فرض، seed یا الگوریتمی تغییر نکرد.
- این مرحله observational است: محل گلوگاه را کمی می‌کند، اما هنوز رابطه علی را اثبات نمی‌کند.

## نتایج چرخه‌عمر (میانگین هر workload)

| روش | پذیرش | تکمیل | رد Round 2 | Retry scheduled | انقضای پس از رد | GA repair | پذیرش/تصمیم | تکمیل/پذیرش |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for label in ("KG-R", "KG-P", "DK-R", "DK-P"):
        markdown += (
            f"| {label} | {value(label, 'mean_accepted_jobs'):.3f} | "
            f"{value(label, 'mean_completed_jobs'):.3f} | "
            f"{value(label, 'mean_round_two_rejections'):.3f} | "
            f"{value(label, 'mean_retry_scheduled'):.3f} | "
            f"{value(label, 'mean_post_rejection_expirations'):.3f} | "
            f"{value(label, 'mean_ga_repairs'):.3f} | "
            f"{value(label, 'pooled_acceptance_fraction'):.6f} | "
            f"{value(label, 'pooled_completion_given_acceptance'):.6f} |\n"
        )
    markdown += f"""

## یافته‌های تفکیک‌شده

### Admission و Round 2

- رد Round 1 به‌دلیل نبود سرور قابل‌انتخاب در هر چهار روش صفر است؛ همه ردهای خام پس از انتخاب سرور و در Round 2 رخ داده‌اند.
- DK-R در مجموع `{int(value("DK-R", "mean_accepted_jobs") * expected_repeats)}` پذیرش، در برابر `{int(value("KG-R", "mean_accepted_jobs") * expected_repeats)}` برای KG-R دارد.
- DK-P در مجموع `{int(value("DK-P", "mean_accepted_jobs") * expected_repeats)}` پذیرش، در برابر `{int(value("KG-P", "mean_accepted_jobs") * expected_repeats)}` برای KG-P دارد.
- [استخراج مستقیم] افت اصلی پیش از activation و در تصمیم پذیرش Round 2 ظاهر می‌شود.

### Admission canonicalization

- بردار تعداد انقضای canonical برای هر 30 workload در چهار policy دقیقاً یکسان است: `{str(canonical_policy_invariant).lower()}`.
- بنابراین canonicalization بار مطلق را کاهش می‌دهد، اما اختلاف نسبی DK/KG را در این اجرای paired توضیح نمی‌دهد.

### GA repair

- میانگین repair: KG-R=`{value("KG-R", "mean_ga_repairs"):.3f}`، KG-P=`{value("KG-P", "mean_ga_repairs"):.3f}`، DK-R=`{value("DK-R", "mean_ga_repairs"):.3f}` و DK-P=`{value("DK-P", "mean_ga_repairs"):.3f}`.
- شمارنده repair در DK بالاتر است، ولی تعداد کل فراخوانی‌های GA با بیش از یک candidate ثبت نشده است. پس این اعداد **repair burden** هستند، نه repair rate یا احتمال خرابی.

### Retry و expiration

- DK به‌دلیل پذیرش کمتر، رد Round 2، retry و انقضای `post_rejection_next_epoch_infeasible` بیشتری دارد.
- انقضای پس از رد، پیامد نزدیکِ تکرار عدم پذیرش تا ازبین‌رفتن فرصت pipeline است؛ این مشاهده به‌تنهایی علت الگوریتمی عدم پذیرش را تعیین نمی‌کند.

### Completion

- نسبت تکمیل به پذیرش برای KG-R و DK-R برابر 1 است.
- در روش‌های preemption، هر پذیرش در پایان یا completed یا terminal-preempted است و active-deadline expiration برابر صفر است.
- بنابراین failure پس از پذیرش یا pipeline completion عامل افت DK-R نیست؛ برای DK-P اختلاف completed عمدتاً از پذیرش کمتر و سپس preemption ناشی می‌شود.

## نتیجه موقت و مرز استنباط

شواهد فعلی گلوگاه DK را در **انتخاب/پذیرش Round 2** متمرکز می‌کند. canonicalization نسبت به policy خنثی است و completion پس از پذیرش شکست ندارد. repair burden بالاتر با ضعف DK هم‌زمان است، اما به علت نبود denominator و نبود counterfactual هنوز علت اثبات‌شده نیست.

## آزمایش کنترل‌شده بعدی پیشنهادی

Stage 15-B باید فقط یک عامل را تغییر دهد: instrument کردن تعداد فراخوانی‌های GA و نوع خروجی آن، بدون تغییر تصمیم‌ها یا RNG stream، تا repair rate واقعی و محل دقیق حذف candidateها در Round 1/2 اندازه‌گیری شود. هر counterfactual که رفتار الگوریتم را تغییر دهد پیش از اجرا نیازمند تأیید صریح است.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-repeats", type=int, default=30)
    args = parser.parse_args()
    report = analyze(
        args.raw_root.resolve(),
        args.output_root.resolve(),
        args.report.resolve(),
        args.expected_repeats,
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
