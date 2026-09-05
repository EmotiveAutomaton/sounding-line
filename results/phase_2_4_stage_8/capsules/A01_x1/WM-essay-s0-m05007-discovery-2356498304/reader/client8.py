"""The Stage 8 capsule client: the Stage 7 loopback client plus the forward-model readouts
(brief §4 FM): sequence log probabilities of continuation lines under the model's own
generative distribution (raw text, no chat template, one batched call per boundary) and
raw log sampling for the generation gate; the letter readout may run with the adapter
disabled (the proposal readout through the base weights, recorded). STDLIB ONLY.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (endpoint callers retry with backoff; every call is charged to the
  capsule receipt), §3 (score the SHORT continuation given the LONG prefix; sum, not mean,
  is the generative quantity over same-grammar lines, the mean reported beside).
gates: none (a transport). bands: none.
"""

from __future__ import annotations

import hashlib

from .client import Client


class Client8(Client):
    def sequence_logprobs(self, prefix: str, continuations: list[str], adapter: bool = True) -> dict:
        """Sum (and mean) log probability of each continuation given the prefix, all in one
        batched forward; the order is the caller's."""
        key = ("seq", self.model, prefix, tuple(continuations), adapter)
        h = hashlib.sha256(repr(key).encode()).hexdigest()
        if h in self._cache:
            self.budget["cache_hits"] += 1
            return self._cache[h]
        r = self._post("sequence_logprobs", {"model": self.model, "prefix": prefix, "continuations": list(continuations), "adapter": bool(adapter)})
        self.budget["model_calls"] += 1
        self.budget["tokens_in"] += int(r.get("n_prompt_tokens", 0))
        self.budget["forward_passes"] += int(r.get("forward_passes", 1))
        self._cache[h] = r
        return r

    def sample_log(self, prefix: str, seed: int, max_lines: int = 40, temperature: float = 1.0, adapter: bool = True) -> dict:
        key = ("smp", self.model, prefix, seed, max_lines, temperature, adapter)
        h = hashlib.sha256(repr(key).encode()).hexdigest()
        if h in self._cache:
            self.budget["cache_hits"] += 1
            return self._cache[h]
        r = self._post("sample_log", {"model": self.model, "prefix": prefix, "seed": int(seed), "max_lines": int(max_lines),
                                      "temperature": float(temperature), "adapter": bool(adapter)})
        self.budget["model_calls"] += 1
        self.budget["tokens_in"] += int(r.get("n_prompt_tokens", 0))
        self.budget["tokens_out"] += int(r.get("n_new_tokens", 0))
        self.budget["forward_passes"] += max(1, int(r.get("n_new_tokens", 0)))
        self._cache[h] = r
        return r

    def likelihood_base(self, body: str, options: dict, evidence_sha: str, salt: str,
                        instruction: str = "Answer with the letter only.") -> dict:
        """The letter readout with the adapter disabled (the base instruct weights)."""
        keys = list(options)
        self.order_rng(evidence_sha, salt).shuffle(keys)
        key = ("likb", self.model, body, tuple(keys), tuple(options[k] for k in keys), instruction)
        h = hashlib.sha256(repr(key).encode()).hexdigest()
        if h in self._cache:
            self.budget["cache_hits"] += 1
            return self._cache[h]
        r = self._post("likelihood", {"model": self.model, "body": body, "order": keys, "options": {k: options[k] for k in keys},
                                      "instruction": instruction, "adapter": False})
        self.budget["model_calls"] += 1
        self.budget["tokens_in"] += int(r.get("n_prompt_tokens", 0))
        self.budget["forward_passes"] += 1
        self._cache[h] = r
        return r
