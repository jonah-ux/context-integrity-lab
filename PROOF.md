# Verification receipt

The project was tested locally on October 2, 2026 using only the synthetic
fixtures in this directory and fresh isolated consumers.

## Test suite

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Result: **5 tests passed**. Coverage includes supported citations, wrong-person
scope, stale evidence, irrelevant fresh evidence, and unavailable sources.

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

## Source and privacy checks

The candidate source archive was built from a clean commit, verified against its
sidecar, and extracted into a separate consumer directory before rerunning the
five-case test suite and supported CLI example. A current-tree secret scan
reported no findings. These checks cover source structure, package behavior,
and synthetic privacy boundaries; they do not claim production deployment,
model accuracy, or external adoption.

## Boundary

The records are fictional. This project has no network calls, model calls,
credentials, employer code, customer data, or meeting transcripts. It proves a
deterministic admission boundary and testable output, not production scale or
model accuracy.
