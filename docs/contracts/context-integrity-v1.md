# `context-integrity/v1`

Context Integrity Lab emits one versioned JSON envelope for every admission
decision. The envelope is designed to cross into evidence tools without
turning a refusal or an unknown into a successful answer.

## Required fields

```json
{
  "schema": "context-integrity/v1",
  "status": "supported",
  "ok": true,
  "observed": true,
  "partial": false,
  "timed_out": false,
  "person_id": "person-a",
  "project_id": "project-a",
  "citations": [],
  "citation_count": 0,
  "unknowns": []
}
```

`ok` is true only for `supported`. `observed` means the deterministic gate ran
against the supplied fixture; it does not mean a user saw or accepted the
answer. `partial` and `timed_out` are explicit future-proof fields and remain
false for the synchronous local implementation.

The `status` values are:

- `supported`: fresh scoped records matched the question and citations are
  present.
- `uncertain`: fresh scoped records exist, but they do not support the
  question.
- `stale`: scoped records exist but none are within the freshness window.
- `unavailable`: no record matched the requested person and project.

Refusal states set `ok` to false and include a machine-readable `reason` and
`unknowns` entry. The source and citation text remain in the original result;
downstream evidence adapters decide which bounded fields may cross a trust
boundary.

Future observations are a distinct stale refusal. When every available record
is newer than the requested `now`, the result uses `reason: "future_evidence"`
and lists those IDs in `future_record_ids`. Mixed stale and future records keep
the established `reason: "no_fresh_records"` while exposing
`future_evidence` in `unknowns`.

## CLI input errors

The command-line loader has a separate stable envelope for malformed JSON,
missing record fields, invalid timestamps, and other rejected input:

```json
{
  "schema": "context-integrity/error/v1",
  "status": "error",
  "ok": false,
  "observed": false,
  "partial": false,
  "timed_out": false,
  "person_id": "person-a",
  "project_id": "project-a",
  "citations": [],
  "citation_count": 0,
  "unknowns": ["records_json_invalid"],
  "reason": "records_json_invalid",
  "error": {
    "code": "records_json_invalid",
    "message": "records file is not valid JSON"
  }
}
```

These input refusals exit `2`; they are not evidence that the requested
context exists or does not exist.

## Agent Proof handoff

The public [Agent Proof](https://github.com/jonah-ux/agent-proof) release
recognizes `context-integrity/v1` as a reviewed adapter:

```console
context-integrity fixtures/records.json "Who owns the API?" \
  --person person-a --project project-a --now 2026-10-01T12:00:00Z \
  > artifacts/context.json
agent-proof normalize artifacts/context.json \
  --artifact-root artifacts --out artifacts/context.interop.json
agent-proof verify-interop artifacts/context.interop.json \
  --artifact-root artifacts --require-input
```

The adapter hashes the requested scope, preserves the explicit status and
observation state, and records unknowns without copying the answer text or raw
source values.
