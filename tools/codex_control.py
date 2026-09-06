"""Inspect and activate reviewed hooks through the installed Codex configuration API.

This starts an API helper, not an agent turn. It never calls thread/start or turn/start.
Only reviewed project definitions are eligible for trust; no wildcard or bypass flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time

from codex_common import REPO, STATE, atomic_json


class Client:
    def __init__(self):
        self.messages = queue.Queue()
        self.counter = 0
        self.err = (STATE / "control-stderr.log").open("a", encoding="utf-8")
        self.proc = subprocess.Popen([shutil.which("codex"), "--strict-config", "app-server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err,
            text=True, encoding="utf-8")
        threading.Thread(target=self.read, daemon=True).start()
        self.call("initialize", {"clientInfo": {"name": "sounding_line_operations", "version": "1.0"},
                                 "capabilities": {"experimentalApi": True}})
        self.send({"method": "initialized"})

    def read(self):
        for line in self.proc.stdout:
            try:
                self.messages.put(json.loads(line))
            except ValueError:
                continue

    def send(self, data):
        self.proc.stdin.write(json.dumps(data) + "\n")
        self.proc.stdin.flush()

    def call(self, method, params):
        self.counter += 1
        self.send({"id": self.counter, "method": method, "params": params})
        while True:
            message = self.messages.get(timeout=30)
            if message.get("id") == self.counter:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def close(self):
        self.proc.terminate()
        self.proc.wait(timeout=10)
        self.err.close()


def owned_hooks(result, plan):
    paths = {str(Path(plan["hooks_path"])), str(REPO / ".codex/hooks.json")}
    expected_commands = {h["commandWindows"] for groups in plan["hooks"]["hooks"].values()
                         for group in groups for h in group["hooks"]}
    found = {}
    for entry in result["data"]:
        if entry["errors"]:
            raise ValueError("Hook discovery returned errors")
        own = [h for h in entry["hooks"] if str(Path(h["sourcePath"])) in paths]
        if len(own) != len(plan["hooks"]["hooks"]):
            raise ValueError(f"Expected one complete hook set in {entry['cwd']}; found {len(own)}")
        for hook in own:
            if hook["command"] not in expected_commands or not hook["enabled"] or hook["matcher"]:
                raise ValueError("Discovered hook differs from the reviewed definition")
            found[hook["key"]] = hook
    return list(found.values())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["inspect", "trust-reviewed", "trust-project"])
    args = p.parse_args()
    plan = json.loads((STATE / "install-plan.json").read_text(encoding="utf-8"))
    client = Client()
    try:
        if args.command == "trust-project":
            # The curator has explicitly authorized this repository's installation.
            path = str(REPO).lower()
            result = client.call("config/value/write", {
                "keyPath": "projects." + json.dumps(path) + ".trust_level",
                "value": "trusted", "mergeStrategy": "upsert"})
            print("Repository project trust recorded:", result["status"])
            return
        result = client.call("hooks/list", {"cwds": [str(REPO.parent), str(REPO)]})
        if args.command == "trust-reviewed":
            for name, expected in plan["sources"].items():
                if hashlib.sha256((REPO / "tools" / name).read_bytes()).hexdigest() != expected:
                    raise ValueError(f"Source changed after review: {name}; prepare again")
            hooks = owned_hooks(result, plan)
            # Preserve a private snapshot, then use Codex's own configuration writer.
            backup = Path.home() / ".codex/sounding-line" / ("config-before-trust-" + str(int(time.time())) + ".toml")
            backup.write_bytes((Path.home() / ".codex/config.toml").read_bytes())
            edits = [{"keyPath": "hooks.state." + json.dumps(h["key"]) + ".trusted_hash",
                      "value": h["currentHash"], "mergeStrategy": "upsert"} for h in hooks]
            receipt = client.call("config/batchWrite", {"edits": edits, "reloadUserConfig": True})
            atomic_json(STATE / "hook-trust-receipt.json", {"at": time.time(), "backup": str(backup),
                        "api_receipt": receipt, "hooks": [{"key": h["key"], "hash": h["currentHash"]} for h in hooks]})
            result = client.call("hooks/list", {"cwds": [str(REPO.parent), str(REPO)]})
            if any(h["trustStatus"] != "trusted" for h in owned_hooks(result, plan)):
                raise ValueError("Codex did not report the reviewed hooks as trusted")
        atomic_json(STATE / "hooks-discovery.json", result)
        for entry in result["data"]:
            ours = [h for h in entry["hooks"] if "sounding-line/tools/codex_hooks.py" in h.get("command", "")]
            print(json.dumps({"cwd": entry["cwd"], "hooks": len(ours),
                              "trust": sorted({h["trustStatus"] for h in ours}),
                              "warnings": entry["warnings"], "errors": entry["errors"]}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
