#!/usr/bin/env python3
"""Native extension packaging and relocated core integration checks."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claude_obsidian.release import _load_config, _selected

ENTRYPOINTS = ("gigacode-extension.json", "qwen-extension.json", "GIGACODE.md")
ADAPTER_FILES = ENTRYPOINTS + (
    "docs/gigacode-workflows.md", "examples/gigacode/save.json",
    "examples/gigacode/ingest.json", "examples/gigacode/mayak-release-guide.md",
)
PRIMARY_SKILLS = ("wiki", "save", "wiki-ingest", "wiki-query", "wiki-lint")


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


class GigaCodeExtensionTests(unittest.TestCase):
    def manifest(self, name: str) -> dict[str, Any]:
        path = ROOT / name
        self.assertTrue(path.is_file(), f"missing native extension entrypoint: {name}")
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict)
        return value

    def test_native_hosts_share_resolvable_context_and_skills(self) -> None:
        primary = self.manifest("gigacode-extension.json")
        compatibility = self.manifest("qwen-extension.json")
        self.assertEqual(primary, compatibility)
        self.assertEqual("gigacode-obsidian", primary["name"])
        context = ROOT / primary["contextFileName"]
        self.assertEqual("GIGACODE.md", context.name)
        self.assertTrue(context.is_file())
        self.assertEqual({}, primary["hooks"], "do not auto-load Claude hooks")
        for skill in PRIMARY_SKILLS:
            self.assertTrue((ROOT / primary["skills"] / skill / "SKILL.md").is_file())

    def test_release_selects_native_entrypoints_and_omits_claude_workers(self) -> None:
        config, errors = _load_config(ROOT)
        self.assertEqual([], errors)
        assert config is not None
        for name in ADAPTER_FILES:
            self.assertTrue(_selected(name, config), f"release omits {name}")
        for path in (ROOT / "agents").glob("*.md"):
            self.assertFalse(_selected(path.relative_to(ROOT).as_posix(), config))

    def test_examples_apply_as_reviewed_transactions(self) -> None:
        for name in ("save", "ingest"):
            with self.subTest(example=name), tempfile.TemporaryDirectory() as directory:
                example = ROOT / "examples" / "gigacode" / (name + ".json")
                self.assertTrue(example.is_file(), f"missing tested example: {name}")
                parent = Path(directory)
                vault = parent / "vault"
                core = [sys.executable, str(ROOT / "scripts/claude-obsidian.py")]
                init = core + ["init", str(vault), "--generated-at", "2020-01-01T00:00:00Z", "--operation-id", "example-setup"]
                preview = json.loads(subprocess.check_output(init, text=True))
                subprocess.check_output(init + ["--apply", "--approved-plan-sha256", preview["approved_plan_sha256"]], text=True)
                source = ROOT / "examples/gigacode/mayak-release-guide.md"
                shutil.copyfile(source, vault / "inbox/mayak-release-guide.md")
                bundle = json.loads(example.read_text(encoding="utf-8"))
                # Examples demonstrate a shape; real preconditions come from this vault.
                for path in bundle["expected_hashes"]:
                    target = vault / path
                    bundle["expected_hashes"][path] = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
                candidate = parent / "bundle.json"
                candidate.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
                before = snapshot(vault)
                inspect_cmd = core + ["transaction", "inspect", str(candidate), "--vault", str(vault)]
                plan = json.loads(subprocess.check_output(inspect_cmd, text=True))
                self.assertTrue(plan["valid"])
                self.assertEqual(before, snapshot(vault))
                apply_cmd = core + ["transaction", "apply", str(candidate), "--vault", str(vault), "--approved-plan-sha256", plan["approval_sha256"]]
                result = json.loads(subprocess.check_output(apply_cmd, text=True))
                self.assertEqual("complete", result["status"])
                self.assertEqual(plan["changed_paths"], result["changed_paths"])
                after = snapshot(vault)
                subprocess.check_output(apply_cmd, text=True)
                self.assertEqual(after, snapshot(vault))
                self.assertEqual(source.read_bytes(), (vault / "inbox/mayak-release-guide.md").read_bytes())
                if name == "ingest":
                    claims = json.loads((vault / "wiki/meta/ledgers/claim-ledger.json").read_text())["claims"]
                    self.assertTrue(claims)
                    self.assertTrue(all(claim["assessment"] == "provisional" for claim in claims.values()))

    def test_relocated_selected_package_doctor_is_read_only(self) -> None:
        config, errors = _load_config(ROOT)
        self.assertEqual([], errors)
        assert config is not None
        manifest = self.manifest("gigacode-extension.json")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            installed = parent / "extension с пробелами"
            installed.mkdir()
            candidates = subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-files", "-z"], text=True
            ).split("\0")
            for relative in sorted(set(candidates) | set(ADAPTER_FILES)):
                if not relative or not _selected(relative, config):
                    continue
                source = ROOT / relative
                if source.is_file():
                    target = installed / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            self.assertTrue((installed / manifest["contextFileName"]).is_file())
            self.assertFalse((installed / "agents").exists())
            for relative in ADAPTER_FILES:
                self.assertTrue((installed / relative).is_file(), relative)
            for skill in PRIMARY_SKILLS:
                self.assertTrue((installed / "skills" / skill / "SKILL.md").is_file())
            vault = parent / "отдельный vault"
            shutil.copytree(installed / "templates" / "vault", vault)
            before = snapshot(vault)
            environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            environment.pop("CLAUDE_OBSIDIAN_VAULT", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts" / "claude-obsidian.py"),
                    "doctor",
                    "--vault",
                    str(vault),
                ],
                cwd=vault,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertTrue(report["ok"])
            self.assertEqual(str(vault), report["vault_root"])
            self.assertEqual("explicit", report["selection_source"])
            self.assertEqual(before, snapshot(vault))


if __name__ == "__main__":
    unittest.main()
