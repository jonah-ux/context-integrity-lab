import unittest
from datetime import datetime, timezone

from context_integrity import Record, answer


NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def record(**overrides):
    data = {
        "record_id": "r-1",
        "source": "calendar",
        "person_id": "person-a",
        "project_id": "project-a",
        "observed_at": "2026-10-01T10:00:00Z",
        "window_start": "2026-10-01T09:00:00Z",
        "window_end": "2026-10-01T11:00:00Z",
        "text": "The launch review is scheduled for Friday and the API owner is Priya.",
    }
    data.update(overrides)
    return Record(**data)


class ContextIntegrityTests(unittest.TestCase):
    def test_supported_answer_contains_provenance(self):
        result = answer([record()], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["schema"], "context-integrity/v1")
        self.assertTrue(result["ok"])
        self.assertTrue(result["observed"])
        self.assertFalse(result["partial"])
        self.assertEqual(result["citation_count"], 1)
        self.assertEqual(result["citations"][0]["record_id"], "r-1")
        self.assertEqual(result["citations"][0]["window"]["start"], "2026-10-01T09:00:00Z")

    def test_wrong_person_fails_closed(self):
        result = answer([record()], "Who owns the API?", person_id="person-b", project_id="project-a", now=NOW)
        self.assertEqual(result["schema"], "context-integrity/v1")
        self.assertFalse(result["ok"])
        self.assertTrue(result["observed"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "no_matching_scope")
        self.assertEqual(result["unknowns"], ["no_matching_scope"])
        self.assertEqual(result["citations"], [])

    def test_stale_context_is_visible(self):
        result = answer([record(observed_at="2026-09-20T10:00:00Z")], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["reason"], "no_fresh_records")
        self.assertFalse(result["ok"])
        self.assertEqual(result["unknowns"], ["no_fresh_records"])

    def test_fresh_but_irrelevant_context_is_uncertain(self):
        result = answer([record(text="The team lunch is tomorrow.")], "What is the API owner?", person_id="person-a", project_id="project-a", now=NOW)
        self.assertEqual(result["status"], "uncertain")
        self.assertFalse(result["ok"])
        self.assertEqual(result["unknowns"], ["fresh_records_do_not_support_question"])

    def test_unavailable_source_is_not_used(self):
        result = answer([record(status="unavailable")], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
        self.assertEqual(result["status"], "stale")

    def test_protocol_envelope_is_ready_for_loss_aware_interop(self):
        result = answer([record()], "Who owns the API?", person_id="person-a", project_id="project-a", now=NOW)
        self.assertEqual(
            set(result),
            {
                "schema", "status", "ok", "observed", "partial", "timed_out",
                "person_id", "project_id", "citations", "citation_count", "unknowns",
                "answer", "scope",
            },
        )


if __name__ == "__main__":
    unittest.main()
