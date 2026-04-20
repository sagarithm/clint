# V2 Release and Versioning Policy

## Purpose
Define predictable release mechanics for library and CLI surfaces.

## Versioning Scheme
Use semantic versioning for package and CLI artifacts.
- Major: breaking changes.
- Minor: backward-compatible features.
- Patch: bug fixes and hardening changes.

## Release Tracks
- Stable: production releases.
- Candidate: pre-production validation releases.
- Development: internal testing builds.

## Release Requirements
- Changelog entry with impact summary.
- Migration notes for behavior and schema changes.
- Rollback procedure documented and tested.
- Version tags aligned across package and CLI.

## Deprecation Lifecycle
1. Mark feature or API as deprecated.
2. Provide migration path and timeline.
3. Emit warnings for at least one minor release cycle.
4. Remove in next major release.

## Documentation Synchronization
No release is complete unless docs reflect exact shipped behavior,
including examples and command/API references.
