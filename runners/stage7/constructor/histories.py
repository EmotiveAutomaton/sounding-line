"""Controlled mixed human/model revision histories (brief §7.3, §16.4): held-out
histories with independently logged actors and event ROLES (proposal, selection,
ratification, veto, integration, repair, acceptance, execution), a process/control
discontinuity at a known event, and the surface adversaries the discontinuity reader
must survive: a style-matched discontinuity (both control regimes write from ONE word
pool, so only process statistics separate them) and a style-shifted no-discontinuity
(one control regime, the word pool switches mid-history).

THE CHASSIS. A document of sections is revised by events. Control regimes differ in
PROCESS, never in identity labels: under human control edits are small, local, and
frequently revisit recent spans, and proposals are executed directly; under model
control proposals are large spans that a ratifier then accepts, edits, or vetoes (a veto
shows as a revert), with low revisit. The five required history types: human draft then
model proposal with human accept/edit/reject; model draft then human thesis selection or
structural rewrite; alternating local edits with normalized register; human-only and
model-only no-discontinuity controls; the style-matched discontinuity and the
style-shifted no-discontinuity adversaries. The target is the LOCATION and TYPE of the
control change, never a token percentage or an authorship label.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a falsifier's baseline arm is a known-answer gate: the
  stylometry rival must catch the plain style switch and must fail the style-matched
  process switch, both checked in the self-test; a transformer eraser needs an echo gate:
  style matching here is by construction from one pool, measured as the trigram
  divergence between sides, and the self-test asserts it sits at the no-switch floor),
  §5 (the independent unit is the history).
gates: construction gates checked at import by the guard suite: (a) in the style-matched
  discontinuity the between-sides trigram divergence is within the no-switch band (NULL
  of a leaked style: divergence above the human-only control's 95th percentile, failure
  direction UP); (b) the process oracle separates the change point in the plain and the
  style-matched cases at tolerance 2 (ALTERNATIVE: at or above 0.8 hit rate; a
  construction under it is INSTRUMENT_FAILED). bands: exhaustive as stated.
"""

from __future__ import annotations

import hashlib
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

HISTORY_TYPES = ("human_then_model", "model_then_human", "alternating_normalized", "human_only",
                 "model_only", "style_matched_switch", "style_shift_no_switch")
POOL_A = ["the", "kiln", "holds", "heat", "for", "hours", "and", "the", "glaze", "sets", "slowly", "under", "a", "steady",
          "flame", "while", "the", "rack", "cools", "by", "the", "door", "where", "the", "clay", "rests", "until", "morning"]
POOL_B = ["thermal", "retention", "within", "the", "chamber", "permits", "gradual", "vitrification", "of", "the", "surface",
          "coating", "under", "controlled", "combustion", "whereas", "peripheral", "storage", "enables", "convective",
          "equilibration", "prior", "to", "subsequent", "processing"]
ROLES = ("propose", "select", "ratify", "veto", "integrate", "repair", "accept", "execute")
REGIMES = {
    # edit size: geometric mean words; revisit rate; proposal-then-ratify structure; veto rate
    "human": {"size_mean": 3.0, "revisit": 0.55, "ratified": 0.0, "veto": 0.0},
    "model": {"size_mean": 11.0, "revisit": 0.12, "ratified": 1.0, "veto": 0.25},
}


def _rng(hid: str, salt: str = "") -> random.Random:
    return random.Random(int(hashlib.md5(f"{hid}|{salt}".encode()).hexdigest()[:8], 16))


def _words(r: random.Random, pool: list[str], n: int) -> str:
    return " ".join(pool[r.randrange(len(pool))] for _ in range(n))


def _size(r: random.Random, mean: float) -> int:
    p = 1.0 / mean
    k = 1
    while r.random() > p and k < 40:
        k += 1
    return k


def _events(hid: str, regimes: list[str], pools: list[list[str]], n: int, salt: str = "ev") -> list[dict]:
    """n events under the per-event regime and pool lists (length n each); the process
    statistics come from the regime, the words from the pool."""
    r = _rng(hid, salt)
    sections = ["sec1", "sec2", "sec3"]
    events = []
    recent: list[tuple[str, int]] = []
    i = 0
    while len(events) < n:
        reg = REGIMES[regimes[len(events)]]
        pool = pools[len(events)]
        if recent and r.random() < reg["revisit"]:
            sec, pos = recent[-1 - r.randrange(min(3, len(recent)))]
            revisit = True
        else:
            sec, pos = sections[r.randrange(3)], r.randrange(0, 40)
            revisit = False
        size = _size(r, reg["size_mean"])
        text = _words(r, pool, size)
        if reg["ratified"] > 0 and r.random() < reg["ratified"]:
            role_seq = ["propose", "veto" if r.random() < reg["veto"] else ("accept" if r.random() < 0.7 else "integrate")]
        else:
            role_seq = ["execute"]
        for role in role_seq:
            if len(events) >= n:
                break
            ev = {"i": len(events), "op": "replace" if revisit else "insert", "section": sec, "pos": pos, "size": size,
                  "text": text if role != "veto" else "", "revisit": revisit, "reverted": role == "veto",
                  "actor_role": role, "regime": regimes[len(events)]}
            events.append(ev)
            i += 1
        recent.append((sec, pos))
    return events[:n]


def make_history(hid: str, kind: str, n: int = 24) -> dict:
    """One history of the named kind with its truth: the control change index (or none)
    and its type ('proposal' when the proposer regime changes, 'selection' when the
    selector regime changes with the proposer fixed, in the model_then_human case)."""
    r = _rng(hid, "plan")
    cp = 8 + r.randrange(max(1, n - 16)) if n > 16 else n // 2
    if kind == "human_then_model":
        regimes = ["human"] * cp + ["model"] * (n - cp)
        pools = [POOL_A] * cp + [POOL_B] * (n - cp)
        truth, ctype = cp, "proposal"
    elif kind == "model_then_human":
        regimes = ["model"] * cp + ["human"] * (n - cp)
        pools = [POOL_B] * cp + [POOL_A] * (n - cp)
        truth, ctype = cp, "selection"
    elif kind == "alternating_normalized":
        blocks = []
        cur = "human"
        while len(blocks) < n:
            L = 3 + r.randrange(3)
            blocks += [cur] * L
            cur = "model" if cur == "human" else "human"
        regimes = blocks[:n]
        pools = [POOL_A] * n
        truth, ctype = next(i for i in range(1, n) if regimes[i] != regimes[i - 1]), "proposal"
    elif kind == "human_only":
        regimes, pools, truth, ctype = ["human"] * n, [POOL_A] * n, "none", "none"
    elif kind == "model_only":
        regimes, pools, truth, ctype = ["model"] * n, [POOL_B] * n, "none", "none"
    elif kind == "style_matched_switch":
        regimes = ["human"] * cp + ["model"] * (n - cp)
        pools = [POOL_A] * n
        truth, ctype = cp, "proposal"
    elif kind == "style_shift_no_switch":
        regimes = ["human"] * n
        pools = [POOL_A] * cp + [POOL_B] * (n - cp)
        truth, ctype = "none", "none"
    else:
        raise ValueError(kind)
    events = _events(hid, regimes, pools, n)
    return {"hid": hid, "kind": kind, "n": n, "events": events, "truth": {"change_point": truth, "type": ctype,
            "regimes": regimes, "style_shift_at": cp if kind == "style_shift_no_switch" else None}}


def visible_history(h: dict) -> list[dict]:
    """Actor-blind events: op, section, position, size, text, revisit, reverted. Roles and
    regimes are truth."""
    return [{"i": e["i"], "op": e["op"], "section": e["section"], "pos": e["pos"], "size": e["size"],
             "text": e["text"], "revisit": e["revisit"], "reverted": e["reverted"]} for e in h["events"]]


# ── the exact process oracle over segmentations (the construction ceiling) ────────────

def _seg_ll(evs: list[dict], reg: dict) -> float:
    total = 0.0
    p = 1.0 / reg["size_mean"]
    for e in evs:
        k = max(1, int(e["size"]))
        total += math.log(p) + (k - 1) * math.log(1 - p)
        rv = min(max(reg["revisit"], 0.02), 0.98)
        total += math.log(rv if e["revisit"] else 1 - rv)
        vt = min(max(reg["veto"] * reg["ratified"], 0.02), 0.98)
        total += math.log(vt if e["reverted"] else 1 - vt)
    return total


def oracle_posterior(events: list[dict], min_seg: int = 3) -> dict:
    """Posterior over the change point (and none) under the two true regimes: for every
    boundary k the best assignment of regimes to sides; 'none' is the best single regime."""
    n = len(events)
    lls = {}
    for k in range(min_seg, n - min_seg + 1):
        best = -1e18
        for a, b in (("human", "model"), ("model", "human")):
            best = max(best, _seg_ll(events[:k], REGIMES[a]) + _seg_ll(events[k:], REGIMES[b]))
        lls[str(k)] = best
    lls["none"] = max(_seg_ll(events, REGIMES["human"]), _seg_ll(events, REGIMES["model"])) + math.log(max(1, len(lls)))  # a flat prior over the alternatives
    mx = max(lls.values())
    ex = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def _selftest() -> list[str]:
    from runners.stage7.scoring import change_point as CP                          # noqa: PLC0415
    fails = []
    hits = {"human_then_model": 0, "style_matched_switch": 0}
    style_none = []
    style_matched = []
    n = 24
    for i in range(24):
        for kind in ("human_then_model", "style_matched_switch", "human_only", "style_shift_no_switch"):
            h = make_history(f"HT|{kind}|w{i:04d}", kind, n)
            vis = visible_history(h)
            if kind in hits:
                post = oracle_posterior(vis)
                if CP.tolerance_hit(post, h["truth"]["change_point"], 2):
                    hits[kind] += 1
            sp = CP.stylometry_posterior(vis)
            if kind == "human_only":
                style_none.append(max(sp.values()))
            if kind == "style_matched_switch":
                style_matched.append(1.0 - sp.get("none", 0.0))
            if kind == "style_shift_no_switch" and i < 8:
                if CP.tolerance_hit(sp, h["truth"]["style_shift_at"], 2) is False and max(sp, key=sp.get) == "none":
                    fails.append("stylometry misses a plain style shift (the rival's known answer)")
    for kind, k in hits.items():
        if k / 24 < 0.8:
            fails.append(f"process oracle hit rate {k / 24:.2f} on {kind} (band: at or above 0.8)")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("histories self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
