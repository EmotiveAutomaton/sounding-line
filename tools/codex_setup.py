"""Prepare/review then install the workspace's Codex hooks and user-local bus config.

No model changes, permission-profile changes, daemon restarts, or hook-trust bypass.
The install receipt holds exact previous bytes outside Git for reversible cutover.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

from codex_common import REPO, STATE, atomic_json, database, put

EVENTS = ("PreToolUse", "PermissionRequest", "PostToolUse", "SessionStart",
          "PostCompact", "UserPromptSubmit", "Stop", "Interrupt", "SessionEnd")


def hook_config(repo=REPO):
    script = (repo / "tools/codex_hooks.py").as_posix()
    handler = {"type": "command", "command": f'python3 -B "{script}"',
               "commandWindows": f'python -B "{script}"', "timeout": 20,
               "statusMessage": "Sounding Line operating contract"}
    return {"description": "Sounding Line: scoped operating hooks; review exact definitions before activation",
            "hooks": {event: [{"hooks": [{**handler, "timeout": 3 if event in
                         {"Interrupt", "SessionEnd"} else 20}]}] for event in EVENTS}}


def prepare(workspace, codex, thread):
    workspace = workspace.resolve()
    if workspace not in {REPO, REPO.parent}:
        raise ValueError("Workspace must be the repository or its enclosing project folder")
    plan = {"workspace": str(workspace), "hooks_path": str(workspace / ".codex/hooks.json"),
            "hooks": hook_config(), "thread": thread, "prepared_at": time.time(),
            "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(set((REPO / "tools").glob("codex_*.py")) | {
                            REPO / "tools" / name for name in (
                                "lintio.py", "lint_hook.py", "theory_lint.py", "design_lint.py",
                                "verify_locks.py", "start_codex_watch.ps1")})}}
    atomic_json(STATE / "install-plan.json", plan)
    if not (STATE / "watch.json").exists():
        atomic_json(STATE / "watch.json", {"codex": str(Path(codex).resolve()),
            "interval_seconds": 60, "fallback_seconds": 28800,
            "manifests": ["results/phase_2_4_stage_8/QUEUE_MANIFEST.json"],
            "queue_inventory": True,
            "paths": ["results/phase_2_4_stage_8/CURATOR_PACKET_FINAL.md",
                      "results/phase_2_4_stage_8/INTERRUPTS.json"]})
    print(f"Review {STATE / 'install-plan.json'}. No external configuration changed.")


def install():
    plan = json.loads((STATE / "install-plan.json").read_text(encoding="utf-8"))
    for name, expected in plan["sources"].items():
        if hashlib.sha256((REPO / "tools" / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"{name} changed after preparation; prepare a fresh reviewable plan")
    receipt_path = STATE / "install-receipt.json"
    if receipt_path.exists():
        raise ValueError("Already installed; inspect receipt before replacing a live installation")
    user_dir = Path.home() / ".codex/sounding-line"
    backup = user_dir / ("backup-" + str(int(time.time())))
    backup.mkdir(parents=True, exist_ok=False)
    target = Path(plan["hooks_path"])
    content = plan["hooks"]
    # Merge unrelated hook definitions instead of replacing someone's configuration.
    if target.exists():
        previous = json.loads(target.read_text(encoding="utf-8-sig"))
        for event, groups in previous.get("hooks", {}).items():
            content["hooks"].setdefault(event, []).extend(groups)
        for key, value in previous.items():
            if key not in {"description", "hooks"}:
                content[key] = value
    bus = user_dir / "bus.conf"
    old_bus = Path.home() / ".claude/hooks/bus.conf"
    startup = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup/SoundingLineCodexWatch.vbs"
    startup_script = ('CreateObject("WScript.Shell").Run "powershell.exe -NoProfile -WindowStyle Hidden '
        '-File ""' + str(REPO / "tools/start_codex_watch.ps1") + '""", 0, False\r\n')
    writes = [(target, (json.dumps(content, indent=2) + "\n").encode()),
              (startup, startup_script.encode("utf-16"))]
    if not bus.exists():
        writes.append((bus, old_bus.read_bytes() if old_bus.exists()
                       else b"BASE=http://192.168.0.2:8093\n"))
    receipt = {"installed_at": time.time(), "backup": str(backup), "files": [],
               "hook_trust": "requires exact-definition review in Codex /hooks"}
    for n, (path, data) in enumerate(writes):
        before = backup / str(n)
        existed = path.exists()
        if existed:
            before.write_bytes(path.read_bytes())
        receipt["files"].append({"path": str(path), "before": str(before) if existed else None,
                                  "after_sha256": hashlib.sha256(data).hexdigest()})
    # Receipt is written BEFORE mutations, so a partial install can be rolled back.
    atomic_json(receipt_path, receipt)
    for path, data in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    with database() as db:
        owner = db.execute("SELECT value FROM meta WHERE key='owner'").fetchone()
        if owner and json.loads(owner[0]) != plan["thread"]:
            raise ValueError("Owner changed during install; do not start the watcher")
        put(db, "owner", plan["thread"])
        put(db, "owner_phase", "active")
    print("Installed scoped hooks, user-local bus configuration, and hidden logon watcher.")
    print("Exact hook definitions still require Codex's normal trust review; no trust was bypassed.")
    refresh()


def rollback():
    (STATE / "watch.cancel").write_text("rollback\n")
    receipt_path = STATE / "install-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    # Validate every target before changing any of them; preserve later user edits.
    for entry in receipt["files"]:
        path = Path(entry["path"])
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["after_sha256"]:
            raise ValueError(f"Installed file changed; reconcile manually before rollback: {path}")
    for entry in reversed(receipt["files"]):
        path = Path(entry["path"])
        if entry["before"]:
            path.write_bytes(Path(entry["before"]).read_bytes())
        else:
            path.unlink()
    receipt["rolled_back_at"] = time.time()
    atomic_json(receipt_path, receipt)
    print("External hooks and startup restored; watcher cancelled. Scientific processes untouched.")


def refresh():
    """Refresh only this dispatcher's definitions, preserving other projects' hooks."""
    plan = json.loads((STATE / "install-plan.json").read_text(encoding="utf-8"))
    for name, expected in plan["sources"].items():
        if hashlib.sha256((REPO / "tools" / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Sources changed after prepare")
    receipt_path = STATE / "install-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    script = (REPO / "tools/codex_hooks.py").as_posix()
    for path in dict.fromkeys([Path(plan["hooks_path"]), REPO / ".codex/hooks.json"]):
        old = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
        kept = {}
        for event, groups in old.get("hooks", {}).items():
            for group in groups:
                handlers = [h for h in group.get("hooks", []) if script not in
                            (h.get("command", "") + h.get("commandWindows", "")).replace("\\", "/")]
                if handlers:
                    kept.setdefault(event, []).append({**group, "hooks": handlers})
        for event, groups in plan["hooks"]["hooks"].items():
            kept.setdefault(event, []).extend(groups)
        new = {**old, "hooks": kept}
        entry = next((x for x in receipt["files"] if Path(x["path"]) == path), None)
        if entry is None:
            before = Path(receipt["backup"]) / str(len(receipt["files"]))
            if path.exists():
                before.write_bytes(path.read_bytes())
            entry = {"path": str(path), "before": str(before) if path.exists() else None}
            receipt["files"].append(entry)
        data = (json.dumps(new, indent=2) + "\n").encode()
        entry["after_sha256"] = hashlib.sha256(data).hexdigest()
        atomic_json(receipt_path, receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if REPO.parent == Path(plan["workspace"]):
        # The enclosing non-Git workspace does not discover nested repository skills.
        path = REPO.parent / ".agents/skills/grind/SKILL.md"
        data = ("---\nname: grind\ndescription: Process the Sounding Line queue, results, and "
                "reporting under its standing grind contract.\n---\n\n"
                f"Read and follow `{REPO.name}/.agents/skills/grind/SKILL.md` in this "
                "workspace. That repository skill is canonical. Read "
                f"`{REPO.name}/AGENTS.md` and its stage-specific precedence before acting.\n").encode()
        entry = next((x for x in receipt["files"] if Path(x["path"]) == path), None)
        if entry is None:
            if path.exists():
                raise ValueError("An enclosing grind skill already exists; reconcile it before replacement")
            entry = {"path": str(path), "before": None}
            receipt["files"].append(entry)
        elif path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != entry["after_sha256"]:
            raise ValueError("The enclosing grind skill was modified after installation")
        entry["after_sha256"] = hashlib.sha256(data).hexdigest()
        atomic_json(receipt_path, receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print("Updated both independently discovered project roots; unrelated hooks retained.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["prepare", "install", "refresh", "rollback"])
    p.add_argument("--workspace", type=Path, default=REPO.parent)
    p.add_argument("--codex", default=shutil.which("codex"))
    p.add_argument("--thread", default=os.environ.get("CODEX_THREAD_ID"))
    args = p.parse_args()
    if args.command == "prepare":
        if not args.codex or not args.thread:
            p.error("--codex and --thread are required to prepare")
        prepare(args.workspace, args.codex, args.thread)
    elif args.command == "install":
        install()
    elif args.command == "refresh":
        refresh()
    else:
        rollback()


if __name__ == "__main__":
    main()
