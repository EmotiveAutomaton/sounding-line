"""The frontier probe FR (brief §4, §12.5, E07, D05, G08): one API reasoning model with
thinking on, read out through a one-call verbalized distribution over the live options, no
tools, capped at forty dollars for the stage, counted per call in the FRONTIER_LEDGER with
the model identifier and unit prices recorded before the first call, a hard stop at the cap,
and no other paid API anywhere in the stage. It runs host-side with the VisibleEvidenceV1
as its only input (no world object, no oracle), its prompts and responses logged in full
under the cell's transcripts directory (gitignored), and the API endpoint as its only
network. Provider: Gemini (the one key on this machine); the model is the cheapest
thinking-capable one that passes the pilot's known-answer calibration fixture.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (a model adjudicator is a ruler: the calibration fixture runs
  BEFORE any science call and a decorative one-mode distribution fails it; the verbalized
  distribution must be able to fail G04 and G07), §5 (retries with backoff; every call
  charged before its result is used).
gates: the calibration fixture: NULL (an unusable readout) is a fixture ECE above 0.35, or
  a degenerate distribution (entropy zero) on more than half the items, or a parse failure
  on more than a fifth (fails DOWN: FR is INSTRUMENT_FAILED and the dollars stop);
  ALTERNATIVE: within all three. The cap: a projected overspend RAISES before the request
  (fails DOWN at the cap). bands: exhaustive.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7.reader.supplied_state import evidence_text                     # noqa: E402
from soundingline.stage8 import (FRONTIER_CAP_USD, S8, FrontierCap, append_jsonl,   # noqa: E402
                                 frontier_charge, now_iso, read_registry, update_registry)

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# unit prices in USD per million tokens, recorded before the first call from the provider's
# pricing page fetched 2026-09-04 (ai.google.dev/gemini-api/docs/pricing; output prices include
# thinking tokens; the 2.5 line is closed to new users, per the API's own 404); cheapest first
CANDIDATES = [
    {"model": "gemini-3.5-flash-lite", "in": 0.30, "out": 2.50, "thinking": True, "price_source": "ai.google.dev/gemini-api/docs/pricing, fetched 2026-09-04"},
    {"model": "gemini-3.6-flash", "in": 0.75, "out": 3.75, "thinking": True, "price_source": "ai.google.dev/gemini-api/docs/pricing, fetched 2026-09-04 (through 2026-12-31)"},
]
THINKING_BUDGET = 1024


def _key() -> str:
    k = os.environ.get("GEMINI_API_KEY", "")
    if not k:
        raise RuntimeError("no GEMINI_API_KEY in the environment")
    return k


def chosen() -> dict | None:
    return (read_registry("FRONTIER_LEDGER") or {}).get("model")


def _call(model: dict, prompt: str, cell: str, max_out: int = 2048, tries: int = 4) -> dict:
    """One generateContent call with thinking on and a JSON response; charged per call."""
    est_in = len(prompt) // 3 + 50
    frontier_charge(cell, model["model"], est_in, max_out + THINKING_BUDGET, 0, model["in"], model["out"], projected=True)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": max_out + 2 * THINKING_BUDGET, "responseMimeType": "application/json",
                                 "thinkingConfig": {"thinkingBudget": THINKING_BUDGET}}}
    url = ENDPOINT.format(model=model["model"]) + "?key=" + _key()
    last = None
    for k in range(tries):
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300]!r}"
            if e.code in (400, 403, 404):
                raise RuntimeError(last)
            time.sleep(min(30, 3 * 2 ** k))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = repr(e)
            time.sleep(min(30, 3 * 2 ** k))
    else:
        raise RuntimeError(f"frontier call failed after {tries} tries: {last}")
    u = d.get("usageMetadata") or {}
    tin, tout, tth = int(u.get("promptTokenCount", est_in)), int(u.get("candidatesTokenCount", 0)), int(u.get("thoughtsTokenCount", 0))
    usd = frontier_charge(cell, model["model"], tin, tout, tth, model["in"], model["out"])
    text = ""
    try:
        text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"] if "text" in p)
    except (KeyError, IndexError, TypeError):
        text = ""
    rec = {"at": now_iso(), "cell": cell, "model": model["model"], "prompt": prompt, "response": text, "tokens_in": tin, "tokens_out": tout,
           "tokens_thought": tth, "usd": usd, "finish": ((d.get("candidates") or [{}])[0]).get("finishReason")}
    tdir = S8 / cell.split("/")[0] / "transcripts"
    tdir.mkdir(parents=True, exist_ok=True)
    append_jsonl(tdir / "frontier_calls.jsonl", [rec])
    return rec


def _parse_dist(text: str, ids: list[str]) -> dict | None:
    try:
        obj = json.loads(text)
    except ValueError:
        s, e = text.find("{"), text.rfind("}")
        if s < 0 or e < 0:
            return None
        try:
            obj = json.loads(text[s:e + 1])
        except ValueError:
            return None
    probs = obj.get("probabilities") if isinstance(obj, dict) else None
    if not isinstance(probs, dict):
        return None
    out = {}
    for k in ids:
        try:
            out[k] = max(0.0, float(probs.get(k, 0.0)))
        except (TypeError, ValueError):
            out[k] = 0.0
    z = sum(out.values())
    if z <= 0:
        return None
    return {k: v / z for k, v in out.items()}


def _entropy(d: dict) -> float:
    return -sum(p * math.log(max(p, 1e-12)) for p in d.values())


def verbalized(model: dict, cell: str, body: str, question: str, options: dict) -> dict:
    """The one-call verbalized distribution: the model returns JSON probabilities over the
    given option ids; a parse failure returns None with the raw text."""
    ids = list(options)
    listing = "\n".join(f"- {k}: {options[k]}" for k in ids)
    prompt = (f"{body}\n\n{question}\n\nThe options, by id:\n{listing}\n\n"
              "Think it through, then answer with a JSON object of the form {\"probabilities\": {<id>: <probability>, ...}} "
              "giving your probability for EVERY option id above, summing to 1. Use the ids exactly as given. No other keys.")
    rec = _call(model, prompt, cell)
    dist = _parse_dist(rec["response"], ids)
    return {"dist": dist, "raw": rec["response"][:2000], "usd": rec["usd"], "tokens": (rec["tokens_in"], rec["tokens_out"], rec["tokens_thought"]), "model": model["model"]}


# ── the calibration fixture (the pilot) ──────────────────────────────────────────────

def calibration_fixture(n: int = 8) -> dict:
    """Known-answer items: constructed worlds with the complete state supplied in language
    and the exact next-action distribution known; the fixture asks each candidate model for
    its distribution and reads the expected calibration error, the parse rate, and the
    degenerate share; the cheapest passing model is chosen and recorded with its prices."""
    from runners.stage7.constructor import worlds as W                            # noqa: PLC0415
    from runners.stage7.reader import law as LAW                                  # noqa: PLC0415
    from runners.stage7.reader.supplied_state import TYPE_WORDS                   # noqa: PLC0415
    items = []
    for i in range(1, 60):
        w = W.make_world(f"FRX|essay|s0|w{i:05d}|pilot", "essay")
        if w["degenerate"] or w["hidden"]["next_action"] is None:
            continue
        cond = {"unit_ref": "u", "condition_ref": "c", "render": "log", "supplied": list(LAW.GOAL_UTILITY and ["external_context", "belief_state", "expertise_law", "maker_context", "subjective_action_space", "proximal_goal", "history_residue"]), "form": "language"}
        ev = W.visible_evidence(w, cond)
        items.append((ev, w))
        if len(items) >= n:
            break
    results = {}
    for cand in CANDIDATES:
        recs = []
        try:
            for ev, w in items:
                opts = {LAW.action_id(a): f"{TYPE_WORDS[a['type']]}: {a['section']} {a['slot']}" for a in LAW.options_at_cut(ev)}
                r = verbalized(cand, "PILOT", evidence_text(ev), "What does the maker do next?", opts)
                truth = w["hidden"]["next_action"]
                d = r["dist"]
                recs.append({"parsed": d is not None, "p_truth": (d or {}).get(truth), "conf": max(d.values()) if d else None,
                             "correct": (max(d, key=d.get) == truth) if d else None, "entropy": _entropy(d) if d else None, "usd": r["usd"],
                             "n_options": len(opts)})
        except FrontierCap as e:
            results[cand["model"]] = {"error": str(e), "pass": False}
            break
        except Exception as e:                                                    # noqa: BLE001
            results[cand["model"]] = {"error": repr(e)[:300], "pass": False}
            continue
        parsed = [r for r in recs if r["parsed"]]
        parse_rate = len(parsed) / max(1, len(recs))
        # calibration over a dozen-option question: the mean confidence against the accuracy (a
        # decorative one-mode readout over-claims; honest uncertainty passes), the degenerate
        # share, and the known-answer half: with the whole state supplied the log score must
        # beat uniform
        mean_conf = (sum(r["conf"] for r in parsed) / len(parsed)) if parsed else None
        acc = (sum(1.0 for r in parsed if r["correct"]) / len(parsed)) if parsed else None
        ece = abs(mean_conf - acc) if parsed else None
        degenerate = (sum(1 for r in parsed if r["entropy"] < 1e-6) / len(parsed)) if parsed else None
        ls = (sum(math.log(max(r["p_truth"] or 0.0, 1e-9)) for r in parsed) / len(parsed)) if parsed else None
        ls_u = (sum(math.log(1.0 / max(1, r["n_options"])) for r in parsed) / len(parsed)) if parsed else None
        beats_uniform = ls is not None and ls_u is not None and ls > ls_u
        ok = parse_rate >= 0.8 and ece is not None and ece <= 0.35 and degenerate is not None and degenerate <= 0.5 and beats_uniform
        results[cand["model"]] = {"pass": ok, "parse_rate": parse_rate, "ece_conf_minus_accuracy": ece, "mean_conf": mean_conf, "accuracy": acc,
                                  "log_score": ls, "uniform_log_score": ls_u, "beats_uniform": beats_uniform, "degenerate_share": degenerate, "n": len(recs),
                                  "usd": sum(r["usd"] for r in recs), "prices_per_m": {"in": cand["in"], "out": cand["out"]}}
        if ok:
            update_registry("FRONTIER_LEDGER", lambda led: {**led, "model": cand, "chosen_at": now_iso(), "fixture": results[cand["model"]],
                                                            "price_note": "unit prices recorded before the first call from the provider's published list as known on 2026-09-04; thinking tokens billed as output; the ledger counts the provider's own usage numbers"})
            break
    update_registry("FRONTIER_LEDGER", lambda led: {**led, "fixture_results": results, "cap_usd": FRONTIER_CAP_USD})
    return results


# ── the FR arms on the evidence ──────────────────────────────────────────────────────

def _opt_words(ev: dict) -> dict:
    from runners.stage7.reader import law as LAW                                  # noqa: PLC0415
    from runners.stage7.reader.supplied_state import TYPE_WORDS                   # noqa: PLC0415
    return {LAW.action_id(a): f"{TYPE_WORDS[a['type']]}: {a['section']} {a['slot']}" for a in LAW.options_at_cut(ev)}


def fr_next_action(cell: str, ev: dict, purpose_line: str | None = None) -> dict:
    m = chosen()
    if not m:
        raise RuntimeError("no frontier model chosen (the pilot's fixture did not pass)")
    body = evidence_text(ev)
    if purpose_line:
        body += f"\n\nWhat the document is for: {purpose_line}"
    return verbalized(m, cell, body, "What does the maker do next? Give a probability for every option.", _opt_words(ev))


def fr_purpose(cell: str, ev: dict, candidates: dict) -> dict:
    m = chosen()
    if not m:
        raise RuntimeError("no frontier model chosen")
    opts = dict(candidates)
    opts["unknown"] = "it is not possible to tell from this"
    return verbalized(m, cell, evidence_text(ev), "What could a reader use this document to do? Give a probability for every option.", opts)


def fr_per_event(cell: str, ev: dict, max_events: int = 12) -> list[dict]:
    """One call per boundary on the whole log's own prefix (the D05 surprise readout)."""
    from runners.stage8.constructor import population as POP                      # noqa: PLC0415
    m = chosen()
    if not m:
        raise RuntimeError("no frontier model chosen")
    full = list(ev.get("process_prefix") or [])
    per_opts = (ev.get("objective_options") or {}).get("per_event") or []
    out = []
    n = len(full)
    idx = list(range(n)) if n <= max_events else sorted(set(int(round(k * (n - 1) / (max_events - 1))) for k in range(max_events)))
    for i in idx:
        ev_i = dict(ev)
        ev_i["process_prefix"] = full[:i]
        from runners.stage7.constructor import worlds as W                        # noqa: PLC0415
        ev_i["artifact_state"] = dict(ev["artifact_state"], prefix_text=W.render_prefix_text(full[:i], "log", ev["artifact_state"].get("topic", "")))
        ids = per_opts[i] if i < len(per_opts) else ev["query"]["next_action_options"]
        opts = {k: k.replace(":", " ") for k in ids}
        r = verbalized(m, cell, evidence_text(ev_i), "What does the maker do next? Give a probability for every option.", opts)
        out.append({"i": i, "dist": r["dist"], "usd": r["usd"]})
    return out
