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
        for name in ENTRYPOINTS:
            self.assertTrue(_selected(name, config), f"release omits {name}")
        for path in (ROOT / "agents").glob("*.md"):
            self.assertFalse(_selected(path.relative_to(ROOT).as_posix(), config))

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
            for relative in sorted(set(candidates) | set(ENTRYPOINTS)):
                if not relative or not _selected(relative, config):
                    continue
                source = ROOT / relative
                if source.is_file():
                    target = installed / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            self.assertTrue((installed / manifest["contextFileName"]).is_file())
            self.assertFalse((installed / "agents").exists())
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
