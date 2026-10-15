# GigaCode extension

gigacode-obsidian packages the upstream claude-obsidian portable core as a
GigaCode extension. Qwen Code is the local compatibility test host.
Linux, macOS and WSL are in scope; native Windows vault writes are not.

## Package contract

- gigacode-extension.json is the primary manifest.
- qwen-extension.json is the compatibility manifest.
- Both load GIGACODE.md and the same skills tree.
- The upstream Python package, vault schemas and configuration names stay intact.
- Empty hooks explicitly disable the inherited Claude lifecycle hooks.
- The release archive omits the Claude-specific agents directory.
- All upstream skills/references are retained for relative-link compatibility.
  The initial validation scope covers wiki, save, wiki-ingest, wiki-query and
  wiki-lint; other workflows are inherited, not newly certified.

Always install the release archive rather than linking the development checkout:
the checkout retains upstream Claude agents for reference and future porting.
Keep each user's vault outside both the checkout and extension installation.

## Build and inspect

Use Python 3.11+ and Bash. With the repository environment activated:

```bash
make test
python3 scripts/claude-obsidian.py release build --output /tmp/gigacode-obsidian.zip
python3 scripts/claude-obsidian.py release audit /tmp/gigacode-obsidian.zip
```

The upstream release builder requires a clean, committed worktree. The build
does not publish, push or create a release.

## Install for local Qwen verification

From a separate test workspace:

```bash
qwen extensions install /tmp/gigacode-obsidian.zip --scope project
qwen extensions list
qwen
```

Inspect the extension in /extensions and its skills in /skills. Qwen 0.25.2
registers primary skills under the extension name, for example
/gigacode-obsidian:wiki-lint. Use the native qwen-extension.json; automatic
conversion of the Claude plugin is not the compatibility test.

For GigaCode, use the corporate CLI's extension installation workflow with the
same archive and gigacode-extension.json. Confirm the installed version's
supported installation syntax rather than substituting Qwen commands blindly.
The public GigaCode documentation confirms extension skills and the GigaCode
manifest; direct installation has not yet been exercised in this environment.

## First workflow

Run the agent from the selected vault or pass an explicit vault path. Ask it to
load the wiki skill and run only doctor against that vault first. Creating a
vault uses the core's init preview followed by apply with the reviewed hash.
The agent must locate Python scripts relative to the installed skill, not the
workspace. Query and lint must leave vault bytes unchanged.

## Update and remove

Install an updated reviewed archive through the host's extension manager.
For Qwen, use qwen extensions update gigacode-obsidian when its recorded source
points to the replaced archive, or uninstall and install the new archive.
Remove the Qwen integration with:

```bash
qwen extensions uninstall gigacode-obsidian
```

The vault is a separate directory and is not part of extension removal.

## Evidence boundaries for M1

M1 verifies native package discovery and a relocated read-only core invocation.
It does not certify model-driven Save/Ingest/Query behavior or direct GigaCode
compatibility. Live model checks were deferred by the owner after the configured
provider returned HTTP 404 for the offered free model routes.

The unchanged upstream test
test_read_runtime_bytes_fails_closed_on_a_same_size_content_change fails in the
local WSL baseline when rapid writes retain the same modification timestamp.
The owner requested recording this result rather than changing the test or core.
Report the full make test result and run later suites separately if it stops
at that test; never present an early exit as a complete green run.

## Recorded offline M1 verification (2026-10-15)

- Qwen Code 0.25.2 installed the audited ZIP in an isolated QWEN_HOME,
  enabled only for a separate synthetic workspace.
- The actual native loader reported format qwen, GIGACODE.md, 15 inherited
  skills including the five primary workflows, zero subagents and empty hooks.
- Doctor from the installed archive reported ok and left vault file bytes intact.
- Three new package/relocation tests and package validation passed.
- make test reproduced the accepted upstream baseline failure described above.
  All 59 other transaction test functions, later Python suites, and the
  test-shell, test-contracts and test-package targets passed separately.
- An independent read-only review reported no actionable M1 findings.
- No live model workflow, direct GigaCode run, macOS run, push or publication
  is claimed by this evidence.
