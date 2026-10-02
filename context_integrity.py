#!/usr/bin/env python3
"""Deterministic provenance and freshness gate for synthetic meeting context."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


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
        return {"status": "unavailable", "reason": "no_matching_scope", "citations": []}

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
        return {
            "status": "stale",
            "reason": "no_fresh_records",
            "stale_record_ids": stale,
            "citations": [],
        }

    query_terms = terms(question)
    ranked = sorted(
        fresh,
        key=lambda record: len(query_terms & terms(record.text)),
        reverse=True,
    )
    selected = [record for record in ranked if query_terms & terms(record.text)]
    if not selected:
        return {
            "status": "uncertain",
            "reason": "fresh_records_do_not_support_question",
            "citations": [],
        }

    citations = [
        {
            "record_id": record.record_id,
            "source": record.source,
            "observed_at": record.observed_at,
            "window": {"start": record.window_start, "end": record.window_end},
        }
        for record in selected[:3]
    ]
    return {
        "status": "supported",
        "answer": " ".join(record.text for record in selected[:3]),
        "citations": citations,
        "scope": {"person_id": person_id, "project_id": project_id},
    }


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
