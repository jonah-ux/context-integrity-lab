# Context Integrity Lab

![Context Integrity Lab admission flow](docs/context-integrity-admission.svg)

**Status:** independent public release candidate.

Context Integrity Lab is a small deterministic demonstration of how an AI
assistant can refuse to answer from the wrong person, stale context, unavailable
sources, or fresh but irrelevant evidence. It is intentionally useful without
an API key or model account.

This is an independent portfolio project. It uses fictional records only and
has no model calls, network connection, credentials, employer code, meeting
transcripts, or customer data.

## What it demonstrates

- Exact person and project scope before retrieval.
- Observation time separated from the source's covered time window.
- Freshness checks with a visible stale disposition.
- Structured citations containing source and provenance window.
- Explicit `supported`, `uncertain`, `stale`, and `unavailable` outcomes.
- A reconciliation view that keeps duplicate and ambiguous identities visible.
- Deterministic behavior that can be tested without an external service.

## Fresh-clone install

```bash
git clone --branch v0.2.0 --depth 1 https://github.com/jonah-ux/context-integrity-lab.git
cd context-integrity-lab
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

The package has no runtime dependencies and supports Python 3.10 through the
versions exercised by CI. Installation is local-only; it does not contact a
provider or upload fixture data.

## Usage

Run the CLI against the included synthetic records:

```bash
context-integrity fixtures/records.json "Who owns the API?" \
  --person person-a --project project-a --now 2026-10-01T12:00:00Z
```

The command prints one JSON result to stdout. A supported answer exits `0`.
Expected refusal states such as a missing scope or stale evidence exit `1` so
callers cannot mistake a refusal for an answer. Invalid command input uses the
standard argparse usage exit. Malformed JSON, missing record fields, and bad
timestamps instead return a `context-integrity/error/v1` JSON envelope and exit
`2`; the envelope includes a stable error code, `observed=false`, and no
citations. Valid admission results use the versioned `context-integrity/v1`
envelope with explicit `ok`, `observed`, `partial`, `timed_out`, scope,
citation-count, and `unknowns` fields.

Try the scope refusal without changing the fixture:

```bash
context-integrity fixtures/records.json "Who owns the API?" \
  --person person-c --project project-a --now 2026-10-01T12:00:00Z
```

The included [reviewer walkthrough](DEMO.md) covers supported, scope, and
freshness cases and explains what each result does and does not prove.

The [protocol contract](docs/contracts/context-integrity-v1.md) shows how to
hand the JSON result to Agent Proof without copying raw answer text across the
evidence boundary.

## Admission explorer

Open the [standalone admission explorer](docs/admission-explorer.html) for a visual tour of the supported, stale, and out-of-scope states. It is a single dependency-free HTML file with synthetic browser state; it does not call the local server or any sibling repository.

## Browser console

```bash
context-integrity-demo --port 8765
```

Open `http://127.0.0.1:8765`. The local console exposes two inspectable flows:

1. **Record reconciliation:** classifies new people, matched applications,
   replayed source records, and ambiguous identity holds from a synthetic
   intake batch.
2. **Context admission:** evaluates a question against scoped, time-bounded
   context and displays the structured answer or refusal state with citations.

The browser console keeps state in memory and uses no external service or
credential.

## Development and agent use

Run the focused checks from a fresh checkout:

```bash
python -m py_compile context_integrity.py web_app.py
python -m unittest discover -s tests -v
git diff --check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the review loop and
[AGENTS.md](AGENTS.md) for the safe machine-readable workflow. Changes should
keep the admission decision deterministic, preserve synthetic-only fixtures,
and make refusal states visible.

## Release and security

- [RELEASES.md](RELEASES.md) defines the version, asset, checksum, and rollback
  procedure.
- [SECURITY.md](SECURITY.md) explains how to report a suspected vulnerability
  without posting sensitive details publicly.
- [CHANGELOG.md](CHANGELOG.md) records user-facing changes.

## Public surface audit

Run `python scripts/audit_public_surface.py --json` from a clean checkout. The receipt checks
dependency and license declarations, release-workflow provenance markers, and high-signal secret
patterns across tracked text files. Pass `--dist-dir dist` to compare wheel and sdist bytes with
`SHA256SUMS`; missing artifacts remain `unavailable`.

## Portfolio boundary

This project is evidence of implementation and design judgment. It does not
prove a live meeting product, model accuracy, production scale, or
employer-system integration. A production version would add authenticated
source adapters, durable review state, stronger ranking, redaction, and a
model behind the same admission boundary.
