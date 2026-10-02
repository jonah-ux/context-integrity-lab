#!/usr/bin/env python3
"""Deterministic provenance and freshness gate for synthetic meeting context."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CONTEXT_SCHEMA = "context-integrity/v1"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass(frozen=True)
class Record:
    record_id: str
    source: str
    person_id: str
    project_id: str
    observed_at: str
    window_start: str
    window_end: str
    text: str
    status: str = "available"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Record":
        return cls(**value)


STOPWORDS = {"a", "an", "and", "are", "for", "is", "of", "the", "to", "what", "who"}


def _result(
    status: str,
    *,
    person_id: str,
    project_id: str,
    reason: str | None = None,
    answer_text: str | None = None,
    citations: list[dict[str, Any]] | None = None,
    stale_record_ids: list[str] | None = None,
    unknowns: list[str] | None = None,
) -> dict[str, Any]:
    """Build one explicit, loss-aware context admission envelope."""

    citation_list = citations or []
    result: dict[str, Any] = {
        "schema": CONTEXT_SCHEMA,
        "status": status,
        "ok": status == "supported",
        "observed": True,
        "partial": False,
        "timed_out": False,
        "person_id": person_id,
        "project_id": project_id,
        "citations": citation_list,
        "citation_count": len(citation_list),
        "unknowns": sorted(set(unknowns or [])),
    }
    if reason is not None:
        result["reason"] = reason
    if answer_text is not None:
        result["answer"] = answer_text
    if stale_record_ids:
        result["stale_record_ids"] = stale_record_ids
    if status == "supported":
        result["scope"] = {"person_id": person_id, "project_id": project_id}
    return result


def terms(question: str) -> set[str]:
    return {
        word.casefold().strip(".,?!:;")
        for word in question.split()
        if len(word) > 2 and word.casefold().strip(".,?!:;") not in STOPWORDS
    }


def answer(
    records: list[Record],
    question: str,
    *,
    person_id: str,
    project_id: str,
    now: datetime,
    max_age_hours: int = 24,
) -> dict[str, Any]:
    """Return cited context or a visible fail-closed disposition."""

    scope = [r for r in records if r.person_id == person_id and r.project_id == project_id]
    if not scope:
        return _result(
            "unavailable",
            person_id=person_id,
            project_id=project_id,
            reason="no_matching_scope",
            unknowns=["no_matching_scope"],
        )

    fresh: list[Record] = []
    stale: list[str] = []
    for record in scope:
        if record.status != "available":
            continue
        age = now - parse_time(record.observed_at)
        if age <= timedelta(hours=max_age_hours) and age >= timedelta(0):
            fresh.append(record)
        else:
            stale.append(record.record_id)

    if not fresh:
        return _result(
            "stale",
            person_id=person_id,
            project_id=project_id,
            reason="no_fresh_records",
            stale_record_ids=stale,
            unknowns=["no_fresh_records"],
        )

    query_terms = terms(question)
    ranked = sorted(
        fresh,
        key=lambda record: len(query_terms & terms(record.text)),
        reverse=True,
    )
    selected = [record for record in ranked if query_terms & terms(record.text)]
    if not selected:
        return _result(
            "uncertain",
            person_id=person_id,
            project_id=project_id,
            reason="fresh_records_do_not_support_question",
            unknowns=["fresh_records_do_not_support_question"],
        )

    citations = [
        {
            "record_id": record.record_id,
            "source": record.source,
            "observed_at": record.observed_at,
            "window": {"start": record.window_start, "end": record.window_end},
        }
        for record in selected[:3]
    ]
    return _result(
        "supported",
        person_id=person_id,
        project_id=project_id,
        answer_text=" ".join(record.text for record in selected[:3]),
        citations=citations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("question")
    parser.add_argument("--person", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--max-age-hours", type=int, default=24)
    args = parser.parse_args()
    records = [Record.from_dict(item) for item in json.loads(args.records.read_text())]
    result = answer(
        records,
        args.question,
        person_id=args.person,
        project_id=args.project,
        now=parse_time(args.now),
        max_age_hours=args.max_age_hours,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "supported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
