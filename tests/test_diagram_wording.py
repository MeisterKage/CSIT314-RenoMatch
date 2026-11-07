"""Every button or link a sequence diagram quotes appears on the site with that exact wording."""

import re
from pathlib import Path

import pytest

from tests.test_diagram_conformance import CONFORMING_USE_CASES

ROOT = Path(__file__).parents[1]
TEMPLATES = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (ROOT / "app" / "boundary" / "templates").rglob("*.html")
)


def quotedLabels(useCase):
    text = ROOT / "docs" / "design" / "use-cases" / useCase / f"{useCase}_diagram_text.md"
    edges = re.findall(r"^\[edge\] \d+: (.*)$", text.read_text(encoding="utf-8"), re.M)
    return [label for edge in edges for label in re.findall(r'"([^"]+)"', edge)]


CASES = [(useCase, label) for useCase in CONFORMING_USE_CASES for label in quotedLabels(useCase)]


def test_the_diagrams_quote_the_expected_labels():
    assert {"Audit Log", "Compare", "Export CSV", "Send Reset Link"} <= {c[1] for c in CASES}


@pytest.mark.parametrize("useCase, label", CASES)
def test_quoted_label_is_used_exactly(useCase, label):
    escaped = re.escape(label)
    assert re.search(rf">\s*{escaped}\s*<|'{escaped}'", TEMPLATES), f"{useCase}: {label}"
