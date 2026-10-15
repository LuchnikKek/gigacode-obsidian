#!/usr/bin/env python3
"""Integration checks for the optional Qwen smoke runner (no model calls)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/manual/qwen_run.py"


class QwenRunnerTests(unittest.TestCase):
    def run_case(self, code: str, timeout: str = "5") -> tuple[subprocess.CompletedProcess[str], Path, tempfile.TemporaryDirectory[str]]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        workspace = root / "workspace"
        profile = root / "profile"
        workspace.mkdir()
        profile.mkdir()
        (profile / "settings.json").write_text(json.dumps({"env": {"TEST_KEY": "PRIVATE_TEST_KEY"}}))
        prompt = root / "prompt.txt"
        prompt.write_text("synthetic smoke")
        cli = root / "fake-qwen"
        cli.write_text("#!" + sys.executable + "\n" + code)
        cli.chmod(0o700)
        output = root / "output"
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--cli", str(cli), "--workspace", str(workspace),
             "--profile", str(profile), "--prompt", str(prompt), "--output", str(output),
             "--model", "test-model", "--timeout", timeout, "--grace", "0.2"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return result, output, directory

    def test_preserves_exit_and_redacts_trace(self) -> None:
        self.assertTrue(RUNNER.is_file(), "missing optional Qwen smoke runner")
        result, output, _ = self.run_case(
            "import json,sys\n"
            "print(json.dumps({'type':'assistant','message':{'content':["
            "{'type':'thinking','thinking':'PRIVATE_REASONING'},"
            "{'type':'tool_use','name':'read_file','input':{'path':'PRIVATE_TEST_KEY'}}]}}),flush=True)\n"
            "print(json.dumps({'type':'result','is_error':False,'result':'READY','session_id':'fixture'}),flush=True)\n"
            "print('PRIVATE_TEST_KEY',file=sys.stderr)\n"
            "sys.exit(7)\n"
        )
        self.assertEqual(7, result.returncode, result.stderr)
        summary = json.loads((output / "summary.json").read_text())
        self.assertEqual(7, summary["exit_code"])
        self.assertFalse(summary["timed_out"])
        self.assertEqual(1, summary["tool_calls"])
        self.assertEqual("READY", summary["result"]["result"])
        self.assertIsNotNone(summary["result_at_seconds"])
        contents = "\n".join(p.read_text() for p in output.iterdir())
        self.assertNotIn("PRIVATE_TEST_KEY", contents)
        self.assertNotIn("PRIVATE_REASONING", contents)
        self.assertIn("[REDACTED]", contents)

    @unittest.skipIf(os.name == "nt", "runner targets Linux/macOS/WSL")
    def test_deadline_kills_an_unresponsive_cli(self) -> None:
        self.assertTrue(RUNNER.is_file(), "missing optional Qwen smoke runner")
        result, output, _ = self.run_case(
            "import signal,time\n"
            "signal.signal(signal.SIGINT,signal.SIG_IGN)\n"
            "signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
            "time.sleep(30)\n", "0.3"
        )
        self.assertEqual(124, result.returncode, result.stderr)
        summary = json.loads((output / "summary.json").read_text())
        self.assertTrue(summary["timed_out"])
        self.assertIsNone(summary["result"])
        self.assertLess(summary["duration_seconds"], 5)


if __name__ == "__main__":
    unittest.main()
