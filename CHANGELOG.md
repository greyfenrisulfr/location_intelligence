# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, with an `Unreleased` section that is finalized during each release.

## [Unreleased]

- 

## [0.1.2] - 2026-05-06

- Added persistent exclusion support for specific `person.*` entities.
- Excluded person entities are now skipped during discovery and removed from derived subjects.
- Added Home Assistant services to exclude or re-include person entities without editing code.
- Extended diagnostics and documentation to expose configured person exclusions.

## [0.1.1] - 2026-05-06

- Added named reference places with per-subject assignment.
- Added dynamic `subject` and `last_known` place kinds for moving or fallback references.
- Persisted bounded recent-fix history for restart continuity and conservative last-known fallback.
- Expanded derived sensors and diagnostics with reference-place distance, bearing, and direction data.
- Added focused unit tests for place resolution and recent-fix history behavior.

## [0.1.0] - 2026-05-06

- Initial Home Assistant Location Intelligence integration scaffold.
- Added release management workflows, version validation, and packaged releases.
- Implemented discovery for `person`, `device_tracker`, and `zone` sources.
- Added persistent subject-to-source mapping and dynamic derived sensors.
- Added diagnostics, service workflows, and focused unit tests for core backend logic.
