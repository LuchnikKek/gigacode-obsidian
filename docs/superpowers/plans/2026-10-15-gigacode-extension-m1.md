# GigaCode extension M1 Implementation Plan

> Execution: implement inline in the existing codex/gigacode-adapter branch.
> Use executing-plans and verification-before-completion; obtain one final
> independent review. No push.

**Goal:** Package and verify the native GigaCode extension through Qwen's loader.
**Architecture:** Two native manifests share GIGACODE.md and the upstream portable
skills/core. The existing release allowlist defines the installed artifact.
**Tech Stack:** Python standard library, Bash, Qwen Code 0.25.2.
**Spec:** ../specs/2026-10-15-gigacode-extension-m1-design.md

## Constraints and review focus
Preserve upstream runtime behavior and schemas. No dependencies or copied skills.
Check relocated paths, archive omissions, inherited Claude hooks/agents,
manifest divergence and accidental writes during doctor.
Report the accepted upstream baseline failure and deferred model checks honestly.

### Task 1: Extension package contract
Files: tests/test_gigacode_extension.py, gigacode-extension.json,
qwen-extension.json, GIGACODE.md, config/release-allowlist.json.
- [x] Write failing package-entrypoint and release-selection tests.
- [x] Observe expected failures before adding native manifests.
- [x] Add the paired manifests/context and narrow release policy changes.
- [x] Run the new tests and package validator.

### Task 2: Relocated installation
Files: tests/test_gigacode_extension.py, docs/gigacode-extension.md, README.md.
- [x] Exercise the selected package from a different synthetic vault.
- [x] Document native extension installation, scope and known acceptance gaps.
- [x] Run make test; preserve and report the accepted baseline failure.
- [x] Run unaffected test files and shell/contracts/package checks to avoid
      treating the suite's early exit as coverage of later files.
- [x] Commit only the reviewed task files locally and build/audit the release.
- [x] Install the archive with Qwen and inspect native loaded components offline.
- [x] Obtain independent review, address relevant findings, record evidence.
