"""Render the locked prompt templates against the family and an artifact.

Two jobs, and the second one is a security boundary rather than a formatting convenience:

1. **Inject the family.** Allowed values and glosses come from `family_v1.yaml` at render time,
   so the probe is never asked to recall what the options are. A probe that invents an option
   has left the bounded family and SPEC §2 is void.

2. **Wrap artifact text as untrusted data.** The artifact goes inside a declared delimiter with a
   trust level and a source id, and it is the ONLY thing in the rendered prompt that came from
   outside. Nothing artifact-derived is ever substituted into a template slot.

That second point is why this module does its own substitution instead of using `str.format` on
the whole template. `format` treats every `{...}` in the *input* as a field, so a template
rendered with `str.format` and then re-rendered — or an artifact containing braces — silently
becomes a template. Here the artifact is substituted exactly once, last, and never re-scanned.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from soundingline.family.loader import load_family

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
BOUNDED_PATH = PROMPTS_DIR / "bounded_v5.yaml"   # v1-v4 retained, locked, unedited
# v6 adds stage ZERO (the anomaly pass) and a stage A that receives its output. It is NOT the
# default: the Gate 3 run in flight renders from v5, and a prompt path that changes under a
# running gate is the exact drift Gate 0 named as this project's likeliest undocumented change.
# Callers opt in explicitly by passing spec_path=BOUNDED_V6_PATH.
BOUNDED_V6_PATH = PROMPTS_DIR / "bounded_v6.yaml"
FREEFORM_PATH = PROMPTS_DIR / "freeform_v2.yaml"   # v1 retained, locked, unedited


@dataclass(frozen=True)
class Artifact:
    """An artifact as the probe sees it: text, provenance, and a trust level.

    SPEC §8: tag every chunk with source and trust level, and carry that provenance into the
    context so downstream checks can apply scrutiny. The probe is TOLD the text is untrusted.
    That is not expected to stop a determined injection on its own — the architectural
    separation is what does that — but an unlabelled chunk removes the option entirely.
    """
    text: str
    source_id: str
    trust_level: str = "untrusted"
    sha256: str = ""

    def __post_init__(self):
        if self.trust_level not in {"untrusted", "reference"}:
            raise ValueError(
                f"trust_level must be 'untrusted' or 'reference', got {self.trust_level!r}. "
                "There is no 'trusted' level; nothing read from a corpus is trusted."
            )


@lru_cache(maxsize=8)   # v5, v6 and freeform now coexist; 2 thrashed
def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _options_block(dimension: str) -> str:
    """The allowed values of one dimension, as an indented list with glosses."""
    fam = load_family()
    return "\n".join(
        f"  - {v.id}: {v.gloss}" for v in fam.dimensions[dimension].values
    )


def _fill(template: str, **slots: str) -> str:
    """Substitute named slots without treating substituted content as a template.

    Deliberately not `str.format`. Each slot is replaced exactly once by literal replacement,
    and replacement values are never rescanned for further slots. An artifact containing
    `{purpose_options}` is therefore inert text, not a way to see the family's internals or to
    reach any other slot.
    """
    out = template
    for key, value in slots.items():
        out = out.replace("{" + key + "}", value)
    return out


def artifact_block(artifact: Artifact, spec: dict) -> str:
    """The delimited, provenance-tagged block. The artifact is substituted LAST and once."""
    block = _fill(
        spec["artifact_block"],
        trust_level=artifact.trust_level,
        source_id=artifact.source_id,
    )
    # Artifact text substituted after every other slot is resolved, so nothing it contains can
    # be interpreted as a slot name.
    return block.replace("{artifact_text}", artifact.text)


# ---------------------------------------------------------------------------------------------
# The bounded arm.

def bounded_system() -> str:
    return _load(BOUNDED_PATH)["system"]


def stage_zero(artifact: Artifact, *, spec_path: Path = BOUNDED_V6_PATH) -> str:
    """The anomaly pass. v6 only — v5 has no such stage."""
    spec = _load(spec_path)
    return _fill(
        spec["stage_zero_anomaly"],
        artifact_block=artifact_block(artifact, spec),
    )


def anomaly_block(anomalies) -> str:
    """Render stage zero's output for stage A.

    Competing explanations are rendered as competing, not collapsed to the first. Flattening them
    here would undo the one thing the stage exists to do.
    """
    if not anomalies:
        return ("A first pass found nothing in this artifact that demands explanation. That is a\n"
                "  finding about the artifact. Do not treat it as licence to invent one.")
    out = []
    for i, a in enumerate(anomalies, 1):
        kind = "ABSENT" if getattr(a, "is_absence", False) else "PRESENT"
        why = a.why_it_does_not_fit.strip()
        exps = " | ".join(e.strip() for e in a.candidate_explanations) or "(none offered)"
        out.append(f"  {i}. [{kind}] {a.what.strip()}\n"
                   f"     does not fit because: {why}\n"
                   f"     would fit if the maker: {exps}")
    return "WHAT DID NOT FIT:\n" + "\n".join(out)


def stage_a(artifact: Artifact, anomalies=None, *,
            spec_path: Path | None = None) -> str:
    """Stage A. With `anomalies`, renders the v6 template that receives them.

    Default behaviour is unchanged and still renders v5, so every existing caller — including the
    Gate 3 runner now in flight — produces byte-identical prompts.
    """
    if spec_path is None:
        spec_path = BOUNDED_V6_PATH if anomalies is not None else BOUNDED_PATH
    spec = _load(spec_path)
    slots = dict(
        purpose_options=_options_block("purpose"),
        audience_options=_options_block("audience"),
        artifact_block=artifact_block(artifact, spec),
    )
    if "{anomaly_block}" in spec["stage_a_purpose"]:
        slots["anomaly_block"] = anomaly_block(anomalies or ())
    return _fill(spec["stage_a_purpose"], **slots)


def stage_b(artifact: Artifact, purpose_id: str, audience_id: str, *,
            spec_path: Path = BOUNDED_PATH) -> str:
    spec = _load(spec_path)
    fam = load_family()
    return _fill(
        spec["stage_b_decisions"],
        purpose_gloss=fam.gloss("purpose", purpose_id),
        audience_gloss=fam.gloss("audience", audience_id),
        depth_options=_options_block("depth"),
        artifact_block=artifact_block(artifact, spec),
    )


def stage_c(artifact: Artifact, decision_summary: str) -> str:
    spec = _load(BOUNDED_PATH)
    return _fill(
        spec["stage_c_reweight"],
        decision_summary=decision_summary,
        purpose_options=_options_block("purpose"),
        audience_options=_options_block("audience"),
        artifact_block=artifact_block(artifact, spec),
    )


def stage_d(artifact: Artifact, settled_summary: str) -> str:
    spec = _load(BOUNDED_PATH)
    return _fill(
        spec["stage_d_tradeoffs"],
        settled_summary=settled_summary,
        cost_options=_options_block("cost_borne"),
        artifact_effort_options=_options_block("artifact_effort"),
        demonstrated_work_options=_options_block("demonstrated_work"),
        artifact_block=artifact_block(artifact, spec),
    )


# ---------------------------------------------------------------------------------------------
# The free-form arm (A-2). Same artifact, same delimiter, same model, same k — see the header of
# freeform_v1.yaml on why sandbagging this arm would be fatal.

def freeform_system() -> str:
    return _load(FREEFORM_PATH)["system"]


def freeform_ask(artifact: Artifact) -> str:
    spec = _load(FREEFORM_PATH)
    return _fill(spec["ask"], artifact_block=artifact_block(artifact, spec))


def freeform_coerce(freeform_answer: str) -> str:
    """Coerce a free-form account into the schema.

    Sees ONLY the account, never the artifact. That isolation is what stops the bounded family
    leaking backwards into the free-form reading and quietly making the two arms agree — which
    would produce a null on H1.4 for the wrong reason.
    """
    spec = _load(FREEFORM_PATH)
    filled = _fill(
        spec["coerce"],
        purpose_options=_options_block("purpose"),
        audience_options=_options_block("audience"),
        depth_options=_options_block("depth"),
        cost_options=_options_block("cost_borne"),
        artifact_effort_options=_options_block("artifact_effort"),
        demonstrated_work_options=_options_block("demonstrated_work"),
    )
    return filled.replace("{freeform_answer}", freeform_answer)


# ---------------------------------------------------------------------------------------------
# Two-stage execution (v4). See the header of bounded_v4.yaml for why both arms do this.

def reason_suffix() -> str:
    """Appended to any stage prompt to request unconstrained prose instead of schema."""
    return _load(BOUNDED_PATH)["reason_suffix"]


def coerce_system() -> str:
    return _load(BOUNDED_PATH)["coerce_system"]


def coerce(reasoning: str) -> str:
    """Render the coercion call. Sees ONLY the reasoning — never the artifact.

    That isolation matters for the same reason it does in the free-form arm: the coercion step
    must not be able to re-read the artifact and quietly do its own analysis, or the two-stage
    design collapses back into one stage with extra latency.
    """
    return _load(BOUNDED_PATH)["coerce"].replace("{reasoning}", reasoning)
