# Agent usage

This repository is a deterministic, synthetic Python project. Agents may run
local read-only commands, edit source and documentation, and execute the
focused test suite. They must keep the project standalone.

## Safe commands

```bash
python -m py_compile context_integrity.py web_app.py
python -m unittest discover -s tests -v
python context_integrity.py fixtures/records.json "Who owns the API?" \
  --person person-a --project project-a --now 2026-10-01T12:00:00Z
git diff --check
```

## Trust boundaries

- Use only the included fictional fixtures in tests and demos.
- Do not add credentials, private paths, employer data, customer data, meeting
  transcripts, or provider-specific configuration.
- Do not make network calls or change external systems from the test suite.
- Keep machine-readable JSON on stdout and human diagnostics on stderr.
- Treat `supported`, `uncertain`, `stale`, and `unavailable` as distinct states.
- A passing test or local browser demo does not prove production behavior,
  model accuracy, deployment, or external adoption.

Before a release, follow [RELEASES.md](RELEASES.md) and preserve the exact
reviewed commit, artifact checksums, and fresh-consumer results.
