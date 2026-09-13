"""Finite Gear 3 Round 1 accounting, used only by runners/gear3.py.

DESIGN CHECK: LESSONS sections 3-5 and Round 1 sections 2/5/6. Under
NULL and ALTERNATIVE the same finite reservations apply. Oversized or duplicate
owners refuse before dispatch; restart cannot reset money or absolute expiry.
Unknown provider outcomes retain their complete reservation. This is an
accounting guard, never evidence of a scientific effect or an actual invoice.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import uuid

CAMPAIGN = "G3-S10-READER-1"
SPEC_SHA256 = "6fbd1e32b63db00d8350812ab7d627e06d4ab6ef87a3d8fc3c1b199fda4596f9"
NODE_CENTS = {"P": 300, "A": 1700, "B": 700, "C": 900, "D": 400, "Reserve": 1000}
RATE_PER_SECOND = Decimal("0.000542") + 2 * Decimal("0.0000131") + 32 * Decimal("0.00000222")
RESOURCE_PROFILE = {"gpu": "L40S", "cpu_request": 2, "cpu_limit": 2,
                    "memory_request_mib": 32768, "memory_limit_mib": 32768,
                    "max_containers": 1, "concurrency": 1, "retries": 0}
CACHE_RESOURCE_PROFILE = {**RESOURCE_PROFILE, "gpu": None, "memory_request_mib": 4096, "memory_limit_mib": 4096}


def authoritative_ledger(repo: Path) -> Path:
    """All worktrees use the original checkout's ledger, never their own copy."""
    common = subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=repo, text=True).strip()
    gitdir = (repo / common).resolve()
    if gitdir.name != ".git" or not gitdir.is_dir():
        raise ValueError("cannot establish canonical Git ledger owner")
    return gitdir.parent / "results" / "gear3_ledger.json"


def capped_cost_cents(seconds: int, overhead_cents: int, *, cache=False) -> int:
    if type(seconds) is not int or not 1 <= seconds <= 86400 or type(overhead_cents) is not int or overhead_cents < 0:
        raise ValueError("invalid bounded duration or overhead")
    rate=2*Decimal('0.0000131')+4*Decimal('0.00000222') if cache else RATE_PER_SECOND
    return int((rate * seconds * 100).to_integral_value(rounding=ROUND_CEILING)) + overhead_cents


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf8", newline="\n") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        for attempt in range(20):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 19: raise
                time.sleep(0.1)
    finally:
        temporary.unlink(missing_ok=True)


class CampaignLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(".lock")  # same lock as the legacy entry point
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise RuntimeError("ledger already owned; no dispatch or stale-lock reclamation") from None
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump({"pid": os.getpid(), "at": time.time()}, stream)
                stream.flush(); os.fsync(stream.fileno())
            data = json.loads(self.path.read_text(encoding="utf8")) if self.path.exists() else {"runs": [], "cap_approvals": []}
            yield data
            atomic_json(self.path, data)
        finally:
            lock.unlink()

    def enroll(self, approval: str, spec: Path):
        if not approval.strip() or hashlib.sha256(spec.read_bytes()).hexdigest() != SPEC_SHA256:
            raise ValueError("campaign requires recorded specific approval and unchanged source")
        with self.transaction() as data:
            campaigns = data.setdefault("campaigns", {})
            frozen = {"campaign": CAMPAIGN, "spec_sha256": SPEC_SHA256, "total_cents": 5000,
                      "ordinary_cents": 4000, "initial_cents": 2000, "node_cents": NODE_CENTS,
                      "resources": RESOURCE_PROFILE, "approval": approval}
            if CAMPAIGN in campaigns:
                if campaigns[CAMPAIGN]["authorization"] != frozen:
                    raise ValueError("authorization is immutable; enrollment cannot reset allowance")
            else:
                campaigns[CAMPAIGN] = {"authorization": frozen, "at": time.time()}

    @staticmethod
    def totals(data):
        rows = [r for r in data["runs"] if r.get("campaign_id") == CAMPAIGN]
        if any(type(r.get("booked_cents")) is not int or r["booked_cents"] < 0 for r in rows):
            raise ValueError("malformed campaign cost history")
        return {node: sum(r["booked_cents"] for r in rows if r["node"] == node) for node in NODE_CENTS}

    def reserve(self, invocation: str, node: str, command: list[str], profile: dict,
                seconds: int, overhead_cents: int, *, approval: str, now: float | None = None,
                recovery_of: str | None = None, cache=False):
        now = time.time() if now is None else now
        if not math.isfinite(now) or node not in NODE_CENTS or not invocation or not approval.strip():
            raise ValueError("invalid invocation authorization")
        if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in invocation):
            raise ValueError('unsafe invocation identifier')
        if not command or any(not isinstance(c, str) or not c for c in command):
            raise ValueError("concrete argument-vector command required")
        if type(cache) is not bool or (cache and node not in {'P','Reserve'}):raise ValueError('undeclared cache reservation')
        cost = capped_cost_cents(seconds, overhead_cents,cache=cache)
        resources=CACHE_RESOURCE_PROFILE if cache else RESOURCE_PROFILE
        with self.transaction() as data:
            auth = data.get("campaigns", {}).get(CAMPAIGN, {}).get("authorization")
            if not auth or auth["spec_sha256"] != SPEC_SHA256 or auth["total_cents"] != 5000:
                raise ValueError("campaign is not enrolled under its ratified cap")
            existing = [r for r in data["runs"] if r.get("campaign_id") == CAMPAIGN and r.get("invocation_id") == invocation]
            if existing:
                if len(existing) != 1: raise ValueError("duplicate invocation ledger records")
                row = existing[0]
                for k, v in {"node": node, "command": command, "profile": profile, "reserved_cents": cost,
                             "duration_cap_seconds": seconds, "approval": approval, "recovery_of": recovery_of,
                             "resources":resources}.items():
                    if row[k] != v: raise ValueError("resume changes frozen invocation")
                # A caller may inspect this receipt; it is never permission to submit twice.
                return {**row, "existing_reservation": True}
            if any(r.get("status") in {"RESERVED", "SUBMITTED", "CANCEL_PENDING", "LAUNCHED"} or (r.get("status") == "UNKNOWN" and not r.get("owner_ended")) for r in data["runs"]):
                raise ValueError("another cloud owner has not ended")
            if node!='Reserve' and profile.get('job_sha256') and any(r.get('campaign_id')==CAMPAIGN and r.get('profile',{}).get('job_sha256')==profile['job_sha256'] for r in data['runs']):
                raise ValueError('the frozen job already has an invocation; no duplicate scientific dispatch')
            if node == "Reserve":
                original = [r for r in data["runs"] if r.get("campaign_id") == CAMPAIGN and r.get("invocation_id") == recovery_of]
                if len(original) != 1 or original[0].get("owner_ended") is not True:
                    raise ValueError("recovery requires verified prior owner termination")
                if any(r.get("recovery_of") == recovery_of for r in data["runs"]):
                    raise ValueError("only one recorded recovery per invocation")
                if now>=original[0]['expires_at']:raise ValueError('recovery cannot reset an expired block clock')
            elif recovery_of is not None:
                raise ValueError("repair cannot consume a scientific branch silently")
            totals = self.totals(data)
            if totals[node] + cost > NODE_CENTS[node] or sum(totals.values()) + cost > 5000:
                raise ValueError("campaign or branch cap exceeded before dispatch")
            if node != "Reserve" and sum(v for k,v in totals.items() if k != "Reserve") + cost > 4000:
                raise ValueError("ordinary science cap exceeded")
            if node in {"P", "A"} and totals["P"] + totals["A"] + cost > 2000:
                raise ValueError("initial release cap exceeded")
            row = {"campaign_id": CAMPAIGN, "invocation_id": invocation, "node": node,
                   "command": command, "profile": profile, "resources": resources,
                   "duration_cap_seconds": seconds, "expires_at": min(now+seconds,original[0]['expires_at']) if recovery_of else now+seconds, "ts": now,
                   "reserved_cents": cost, "booked_cents": cost, "overhead_cents": overhead_cents,
                   "approval": approval, "campaign_authorization": auth, "recovery_of": recovery_of,
                   "status": "RESERVED", "owner_ended": False, "provider_charge_cents": None,
                   "service_estimate_cents": None, "est_actual_dollars": cost / 100,
                   "cost_basis": "entire capped reservation; not an invoice", "events": []}
            data["runs"].append(row)
            return dict(row)

    def transition(self, invocation: str, state: str, *, call_id=None, owner_ended=False,
                   service_estimate_cents=None, evidence=None):
        allowed = {"RESERVED": {"SUBMITTED", "UNKNOWN", "CANCELLED"},
                   "SUBMITTED": {"COMPLETE", "FAILED", "UNKNOWN", "CANCEL_PENDING"},
                   "CANCEL_PENDING": {"CANCELLED", "UNKNOWN"},
                   "UNKNOWN": {"COMPLETE", "FAILED", "CANCELLED"}}
        with self.transaction() as data:
            rows = [r for r in data["runs"] if r.get("campaign_id") == CAMPAIGN and r.get("invocation_id") == invocation]
            if len(rows) != 1: raise ValueError("unknown invocation")
            row = rows[0]
            if state not in allowed.get(row["status"], set()): raise ValueError("invalid owner transition")
            if state == "SUBMITTED" and not call_id: raise ValueError("persist actual call identity")
            if state in {"COMPLETE", "FAILED", "CANCELLED"} and (not owner_ended or not evidence):
                raise ValueError("terminal transition requires owner termination evidence")
            if service_estimate_cents is not None and (type(service_estimate_cents) is not int or service_estimate_cents < 0):
                raise ValueError("invalid service estimate")
            row["events"].append({"at": time.time(), "from": row["status"], "to": state, "evidence": evidence})
            row.update(status=state, owner_ended=owner_ended,
                       service_estimate_cents=service_estimate_cents)
            if call_id is not None: row["call_id"] = call_id
            # Never lower booked cost from a service estimate. Unknown billing stays reserved.
            return dict(row)
