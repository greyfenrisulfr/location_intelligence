# Home Assistant Location Intelligence

Home Assistant custom integration scaffold for generic spatial awareness across people, devices, animals, vehicles, assets, and places.

## Scope

This repository starts the backend architecture for:

- source discovery
- source classification
- subject/source mapping
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
  Triggers discovery refresh.
- `location_intelligence.ingest_fix`
  Injects a location fix for a subject from a named source.

## Development notes

The current scaffold intentionally avoids fake precision:

- discovery returns no inferred subjects by default
- fusion uses weighted averaging only when coordinates are reasonably clustered
- confidence is capped by age and source diversity
- diagnostics expose explainable intermediate data

## Release management

Versioned releases use Git tags in the form `vX.Y.Z`.

1. Run `python scripts/bump_version.py X.Y.Z`.
2. Review `CHANGELOG.md` and commit the release changes.
3. Create and push the tag: `git tag vX.Y.Z && git push origin main --tags`.
4. GitHub Actions will validate the tag, build the integration archive, and publish a GitHub Release.

Pull requests are also grouped automatically by Release Drafter to keep release notes maintainable.

## Next steps

1. Add real Home Assistant entity discovery for `person`, `device_tracker`, and zone-aware sources.
2. Persist subject/source mapping in storage.
3. Build richer derived entities for direction, range, and confidence bands.
4. Expand derived entities, diagnostics, and service workflows for production use.
