# Contributing

## Branch and PR guidance

- Use focused pull requests with clear titles.
- Apply one of these labels when possible so release notes categorize changes:
  - `feature`
  - `fix`
  - `docs`
  - `maintenance`
  - `breaking`

## Preparing a release

1. Update versions with `python scripts/bump_version.py X.Y.Z`.
2. Move relevant items from `Unreleased` in `CHANGELOG.md` into a new version header.
3. Commit the release changes.
4. Tag the release with `vX.Y.Z`.
5. Push `main` and the tag.

GitHub Actions will create the release and attach a packaged `custom_components/location_intelligence` archive.

