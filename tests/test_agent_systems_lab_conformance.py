import json
from datetime import datetime, timezone
from pathlib import Path

from context_integrity import Record, answer


FIXTURE = Path(__file__).parent / "../conformance/agent-systems-lab.json"
NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def record(**overrides):
    data = {
        "record_id": "fixture-001",
        "source": "synthetic-calendar",
        "person_id": "person-a",
        "project_id": "project-a",
        "observed_at": "2026-10-01T10:00:00Z",
        "window_start": "2026-10-01T09:00:00Z",
        "window_end": "2026-10-01T11:00:00Z",
        "text": "The API owner is Priya.",
    }
    data.update(overrides)
    return Record(**data)


def test_manifest_pins_native_owner_and_shared_adapter():
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert manifest["schema"] == "agent-systems-lab-context-conformance/v1"
    assert manifest["owner"] == "context-integrity-lab"
    assert manifest["native_schema"] == "context-integrity/v1"
    assert manifest["shared_adapter"]["schema"] == "agent-proof/interop/v1"
    assert len(manifest["cases"]) == 5
    assert manifest["privacy"]["downstream_adapter_allowlist_required"] is True


def test_supported_and_refusal_statuses_match_the_manifest():
    cases = {item["name"]: item for item in json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]}
    supported = answer([record()], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
    wrong_scope = answer([record()], "Who owns the API?", person_id="person-b", project_id="project-a", now=NOW)
    stale = answer([record(observed_at="2026-09-20T10:00:00Z")], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
    uncertain = answer([record(text="The team lunch is tomorrow.")], "What is the API owner?", person_id="person-a", project_id="project-a", now=NOW)
    unavailable = answer([record(status="unavailable")], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
    for actual, expected in (
        (supported, cases["supported"]),
        (wrong_scope, cases["wrong-scope"]),
        (stale, cases["stale"]),
        (uncertain, cases["fresh-irrelevant"]),
        (unavailable, cases["unavailable-source"]),
    ):
        assert actual["schema"] == "context-integrity/v1"
        assert actual["status"] == expected["status"]
        assert actual.get("reason") == expected.get("reason")
        assert actual["ok"] is (actual["status"] == "supported")
        assert actual["observed"] is True
        assert actual["partial"] is False
        assert actual["timed_out"] is False


def test_supported_envelope_has_citations_and_refusal_has_unknowns():
    supported = answer([record()], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
    assert supported["citation_count"] == 1
    assert supported["citations"][0]["record_id"] == "fixture-001"
    refused = answer([record(observed_at="2026-09-20T10:00:00Z")], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
    assert refused["unknowns"] == ["no_fresh_records"]
