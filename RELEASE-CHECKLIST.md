# Release checklist

This is a reviewable publication checklist. It does not publish or modify any
external account.

## Ready in the local release candidate

- [x] Narrow problem statement and honest boundary.
- [x] Standard-library implementation with no runtime dependency.
- [x] Synthetic fixture data only.
- [x] Supported, stale, uncertain, and unavailable outcomes.
- [x] Structured citations with source and covered time window.
- [x] README, reviewer demo, license, and changelog.
- [x] Packaging metadata and console entry point.
- [x] CI workflow for Python 3.10, 3.11, and 3.12.
- [x] Local browser console for reconciliation, context admission, and audit readback.
- [x] Five focused tests recorded in `PROOF.md`.

## Before adding it to a public résumé

1. Review the repository name, author metadata, and README wording.
2. Run the clean-checkout install and demo from a fresh virtual environment.
3. Run the test suite and confirm the CI workflow is green.
4. Create a versioned release tag after the source is reviewed.
5. Add the public URL to the résumé, LinkedIn draft, and application answer bank.
6. Record the public URL and release tag in the candidate dossier.

The résumé currently describes this as an **independent release candidate** so
the application does not point reviewers at a repository that has not been
published.
