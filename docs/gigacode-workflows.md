# GigaCode workflow quick reference

Use this alongside the selected skill and its routed references. Paths below
are relative to the installed extension, not the vault. The examples are
synthetic fixtures tested against the existing portable core.

## Find the core

Resolve PRODUCT_ROOT from the loaded skills/<name>/SKILL.md (two parent
directories), then use:

```bash
CORE="$PRODUCT_ROOT/scripts/claude-obsidian.py"
python3 "$CORE" doctor --vault "$VAULT"
```

Read the selected skill and installed AGENTS.md once. For routine vault work,
start with this reference, the matching example and the relevant subcommand's
--help. Broad searches through the Python implementation are development work;
they are not a prerequisite for preparing an ordinary transaction. If inspect
rejects a draft, use its concrete error and the relevant reference to correct it.

## Initialize

Pin both the operation ID and UTC timestamp, then preview:

```bash
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 "$CORE" init "$VAULT" --operation-id "$OPERATION_ID" \
  --generated-at "$STAMP" > "$PROPOSALS/init-plan.json"
```

After the operator reviews that plan, repeat the same command arguments with
--approved-plan-sha256 set to approved_plan_sha256 and add --apply.
The vault is created only at apply. Keep plans outside the vault.

## Save and Ingest

Read the current hot cache, active index and relevant existing pages within the
skill's budget. Read the selected input completely. Use the appropriate shape:

- Save: [save.json](../examples/gigacode/save.json).
- Ingest: [ingest.json](../examples/gigacode/ingest.json), paired with
  [the synthetic input](../examples/gigacode/mayak-release-guide.md).

These are examples, not ready-to-apply user plans. Replace the example facts,
paths, operation ID and dates with the actual task. Preserve existing page
content and existing ledger records when merging additions. Use the UTC date
for ledger generated_at; never copy an example date into a real operation.

Build one bundle outside the vault. For each target, record the SHA-256 of the
bytes actually read; use null only when the target must not exist.
CURRENT_SHA256 in the examples must be replaced with the observed hash.
The optional per-write sha256 is omitted in these examples; the core computes
the resulting hashes during inspect.

Save couples the selected note with the active index, log and hot cache.
Ingest also couples source/claim ledgers and source_manifest_updates.
New source pages use address_requests. Let the core expand managed manifest
and address-counter writes; do not edit those files directly.

For a local input already in inbox/ or .raw/, a second raw copy is optional.
Keep the original bytes unchanged and use its vault-relative locator. Compute
content_sha256 from those bytes. To derive the existing core's stable source ID
without reading its implementation:

```python
import hashlib
import sys
from pathlib import Path

product_root = Path("/absolute/installed/extension")
sys.path.insert(0, str(product_root))
from claude_obsidian.ledgers import stable_source_id

payload = Path("/absolute/vault/inbox/my-source.md").read_bytes()
content_sha256 = hashlib.sha256(payload).hexdigest()
source_id = stable_source_id("file", "inbox/my-source.md", content_sha256)
```

Classify actual evidence honestly. The examples use synthetic/unreviewed sources
and provisional claims because their input is fictional. Those classifications
must not turn a fictional source into accepted evidence.

Log/hot content inside a bundle describes the state after successful apply.
Keep “waiting for approval” in the conversational preview, not in the persisted
operation entry. This is a factual distinction; no particular prose style is
required.

```bash
python3 "$CORE" transaction inspect "$PROPOSALS/bundle.json" --vault "$VAULT"
# After review, use approval_sha256 from that exact inspect result:
python3 "$CORE" transaction apply "$PROPOSALS/bundle.json" --vault "$VAULT" \
  --approved-plan-sha256 "$APPROVAL_SHA256"
```

Do not regenerate an approved bundle. A changed bundle needs a fresh inspect
and approval. Repeating the identical operation ID and bundle is idempotent.
After apply, report the actual status, operation ID and changed paths briefly.

## Query and Lint

Query follows wiki/index.md or the active index to relevant canonical pages.
If an optional retrieval index is absent, use the skill's local text-reading
fallback and cite actual page/section locations. Do not build an index or save
the answer as a side effect of a read-only question.

```bash
python3 "$CORE" lint --vault "$VAULT" --format json --strict
```

Strict lint may return nonzero because it found issues. Report those findings;
repair is a separate approved operation. Any saved report belongs outside the
vault. Judge answers by supported facts and file operations, not wording polish.
