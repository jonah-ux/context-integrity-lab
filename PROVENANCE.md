# Release provenance

Context Integrity Lab publishes source releases from annotated `vMAJOR.MINOR.PATCH` tags. The
release workflow validates the tag against `pyproject.toml`, builds a wheel and sdist, writes
`SHA256SUMS`, and exercises a clean installed consumer before publishing prerelease assets.

The public audit checks these workflow markers, the dependency/license declarations, and the tracked
source surface. It does not claim a complete supply-chain guarantee. Artifact verification is
`pass` only with an explicit distribution directory and checksum manifest; otherwise it remains
`unavailable`.
