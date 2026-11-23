# Spawn Learning: software_engineering (kernel-plugin-dev-1)

- **KI ID**: `ki-kernel-plugin-ioc-seam-and-shift-left-gate`
- **Domain**: `software_engineering`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-kernel-plugin-dev_20dd44ab` (`kernel-plugin-dev-1`)
- **Proposal ID**: `prop_kernel-plugin-dev-1_5e91c658`

## Transferable Claim
- **Cue**: when developing or refactoring Brain Harness kernel services, ServiceKey protocols, or internal plugins
- **Lesson**: audit IoC provides/requires DAG topology and AST documentation mirroring with plugin_auditor.py, enforce @dataclass(slots=True, frozen=True) domain models, and run shift-left pre-commit SAST/secret scans before committing
- **Evidence**: standalone plugin_auditor.py dag (cycles=0) + PreCommitSecurityService passed=True (findings=0); ICM 10/10

## Rationale
Catches manifest-vs-code drift, cyclic ServiceKey dependencies, and accidental credential leaks prior to CI.
