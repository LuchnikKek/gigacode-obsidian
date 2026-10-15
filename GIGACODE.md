# gigacode-obsidian

This extension provides source-cited Obsidian knowledge workflows for GigaCode.
Qwen Code is a compatibility host and reads this same file.

Use the extension's skills when the user asks to work with an Obsidian vault.
The primary workflows are wiki, save, wiki-ingest, wiki-query and wiki-lint.
Follow the selected SKILL.md and its relative references. For the five primary
workflows, use docs/gigacode-workflows.md and its tested Save/Ingest examples
before exploring implementation code. Adapt the examples to the actual input
and current vault bytes; examples never authorize an apply.

Resolve the installed product root from the absolute location of the loaded
skill: skills/<name>/SKILL.md is two directories below the product root.
Run scripts/claude-obsidian.py from that root with Python 3.11 or newer.
Never infer the product root from the current directory, a hard-coded host
cache path, or the selected vault. Read the installed AGENTS.md for the shared
vault and transaction contract.

The product installation and user vault are separate directories. Select the
vault through explicit --vault, CLAUDE_OBSIDIAN_VAULT, workspace config, then
current-directory discovery. Preserve these upstream configuration names.

All writes go through the portable core's inspected transactions and approval
hashes. Query and lint are read-only. No automatic Git commits, transcript
capture, remote fetching or dependency installation.

This bootstrap version uses sequential workflows without subagents or host
hooks. Additional inherited skills remain available, but only the five primary
workflows are in the initial validation scope. State missing capabilities
honestly; never claim a source was read or an operation passed without evidence.
