# GigaCode extension M1 design

## Accepted scope
The product is a GigaCode extension, developed in the existing fork and tested
with Qwen Code on Linux/macOS/WSL. GigaCode naming takes priority. No push,
publication, new dependencies, or native Windows write implementation.

M1 delivers native extension loading and a relocated, read-only core smoke test.
The five primary workflows are wiki, save, wiki-ingest, wiki-query and wiki-lint.
The upstream skill/reference tree is retained to preserve relative references;
its additional workflows are not claimed as validated by this milestone.

## Packaging
Use gigacode-extension.json as the primary manifest and qwen-extension.json as
the compatibility entry point. Both load the same short GIGACODE.md and skills.
Keep Python package names, vault schemas and source skills unchanged.
Disable host hooks explicitly. Exclude the upstream Claude-specific agents from
the release archive; their source files remain in the repository.
Use the existing audited release builder and its allowlist.

## Acceptance
- The paired manifests select the same context and portable skill tree.
- A release contains both manifests, context and portable dependencies.
- Qwen 0.25.2 installs the native package without Claude conversion.
- Its loader discovers the primary skills, loads GIGACODE.md and no host hooks
  or Claude-specific subagents.
- The extracted core's doctor runs from a separate synthetic vault with spaces
  and Unicode in paths, and leaves vault bytes unchanged.
- Run the repository's exact make test command and report all failures.

## Explicit acceptance exceptions
The upstream same-size runtime-read test fails before our changes because fast
writes in WSL can retain the same mtime. The user requested that the test remain
unchanged and that the failure be recorded.
The configured provider rejects both offered free model slugs with HTTP 404.
The user requested checks without a model for now. Model-driven skill execution
and direct GigaCode execution are therefore deferred, not reported as passing.
