"""Reproduce the conceptual structure of Figure 1 from arXiv:2403.15665v2.

The source paper is never read by this script.  A single, explicit inventory
drives the editable SVG and the derived PDF/PNG renderings, so every visible
relationship can be traced to a documented paper statement or to a clearly
labelled graphical convention.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Final, Literal

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "edge-reproduction-matplotlib")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

EvidenceLabel = Literal["[صریح در مقاله]", "[استخراج مستقیم]", "[نامشخص]", "[پیشنهاد فنی]"]
ElementKind = Literal["lane", "boundary", "label", "marker", "relation"]

FIGURE_WIDTH: Final[float] = 12.0
FIGURE_HEIGHT: Final[float] = 5.6
SOURCE_ID: Final[str] = "arXiv:2403.15665v2_2024_figure1_pdf_page_3_section_III"
SOURCE_CAPTION: Final[str] = (
    "The arrival of jobs, along with the bidding and processing procedures."
)


@dataclass(frozen=True)
class FigureElement:
    """One visible Figure-1 component or directed relation."""

    element_id: str
    kind: ElementKind
    label: str
    evidence: EvidenceLabel
    source_location: str
    interpretation: str
    x: float | None = None
    y: float | None = None
    x2: float | None = None
    y2: float | None = None
    source_id: str | None = None
    target_id: str | None = None


def figure_inventory() -> list[FigureElement]:
    """Return the complete structural inventory used to render Figure 1."""

    paper = "arXiv v2, PDF p.3, Fig.1"
    text = "arXiv v2, PDF p.3, Section III, paragraph beginning 'The goal'"
    graphic = "Stage 15-G graphical convention"
    unknown = "arXiv v2, PDF p.3, Fig.1; not defined in caption/body"
    return [
        FigureElement(
            "lane_epoch", "lane", "Epoch", "[صریح در مقاله]", paper, "lane heading", x=0.55, y=5.05
        ),
        FigureElement(
            "lane_arrivals",
            "lane",
            "Arrivals",
            "[صریح در مقاله]",
            paper,
            "job-arrival lane",
            x=0.55,
            y=4.15,
        ),
        FigureElement(
            "lane_bidding",
            "lane",
            "Bidding",
            "[صریح در مقاله]",
            paper,
            "two-round bidding phase (internal rounds are not drawn)",
            x=0.55,
            y=2.92,
        ),
        FigureElement(
            "lane_processing",
            "lane",
            "Processing",
            "[صریح در مقاله]",
            paper,
            "processing phase",
            x=0.55,
            y=1.15,
        ),
        FigureElement(
            "boundary_0",
            "boundary",
            "epoch boundary",
            "[صریح در مقاله]",
            paper,
            "left boundary of epoch 0",
            x=2.05,
            y=0.52,
            x2=2.05,
            y2=5.28,
        ),
        FigureElement(
            "boundary_1",
            "boundary",
            "epoch boundary",
            "[صریح در مقاله]",
            paper,
            "boundary between epochs 0 and 1",
            x=3.35,
            y=0.52,
            x2=3.35,
            y2=5.28,
        ),
        FigureElement(
            "boundary_2",
            "boundary",
            "epoch boundary",
            "[صریح در مقاله]",
            paper,
            "boundary between epochs 1 and 2",
            x=7.00,
            y=0.52,
            x2=7.00,
            y2=5.28,
        ),
        FigureElement(
            "boundary_future",
            "boundary",
            "future boundary",
            "[نامشخص]",
            unknown,
            "right boundary is shown but its epoch number is not labelled",
            x=10.05,
            y=0.52,
            x2=10.05,
            y2=5.28,
        ),
        FigureElement(
            "epoch_0", "label", "0", "[صریح در مقاله]", paper, "epoch label", x=2.70, y=5.05
        ),
        FigureElement(
            "epoch_1", "label", "1", "[صریح در مقاله]", paper, "epoch label", x=5.18, y=5.05
        ),
        FigureElement(
            "epoch_2", "label", "2", "[صریح در مقاله]", paper, "epoch label", x=8.52, y=5.05
        ),
        FigureElement(
            "arrivals_0",
            "marker",
            "••••  •",
            "[صریح در مقاله]",
            paper,
            "symbolic arrivals in epoch 0; [نامشخص] semantic meaning of dot count",
            x=2.47,
            y=4.14,
        ),
        FigureElement(
            "arrivals_1",
            "marker",
            "••  ••  •",
            "[صریح در مقاله]",
            paper,
            "symbolic arrivals in epoch 1; [نامشخص] semantic meaning of dot count",
            x=5.30,
            y=4.14,
        ),
        FigureElement(
            "arrivals_2",
            "marker",
            "••••",
            "[صریح در مقاله]",
            paper,
            "symbolic arrivals in epoch 2; [نامشخص] semantic meaning of dot count",
            x=8.52,
            y=4.14,
        ),
        FigureElement(
            "continuation",
            "marker",
            "•••",
            "[نامشخص]",
            unknown,
            "ellipsis denotes continuation; next epoch number is not specified",
            x=10.88,
            y=2.98,
        ),
        FigureElement(
            "job_set_1",
            "label",
            "Job set 1",
            "[صریح در مقاله]",
            paper,
            "jobs from the preceding arrival epoch enter bidding",
            x=4.20,
            y=3.28,
        ),
        FigureElement(
            "allocated_1",
            "label",
            "Allocated",
            "[صریح در مقاله]",
            paper,
            "accepted branch after bidding",
            x=4.20,
            y=2.18,
        ),
        FigureElement(
            "rejected_1",
            "label",
            "Rejected",
            "[صریح در مقاله]",
            paper,
            "rejected branch after bidding",
            x=5.82,
            y=2.18,
        ),
        FigureElement(
            "job_set_2",
            "label",
            "Job set 2",
            "[صریح در مقاله]",
            paper,
            "jobs from epoch 1 enter bidding in epoch 2",
            x=7.78,
            y=3.28,
        ),
        FigureElement(
            "allocated_2",
            "label",
            "Allocated",
            "[صریح در مقاله]",
            paper,
            "accepted branch after bidding",
            x=7.78,
            y=2.18,
        ),
        FigureElement(
            "rejected_2",
            "label",
            "Rejected",
            "[صریح در مقاله]",
            paper,
            "rejected branch after bidding",
            x=9.36,
            y=2.18,
        ),
        FigureElement(
            "processing_1",
            "label",
            "Accepted jobs at Epoch 1",
            "[صریح در مقاله]",
            paper,
            "accepted jobs from epoch 1 begin processing in epoch 2",
            x=8.25,
            y=0.92,
        ),
        FigureElement(
            "processing_future",
            "label",
            "",
            "[استخراج مستقیم]",
            text,
            "processing continues rightward; duration is unspecified",
            x=10.04,
            y=0.92,
        ),
        FigureElement(
            "r_arrival0_jobset1",
            "relation",
            "arrival-to-bidding",
            "[استخراج مستقیم]",
            text,
            "jobs arriving in one epoch bid in the next epoch",
            x=2.87,
            y=3.87,
            x2=3.73,
            y2=3.36,
            source_id="arrivals_0",
            target_id="job_set_1",
        ),
        FigureElement(
            "r_arrival1_jobset2",
            "relation",
            "arrival-to-bidding",
            "[صریح در مقاله]",
            text,
            "jobs arriving in epoch 1 form Job set 2 in epoch 2",
            x=6.38,
            y=3.87,
            x2=7.32,
            y2=3.36,
            source_id="arrivals_1",
            target_id="job_set_2",
        ),
        FigureElement(
            "r_arrival2_future",
            "relation",
            "arrival-to-future-bidding",
            "[استخراج مستقیم]",
            text,
            "the same one-epoch delay is shown continuing",
            x=9.58,
            y=3.87,
            x2=10.40,
            y2=3.38,
            source_id="arrivals_2",
            target_id="continuation",
        ),
        FigureElement(
            "r_jobset1_allocated",
            "relation",
            "allocation outcome",
            "[صریح در مقاله]",
            paper,
            "bidding can allocate a job",
            x=4.20,
            y=3.02,
            x2=4.20,
            y2=2.43,
            source_id="job_set_1",
            target_id="allocated_1",
        ),
        FigureElement(
            "r_jobset1_rejected",
            "relation",
            "rejection outcome",
            "[صریح در مقاله]",
            paper,
            "bidding can reject a job",
            x=4.92,
            y=3.10,
            x2=5.55,
            y2=2.43,
            source_id="job_set_1",
            target_id="rejected_1",
        ),
        FigureElement(
            "r_rejected1_retry",
            "relation",
            "resubmission",
            "[صریح در مقاله]",
            text,
            "a rejected job may be resubmitted in the next bidding phase",
            x=6.18,
            y=2.48,
            x2=7.30,
            y2=3.16,
            source_id="rejected_1",
            target_id="job_set_2",
        ),
        FigureElement(
            "r_allocated1_processing",
            "relation",
            "start processing",
            "[صریح در مقاله]",
            text,
            "jobs accepted in epoch 1 begin processing in epoch 2",
            x=4.15,
            y=1.90,
            x2=7.46,
            y2=1.18,
            source_id="allocated_1",
            target_id="processing_1",
        ),
        FigureElement(
            "r_jobset2_allocated",
            "relation",
            "allocation outcome",
            "[صریح در مقاله]",
            paper,
            "bidding can allocate a job",
            x=7.78,
            y=3.02,
            x2=7.78,
            y2=2.43,
            source_id="job_set_2",
            target_id="allocated_2",
        ),
        FigureElement(
            "r_jobset2_rejected",
            "relation",
            "rejection outcome",
            "[صریح در مقاله]",
            paper,
            "bidding can reject a job",
            x=8.50,
            y=3.10,
            x2=9.12,
            y2=2.43,
            source_id="job_set_2",
            target_id="rejected_2",
        ),
        FigureElement(
            "r_rejected2_retry",
            "relation",
            "resubmission",
            "[صریح در مقاله]",
            text,
            "a rejected job may be resubmitted in the next bidding phase",
            x=9.72,
            y=2.48,
            x2=10.42,
            y2=3.16,
            source_id="rejected_2",
            target_id="continuation",
        ),
        FigureElement(
            "r_allocated2_processing",
            "relation",
            "start processing",
            "[استخراج مستقیم]",
            text,
            "the allocation-to-processing pattern repeats for Job set 2",
            x=7.82,
            y=1.91,
            x2=10.46,
            y2=1.46,
            source_id="allocated_2",
            target_id="processing_future",
        ),
        FigureElement(
            "r_processing_continues",
            "relation",
            "processing continues",
            "[نامشخص]",
            unknown,
            "horizontal arrow denotes continuation; exact duration is not given",
            x=9.52,
            y=0.92,
            x2=11.42,
            y2=0.92,
            source_id="processing_1",
            target_id="processing_future",
        ),
        FigureElement(
            "style_palette",
            "label",
            "blue/red epoch accents",
            "[پیشنهاد فنی]",
            graphic,
            "colour separates demonstrated epochs and carries no algorithmic meaning",
        ),
        FigureElement(
            "style_layout",
            "label",
            "expanded landscape layout",
            "[پیشنهاد فنی]",
            graphic,
            "spacing and typography improve legibility without changing topology",
        ),
    ]


def _validate_inventory(elements: list[FigureElement]) -> None:
    ids = [element.element_id for element in elements]
    if len(ids) != len(set(ids)):
        raise ValueError("inventory contains duplicate element_id values")
    known = set(ids)
    for element in elements:
        if element.kind == "relation":
            if not element.source_id or not element.target_id:
                raise ValueError(f"relation lacks endpoints: {element.element_id}")
            if element.source_id not in known or element.target_id not in known:
                raise ValueError(f"relation references an unknown endpoint: {element.element_id}")
            if None in (element.x, element.y, element.x2, element.y2):
                raise ValueError(f"relation lacks coordinates: {element.element_id}")
        if element.evidence not in {
            "[صریح در مقاله]",
            "[استخراج مستقیم]",
            "[نامشخص]",
            "[پیشنهاد فنی]",
        }:
            raise ValueError(f"unsupported evidence label: {element.evidence}")


def render_figure(elements: list[FigureElement], output_base: Path) -> dict[str, Path]:
    """Render editable SVG plus PDF and PNG from the inventory."""

    _validate_inventory(elements)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 13,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), constrained_layout=False)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0.0, 12.0)
    ax.set_ylim(0.0, 5.6)
    ax.axis("off")

    accent = {"epoch_1": "#3155A6", "epoch_2": "#B3263A"}
    for element in elements:
        if element.kind == "boundary":
            assert element.x is not None and element.y is not None
            assert element.x2 is not None and element.y2 is not None
            ax.plot(
                [element.x, element.x2],
                [element.y, element.y2],
                color="#202020",
                lw=1.8,
                zorder=1,
            )
        elif element.kind in {"lane", "label", "marker"} and element.x is not None:
            assert element.y is not None
            if element.element_id.startswith("style_") or element.element_id == "processing_future":
                continue
            color = accent.get(element.element_id, "#202020")
            weight = "bold" if element.kind == "lane" else "normal"
            size = 14 if element.kind == "lane" else 13
            text_options: dict[str, Any] = {"zorder": 3}
            if element.element_id == "processing_1":
                text_options["bbox"] = {
                    "facecolor": "white",
                    "edgecolor": "none",
                    "pad": 1.5,
                }
            ax.text(
                element.x,
                element.y,
                element.label,
                ha="center",
                va="center",
                color=color,
                fontweight=weight,
                fontsize=size,
                **text_options,
            )
        elif element.kind == "relation":
            assert element.x is not None and element.y is not None
            assert element.x2 is not None and element.y2 is not None
            arrow = FancyArrowPatch(
                (element.x, element.y),
                (element.x2, element.y2),
                arrowstyle="-|>",
                mutation_scale=16,
                linewidth=1.9,
                color="#202020",
                shrinkA=0,
                shrinkB=0,
                zorder=2,
            )
            ax.add_patch(arrow)

    ax.text(
        6.0,
        0.10,
        "Conceptual reconstruction of Fig. 1 (arXiv:2403.15665v2, 2024)",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    paths = {suffix: output_base.with_suffix(f".{suffix}") for suffix in ("svg", "pdf", "png")}
    fig.savefig(paths["svg"], format="svg", bbox_inches=None, metadata={"Date": None})
    fig.savefig(
        paths["pdf"],
        format="pdf",
        bbox_inches=None,
        metadata={
            "Title": "Conceptual reconstruction of Figure 1",
            "Author": "edge-preemption-reproduction",
            "Subject": "arXiv:2403.15665v2 Figure 1 structural reconstruction",
            "Creator": "scripts/reproduce_figure1.py",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(paths["png"], format="png", dpi=220, bbox_inches=None, metadata={})
    plt.close(fig)
    return paths


def write_svg_inventory_metadata(svg_path: Path, elements: list[FigureElement]) -> None:
    """Embed a compact editable-structure inventory into the generated SVG."""

    svg_text = svg_path.read_text(encoding="utf-8")
    clip_id_start = svg_text.find('id="p', svg_text.find("<clipPath"))
    if clip_id_start == -1:
        raise ValueError("generated SVG has no Matplotlib clip identifier")
    clip_id_start += len('id="')
    clip_id_end = svg_text.find('"', clip_id_start)
    clip_id = svg_text[clip_id_start:clip_id_end]
    svg_text = svg_text.replace(clip_id, "stage15g_figure1_clip")
    svg_text = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
    marker = "</svg>"
    if marker not in svg_text:
        raise ValueError("generated SVG has no closing svg element")
    embedded = {
        "source": SOURCE_ID,
        "relations": [
            {
                "id": element.element_id,
                "source": element.source_id,
                "target": element.target_id,
                "evidence": element.evidence,
            }
            for element in elements
            if element.kind == "relation"
        ],
    }
    metadata = json.dumps(embedded, separators=(",", ":"), ensure_ascii=False)
    svg_text = svg_text.replace(marker, f"<metadata>{metadata}</metadata>\n{marker}")
    svg_path.write_text(svg_text, encoding="utf-8")


def write_inventory(elements: list[FigureElement], output_dir: Path) -> dict[str, Path]:
    """Write machine-readable JSON and CSV inventories."""

    _validate_inventory(elements)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "figure1_inventory.json"
    csv_path = output_dir / "figure1_inventory.csv"
    payload = {
        "schema_version": "stage15g-figure1-inventory-v1",
        "source": SOURCE_ID,
        "caption": SOURCE_CAPTION,
        "scope": "conceptual_scientific_and_structural_reconstruction",
        "pixel_copy": False,
        "elements": [asdict(element) for element in elements],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = list(asdict(elements[0]))
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(element) for element in elements)
    return {"json": json_path, "csv": csv_path}


def file_sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one file."""

    return sha256(path.read_bytes()).hexdigest()


def generate(project_root: Path) -> dict[str, object]:
    """Generate all Stage 15-G public artifacts and their manifest."""

    elements = figure_inventory()
    figure_paths = render_figure(
        elements, project_root / "figures" / "stage15g" / "figure1_reconstructed"
    )
    write_svg_inventory_metadata(figure_paths["svg"], elements)
    inventory_paths = write_inventory(
        elements, project_root / "results" / "aggregated" / "stage15g"
    )
    generated = {**figure_paths, **inventory_paths}
    manifest_path = project_root / "results" / "aggregated" / "stage15g" / "manifest.json"
    manifest = {
        "schema_version": "stage15g-figure1-manifest-v1",
        "source": SOURCE_ID,
        "reproduction_level": "structural_conceptual_reproduction",
        "numeric_experiment_executed": False,
        "figure6_status_changed": False,
        "inventory_counts": {
            kind: sum(element.kind == kind for element in elements)
            for kind in ("lane", "boundary", "label", "marker", "relation")
        },
        "files": [
            {
                "path": path.relative_to(project_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
            for path in generated.values()
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    manifest = generate(args.project_root.resolve())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
