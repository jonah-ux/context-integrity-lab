# Changelog

## 0.2.0 - 2026-10-02

- Added the versioned `context-integrity/v1` result envelope.
- Added explicit `ok`, observation, partial, timeout, scope, citation-count,
  and unknown fields for loss-aware downstream evidence adapters.
- Kept refusal states fail-closed while making their reasons machine-readable.

## 0.1.0 - 2026-10-02

- Added exact person/project scope admission.
- Added observation freshness and source availability checks.
- Added structured citations with source and covered time window.
- Added explicit supported, uncertain, stale, and unavailable outcomes.
- Added synthetic fixtures and a six-case standard-library test suite.
- Added public contributor, security, release, and agent usage guides.
- Packaged browser fixtures and static assets so the installed demo works from
  both wheel and source distribution consumers.
