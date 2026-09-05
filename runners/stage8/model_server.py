"""Stage 8 loopback model endpoint (brief §4, §11): the Stage 7 server's contract (host-side,
127.0.0.1, token-gated, one resident base model, the per-token ledger) plus the trained
adapters: a model id `adapter:<name>` names a frozen low-rank adapter directory whose hash
is checked against the ADAPTERS registry at load and returned on every response; the
generative readouts the forward model uses (`sequence_logprobs`: batched teacher-forced sum
log probability of continuation lines under the model, raw text, no chat template;
`sample_log`: raw sampling to a line budget); the letter readout with `adapter: false`
(the base weights through the same resident model). The `--fake` route keeps every engine
runnable without a GPU (hash-seeded readouts; a fake log sampler that emits grammatical
lines from the header).

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (a serving endpoint under VRAM churn: OOM as 503; the GPU lock is
  the engine's; the adapter loads once per resident base), §4 (record measured revisions:
  base revision plus adapter hash on every response; assert the adapter took: the number of
  trainable adapter parameters is checked nonzero at load).
gates: the adapter hash gate: NULL (a moved or altered adapter) is a directory hash unequal
  to the registry's and the load REFUSES (fails DOWN: the cell cannot run on a changed
  adapter); ALTERNATIVE: equal, the load proceeds. bands: exhaustive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import model_server as MS7                                     # noqa: E402

FAKE = False
STATE = {"model": None, "tok": None, "base": None, "revision": None, "adapter": None, "adapter_sha": None,
         "lock": threading.Lock(), "ledger": {}, "allowed": set(), "adapters": {}, "adapter_hashes": {},
         "token": "", "started": time.time(), "loads": 0}
LETTERS = "ABCDEF"


def _ledger(token: str) -> dict:
    return STATE["ledger"].setdefault(token, {"model_calls": 0, "tokens_in": 0, "tokens_out": 0, "forward_passes": 0, "oom": 0})


def _split(model_id: str) -> tuple[str, str | None]:
    """'adapter:<name>' -> (base id from the adapter map, name); a bare id -> (id, None)."""
    if model_id.startswith("adapter:"):
        name = model_id.split(":", 1)[1]
        spec = STATE["adapters"].get(name)
        if not spec:
            raise ValueError(f"adapter {name} is not admitted on this endpoint")
        return spec["base"], name
    return model_id, None


def _dir_hash(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(x for x in Path(path).rglob("*") if x.is_file()):
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def _ensure(model_id: str) -> None:
    base, name = _split(model_id)
    if base not in STATE["allowed"] and model_id not in STATE["allowed"]:
        raise ValueError(f"model {model_id} is not admitted on this endpoint")
    if FAKE:
        STATE.update({"base": base, "adapter": name, "revision": "fake", "adapter_sha": ("fake-" + name) if name else None})
        return
    if STATE["base"] != base or STATE["model"] is None:
        if STATE["model"] is not None:
            MS7._lib().free_model(STATE["model"])
            STATE["model"] = STATE["tok"] = None
        model, tok, rev = MS7._lib().load_model(base)
        STATE.update({"model": model, "tok": tok, "base": base, "revision": rev, "adapter": None, "adapter_sha": None})
        STATE["loads"] += 1
    if name and STATE["adapter"] != name:
        spec = STATE["adapters"][name]
        path = Path(spec["path"])
        sha = _dir_hash(path)
        expected = STATE["adapter_hashes"].get(name)
        if expected and sha != expected:
            raise ValueError(f"adapter {name} hash {sha} differs from the registry's {expected}; refusing to load")
        from peft import PeftModel                                                # noqa: PLC0415
        m = STATE["model"]
        if hasattr(m, "peft_config"):
            if name not in m.peft_config:
                m.load_adapter(str(path), adapter_name=name)
            m.set_adapter(name)
        else:
            m = PeftModel.from_pretrained(m, str(path), adapter_name=name)
            STATE["model"] = m
        n_train = sum(p.numel() for n, p in m.named_parameters() if "lora" in n.lower())
        if n_train <= 0:
            raise ValueError("the adapter loaded no trainable parameters")
        import torch                                                              # noqa: PLC0415
        STATE["model"] = STATE["model"].to(torch.float16)                         # the adapter's weights to the base's dtype
        STATE["model"].eval()
        STATE.update({"adapter": name, "adapter_sha": sha})
        STATE["loads"] += 1
    if not name and STATE["adapter"] is not None:
        STATE.update({"adapter": None, "adapter_sha": None})       # the base is asked for: the adapter is disabled per call


class _adapter_ctx:
    """Enable or disable the resident adapter for one call."""

    def __init__(self, on: bool):
        self.on = on
        self.cm = None

    def __enter__(self):
        m = STATE["model"]
        if m is not None and hasattr(m, "disable_adapter") and (not self.on or STATE["adapter"] is None):
            self.cm = m.disable_adapter()
            self.cm.__enter__()
        return self

    def __exit__(self, *exc):
        if self.cm is not None:
            self.cm.__exit__(*exc)
        return False


def sequence_logprobs(prefix: str, conts: list[str], batch: int = 12) -> dict:
    """Sum and mean log probability of each continuation given the prefix (raw text; the
    tokenizer's BOS if it has one), batched with right padding. Only the continuation span's
    logits are kept (the last L-P+1 positions; every row shares the prefix length P), which
    is the same number at a fraction of the memory; on out-of-memory the batch halves down
    to one before the error surfaces (2026-09-04, L361)."""
    import torch                                                                  # noqa: PLC0415
    model, tok = STATE["model"], STATE["tok"]
    dev = next(model.parameters()).device
    pre = tok(prefix, add_special_tokens=True, return_tensors="pt").input_ids[0]
    P = pre.shape[0]
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    conts_ids = [tok(c, add_special_tokens=False, return_tensors="pt").input_ids[0] for c in conts]
    out_sum, out_mean, out_n = [], [], []
    passes = 0

    def score_chunk(chunk):
        nonlocal passes
        seqs = [torch.cat([pre, c]) for c in chunk]
        L = max(x.shape[0] for x in seqs)
        keep = L - P + 1
        ids = torch.full((len(seqs), L), pad, dtype=torch.long)
        att = torch.zeros((len(seqs), L), dtype=torch.long)
        for i, x in enumerate(seqs):
            ids[i, :x.shape[0]] = x
            att[i, :x.shape[0]] = 1
        ids, att = ids.to(dev), att.to(dev)
        with torch.no_grad():
            try:
                logits = model(input_ids=ids, attention_mask=att, logits_to_keep=keep).logits.float()
            except TypeError:
                logits = model(input_ids=ids, attention_mask=att).logits[:, -keep:].float()
        passes += 1
        lp = torch.log_softmax(logits[:, :-1], dim=-1)          # positions P-1 .. L-2 predict tokens P .. L-1
        tgt = ids[:, P:]
        gathered = lp.gather(2, tgt.unsqueeze(-1)).squeeze(-1)
        res = []
        for i, x in enumerate(seqs):
            n = x.shape[0] - P
            span = gathered[i, :n]
            res.append((float(span.sum()), float(span.mean()) if n > 0 else 0.0, int(n)))
        del logits, lp, gathered
        return res

    k = 0
    while k < len(conts_ids):
        chunk = conts_ids[k:k + batch]
        try:
            res = score_chunk(chunk)
        except Exception as e:                                                    # noqa: BLE001
            if batch > 1 and MS7._lib().is_oom(e):
                try:
                    torch.cuda.empty_cache()
                except Exception:                                                 # noqa: BLE001
                    pass
                batch = max(1, batch // 2)
                continue
            raise
        for a, b, n in res:
            out_sum.append(a)
            out_mean.append(b)
            out_n.append(n)
        k += len(chunk)
    return {"logprobs": out_sum, "mean_logprobs": out_mean, "n_tokens": out_n, "n_prompt_tokens": int(P), "forward_passes": passes, "batch": batch}


def sample_log(prefix: str, seed: int, max_lines: int, temperature: float) -> dict:
    import torch                                                                  # noqa: PLC0415
    model, tok = STATE["model"], STATE["tok"]
    ids = tok(prefix, add_special_tokens=True, return_tensors="pt").input_ids.to("cuda")
    torch.manual_seed(int(seed))
    max_new = max(16, 12 * int(max_lines))
    with torch.no_grad():
        out = model.generate(ids, do_sample=temperature > 0, temperature=max(temperature, 1e-3), top_p=1.0,
                             max_new_tokens=max_new, pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id)
    new = out[0][ids.shape[1]:].tolist()
    text = tok.decode(new, skip_special_tokens=True)
    lines = text.split("\n")[:max_lines]
    return {"text": "\n".join(lines), "n_new_tokens": len(new), "n_prompt_tokens": int(ids.shape[1])}


# ── the fake route ───────────────────────────────────────────────────────────────────

def _fake_seq(prefix: str, conts: list[str]) -> dict:
    lps = []
    for c in conts:
        h = int(hashlib.md5((prefix[-400:] + "|" + c).encode("utf-8")).hexdigest()[:8], 16)
        lps.append(-8.0 + 5.0 * (h % 1000) / 1000.0 - (2.0 if c.strip().endswith("stop") else 0.0))
    return {"logprobs": lps, "mean_logprobs": [v / 4 for v in lps], "n_tokens": [4] * len(conts),
            "n_prompt_tokens": max(1, len(prefix) // 4), "forward_passes": 1}


def _fake_sample(prefix: str, seed: int, max_lines: int) -> dict:
    rnd = random.Random(int(hashlib.md5(f"{prefix[-600:]}|{seed}".encode("utf-8")).hexdigest()[:8], 16))
    secs = re.search(r"sections: (.+)", prefix)
    plan = []
    if secs:
        for tokn in secs.group(1).split():
            m = re.match(r"(\w+)\((\d+)\)", tokn)
            if m:
                plan.append((m.group(1), int(m.group(2))))
    if not plan:
        plan = [("sec1", 2), ("sec2", 2)]
    lines = []
    i = 0
    for name, n in plan:
        for k in range(n):
            lines.append(f"{i:02d} write {name} s{name[3:]}.{k + 1} done")
            i += 1
            if i >= max_lines - 1:
                break
    if rnd.random() < 0.5 and i < max_lines - 1:
        lines.append(f"{i:02d} check {plan[0][0]} s{plan[0][0][3:]}.1 done")
        i += 1
    lines.append(f"{i:02d} stop")
    return {"text": "\n".join(lines), "n_new_tokens": 6 * len(lines), "n_prompt_tokens": max(1, len(prefix) // 4)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
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
            self._send(200, {"ledger": STATE["ledger"], "resident": STATE["base"], "adapter": STATE["adapter"], "adapter_sha": STATE["adapter_sha"],
                             "revision": STATE["revision"], "loads": STATE["loads"], "uptime_s": round(time.time() - STATE["started"], 1)})
        elif self.path == "/health":
            self._send(200, {"ok": True, "resident": STATE["base"], "adapter": STATE["adapter"]})
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
                use_adapter = bool(req.get("adapter", True)) and STATE["adapter"] is not None
                stamp = {"revision": STATE["revision"], "adapter_sha": STATE["adapter_sha"] if use_adapter else None, "adapter": STATE["adapter"] if use_adapter else None}
                if FAKE:
                    if op == "sequence_logprobs":
                        r = _fake_seq(req["prefix"], list(req["continuations"]))
                    elif op == "sample_log":
                        r = _fake_sample(req["prefix"], int(req.get("seed", 0)), int(req.get("max_lines", 40)))
                        led["tokens_out"] += int(r["n_new_tokens"])
                    elif op == "likelihood":
                        r = MS7._fake_likelihood(req["body"], list(req["order"]), req["options"])
                    elif op == "generate":
                        r = MS7._fake_generate(req["body"], int(req.get("seed", 0)), int(req.get("max_new", 96)), bool(req.get("greedy", True)))
                        led["tokens_out"] += len(r.get("token_ids") or [])
                    else:
                        self._send(404, {"error": f"no such op {op}"})
                        return
                    led["model_calls"] += 1
                    led["forward_passes"] += int(r.get("forward_passes", 1))
                    led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                    r.update(stamp)
                    self._send(200, r)
                    return
                model, tok = STATE["model"], STATE["tok"]
                with _adapter_ctx(use_adapter):
                    if op == "sequence_logprobs":
                        r = sequence_logprobs(req["prefix"], list(req["continuations"]))
                        led["forward_passes"] += int(r["forward_passes"])
                    elif op == "sample_log":
                        r = sample_log(req["prefix"], int(req.get("seed", 0)), int(req.get("max_lines", 40)), float(req.get("temperature", 1.0)))
                        led["tokens_out"] += int(r["n_new_tokens"])
                        led["forward_passes"] += max(1, int(r["n_new_tokens"]))
                    elif op == "likelihood":
                        order = list(req["order"])
                        options = {k: req["options"][k] for k in order}
                        r = MS7._lib().likelihood_choice(model, tok, req["body"], options, random.Random(0),
                                                         instruction=req.get("instruction", "Answer with the letter only."), shuffle=False)
                        led["forward_passes"] += 1
                    elif op == "generate":
                        r = MS7._lib().generate(model, tok, req["body"], seed=int(req.get("seed", 0)),
                                                max_new=int(req.get("max_new", 96)), greedy=bool(req.get("greedy", True)))
                        led["tokens_out"] += len(r.get("token_ids") or [])
                        led["forward_passes"] += max(1, len(r.get("token_ids") or []))
                    else:
                        self._send(404, {"error": f"no such op {op}"})
                        return
                led["model_calls"] += 1
                led["tokens_in"] += int(r.get("n_prompt_tokens") or 0)
                r.update(stamp)
                self._send(200, r)
        except Exception as e:                                                    # noqa: BLE001
            if not FAKE and MS7._lib().is_oom(e):
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
    ap.add_argument("--models", required=True, help="comma-separated admitted base model ids")
    ap.add_argument("--adapters", default="", help="name=base=path[=sha],... admitted adapters")
    ap.add_argument("--ready-file", required=True)
    ap.add_argument("--fake", action="store_true")
    a = ap.parse_args()
    global FAKE
    FAKE = bool(a.fake)
    STATE["token"] = a.token
    STATE["allowed"] = set(x for x in a.models.split(",") if x)
    for spec in (x for x in a.adapters.split(",") if x):
        parts = spec.split("=")
        name, base, path = parts[0], parts[1], parts[2]
        STATE["adapters"][name] = {"base": base, "path": path}
        if len(parts) > 3 and parts[3]:
            STATE["adapter_hashes"][name] = parts[3]
        STATE["allowed"].add(base)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    Path(a.ready_file).write_text(json.dumps({"port": a.port, "pid": __import__("os").getpid(), "at": time.time()}), encoding="utf-8")
    try:
        srv.serve_forever()
    finally:
        if STATE["model"] is not None:
            MS7._lib().free_model(STATE["model"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
