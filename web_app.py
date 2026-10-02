#!/usr/bin/env python3
"""Local browser demo for reconciliation and context-integrity decisions."""

from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from context_integrity import Record, answer, parse_time


ROOT = Path(__file__).resolve().parent
PACKAGE_ASSETS = ROOT / "context_integrity_lab"
FIXTURES = ROOT / "fixtures"
if not FIXTURES.exists():
    FIXTURES = PACKAGE_ASSETS / "fixtures"
STATIC_ROOT = ROOT / "static"
if not STATIC_ROOT.exists():
    STATIC_ROOT = PACKAGE_ASSETS / "static"


def normalize(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def normalize_email(value: str | None) -> str:
    return (value or "").strip().casefold()


def reconcile(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify synthetic intake records with explainable decisions."""

    people: list[dict[str, Any]] = []
    applications: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    audit: list[dict[str, Any]] = []

    for record in records:
        source_id = str(record.get("source_record_id", "")).strip()
        event_id = str(record.get("event_id", "")).strip()
        name = " ".join(str(record.get("name", "")).split())
        email = normalize_email(record.get("email"))
        if not source_id or not event_id or not name:
            decision = "held"
            reason = "missing_identity"
            person_id = None
        elif source_id in seen_sources:
            decision = "duplicate"
            reason = "replayed_source_record"
            person_id = None
        else:
            email_matches = [p for p in people if normalize_email(p["email"]) == email and email]
            name_matches = [p for p in people if normalize(p["name"]) == normalize(name)]
            if len(email_matches) == 1:
                person_id = email_matches[0]["person_id"]
                decision = "matched"
                reason = "matched_email"
            elif len(name_matches) > 1 and not email:
                person_id = None
                decision = "held"
                reason = "ambiguous_name"
            elif len(name_matches) == 1 and not email_matches:
                existing_email = normalize_email(name_matches[0]["email"])
                if email and existing_email not in {"", email}:
                    person_id = f"person-{len(people) + 1:03d}"
                    people.append({"person_id": person_id, "name": name, "email": email})
                    decision = "created"
                    reason = "conflicting_email"
                else:
                    person_id = name_matches[0]["person_id"]
                    decision = "matched"
                    reason = "matched_name"
            else:
                person_id = f"person-{len(people) + 1:03d}"
                people.append({"person_id": person_id, "name": name, "email": email})
                decision = "created"
                reason = "new_person"

        if decision in {"matched", "created"} and person_id:
            application_id = f"application-{len(applications) + 1:03d}"
            applications.append({
                "application_id": application_id,
                "person_id": person_id,
                "event_id": event_id,
                "source_record_id": source_id,
                "status": record.get("status", "received"),
            })
        else:
            application_id = None

        if source_id:
            seen_sources.add(source_id)
        item = {
            "source_record_id": source_id,
            "name": name,
            "event_id": event_id,
            "decision": decision,
            "reason": reason,
            "person_id": person_id,
            "application_id": application_id,
        }
        decisions.append(item)
        audit.append({
            "event": "reconcile.decision",
            "source_record_id": source_id,
            "decision": decision,
            "reason": reason,
        })

    summary = {key: sum(item["decision"] == key for item in decisions) for key in ("created", "matched", "duplicate", "held")}
    return {
        "summary": summary,
        "people": people,
        "applications": applications,
        "decisions": decisions,
        "audit": audit,
    }


class DemoState:
    def __init__(self) -> None:
        self.records = json.loads((FIXTURES / "intake.json").read_text(encoding="utf-8"))
        self.context_records = [
            Record.from_dict(item)
            for item in json.loads((FIXTURES / "records.json").read_text(encoding="utf-8"))
        ]
        self.lock = threading.Lock()
        self.last_reconciliation: dict[str, Any] | None = None
        self.audit: list[dict[str, Any]] = []

    def run_reconciliation(self) -> dict[str, Any]:
        with self.lock:
            result = reconcile(self.records)
            self.last_reconciliation = result
            self.audit.extend(result["audit"])
            return result

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = answer(
            self.context_records,
            str(payload.get("question", "")),
            person_id=str(payload.get("person_id", "")),
            project_id=str(payload.get("project_id", "")),
            now=parse_time(str(payload.get("now", "2026-10-01T12:00:00Z"))),
            max_age_hours=int(payload.get("max_age_hours", 24)),
        )
        with self.lock:
            self.audit.append({
                "event": "context.answer",
                "status": result["status"],
                "reason": result.get("reason", "supported"),
            })
        return result


STATE = DemoState()


class Handler(BaseHTTPRequestHandler):
    server_version = "ContextIntegrityDemo/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self.send_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
        elif path == "/app.js":
            self.send_file(STATIC_ROOT / "app.js", "text/javascript; charset=utf-8")
        elif path == "/styles.css":
            self.send_file(STATIC_ROOT / "styles.css", "text/css; charset=utf-8")
        elif path == "/api/health":
            self.send_json({"status": "ok", "service": "context-integrity-demo", "time": datetime.now(timezone.utc).isoformat()})
        elif path == "/api/overview":
            result = STATE.last_reconciliation or reconcile(STATE.records)
            self.send_json({"input_count": len(STATE.records), "reconciliation": result, "audit": STATE.audit[-30:]})
        elif path == "/api/records":
            self.send_json({"records": STATE.records})
        else:
            self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/reconcile":
            self.send_json(STATE.run_reconciliation())
        elif path == "/api/ask":
            self.send_json(STATE.ask(payload))
        else:
            self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Context Integrity Lab running at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
