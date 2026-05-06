# Home Assistant Location Intelligence

Home Assistant custom integration and frontend card scaffold for generic spatial awareness across people, devices, animals, vehicles, assets, and places.

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

It also includes a frontend workspace placeholder for future custom cards.

## Repository layout

```text
custom_components/location_intelligence/
frontend/cards/location-intelligence-card/
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

## Next steps

1. Add real Home Assistant entity discovery for `person`, `device_tracker`, and zone-aware sources.
2. Persist subject/source mapping in storage.
3. Build richer derived entities for direction, range, and confidence bands.
4. Implement frontend cards against the backend service and entity model.

