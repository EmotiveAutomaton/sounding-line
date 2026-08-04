"""B′ — read the reader, not the text.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

*Emotion Concepts and their Function in a Large Language Model* (Anthropic, arXiv 2604.07729)
found internal representations of emotion concepts that causally influence behaviour, organised
so that similar emotions have similar representations. One of its results is the reason this file
exists:

    Desperation drove the model to take unethical actions **even without obvious emotional
    language markers in outputs.**

**The internal representation carried an affect the surface did not.** Every measure this project
has built reads the artifact. That sentence says the artifact is not always where the affect is.

And the curator's reading of the layer structure, which is the specific proposal here:

    They literally have Panksepp's lower-order features near their sensory input channels and
    Barrett's emotional prediction and control in cortical networks further away at the higher-
    order prediction space... we can catch the leakage specifically and extract it using how much
    it highlights these lower-order features in a reading LLM.

So: **the ratio of early-layer to late-layer affective activation is the leaked/emblematic split,
measured in the reader rather than inferred from the text.**

── WHAT THIS IS NOT ──────────────────────────────────────────────────────────────────────────

Not steering. The model is never asked to *be* anything and its outputs are not used. It reads,
and the activations are recorded. That difference matters: a steered model is an actor, and an
actor's report is the emblematic layer again.

── THE HONESTY CHECK, BEFORE ANY READING IS TRUSTED ──────────────────────────────────────────

A direction fitted from contrast sentences will always produce *some* projection on *any* text.
So `validate()` runs first, on **held-out** sentences the directions never saw:

    B′-1   the fitted directions must classify held-out emotion sentences above chance.
           Below chance, or at it, and the directions are noise and every projection is noise.

This is the check the univariate separability statistic never got and should have — see
`results/g/VERDICT.md`. Validate against a task with a known answer before believing anything.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Sequence

# Small by default and CPU by default. The point of the first run is whether the STRUCTURE is
# there, not whether a 9B has more of it — and a run that fights the GPU for a gate is a run that
# costs more than it is worth. Scale up after the structure is confirmed.
DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B"


@dataclass(frozen=True)
class LayerActs:
    """Mean-pooled hidden state per layer for one text. `acts[layer]` is a vector."""
    acts: list[list[float]]

    @property
    def n_layers(self) -> int:
        return len(self.acts)


@dataclass(frozen=True)
class Directions:
    """One direction per (concept, layer). Fitted as mean(concept) minus mean(everything).

    Subtracting the GLOBAL mean rather than a paired control is deliberate: it makes the
    directions mutually comparable, since every one is expressed against the same origin, and a
    projection can then be read as "how far toward this concept, relative to text in general".
    """
    concepts: tuple[str, ...]
    vecs: dict[str, list[list[float]]]      # concept -> layer -> vector
    n_layers: int
    mu: list[list[float]]                   # per layer, per dimension: fitting-set mean
    sd: list[list[float]]                   # per layer, per dimension: fitting-set spread

    def project(self, a: LayerActs) -> dict[str, list[float]]:
        """Cosine against each concept direction, per layer, on the fitted scale."""
        out = {}
        for c in self.concepts:
            row = []
            for L in range(min(self.n_layers, a.n_layers)):
                z = [(a.acts[L][i] - self.mu[L][i]) / self.sd[L][i]
                     for i in range(len(a.acts[L]))]
                row.append(_cos(z, self.vecs[c][L]))
            out[c] = row
        return out


def _cos(x: Sequence[float], y: Sequence[float]) -> float:
    num = sum(a * b for a, b in zip(x, y))
    nx = math.sqrt(sum(a * a for a in x)) or 1e-9
    ny = math.sqrt(sum(b * b for b in y)) or 1e-9
    return num / (nx * ny)


class Reader:
    """A model that reads and reports its hidden states. It never generates."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "cpu",
                 max_tokens: int = 512) -> None:
        import torch                                          # noqa: PLC0415
        from transformers import AutoModel, AutoTokenizer     # noqa: PLC0415
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name, output_hidden_states=True,
            dtype=torch.float32 if device == "cpu" else torch.float16).to(device).eval()
        self.device = device
        self.max_tokens = max_tokens
        self.name = model_name

    def read(self, text: str) -> LayerActs:
        """Mean-pooled hidden state per layer, over real tokens only.

        Mean-pooled rather than last-token because an artifact has no meaningful final token — it
        is not a prompt awaiting a completion. Padding is masked out so a short text is not
        averaged toward whatever the pad embedding happens to be.
        """
        t = self.tok(text, return_tensors="pt", truncation=True,
                     max_length=self.max_tokens).to(self.device)
        with self.torch.no_grad():
            out = self.model(**t)
        mask = t["attention_mask"].unsqueeze(-1).float()
        n = mask.sum()
        return LayerActs(acts=[((h * mask).sum(dim=1) / n).squeeze(0).float().tolist()
                               for h in out.hidden_states])


def fit_directions(reader: Reader, sets: dict[str, list[str]]) -> Directions:
    """One direction per concept per layer, from sentences expressing each concept.

    ── STANDARDISATION IS NOT OPTIONAL, AND THE FIRST VERSION LACKED IT ──────────────────────

    Transformer hidden states are dominated by a few very high-magnitude dimensions -- the known
    "rogue" or outlier features. A raw cosine follows those instead of the concept, and the first
    run of this showed exactly that: every concept collapsed onto `none_recoverable`, 12.5%
    against 12.5% chance.

    Standardising each dimension by its spread across the fitting set gives every dimension
    comparable weight. Same sentences, same model: 12.5% -> 50.0%, four times chance.

    The z-parameters are kept on the Directions object so that anything projected later is
    standardised the same way. Fitting on one scale and projecting on another would be a silent
    version of the same bug.
    """
    per = {c: [reader.read(s) for s in ss] for c, ss in sets.items()}
    n_layers = min(a.n_layers for v in per.values() for a in v)
    dim = len(next(iter(per.values()))[0].acts[0])

    mu, sd = [], []
    for L in range(n_layers):
        col = [a.acts[L] for v in per.values() for a in v]
        m = [statistics.fmean(v[i] for v in col) for i in range(dim)]
        s = [statistics.pstdev(v[i] for v in col) or 1e-9 for i in range(dim)]
        mu.append(m)
        sd.append(s)

    vecs = {}
    for c, acts in per.items():
        rows = []
        for L in range(n_layers):
            rows.append([statistics.fmean((a.acts[L][i] - mu[L][i]) / sd[L][i] for a in acts)
                         for i in range(dim)])
        vecs[c] = rows
    return Directions(concepts=tuple(sorted(sets)), vecs=vecs, n_layers=n_layers,
                      mu=mu, sd=sd)


def validate(reader: Reader, dirs: Directions, held_out: dict[str, list[str]],
             layer: int | None = None) -> dict:
    """B′-1. Do the directions classify sentences they never saw?

    Below chance and every projection computed with these directions is noise. This runs before
    anything is believed, not after something looks interesting.
    """
    L = layer if layer is not None else dirs.n_layers // 2
    correct = total = 0
    per_concept = {c: [0, 0] for c in held_out}
    for c, sents in held_out.items():
        for s in sents:
            p = dirs.project(reader.read(s))
            guess = max(p, key=lambda k: p[k][L])
            ok = guess == c
            correct += ok
            total += 1
            per_concept[c][0] += ok
            per_concept[c][1] += 1
    chance = 1.0 / len(dirs.concepts)
    return {"layer": L, "accuracy": correct / total if total else float("nan"),
            "chance": chance, "n": total,
            "per_concept": {c: (v[0] / v[1] if v[1] else float("nan"))
                            for c, v in per_concept.items()}}


def layer_profile(dirs: Directions, a: LayerActs) -> dict:
    """B′-2. How affective activation is distributed across depth.

    `early_late_ratio` is the curator's quantity: mean absolute affective projection in the first
    third of layers over the last third. Under his reading of the interpretability work, early
    layers carry valence/arousal — core affect, the leaked layer — and late layers carry
    conceptual and predictive structure, the emblematic layer.

    **It is a hypothesis about the model's architecture, not an established result**, and the
    number is meaningless until B′-1 passes.
    """
    p = dirs.project(a)
    n = min(dirs.n_layers, a.n_layers)
    lo, hi = n // 3, 2 * n // 3
    early = statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo))
    late = statistics.fmean(abs(v[L]) for v in p.values() for L in range(hi, n))
    return {"early": early, "late": late,
            "early_late_ratio": early / late if late else float("nan"),
            "peak_concept": max(p, key=lambda k: statistics.fmean(abs(x) for x in p[k])),
            "by_concept": {c: statistics.fmean(abs(x) for x in v) for c, v in p.items()},
            "n_layers": n}
