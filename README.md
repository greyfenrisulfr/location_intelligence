# Home Assistant Location Intelligence

Home Assistant custom integration scaffold for generic spatial awareness across people, devices, animals, vehicles, assets, and places.

## Scope

This repository now includes a working backend baseline for:

- source discovery from `person`, `device_tracker`, and `zone`
- source classification
- persistent subject/source mapping
- source fusion
- confidence scoring
- distance and bearing calculations
- derived Home Assistant entities
- diagnostics and services

## Repository layout

```text
custom_components/location_intelligence/
```

## Current backend services

- `location_intelligence.refresh`
  Triggers discovery refresh and estimate rebuild.
- `location_intelligence.ingest_fix`
  Injects a location fix for a subject from a named source.
- `location_intelligence.link_source`
  Persists a subject-to-source mapping without adding a manual fix.
- `location_intelligence.clear_subject`
  Removes a subject and its current derived state.

## Development notes

The current integration intentionally avoids fake precision:

- discovery only links clearly identifiable `person` and `device_tracker` sources
- fusion uses weighted averaging only when coordinates are reasonably clustered
- confidence is capped by age and source diversity
- diagnostics expose explainable intermediate data and stored mappings

## Release management

Versioned releases use Git tags in the form `vX.Y.Z`.

1. Run `python scripts/bump_version.py X.Y.Z`.
2. Review `CHANGELOG.md` and commit the release changes.
3. Create and push the tag: `git tag vX.Y.Z && git push origin main --tags`.
4. GitHub Actions will validate the tag, build the integration archive, and publish a GitHub Release.

Pull requests are also grouped automatically by Release Drafter to keep release notes maintainable.

## Next steps

1. Add subject-specific reference places beyond Home Assistant home coordinates.
2. Support temporary and dynamic places such as vehicle, group leader, and last-known position.
3. Persist selected recent fixes for restart continuity.
4. Add more complete Home Assistant tests around entity setup and service flows.
