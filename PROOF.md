# Verification receipt

The project was tested locally on October 2, 2026 using only the synthetic
fixtures in this directory and fresh isolated consumers.

## Test suite

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Result: **6 tests passed**. Coverage includes supported citations, wrong-person
scope, stale evidence, irrelevant fresh evidence, unavailable sources, and the
versioned loss-aware interop envelope.

## CLI behavior

The supported demo returns a cited answer from `calendar-001`, including its
source, observation time, and covered time window. A nonexistent `person-c`
returns:

```json
{"citations": [], "reason": "no_matching_scope", "status": "unavailable"}
```

The unavailable result exits with status 1, which keeps a caller from treating
a failed admission as a successful answer.

## Browser console readback

The local server was opened at `http://127.0.0.1:8766` and the visible console
was exercised with the synthetic fixture:

- Reconciliation showed `created=3`, `matched=1`, `held=1`, and `duplicate=1`.
- The conflicting Jordan Lee email created a distinct person instead of
  silently merging records.
- The name-only Jordan Lee record was held as `ambiguous_name`.
- The replayed `intake-004` record was reported as
  `replayed_source_record`.
- A supported context question returned a citation for `calendar-001`.
- A `person-c` request returned `unavailable` with `no_matching_scope`.

The browser console keeps state in memory and uses only local synthetic data.

## Fresh package consumers

The release candidate was built as both a wheel and a source distribution in a
clean Python 3.11 build environment. Each artifact was installed into its own
fresh virtual environment and checked with `pip check`.

Both consumers exercised:

- `context-integrity --help` and a supported cited answer.
- A wrong-person request returning `unavailable` with
  `no_matching_scope` and exit status `1`.
- `context-integrity-demo` serving `/api/health` and the browser HTML.
- The reconciliation endpoint returning `created=3`, `matched=1`,
  `held=1`, and `duplicate=1`.

The source distribution also rebuilt successfully from its isolated archive.

The installed cross-project consumer path was exercised with the built Context
Integrity Lab, Agent Proof, and Forgeyard artifacts. A supported
`context-integrity/v1` result was normalized and source-bound with Agent Proof,
then composed by Forgeyard through `projection.status.ok` into
`ready_for_review`. The normalized envelope retained scope digests and a
citation count while excluding the answer text and raw person identifier.

The `context-integrity/v1` envelope was also checked as a downstream contract:
its supported result exposes explicit `ok=true`, `observed=true`,
`partial=false`, `timed_out=false`, scope, citation-count, and empty unknowns;
refusal results expose `ok=false` and a stable reason/unknown entry.

## Source and privacy checks

The candidate source archive was built from a clean commit, verified against its
sidecar, and extracted into a separate consumer directory before rerunning the
six-case test suite and supported CLI example. A current-tree secret scan
reported no findings. These checks cover source structure, package behavior,
and synthetic privacy boundaries; they do not claim production deployment,
model accuracy, or external adoption.

## Boundary

The records are fictional. This project has no network calls, model calls,
credentials, employer code, customer data, or meeting transcripts. It proves a
deterministic admission boundary and testable output, not production scale or
model accuracy.
