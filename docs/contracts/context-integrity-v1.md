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
