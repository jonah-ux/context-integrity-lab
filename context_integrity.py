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
ERROR_SCHEMA = "context-integrity/error/v1"

_REQUIRED_RECORD_FIELDS = (
    "record_id",
    "source",
    "person_id",
    "project_id",
    "observed_at",
    "window_start",
    "window_end",
    "text",
)
_RECORD_FIELDS = frozenset((*_REQUIRED_RECORD_FIELDS, "status"))


class InputBoundaryError(ValueError):
    """A stable, safe-to-render refusal at the CLI input boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        record_index: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.record_index = record_index

    def with_record_index(self, index: int) -> "InputBoundaryError":
        if self.record_index is not None:
            return self
        return InputBoundaryError(
            self.code,
            self.message,
            field=self.field,
            record_index=index,
        )


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty RFC 3339 string")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("timestamp must be a valid RFC 3339 string") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


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
        if not isinstance(value, dict):
            raise InputBoundaryError("record_invalid", "record must be a JSON object")
        missing = sorted(set(_REQUIRED_RECORD_FIELDS) - set(value))
        if missing:
            raise InputBoundaryError(
                "record_missing_fields",
                f"record is missing required field(s): {', '.join(missing)}",
            )
        unknown = sorted(set(value) - _RECORD_FIELDS)
        if unknown:
            raise InputBoundaryError(
                "record_unknown_fields",
                f"record contains unsupported field(s): {', '.join(unknown)}",
            )
        for field in _REQUIRED_RECORD_FIELDS:
            field_value = value.get(field)
            if not isinstance(field_value, str) or not field_value.strip():
                raise InputBoundaryError(
                    "record_field_invalid",
                    f"record field '{field}' must be non-empty text",
                    field=field,
                )
        if "status" in value and (
            not isinstance(value["status"], str) or not value["status"].strip()
        ):
            raise InputBoundaryError(
                "record_field_invalid",
                "record field 'status' must be non-empty text",
                field="status",
            )
        for field in ("observed_at", "window_start", "window_end"):
            try:
                parse_time(value[field])
            except ValueError as error:
                raise InputBoundaryError(
                    "record_timestamp_invalid",
                    f"record field '{field}' must be a valid timezone-aware timestamp",
                    field=field,
                ) from error
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
    future_record_ids: list[str] | None = None,
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
    if future_record_ids:
        result["future_record_ids"] = future_record_ids
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
    future: list[str] = []
    for record in scope:
        if record.status != "available":
            continue
        age = now - parse_time(record.observed_at)
        if age < timedelta(0):
            future.append(record.record_id)
        elif age <= timedelta(hours=max_age_hours):
            fresh.append(record)
        else:
            stale.append(record.record_id)

    if not fresh:
        reason = "future_evidence" if future and not stale else "no_fresh_records"
        unknowns = [reason]
        if future and reason != "future_evidence":
            unknowns.append("future_evidence")
        return _result(
            "stale",
            person_id=person_id,
            project_id=project_id,
            reason=reason,
            stale_record_ids=stale,
            future_record_ids=future,
            unknowns=unknowns,
        )

    query_terms = terms(question)
    ranked = sorted(
        fresh,
        key=lambda record: (
            -len(query_terms & terms(record.text)),
            record.record_id,
            record.source,
        ),
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


def _load_records(path: Path) -> list[Record]:
    """Load and validate the complete synthetic record boundary."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InputBoundaryError("records_file_not_found", "records file does not exist") from error
    except IsADirectoryError as error:
        raise InputBoundaryError("records_file_invalid", "records path is not a regular file") from error
    except OSError as error:
        raise InputBoundaryError("records_file_unreadable", "records file could not be read") from error
    except UnicodeDecodeError as error:
        raise InputBoundaryError("records_encoding_invalid", "records file must be UTF-8 JSON") from error
    except json.JSONDecodeError as error:
        raise InputBoundaryError("records_json_invalid", "records file is not valid JSON") from error
    if not isinstance(payload, list):
        raise InputBoundaryError("records_root_invalid", "records JSON root must be an array")
    records: list[Record] = []
    for index, item in enumerate(payload):
        try:
            records.append(Record.from_dict(item))
        except InputBoundaryError as error:
            raise error.with_record_index(index) from error
    return records


def _error_result(
    error: InputBoundaryError,
    *,
    person_id: str,
    project_id: str,
) -> dict[str, Any]:
    """Build a stable machine-readable refusal without exposing a traceback."""

    details: dict[str, Any] = {"code": error.code, "message": error.message}
    if error.field is not None:
        details["field"] = error.field
    if error.record_index is not None:
        details["record_index"] = error.record_index
    return {
        "schema": ERROR_SCHEMA,
        "status": "error",
        "ok": False,
        "observed": False,
        "partial": False,
        "timed_out": False,
        "person_id": person_id,
        "project_id": project_id,
        "citations": [],
        "citation_count": 0,
        "unknowns": [error.code],
        "reason": error.code,
        "error": details,
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
    try:
        if args.max_age_hours < 0:
            raise InputBoundaryError(
                "max_age_invalid",
                "max-age-hours must be zero or greater",
                field="max-age-hours",
            )
        records = _load_records(args.records)
        try:
            now = parse_time(args.now)
        except ValueError as error:
            raise InputBoundaryError(
                "now_timestamp_invalid",
                "now must be a valid timezone-aware timestamp",
                field="now",
            ) from error
        result = answer(
            records,
            args.question,
            person_id=args.person,
            project_id=args.project,
            now=now,
            max_age_hours=args.max_age_hours,
        )
    except InputBoundaryError as error:
        result = _error_result(error, person_id=args.person, project_id=args.project)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "supported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
