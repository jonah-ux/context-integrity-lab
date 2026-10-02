# Release guide

Releases are versioned snapshots of the standalone synthetic CLI. A release is
source and package proof; it is not a production deployment or evidence of
external adoption.

## Prepare a release

1. Review the current `main` commit and confirm the tree contains only intended
   public files.
2. Update `[project].version` in `pyproject.toml` and add a dated entry to
   `CHANGELOG.md`.
3. Run the syntax check, standard-library tests, and `git diff --check`.
4. Build a wheel and source distribution outside the checkout:

   ```bash
   python -m build --sdist --wheel --outdir /tmp/context-integrity-lab-dist
   ```

5. Record the SHA-256 of each artifact and install each one in a fresh virtual
   environment. Run `pip check`, `context-integrity --help`, the supported
   example, and one expected refusal.
6. Push the reviewed commit and create an annotated `vX.Y.Z` tag through the
   repository's normal review path.

## Release assets

Upload the wheel, source distribution, and a `SHA256SUMS` file. Read back the
tag target, release state, asset names, and independent checksums from GitHub.
Download the assets into a new directory and repeat the fresh-install smoke
before describing the release as downloadable.

## Rollback

Keep the previous stable tag available. If an asset or install smoke fails,
mark the release as affected, point readers to the previous tag, and prepare a
new version. Do not rewrite published tags or claim a runtime rollback that was
not performed.
