"""Stage 7 loopback model endpoint (brief §6.2): the ONLY route from a reader capsule to a
local model. Host-side, started by the engine inside its GPU session, bound to 127.0.0.1
on a free port, token-gated, one resident model at a time (loaded on first request,
freed when another is requested), serving the three readouts the readers use through
runners/s4_lib (the same code path as every earlier stage): the letter-likelihood readout
under a CALLER-FIXED option order, option-text log probabilities, and greedy or sampled
generation. A per-token compute ledger (calls, prompt tokens, output tokens, forward
passes) is the I13 receipt. The server never sees evidence semantics, never touches a
world object, and never reads the repository's results.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (a serving endpoint under VRAM churn: callers retry; the server
  reports OOM as a 503 with the reason; the GPU lock is the engine's, taken once per
  card invocation and held through this process's life), §4 (record measured model
  revisions in every response).
gates: none here (a transport). bands: none.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import hashlib                                                                     # noqa: E402
import math                                                                        # noqa: E402
import re                                                                          # noqa: E402
import urllib.request                                                              # noqa: E402

s4_lib = None                                                                      # imported lazily (the fake route loads no torch)


def _lib():
    global s4_lib
    if s4_lib is None:
        from runners import s4_lib as _s4                                          # noqa: PLC0415
        s4_lib = _s4
    return s4_lib


# ── the fake route: deterministic pseudo-readouts for dress rehearsals (S7_FAKE_SERVER) ─
# Never a reader: it exists so every engine, capsule, scorer, and verdict path runs end to
# end without a GPU. Likelihoods are hash-seeded; generations carry one well-formed line
# per proposal grammar the joint arms parse, with ids taken from the prompt where needed.
FAKE = False
FAKE_TYPES = ["write", "revise", "check", "consult", "cite", "restructure", "probe", "fix"]


def _fake_likelihood(body: str, order: list, options: dict) -> dict:
    labels = {k: LETTERS[i] for i, k in enumerate(order)}
    raw = {}
    for k in order:
        h = int(hashlib.md5((body[-600:] + "|" + str(options[k])).encode("utf-8")).hexdigest()[:8], 16)
        raw[k] = -3.0 + 3.0 * (h % 1000) / 1000.0
    m = max(raw.values())
    z = sum(math.exp(v - m) for v in raw.values())
    probs = {k: math.exp(raw[k] - m) / z for k in order}
    return {"valid": True, "validity_reason": "ok", "order": order, "labels": labels, "probs": probs,
            "pred": max(probs, key=probs.get), "label_logits": {labels[k]: raw[k] for k in order},
            "n_prompt_tokens": max(1, len(body) // 4), "readout": "fake-hash-readout", "revision": "fake"}


def _fake_generate(body: str, seed: int, max_new: int, greedy: bool) -> dict:
    rnd = random.Random(int(hashlib.md5(f"{body[-800:]}|{seed}".encode("utf-8")).hexdigest()[:8], 16))
    T = FAKE_TYPES
    lines = []
    for _ in range(3):
        a, b = rnd.sample(T, 2)
        lines.append(f"pull: {a} > {b}")
    for _ in range(3):
        lines.append(f"belief: library={rnd.choice(['yes', 'no'])} source={rnd.choice(['yes', 'no'])} "
                     f"deadline={rnd.choice(['tight', 'loose'])} checked={rnd.choice(['none', 'sec1', 'sec2'])}")
    for _ in range(3):
        a, b, c, d = rnd.sample(T, 4)
        lines.append(f"skill: {a},{b} weak: {c},{d} pace: {rnd.choice(['steady', 'erratic'])}")
    m = re.search(r"using ids from: (.+?)\. Nothing else", body)
    if m:
        ids = [x.strip() for x in m.group(1).split(",") if x.strip()]
        for _ in range(3):
            k = rnd.randint(1, max(1, len(ids)))
            lines.append("open: " + ", ".join(rnd.sample(ids, min(k, len(ids)))))
    for _ in range(3):
        lines.append(f"sees: library={rnd.choice(['usable', 'not'])} deadline={rnd.choice(['tight', 'loose'])} audience={rnd.choice(['high', 'low', 'none'])}")
    for _ in range(3):
        lines.append(f"habit: {rnd.choice(T + ['none'])} intention: none")
    for _ in range(3):
        a, b = rnd.sample(T, 2)
        lines.append(f"H: the maker leans on {a} before {b} | rule: {a}={rnd.choice([1.5, 2.0, 3.0])}, {b}={rnd.choice([0.5, 1.0])}")
    lines.append("model: " + " ".join(f"{t}={rnd.random():.2f}/{rnd.random():.2f}" for t in T) + f" pace={rnd.choice(['steady', 'erratic'])}")
    lines.append(f"The maker believes the library is {rnd.choice(['available', 'unavailable'])}, source access is available, "
                 f"the deadline is {rnd.choice(['tight', 'loose'])}, and believes {rnd.choice(['sec1', 'sec2', 'sec3'])} is already checked.")
    text = "\n".join(lines)
    return {"text": text, "token_ids": list(range(min(int(max_new), 40))), "seed": seed, "greedy": greedy,
            "n_prompt_tokens": max(1, len(body) // 4), "revision": "fake"}

OLLAMA = "http://127.0.0.1:11434"
LETTERS = "ABCDEF"


def _ollama(payload: dict, timeout: float = 600.0) -> dict:
    """The 9B route (A16): Ollama on its own loopback port, reached ONLY through this
    server (a capsule never sees it). Thinking off, temperature zero, letter log
    probabilities from top_logprobs; the family (Qwen3.5), quantization (Q4_K_M), and
    tokenizer are the interface caveats recorded on every response."""
    req = urllib.request.Request(OLLAMA + "/api/generate", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _ollama_likelihood(name: str, body: str, order: list, options: dict, instruction: str) -> dict:
    labels = {k: LETTERS[i] for i, k in enumerate(order)}
    listing = "\n".join(f"{labels[k]}) {options[k]}" for k in order)
    prompt = f"{body}\nOptions:\n{listing}\n{instruction}\nAnswer:"
    d = _ollama({"model": name, "prompt": prompt, "stream": False, "think": False, "logprobs": True, "top_logprobs": 20,
                 "keep_alive": "10m", "options": {"num_predict": 1, "temperature": 0}})
    tops = ((d.get("logprobs") or [{}])[0].get("top_logprobs") or [])
    raw = {}
    for k in order:
        L = labels[k]
        best = None
        for t in tops:
            if t["token"].strip() == L:
                best = t["logprob"] if best is None else max(best, t["logprob"])
        raw[k] = best if best is not None else -30.0
    m = max(raw.values())
    z = sum(math.exp(v - m) for v in raw.values())
    probs = {k: math.exp(raw[k] - m) / z for k in order}
    return {"valid": True, "validity_reason": "ok", "order": order, "labels": labels, "probs": probs,
            "pred": max(probs, key=probs.get), "label_logits": {labels[k]: raw[k] for k in order},
            "n_prompt_tokens": int(d.get("prompt_eval_count") or 0), "readout": "s7-ollama-letter-logprob-1.0",
            "interface_caveats": "Qwen3.5 family, Q4_K_M quantization, Ollama tokenizer, top-20 log probabilities (absent letters floored at -30)"}


def _ollama_generate(name: str, body: str, seed: int, max_new: int, greedy: bool) -> dict:
    d = _ollama({"model": name, "prompt": body, "stream": False, "think": False, "keep_alive": "10m",
                 "options": {"num_predict": int(max_new), "temperature": 0 if greedy else 0.8, "seed": int(seed)}})
    return {"text": (d.get("response") or "").strip(), "token_ids": list(range(int(d.get("eval_count") or 0))), "seed": seed,
            "greedy": greedy, "n_prompt_tokens": int(d.get("prompt_eval_count") or 0)}


def _ollama_unload(name: str) -> None:
    try:
        _ollama({"model": name, "prompt": "", "stream": False, "keep_alive": 0}, timeout=60)
    except Exception:                                                              # noqa: BLE001
        pass

STATE = {"model": None, "tok": None, "name": None, "revision": None, "lock": threading.Lock(),
         "ledger": {}, "allowed": set(), "token": "", "started": time.time(), "loads": 0}


def _ledger(token: str) -> dict:
    return STATE["ledger"].setdefault(token, {"model_calls": 0, "tokens_in": 0, "tokens_out": 0, "forward_passes": 0, "oom": 0})


def _ensure(name: str) -> None:
    if name not in STATE["allowed"]:
        raise ValueError(f"model {name} is not admitted on this endpoint")
    if STATE["name"] == name and (STATE["model"] is not None or name.startswith("ollama:") or FAKE):
        return
    if FAKE:
        STATE.update({"model": None, "tok": None, "name": name, "revision": "fake"})
        STATE["loads"] += 1
        return
    if STATE["model"] is not None:
        _lib().free_model(STATE["model"])
        STATE["model"] = STATE["tok"] = None
    if STATE["name"] and STATE["name"].startswith("ollama:"):
        _ollama_unload(STATE["name"].split(":", 1)[1])          # the card is shared; unload before an HF load
    if name.startswith("ollama:"):
        STATE.update({"model": None, "tok": None, "name": name, "revision": "ollama:" + name.split(":", 1)[1]})
        STATE["loads"] += 1
        return
    model, tok, rev = _lib().load_model(name)
    STATE.update({"model": model, "tok": tok, "name": name, "revision": rev})
    STATE["loads"] += 1


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):                                             # quiet
        pass

    def _send(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/stats"):
            self._send(200, {"ledger": STATE["ledger"], "resident": STATE["name"], "revision": STATE["revision"],
                             "loads": STATE["loads"], "uptime_s": round(time.time() - STATE["started"], 1)})
        elif self.path == "/health":
            self._send(200, {"ok": True, "resident": STATE["name"]})
        else:
            self._send(404, {"error": "no such route"})

    def do_POST(self):
        token = self.headers.get("X-S7-Token", "")
        if token != STATE["token"]:
            self._send(403, {"error": "bad token"})
            return
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except ValueError:
            self._send(400, {"error": "bad json"})
            return
        op = self.path.strip("/")
        if op == "shutdown":
            self._send(200, {"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        led = _ledger(token)
        try:
            with STATE["lock"]:
                _ensure(req["model"])
                model, tok = STATE["model"], STATE["tok"]
                if FAKE:
                    if op == "likelihood":
                        r = _fake_likelihood(req["body"], list(req["order"]), req["options"])
                        led["model_calls"] += 1
                        led["forward_passes"] += 1
                        led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                        self._send(200, r)
                    elif op == "generate":
                        r = _fake_generate(req["body"], int(req.get("seed", 0)), int(req.get("max_new", 96)), bool(req.get("greedy", True)))
                        led["model_calls"] += 1
                        led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                        led["tokens_out"] += len(r.get("token_ids") or [])
                        led["forward_passes"] += max(1, len(r.get("token_ids") or []))
                        self._send(200, r)
                    elif op == "option_logprobs":
                        led["model_calls"] += 1
                        self._send(200, {"logprobs": {o: -float(1 + (hash(o) % 7)) for o in req["options"]}, "revision": "fake"})
                    else:
                        self._send(404, {"error": f"no such op {op}"})
                    return
                if req["model"].startswith("ollama:"):
                    oname = req["model"].split(":", 1)[1]
                    if op == "likelihood":
                        r = _ollama_likelihood(oname, req["body"], list(req["order"]), req["options"], req.get("instruction", "Answer with the letter only."))
                        led["model_calls"] += 1
                        led["forward_passes"] += 1
                        led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                        r["revision"] = STATE["revision"]
                        self._send(200, r)
                    elif op == "generate":
                        r = _ollama_generate(oname, req["body"], int(req.get("seed", 0)), int(req.get("max_new", 96)), bool(req.get("greedy", True)))
                        led["model_calls"] += 1
                        led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                        led["tokens_out"] += len(r.get("token_ids") or [])
                        led["forward_passes"] += max(1, len(r.get("token_ids") or []))
                        r["revision"] = STATE["revision"]
                        self._send(200, r)
                    else:
                        self._send(404, {"error": f"no such op {op} on the ollama route"})
                    return
                if op == "likelihood":
                    order = list(req["order"])
                    options = {k: req["options"][k] for k in order}
                    r = _lib().likelihood_choice(model, tok, req["body"], options, random.Random(0),
                                                 instruction=req.get("instruction", "Answer with the letter only."), shuffle=False)
                    led["model_calls"] += 1
                    led["forward_passes"] += 1
                    led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                    r["revision"] = STATE["revision"]
                    self._send(200, r)
                elif op == "option_logprobs":
                    r = _lib().option_text_logprobs(model, tok, req["body"], req["options"])
                    led["model_calls"] += 1
                    led["forward_passes"] += len(req["options"])
                    self._send(200, {"logprobs": r, "revision": STATE["revision"]})
                elif op == "generate":
                    r = _lib().generate(model, tok, req["body"], seed=int(req.get("seed", 0)),
                                        max_new=int(req.get("max_new", 96)), greedy=bool(req.get("greedy", True)))
                    led["model_calls"] += 1
                    led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                    led["tokens_out"] += len(r.get("token_ids") or [])
                    led["forward_passes"] += max(1, len(r.get("token_ids") or []))
                    r["revision"] = STATE["revision"]
                    self._send(200, r)
                else:
                    self._send(404, {"error": f"no such op {op}"})
        except Exception as e:                                                    # noqa: BLE001
            if not FAKE and _lib().is_oom(e):
                led["oom"] += 1
                try:
                    import torch                                                  # noqa: PLC0415
                    torch.cuda.empty_cache()
                except Exception:                                                 # noqa: BLE001
                    pass
                self._send(503, {"error": "oom", "detail": repr(e)[:300]})
            else:
                self._send(500, {"error": repr(e)[:500]})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--models", required=True, help="comma-separated admitted model ids")
    ap.add_argument("--ready-file", required=True)
    ap.add_argument("--fake", action="store_true", help="dress-rehearsal transport: hash-seeded readouts, no model")
    a = ap.parse_args()
    global FAKE
    FAKE = bool(a.fake)
    STATE["token"] = a.token
    STATE["allowed"] = set(a.models.split(","))
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    Path(a.ready_file).write_text(json.dumps({"port": a.port, "pid": __import__("os").getpid(), "at": time.time()}), encoding="utf-8")
    try:
        srv.serve_forever()
    finally:
        if STATE["model"] is not None:
            _lib().free_model(STATE["model"])
        if STATE["name"] and STATE["name"].startswith("ollama:") and not FAKE:
            _ollama_unload(STATE["name"].split(":", 1)[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
