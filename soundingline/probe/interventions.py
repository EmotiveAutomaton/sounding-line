"""Phase 2.4 intervention interface — block-local capture, subspace amplification, ablation.

The engineering boundary (context §8): PyTorch is the mechanism, never the theory. This module
alters activations during a forward pass by projecting onto a frozen subspace and scaling that
component; it does not inject an answer, and nothing here licenses mechanism language — a basis
is "a fitted basis" until the causal gates in `prereg/g174.py` pass.

Contract, enforced by tools/test_p24_spine.py:
  - hooks install on the intended blocks only, via the per-family registry below;
  - only token positions at or past the declared boundary are modified (context §8.3: the
    intervention begins at the first artifact token, never while reading a candidate);
  - tensor shape, dtype, and device are preserved (asserted in the hook itself);
  - hooks are removed after every scored call, success or exception (context-manager finally);
  - the whole configuration (basis bytes, block indices, strength, mode, boundary) hashes into
    `config_hash()` for result manifests.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager

import torch


# ── block registry ────────────────────────────────────────────────────────────────────────────
# model.config.model_type -> how to reach the decoder block list. SmolLM2 is llama-typed.

_BLOCK_PATHS = {
    "gpt2": lambda m: m.transformer.h,
    "gpt_neox": lambda m: m.gpt_neox.layers,
    "qwen2": lambda m: m.model.layers,
    "llama": lambda m: m.model.layers,
}


def get_blocks(model):
    """The decoder block ModuleList for any supported family; KeyError names the gap."""
    mt = model.config.model_type
    if mt not in _BLOCK_PATHS:
        raise KeyError(f"no block path registered for model_type={mt!r}; "
                       f"add it to soundingline/probe/interventions.py")
    blocks = _BLOCK_PATHS[mt](model)
    n = getattr(model.config, "num_hidden_layers", None) or getattr(model.config, "n_layer")
    assert len(blocks) == n, f"registry found {len(blocks)} blocks, config says {n}"
    return blocks


def orthonormal(mat: torch.Tensor) -> torch.Tensor:
    """(d, k) matrix -> orthonormal basis of its span via QR. Frozen bases pass through here."""
    q, _ = torch.linalg.qr(mat.to(torch.float32))
    return q[:, : mat.shape[1]].contiguous()


class SubspaceIntervention:
    """h' = h + sign * alpha * U U^T (h - mu) on positions >= boundary, at chosen blocks.

    mode "amplify" adds the projected component (sign +1); "ablate" removes it fully at
    alpha=1.0 (sign -1). basis/mu are dicts keyed by block index: basis[i] is (d, k)
    orthonormal, mu[i] is (d,). boundary is set per call by the reader (token index where
    the artifact begins in the concatenated sequence).
    """

    def __init__(self, basis: dict[int, torch.Tensor], mu: dict[int, torch.Tensor],
                 alpha: float, mode: str):
        assert mode in ("amplify", "ablate"), mode
        assert set(basis) == set(mu), "basis and mu must cover the same blocks"
        self.basis = {i: orthonormal(b) for i, b in basis.items()}
        self.mu = {i: m.to(torch.float32) for i, m in mu.items()}
        self.alpha = float(alpha)
        self.sign = 1.0 if mode == "amplify" else -1.0
        self.mode = mode
        self.boundary = 0

    def _make_hook(self, idx: int):
        def hook(_module, _inputs, output):
            hs = output[0] if isinstance(output, tuple) else output
            b = self.boundary
            if self.alpha == 0.0 or b >= hs.shape[1]:
                return None                       # nothing to change; leave output untouched
            shape, dtype, device = hs.shape, hs.dtype, hs.device
            u = self.basis[idx].to(device=device)
            mu = self.mu[idx].to(device=device)
            seg = hs[:, b:, :].to(torch.float32)
            proj = (seg - mu) @ u @ u.T
            seg2 = (seg + self.sign * self.alpha * proj).to(dtype)
            out = torch.cat([hs[:, :b, :], seg2], dim=1)
            assert out.shape == shape and out.dtype == dtype and out.device == device
            if isinstance(output, tuple):
                return (out,) + tuple(output[1:])
            return out
        hook._p24_intervention = True     # cleanup audits count OUR hooks only: transformers 5
        return hook                       # keeps its own persistent recorder hooks on blocks

    @contextmanager
    def applied(self, model):
        """Install on the declared blocks; guaranteed removal on exit."""
        blocks = get_blocks(model)
        handles = []
        try:
            for i in self.basis:
                handles.append(blocks[i].register_forward_hook(self._make_hook(i)))
            yield self
        finally:
            for h in handles:
                h.remove()

    def config_hash(self) -> str:
        h = hashlib.sha256()
        h.update(f"{self.mode}|{self.alpha}|{self.boundary}|".encode())
        for i in sorted(self.basis):
            h.update(str(i).encode())
            h.update(self.basis[i].cpu().numpy().tobytes())
            h.update(self.mu[i].cpu().numpy().tobytes())
        return h.hexdigest()[:16]


def capture_block_states(model, tok, text: str, device: str = "cpu") -> list[torch.Tensor]:
    """Per-block output hidden states for one text (no pooling): list of (seq, d) float32.

    Uses output_hidden_states; index i is the output of block i (embedding output dropped),
    matching the indices SubspaceIntervention takes.
    """
    enc = tok(text, return_tensors="pt", add_special_tokens=False).to(device)
    with torch.no_grad():
        out = model(**enc, output_hidden_states=True)
    return [h[0].to(torch.float32).cpu() for h in out.hidden_states[1:]]
