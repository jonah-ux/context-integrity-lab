# Contributing

Thanks for helping improve Context Integrity Lab. Keep changes small,
deterministic, and easy to inspect from a clean checkout.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

The project uses the Python standard library at runtime. Do not add a provider,
network service, credential, private fixture, or employer data to make a test
pass.

## Change expectations

1. Start with a synthetic fixture that expresses the expected state.
2. Add or update a focused test for supported and refusal behavior.
3. Keep JSON output stable and send human-facing diagnostics to stderr.
4. Update `README.md`, `DEMO.md`, or `CHANGELOG.md` when the user-facing
   contract changes.
5. Run the syntax check, test suite, and `git diff --check` before opening a
   pull request.

## Pull requests

Describe the user-visible behavior, the fixture or test that proves it, and the
remaining boundary. Do not include secrets, private URLs, customer records, or
unverified production claims.
