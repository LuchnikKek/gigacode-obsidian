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

## Live M2 results and bounded follow-up

On 2026-10-16, Qwen 0.25.2 with deepseek/deepseek-v4-flash-0731 exercised the
five primary workflows in WSL. Save, Ingest, Query and Lint completed, with
operator continuations for Save/Ingest and one review correction to proposed
log/hot wording. Init wrote the exact approved files, but its CLI process did
not return a final result within the test limit. Query/Lint preserved vault
bytes; identical Save/Ingest reapply created no duplicates.

Version 0.1.1 adds a [short workflow reference](gigacode-workflows.md) and
tested synthetic Save/Ingest examples. This is an adapter/documentation change.
It does not redesign the inherited provenance or transaction architecture.
Evaluate supported facts, approved file changes and data preservation; prose
style and model verbosity are observations, not adapter failures.

## Repeatable Qwen checks

The optional standard-library runner is tests/manual/qwen_run.py. It is not
part of vault mutation logic and makes no model calls during make test.

Use a fresh workspace and a separate QWEN_HOME for each independent scenario.
Configure only the selected model/provider credentials in that profile, keeping
settings.json private. Do not copy old project memory, hooks or MCP settings.
For isolated checks in the tested Qwen version, add this settings object:

```json
{
  "memory": {
    "enableManagedAutoMemory": false,
    "enableManagedAutoDream": false,
    "enableAutoSkill": false
  },
  "telemetry": {"enabled": false}
}
```

These are test-host settings, not GigaCode requirements or changes to the
user's normal Qwen profile. The installed Qwen headless implementation waits
for pending memory tasks before emitting its result. In one paired check of the
same approved init operation, memory enabled took 120.1 seconds versus 26.8
seconds disabled; both completed successfully. The earlier 371-second hang was
not reproduced. Model/provider variability remains a possible contributor.

Install the audited archive into the isolated profile and run a scoped prompt:

```bash
QWEN_HOME="$PROFILE" qwen extensions install "$ARCHIVE" --scope user --consent
python3 tests/manual/qwen_run.py --profile "$PROFILE" --workspace "$WORKSPACE" \
  --prompt "$PROMPT_FILE" --output "$NEW_OUTPUT_DIRECTORY" \
  --model deepseek/deepseek-v4-flash-0731 --timeout 480 --max-tool-calls 50
```

The runner preserves CLI exit status independently from the model's result,
records tool/result timing, strips thinking blocks and redacts profile env
values from exported logs. Its outer deadline interrupts then kills only its
own process group if the CLI does not exit. Exit 124 denotes that deadline.
Use only synthetic vaults: allowed shell/file tools are not an OS sandbox.

Keep preview and apply as separate phases with exact hash approval. Snapshot
all vault file hashes before and after Query/Lint and before any unapproved
preview. Use a fresh conversation for Query and verify citations against pages
actually read. Record failures as adapter/core/host/model observations; do not
hide a failed attempt by overwriting its output directory.

## Recorded 0.1.1 acceptance (2026-10-16)

The audited 0.1.1 candidate passed all five synthetic workflows in WSL on the
same DeepSeek model, using separate Qwen profiles with managed memory disabled.
Each CLI phase completed with exit 0 within 480 seconds / 50 tool calls.
Preview and apply remained separate operator-reviewed phases; no continuations
or corrective hints were needed. Approximate CLI durations were:

| Workflow | Preview | Apply / read-only run |
| --- | ---: | ---: |
| Init | 27 s | 87 s |
| Save | 131 s | 48 s |
| Ingest | 266 s | 23 s |
| Query | — | 70 s |
| Lint | — | 95 s |

Input facts differed from the shipped examples. Save preserved selected content
only; Ingest preserved source bytes and four provisional claims. Approved
transaction paths matched actual changes; repeat apply was byte-idempotent.
Query returned the new facts with valid section citations. Lint found exactly
one deliberately broken link; Query/Lint left every vault file hash unchanged.
No memory documents were generated in the five acceptance profiles.

One Save preview response used Chinese despite the requested Russian; the note
and operations were correct. This was recorded as a model-output observation,
not repaired as an adapter defect. These timings are observations from one run,
not a model benchmark or a guarantee. Direct GigaCode/macOS remain untested.

The six adapter/runner checks passed, including real core inspect/apply of both
examples and deadline/redaction checks against a local executable. make test
still reaches the accepted unchanged mtime failure; the remaining 59 transaction
functions, later Python suites and shell/contracts/package checks pass separately.
