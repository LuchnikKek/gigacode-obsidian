#!/usr/bin/env python3
"""Optional headless Qwen check; use only isolated profiles and synthetic vaults."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default="qwen")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=float, default=480)
    parser.add_argument("--grace", type=float, default=3)
    parser.add_argument("--max-tool-calls", type=int, default=50)
    args = parser.parse_args()
    if os.name == "nt":
        parser.error("run this manual check in Linux, macOS or WSL")
    if args.timeout <= 0 or args.grace < 0:
        parser.error("timeout must be positive and grace non-negative")
    profile = args.profile.resolve()
    settings = json.loads((profile / "settings.json").read_text(encoding="utf-8"))
    secrets = [v for v in settings.get("env", {}).values() if isinstance(v, str) and v]

    def redact(text: str) -> str:
        for secret in secrets:
            text = text.replace(secret, "[REDACTED]")
        return text

    def scrub(value: Any) -> Any:
        if isinstance(value, str):
            return redact(value)
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        return value

    args.output.mkdir(parents=True, exist_ok=False)
    command = [
        args.cli, "--model", args.model, "--extensions", "gigacode-obsidian",
        "--approval-mode", "default", "--allowed-tools", "run_shell_command",
        "read_file", "read_many_files", "list_directory", "glob", "grep_search",
        "skill", "write_file", "edit", "--max-session-turns", "30",
        "--max-tool-calls", str(args.max_tool_calls),
        "--max-wall-time", f"{args.timeout:g}s", "--output-format", "stream-json",
        "--prompt", args.prompt.read_text(encoding="utf-8"),
    ]
    environment = {**os.environ, "QWEN_HOME": str(profile),
                   "QWEN_USAGE_STATISTICS_ENABLED": "false", "PYTHONDONTWRITEBYTECODE": "1"}
    started = time.monotonic()
    finished = threading.Event()
    timed_out = threading.Event()
    summary: dict[str, Any] = {
        "model": args.model, "tool_calls": 0, "last_tool_result_at_seconds": None,
        "result_at_seconds": None, "result": None,
    }
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errors, (
        args.output / "events.jsonl"
    ).open("w", encoding="utf-8") as trace:
        process = subprocess.Popen(
            command, cwd=args.workspace.resolve(), env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors,
            text=True, encoding="utf-8", start_new_session=True,
        )

        def stop_group(sig: int) -> None:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass

        def deadline() -> None:
            if finished.is_set():
                return
            timed_out.set()
            stop_group(signal.SIGINT)
            if not finished.wait(args.grace):
                stop_group(signal.SIGKILL)

        timer = threading.Timer(args.timeout, deadline)
        timer.start()
        try:
            assert process.stdout is not None
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                elapsed = round(time.monotonic() - started, 3)
                kind = event.get("type")
                if kind in ("assistant", "user"):
                    blocks = event.get("message", {}).get("content", [])
                    if not isinstance(blocks, list):
                        continue
                    blocks = [b for b in blocks if b.get("type") in ("tool_use", "tool_result", "text")]
                    if not blocks:
                        continue
                    event = {"type": kind, "content": blocks}
                    for block in blocks:
                        if block["type"] == "tool_use":
                            summary["tool_calls"] += 1
                            print(f"{elapsed}s tool: {block.get('name')}", flush=True)
                        if block["type"] == "tool_result":
                            summary["last_tool_result_at_seconds"] = elapsed
                elif kind == "result":
                    event = {k: event[k] for k in
                             ("type", "subtype", "is_error", "result", "error", "usage", "session_id")
                             if k in event}
                    summary["result"] = scrub(event)
                    summary["result_at_seconds"] = elapsed
                else:
                    continue
                trace.write(json.dumps({"elapsed_seconds": elapsed, **scrub(event)}, ensure_ascii=False) + "\n")
                trace.flush()
            code = process.wait()
        finally:
            finished.set()
            timer.cancel()
            stop_group(signal.SIGKILL)
            process.wait()
            timer.join()
        errors.seek(0)
        (args.output / "stderr.txt").write_text(redact(errors.read()), encoding="utf-8")
    summary.update(exit_code=code, timed_out=timed_out.is_set(),
                   duration_seconds=round(time.monotonic() - started, 3))
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(scrub(summary), ensure_ascii=False), flush=True)
    return 124 if timed_out.is_set() else (code if code >= 0 else 128 - code)


if __name__ == "__main__":
    raise SystemExit(main())
