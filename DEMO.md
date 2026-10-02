# Reviewer demo path

This walkthrough takes about three minutes and uses only the included
fictional records.

## Supported answer

```bash
python3 context_integrity.py fixtures/records.json "Who owns the API?" \
  --person person-a --project project-a --now 2026-10-01T12:00:00Z
```

Point out the `supported` status, the answer text, and the citation containing
the source, observation time, and covered time window.

## Scope refusal

```bash
python3 context_integrity.py fixtures/records.json "Who owns the API?" \
  --person person-c --project project-a --now 2026-10-01T12:00:00Z
```

The result is `unavailable` with `no_matching_scope` and no citations. The
process exits with status 1 so a caller cannot treat the refusal as an answer.

## Freshness refusal

```bash
python3 context_integrity.py fixtures/records.json "What is the old launch date?" \
  --person person-a --project project-a --now 2026-10-01T12:00:00Z \
  --max-age-hours 1
```

The included records are outside the one-hour budget, so the result is
`stale`. Explain that the system keeps the evidence state visible instead of
silently presenting old notes as current context.

## Design question

If asked what would come next, describe authenticated source adapters, explicit
redaction, durable review state, stronger retrieval ranking, and a model behind
the same admission boundary. Keep the admission decision independently
testable.
