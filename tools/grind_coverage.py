"""Report actionable work at an owner's handoff from a scoped local roster.

This is an operations read. It never opens research sources, admits a job,
queues a notification, edits the roster or changes a scientific decision.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def actionable(state, owner, *, now=None):
    path = Path(state) / "work-coverage.json"
    if not path.is_file():
        return []
    if path.stat().st_size > 65536:
        return ["Inspect the oversized work-coverage record"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if payload["owner"] != owner or not payload["active"]:
            return []
        instant = now or datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(payload["until"])
        if instant >= deadline:
            return []
        actions = []
        for row in payload["work"]:
            host, card, status = row["host"], row["card"], row["state"]
            if status in ("build", "admit", "file", "recover"):
                actions.append(f"{host} {card}: {status}")
            elif status in ("running", "building", "waiting", "closed"):
                if not row.get("evidence"):
                    actions.append(f"{host} {card}: reconcile missing evidence")
                elif status != "closed" and instant >= datetime.fromisoformat(row["review_by"]):
                    actions.append(f"{host} {card}: verify the expired {status} disposition")
            else:
                actions.append(f"{host} {card}: resolve unknown disposition")
        return actions
    except (ValueError, TypeError, KeyError, OSError):
        return ["Reconcile the invalid work-coverage record"]


def stop_reason(actions):
    if not actions:
        return None
    return ("The research work roster has actionable work. Continue the first available "
            "item and update its evidence. " + " | ".join(actions[:6]))


if __name__ == "__main__":
    from codex_common import STATE, database, get
    with database(STATE) as db:
        current_owner = get(db, "owner")
    print(json.dumps({"actionable": actionable(STATE, current_owner)}, indent=2))
