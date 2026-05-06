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
- `location_intelligence.upsert_place`
  Creates or updates static places, dynamic subject-following places, and last-known places.
- `location_intelligence.assign_reference_place`
  Assigns a subject-specific reference place.
- `location_intelligence.remove_place`
  Removes a named place and any assignments to it.
- `location_intelligence.clear_reference_place`
  Resets a subject to the default Home reference place.
- `location_intelligence.exclude_person_entity`
  Excludes a specific `person.*` entity from discovery and derived subjects.
- `location_intelligence.include_person_entity`
  Removes a `person.*` entity from the exclusion list.
- `location_intelligence.clear_subject`
  Removes a subject and its current derived state.

## Development notes

The current integration intentionally avoids fake precision:

- discovery only links clearly identifiable `person` and `device_tracker` sources
- defined `person.*` entities can be explicitly excluded from discovery
- fusion uses weighted averaging only when coordinates are reasonably clustered
- confidence is capped by age and source diversity
- persisted recent fixes are used conservatively as last-known fallback
- diagnostics expose explainable intermediate data, stored mappings, and place definitions

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

These are now partially implemented through named places, dynamic `subject` and `last_known`
place kinds, persisted recent fixes, and broader unit coverage. The remaining gap is full
Home Assistant runtime testing with the HA dependency stack installed.
