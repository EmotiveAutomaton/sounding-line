"""The capsule's model client (brief §6.2): the ONLY network the capsule may open is the
loopback model endpoint, and the audit hook installed by the bootstrap refuses any other
socket. STDLIB ONLY. Every call retries with backoff before dying (LESSONS §5: a serving
endpoint under VRAM churn throws transient errors) and is charged to the capsule's compute
receipt (calls, tokens, forward passes, retries).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (endpoint callers retry with backoff; the budget is recorded per
  call, never estimated after), §3 (fixed option order per unit across arms, seeded from
  the evidence hash and never from the arm: the L283 lesson).
gates: none here (a transport). bands: none.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request

LETTERS = "ABCDEF"


class EndpointError(RuntimeError):
    pass


class Client:
    def __init__(self, endpoint: str | None = None, token: str | None = None, model: str | None = None):
        self.endpoint = (endpoint or os.environ.get("S7_ENDPOINT", "")).rstrip("/")
        self.token = token or os.environ.get("S7_TOKEN", "")
        self.model = model or os.environ.get("S7_MODEL", "")
        self.budget = {"model_calls": 0, "tokens_in": 0, "tokens_out": 0, "forward_passes": 0,
                       "retries": 0, "solver_operations": 0, "cache_hits": 0}
        self._cache: dict = {}
        # no proxy discovery: urllib's default opener reads the Windows registry for proxy
        # settings, which the capsule's audit hook forbids; loopback needs no proxy
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _post(self, op: str, payload: dict, tries: int = 5) -> dict:
        data = json.dumps(payload).encode("utf-8")
        last = None
        for k in range(tries):
            req = urllib.request.Request(f"{self.endpoint}/{op}", data=data,
                                         headers={"Content-Type": "application/json", "X-S7-Token": self.token})
            try:
                with self._opener.open(req, timeout=600) as r:
                    return json.loads(r.read().decode("utf-8"))
            except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError, TimeoutError, OSError) as e:
                last = e
                self.budget["retries"] += 1
                time.sleep(min(30, 2 ** k))
        raise EndpointError(f"{op} failed after {tries} tries: {last!r}")

    def order_rng(self, evidence_sha: str, salt: str) -> random.Random:
        """Option order per unit and question, never per arm."""
        return random.Random(int(hashlib.md5(f"{evidence_sha}|{salt}".encode()).hexdigest()[:8], 16))

    def likelihood(self, body: str, options: dict, evidence_sha: str, salt: str,
                   instruction: str = "Answer with the letter only.") -> dict:
        """Normalized next-token likelihood over the balanced letter labels; at most six
        options per call (larger sets go through `likelihood_any`)."""
        keys = list(options)
        if len(keys) > len(LETTERS):
            raise ValueError("more than six options; use likelihood_any")
        self.order_rng(evidence_sha, salt).shuffle(keys)
        key = ("lik", self.model, body, tuple(keys), tuple(options[k] for k in keys), instruction)
        h = hashlib.sha256(repr(key).encode()).hexdigest()
        if h in self._cache:
            self.budget["cache_hits"] += 1
            return self._cache[h]
        r = self._post("likelihood", {"model": self.model, "body": body, "order": keys,
                                      "options": {k: options[k] for k in keys}, "instruction": instruction})
        self.budget["model_calls"] += 1
        self.budget["tokens_in"] += int(r.get("n_prompt_tokens", 0))
        self.budget["forward_passes"] += 1
        self._cache[h] = r
        return r

    def likelihood_any(self, body: str, options: dict, evidence_sha: str, salt: str,
                       instruction: str = "Answer with the letter only.") -> dict:
        """Option sets past six: seeded groups of at most six, the top three of each meet
        in a final, every option's probability is its group mass times its final mass
        (the Stage-6 composition rule, one declared rule for every arm)."""
        if len(options) <= len(LETTERS):
            return self.likelihood(body, options, evidence_sha, salt, instruction)
        keys = sorted(options)
        self.order_rng(evidence_sha, salt + "|split").shuffle(keys)
        ng = 2 if len(keys) <= 12 else (3 if len(keys) <= 18 else 4)
        groups = [keys[i::ng] for i in range(ng)]
        gp: dict = {}
        finalists: list = []
        for gi, g in enumerate(groups):
            rr = self.likelihood(body, {k: options[k] for k in g}, evidence_sha, f"{salt}|g{gi}", instruction)
            probs = rr["probs"] if rr.get("valid") else {k: 1.0 / len(g) for k in g}
            for k in g:
                gp[k] = probs.get(k, 0.0)
            finalists += [k for k, _ in sorted(probs.items(), key=lambda kv: -kv[1])[:3]]
        finalists = finalists[:len(LETTERS)]
        fr = self.likelihood(body, {k: options[k] for k in finalists}, evidence_sha, f"{salt}|final", instruction)
        fp = fr["probs"] if fr.get("valid") else {k: 1.0 / len(finalists) for k in finalists}
        floor = min(fp.values()) * 0.5 if fp else 0.1
        out = {k: max(gp.get(k, 0.0), 1e-9) * (fp.get(k, floor) if k in fp else floor) for k in keys}
        z = sum(out.values())
        out = {k: v / z for k, v in out.items()}
        return {"valid": True, "probs": out, "pred": max(out, key=out.get), "composed": True}

    def generate(self, body: str, seed: int, max_new: int = 96, greedy: bool = True) -> dict:
        key = ("gen", self.model, body, seed, max_new, greedy)
        h = hashlib.sha256(repr(key).encode()).hexdigest()
        if h in self._cache:
            self.budget["cache_hits"] += 1
            return self._cache[h]
        r = self._post("generate", {"model": self.model, "body": body, "seed": seed, "max_new": max_new, "greedy": greedy})
        self.budget["model_calls"] += 1
        self.budget["tokens_in"] += int(r.get("n_prompt_tokens", 0))
        self.budget["tokens_out"] += len(r.get("token_ids") or [])
        self.budget["forward_passes"] += max(1, len(r.get("token_ids") or []))
        self._cache[h] = r
        return r

    def solver(self, n: int = 1) -> None:
        self.budget["solver_operations"] += n
