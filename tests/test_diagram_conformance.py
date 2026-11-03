"""Diagram conformance: the code uses the exact names in the team's class diagrams.

Each `docs/design/use-cases/US-xx/US-xx_diagram_text.md` holds a text extract of the
use case's drawio file. Only its class-diagram section defines names. A class box is
three `[box]` lines:

    [box] «entity» | AuditLogEntity                       stereotype and class name
    [box] - logId: int | - adminId: int                   attributes (the box may be empty)
    [box] + getAuditLogs(startDate: Date, endDate: Date): AuditLog[]    methods

For every use case in CONFORMING_USE_CASES this test finds the Python class with that
exact name under `app`, then checks each attribute and each method with its parameter
names in order. Each task appends its diagrammed use cases to the list.
"""

import difflib
import importlib
import inspect
import pkgutil
import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import app as app_package

CONFORMING_USE_CASES: list[str] = [
    "US-05",
    "US-12",
    "US-13",
    "US-19",
    "US-32",
    "US-34",
    "US-38",
    "US-43",
    "US-48",
    "US-54",
    "US-56",
    "US-60",
]

# Where a class diagram and its sequence diagram disagree, the sequence diagram wins. Each
# entry names one method (use case, class, method) and the extra parameters, in order, that
# it takes after the class diagram's own. US-19 sequence step 1.4 calls
# displayReviewForm(existingReview) while the class diagram omits the parameter.
SEQUENCE_DIAGRAM_PARAMETERS: dict[tuple[str, str, str], list[str]] = {
    ("US-19", "DesignerProfilePage", "displayReviewForm"): ["existingReview"],
}

USE_CASES_DIR = Path(__file__).resolve().parent.parent / "docs" / "design" / "use-cases"
ALL_USE_CASES = sorted(path.name for path in USE_CASES_DIR.glob("US-*") if path.is_dir())

STEREOTYPE_LINE = re.compile(r"«(?P<stereotype>boundary|control|entity)»\s*\|\s*(?P<name>\w+)")
METHOD_MEMBER = re.compile(r"(?P<visibility>[+-])\s*(?P<name>\w+)\((?P<params>[^)]*)\)\s*:.*")
ATTRIBUTE_MEMBER = re.compile(r"(?P<visibility>[+-])\s*(?P<name>\w+)\s*:\s*\S.*")
PARAMETER = re.compile(r"(?P<name>\w+)\s*:\s*\S.*")


@dataclass
class DiagramMethod:
    name: str
    params: list[str]
    text: str


@dataclass
class DiagramClass:
    stereotype: str
    name: str
    attributes: dict[str, str] = field(default_factory=dict)  # name -> diagram text
    methods: list[DiagramMethod] = field(default_factory=list)


# Parsing


def extract_path(use_case: str) -> Path:
    return USE_CASES_DIR / use_case / f"{use_case}_diagram_text.md"


def class_diagram_lines(use_case: str) -> list[str]:
    """The `[box]` lines of the class-diagram section, without the `[box] ` prefix."""
    lines, in_section = [], False
    for raw in extract_path(use_case).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("==="):
            in_section = "Class Diagram" in line
        elif in_section and line.startswith("[box]"):
            lines.append(line.removeprefix("[box]").strip())
    if not lines:
        raise ValueError(f"{use_case}: no class-diagram section in {extract_path(use_case)}")
    return lines


def parse_member(use_case: str, box: DiagramClass, member: str) -> None:
    if match := METHOD_MEMBER.fullmatch(member):
        params = []
        for param in filter(None, (p.strip() for p in match["params"].split(","))):
            if not (param_match := PARAMETER.fullmatch(param)):
                raise ValueError(f"{use_case}: cannot parse parameter {param!r} in {member!r}")
            params.append(param_match["name"])
        box.methods.append(DiagramMethod(match["name"], params, member))
    elif match := ATTRIBUTE_MEMBER.fullmatch(member):
        box.attributes[match["name"]] = member
    else:
        raise ValueError(f"{use_case}: cannot parse member {member!r} of {box.name}")


def parse_class_diagram(use_case: str) -> dict[str, DiagramClass]:
    """Every class box of the use case's class diagram, by class name."""
    classes: dict[str, DiagramClass] = {}
    box = None
    for line in class_diagram_lines(use_case):
        if match := STEREOTYPE_LINE.fullmatch(line):
            box = DiagramClass(match["stereotype"], match["name"])
            classes[box.name] = box
        elif box is None:
            raise ValueError(f"{use_case}: line {line!r} comes before any class box")
        else:
            for member in line.split(" | "):
                parse_member(use_case, box, member.strip())
    return classes


# Checking


def app_classes() -> dict[str, list[type]]:
    """Every class defined in a module under `app`, by `__name__`."""
    found: dict[str, list[type]] = {}
    for module_info in pkgutil.walk_packages(app_package.__path__, "app."):
        module = importlib.import_module(module_info.name)
        for cls in vars(module).values():
            if inspect.isclass(cls) and cls.__module__ == module.__name__:
                found.setdefault(cls.__name__, []).append(cls)
    return found


def did_you_mean(name: str, candidates) -> str:
    close = difflib.get_close_matches(name.lower(), [c.lower() for c in candidates], n=1)
    if not close:
        return ""
    original = next(c for c in candidates if c.lower() == close[0])
    return f" (found {original!r}: check the spelling and capitalisation)"


def public_names(target) -> list[str]:
    return [name for name in dir(target) if not name.startswith("__")]


def parameter_names(method) -> list[str]:
    return [
        p.name
        for p in inspect.signature(method).parameters.values()
        if p.name not in ("self", "cls")
    ]


def expected_parameters(use_case: str, box: DiagramClass, method: DiagramMethod) -> list[str]:
    """The class diagram's parameters plus any sequence-diagram extras for this one method."""
    extra = SEQUENCE_DIAGRAM_PARAMETERS.get((use_case, box.name, method.name), [])
    return method.params + extra


def check_class(use_case: str, box: DiagramClass, cls: type) -> list[str]:
    """Problems with `cls` against its diagram box; an empty list means it conforms."""
    where = f"{use_case} {box.name} ({cls.__module__})"
    target = cls if box.stereotype == "entity" else cls()
    problems = []
    for name, text in box.attributes.items():
        if not hasattr(target, name):
            problems.append(
                f"{where}: missing attribute {name!r} [diagram: {text}]"
                + did_you_mean(name, public_names(target))
            )
    for method in box.methods:
        actual = getattr(target, method.name, None)
        if actual is None or not callable(actual):
            problems.append(
                f"{where}: missing method {method.name!r} [diagram: {method.text}]"
                + did_you_mean(method.name, public_names(target))
            )
        elif (params := parameter_names(actual)) != (
            expected := expected_parameters(use_case, box, method)
        ):
            problems.append(
                f"{where}: method {method.name!r} has parameters {params}, "
                f"diagram has {expected} [diagram: {method.text}]"
            )
    return problems


def conformance_problems(use_case: str) -> list[str]:
    classes = app_classes()
    problems = []
    for box in parse_class_diagram(use_case).values():
        matches = classes.get(box.name, [])
        if not matches:
            problems.append(
                f"{use_case}: no class named {box.name!r} («{box.stereotype}») under app/"
                + did_you_mean(box.name, classes)
            )
        elif len(matches) > 1:
            modules = ", ".join(cls.__module__ for cls in matches)
            problems.append(f"{use_case}: class name {box.name!r} is defined twice: {modules}")
        else:
            problems.extend(check_class(use_case, box, matches[0]))
    return problems


# The conformance test


@pytest.mark.parametrize("use_case", CONFORMING_USE_CASES)
def test_code_matches_class_diagram(app, use_case):
    problems = conformance_problems(use_case)
    assert not problems, "Diagram names missing or misspelled:\n" + "\n".join(problems)


# Self-tests of the harness


def test_conforming_use_cases_are_known_diagrams():
    assert set(CONFORMING_USE_CASES) <= set(ALL_USE_CASES)
    assert len(ALL_USE_CASES) == 12


def test_parser_reads_us32_class_diagram():
    classes = parse_class_diagram("US-32")
    assert list(classes) == ["AuditLogPage", "ViewAuditLogController", "AuditLogEntity"]
    assert [c.stereotype for c in classes.values()] == ["boundary", "control", "entity"]
    entity = classes["AuditLogEntity"]
    assert "timestamp" in entity.attributes
    assert list(entity.attributes) == [
        "logId",
        "adminId",
        "action",
        "targetType",
        "targetId",
        "timestamp",
    ]
    assert [(m.name, m.params) for m in entity.methods] == [
        ("getAuditLogs", ["startDate", "endDate"]),
    ]
    assert list(classes["AuditLogPage"].attributes) == ["controller"]


def test_us32_audit_log_entity_attributes_exist_in_the_code(app):
    """The attribute and method check passes against the real AuditLogEntity."""
    box = parse_class_diagram("US-32")["AuditLogEntity"]
    (cls,) = app_classes()["AuditLogEntity"]
    assert check_class("US-32", box, cls) == []


@pytest.mark.parametrize("use_case", ALL_USE_CASES)
def test_parser_reads_every_extract(use_case):
    classes = parse_class_diagram(use_case)
    stereotypes = {c.stereotype for c in classes.values()}
    assert stereotypes == {"boundary", "control", "entity"}
    assert all(c.methods for c in classes.values())


def test_parser_handles_a_box_without_attributes_and_private_methods():
    classes = parse_class_diagram("US-48")
    email = classes["EmailService"]
    assert email.attributes == {}
    assert [(m.name, m.params) for m in email.methods] == [
        ("sendSummaryEmail", ["email", "content"]),
    ]
    controller = classes["SendWeeklySummaryController"]
    assert list(controller.attributes) == ["emailService", "entity"]
    assert [m.name for m in controller.methods] == [
        "sendWeeklySummaries",
        "composeSummary",
        "composeNoActivityNotice",
        "scheduleRetry",
    ]


def test_parser_ignores_the_sequence_diagram():
    classes = parse_class_diagram("US-60")
    assert set(classes) == {"ManageFeaturedIDPsPage", "FeatureIDPController", "IDPEntity"}


class MisspelledEntity:
    timeStamp = None

    @classmethod
    def getAuditLogs(cls, startDate, enddate):
        return []


def test_check_reports_misspelled_attribute_and_parameter():
    box = parse_class_diagram("US-32")["AuditLogEntity"]
    box.attributes = {"timestamp": box.attributes["timestamp"]}
    problems = check_class("US-32", box, MisspelledEntity)
    assert len(problems) == 2
    assert "missing attribute 'timestamp'" in problems[0]
    assert "found 'timeStamp'" in problems[0]
    assert "has parameters ['startDate', 'enddate']" in problems[1]
    assert "diagram has ['startDate', 'endDate']" in problems[1]


class EmptyController:
    pass


def test_check_reports_missing_instance_attribute_and_method():
    box = parse_class_diagram("US-32")["ViewAuditLogController"]
    problems = check_class("US-32", box, EmptyController)
    assert any("missing attribute 'entity'" in p for p in problems)
    assert any("missing method 'getAuditLogs'" in p for p in problems)


def test_sequence_diagram_exception_only_affects_its_one_method():
    box = parse_class_diagram("US-19")["DesignerProfilePage"]
    by_name = {m.name: m for m in box.methods}
    assert by_name["displayReviewForm"].params == []
    assert expected_parameters("US-19", box, by_name["displayReviewForm"]) == ["existingReview"]
    assert expected_parameters("US-19", box, by_name["displayMessage"]) == []
    assert expected_parameters("US-19", box, by_name["displayReview"]) == []
    # The same method name in another use case or class stays strict.
    assert expected_parameters("US-05", box, by_name["displayReviewForm"]) == []
    other = DiagramClass("boundary", "SomethingElse")
    assert expected_parameters("US-19", other, by_name["displayReviewForm"]) == []
    assert set(SEQUENCE_DIAGRAM_PARAMETERS) == {
        ("US-19", "DesignerProfilePage", "displayReviewForm")
    }
