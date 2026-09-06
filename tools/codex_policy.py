"""Codex shell policy: destructive denies, narrow reads, otherwise native approval.

The previous Claude classifier treated arbitrary Python/node scripts, git pushes,
and relative recursive deletion as auto-approvable. Those are not permission rules:
script contents and resolved deletion targets cannot be proved from a command head.
Codex's workspace sandbox handles ordinary authorized work; unknown commands retain
its normal approval flow. Never emit an allow for a request to leave that sandbox.
"""
from __future__ import annotations

import re
import shlex


def classify(command: str) -> tuple[str, str]:
    if not isinstance(command, str) or not command.strip():
        return "default", "No command to classify"
    # Only command positions; quoted fixture prose must not block file editing.
    if re.search(r"(?:^|[;|&\n])\s*(?:shutdown|restart-computer|stop-computer|"
                 r"mkfs(?:\.\w+)?|diskpart|bcdedit)(?:\s|$)", command, re.I):
        return "deny", "Machine shutdown or disk/boot modification"
    if re.search(r"^\s*(?:rm\s+-[a-z]*[rf][a-z]*\s+|"
                 r"Remove-Item\s+(?:(?:-Recurse|-Force|-LiteralPath|-Path)\s+)*)"
                 r"[\"']?(?:/|[A-Za-z]:[\\/]?)[\"']?\s*$", command, re.I):
        return "deny", "Recursive removal of a filesystem root"
    if re.search(r"^\s*format\s+[A-Za-z]:", command, re.I):
        return "deny", "Formatting a drive"
    # No parser pretends to prove safety across two different shell grammars.
    if re.search(r"[;&|<>`$\n\r{}()]", command):
        return "default", "Compound or dynamic command: native permission flow"
    if re.search(r"https?://|(?:^|[/\\\s])\.env(?:\b|\.)|\.ssh|\.aws|"
                 r"bus\.conf|auth\.json|API_KEY|SECRET_KEY", command, re.I):
        return "default", "Network or credential-bearing command"
    try:
        words = shlex.split(command.replace("\\", "/"))
    except ValueError:
        return "default", "Shell parse uncertain"
    if not words:
        return "default", "Empty command"
    head = words[0].rsplit("/", 1)[-1].lower().removesuffix(".exe")
    if head == "git":
        args = words[1:]
        if args[:1] == ["--no-pager"]:
            args = args[1:]
        if args and args[0] in {"status", "diff", "log", "show", "rev-parse", "ls-files"}:
            if not any(a.startswith(("--ext-diff", "--textconv", "--output")) for a in args):
                return "allow", "Static Git inspection within the current sandbox"
    elif head == "rg":
        if not any(a.startswith(("--pre", "--hostname-bin")) for a in words[1:]):
            return "allow", "Static repository search within the current sandbox"
    elif head in {"get-content", "get-childitem", "get-item", "get-process", "get-date",
                  "get-location", "get-command", "test-path", "get-filehash", "pwd",
                  "head", "tail", "wc", "cat", "ls", "whoami"}:
        return "allow", "Static inspection within the current sandbox"
    return "default", "Use Codex's normal permission flow"


def decision(payload: dict):
    inp = payload.get("tool_input") or {}
    result, reason = classify(inp.get("command", inp.get("cmd", "")))
    # Explicit escalation remains subject to the platform's approval reviewer.
    if result == "allow" and (inp.get("sandbox_permissions") == "require_escalated"
                              or payload.get("hook_event_name") == "PermissionRequest"):
        result, reason = "default", "Escalation requires native approval"
    return result, reason
