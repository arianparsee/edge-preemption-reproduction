from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path
from types import ModuleType

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "reproduce_figure1.py"
    spec = importlib.util.spec_from_file_location("reproduce_figure1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _audit_module() -> ModuleType:
    path = ROOT / "scripts" / "audit_stage15g_publication.py"
    spec = importlib.util.spec_from_file_location("audit_stage15g_publication", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_inventory_has_expected_topology_and_evidence_labels() -> None:
    module = _module()
    elements = module.figure_inventory()
    module._validate_inventory(elements)
    by_id = {element.element_id: element for element in elements}
    relations = {element.element_id: element for element in elements if element.kind == "relation"}

    assert {"lane_epoch", "lane_arrivals", "lane_bidding", "lane_processing"} <= set(by_id)
    assert {"job_set_1", "allocated_1", "rejected_1", "job_set_2"} <= set(by_id)
    assert relations["r_rejected1_retry"].target_id == "job_set_2"
    assert relations["r_allocated1_processing"].target_id == "processing_1"
    assert by_id["continuation"].evidence == "[نامشخص]"
    assert by_id["style_layout"].evidence == "[پیشنهاد فنی]"
    assert all(element.evidence for element in elements)


def test_generator_writes_editable_svg_pdf_png_and_inventory(tmp_path: Path) -> None:
    module = _module()
    manifest = module.generate(tmp_path)
    svg = tmp_path / "figures/stage15g/figure1_reconstructed.svg"
    pdf = tmp_path / "figures/stage15g/figure1_reconstructed.pdf"
    png = tmp_path / "figures/stage15g/figure1_reconstructed.png"
    inventory = tmp_path / "results/aggregated/stage15g/figure1_inventory.json"

    root = ET.parse(svg).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 864 403.2"
    svg_text = svg.read_text(encoding="utf-8")
    assert "Job set 1" in svg_text
    assert "Accepted jobs at Epoch 1" in svg_text
    assert "<text" in svg_text
    assert "stage15g_figure1_clip" in svg_text
    assert '<clipPath id="p' not in svg_text

    pdf_bytes = pdf.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 10_000

    with Image.open(png) as image:
        assert image.size == (2640, 1232)
        assert image.mode in {"RGB", "RGBA"}

    payload = json.loads(inventory.read_text(encoding="utf-8"))
    assert payload["source"] == module.SOURCE_ID
    assert payload["caption"] == module.SOURCE_CAPTION
    assert len(payload["elements"]) == sum(manifest["inventory_counts"].values())
    assert manifest["numeric_experiment_executed"] is False
    assert manifest["figure6_status_changed"] is False


def test_inventory_coordinates_fit_canvas_and_labels_do_not_share_centres() -> None:
    module = _module()
    elements = module.figure_inventory()
    positioned = [element for element in elements if element.x is not None]
    assert all(0.0 <= element.x <= module.FIGURE_WIDTH for element in positioned)
    assert all(
        element.y is not None and 0.0 <= element.y <= module.FIGURE_HEIGHT for element in positioned
    )
    for element in elements:
        if element.x2 is not None:
            assert 0.0 <= element.x2 <= module.FIGURE_WIDTH
            assert element.y2 is not None and 0.0 <= element.y2 <= module.FIGURE_HEIGHT

    visible_labels = [
        element
        for element in elements
        if element.kind in {"lane", "label", "marker"}
        and element.label
        and not element.element_id.startswith("style_")
    ]
    centres = [(element.x, element.y) for element in visible_labels]
    assert len(centres) == len(set(centres))


def test_publication_audit_allows_generated_outputs_and_rejects_source_like_pdf(
    tmp_path: Path,
) -> None:
    module = _module()
    audit_module = _audit_module()
    module.generate(tmp_path)
    allowed = [
        "scripts/reproduce_figure1.py",
        "figures/stage15g/figure1_reconstructed.svg",
        "figures/stage15g/figure1_reconstructed.pdf",
        "figures/stage15g/figure1_reconstructed.png",
        "results/aggregated/stage15g/figure1_inventory.json",
    ]
    source_script = ROOT / "scripts/reproduce_figure1.py"
    (tmp_path / "scripts").mkdir(exist_ok=True)
    (tmp_path / allowed[0]).write_bytes(source_script.read_bytes())
    report = audit_module.audit(tmp_path, allowed)
    assert report["status"] == "passed"

    source_like = tmp_path / "data/raw/paper.pdf"
    source_like.parent.mkdir(parents=True)
    source_like.write_bytes(b"%PDF-1.4\n%%EOF\n")
    try:
        audit_module.audit(tmp_path, ["data/raw/paper.pdf"])
    except ValueError as exc:
        assert "forbidden_directory" in str(exc)
    else:
        raise AssertionError("raw source-like PDF must not pass the publication audit")


def test_generation_is_byte_reproducible(tmp_path: Path) -> None:
    module = _module()
    module.generate(tmp_path)
    paths = sorted(
        [*tmp_path.glob("figures/stage15g/*"), *tmp_path.glob("results/aggregated/stage15g/*")]
    )
    first = {path.relative_to(tmp_path): sha256(path.read_bytes()).hexdigest() for path in paths}
    module.generate(tmp_path)
    second = {path.relative_to(tmp_path): sha256(path.read_bytes()).hexdigest() for path in paths}
    assert second == first
