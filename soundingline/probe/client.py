"""The probe clients. Two arms (A-5), one interface, and no tools on either.

SPEC §8 is the governing constraint and it is enforced here rather than documented here:

    The probe model gets no tools. It reads and returns a constrained schema. It cannot fetch,
    write, execute, or call anything. Structured output only — never free-form action.

Both clients construct their requests without a `tools` parameter, and `_assert_no_tools` runs
on every call. That check is not defensive programming — the probe reads adversarial content
whose stated purpose is to make models take actions, so "we never pass tools" needs to be an
assertion rather than a convention.

── ON THE ONE PLACE THIS ARCHITECTURE IS HONESTLY IMPERFECT ──────────────────────────────────

SPEC §8 says analysis "has no network at all". The local arm satisfies that in the sense that
matters — Ollama is on loopback, and no artifact-derived string ever reaches a socket that
leaves the machine. The API arm does not: it egresses to api.anthropic.com by construction.

That is a real weakening and it is recorded rather than glossed. The posture that is actually
enforceable:

  * the probe process may reach EXACTLY ONE host, declared in `EGRESS_ALLOWLIST`;
  * it may never reach a host named, linked, or implied by any artifact;
  * it never fetches — it only posts a prompt and reads a schema back.

The last point is what keeps this defensible. An egress channel that cannot be pointed at an
attacker-chosen destination is not a fetch capability, so the fetch/analysis separation survives
even though "no network at all" does not. Anyone who disagrees should run the local arm only;
`--arm local` is a supported configuration and Gate 1's H1.5 exists to establish whether the two
arms even agree.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from soundingline.probe.schema import Reading, json_schema

# The probe process may reach these hosts and no others. Loopback for the local arm; the API
# endpoint for the reference arm. Nothing artifact-derived may ever be added to this list.
EGRESS_ALLOWLIST = frozenset({"127.0.0.1", "localhost", "api.anthropic.com"})

# A-5, local arm. Deliberately a constant rather than a default argument: the model is part of
# the measurement, so it is recorded in every ProbeResult and belongs in one place.
#
# NOTE FOR GATE 1: this is a placeholder and must be pinned to a model that is actually
# installed before the first run. The machine currently has only `deepseek-r1`, which is a poor
# fit — reasoning models emit long chains of thought and adhere weakly to JSON schemas, and the
# probe needs schema adherence at k× volume rather than visible reasoning. Context length is the
# binding constraint: a full artifact + the family + the loop state must fit.
LOCAL_MODEL = "qwen3:8b"

# A-5, reference arm. Structured outputs are supported on this model; `messages.parse()`
# validates the response against the pydantic schema and the model retries on mismatch.
API_MODEL = "claude-opus-5"

# Medium rather than high: the probe's task is constrained extraction inside a fixed family,
# not open-ended reasoning, and convergence sampling multiplies every token by k. Raise it if
# Gate 1 shows the reference arm under-recovering decisions.
API_EFFORT = "medium"

MAX_TOKENS = 16000


class ProbeRefusal(RuntimeError):
    """The model declined to answer.

    Expected and not exceptional: the corpus includes adversarial content, and a probe that
    never refused anything on this corpus would be the surprising result. Recorded as an
    outcome, never retried with the same prompt, and never silently dropped — a refusal that
    vanishes from the record would bias the sample toward artifacts the model finds comfortable.
    """


@dataclass(frozen=True)
class ProbeResult:
    """One model call, with everything needed to reproduce or audit it.

    The hashes rather than the texts: SPEC §8 says store hashes and offsets publicly, text
    privately. A results file carrying `prompt_sha256` can be published; one carrying the prompt
    would republish the artifact.

    `parsed` is whichever stage schema the call requested — the loop's stages each return their
    own type (SPEC §3), so this is deliberately not narrowed to `Reading`.
    """
    parsed: BaseModel
    model: str
    arm: str
    prompt_sha256: str
    response_sha256: str
    latency_s: float
    usage: dict[str, Any] = field(default_factory=dict)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assert_no_tools(**kwargs: Any) -> None:
    """Fail loudly if any tool-shaped parameter reached a probe request.

    Checked on every call rather than once at construction, because the failure this guards
    against is a future edit that adds a tool "just for retrieval" — which is exactly the
    capability the corpus is engineered to exploit.
    """
    forbidden = {"tools", "tool_choice", "mcp_servers", "container", "betas"}
    present = forbidden & set(kwargs)
    if present:
        raise RuntimeError(
            f"probe request carried {sorted(present)}. SPEC §8: the probe model gets no tools. "
            f"This is not a restriction to be relaxed — it is the security boundary."
        )


class ProbeClient(Protocol):
    """One call, one Reading. No conversation, no state, no tools."""

    arm: str
    model: str

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading) -> ProbeResult: ...


# ---------------------------------------------------------------------------------------------

class LocalClient:
    """A-5 local arm. Carries convergence-sampling volume.

    Ollama's `format` parameter takes a JSON schema and constrains decoding to it, which is the
    same guarantee the API arm gets from `messages.parse()`. `keep_alive` holds the model in
    VRAM across the k samples of one artifact — on 12GB that is the difference between a
    convergence run and a slideshow.
    """

    arm = "local"

    def __init__(self, model: str = LOCAL_MODEL, *, seed: int | None = None,
                 num_ctx: int = 16384) -> None:
        self.model = model
        self.seed = seed
        self.num_ctx = num_ctx

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading) -> ProbeResult:
        import ollama  # imported lazily: the analysis package must import with no client present

        options: dict[str, Any] = {"num_ctx": self.num_ctx}
        if self.seed is not None:
            # Recorded per sample. Convergence is measured ACROSS seeds (SPEC §5), so the seed
            # is an experimental variable, not a reproducibility knob to be fixed.
            options["seed"] = self.seed

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": json_schema(schema),
            "options": options,
            "keep_alive": "10m",
        }
        _assert_no_tools(**kwargs)

        t0 = time.perf_counter()
        response = ollama.chat(**kwargs)
        latency = time.perf_counter() - t0

        raw = response["message"]["content"]
        return ProbeResult(
            parsed=schema.model_validate_json(raw),
            model=self.model,
            arm=self.arm,
            prompt_sha256=_sha(system + "\n" + prompt),
            response_sha256=_sha(raw),
            latency_s=latency,
            usage={
                "eval_count": response.get("eval_count"),
                "prompt_eval_count": response.get("prompt_eval_count"),
            },
        )


# ---------------------------------------------------------------------------------------------

class ApiClient:
    """A-5 reference arm. Quality reference on a held-out slice.

    Not the primary measurement instrument. Its job is to answer H1.5 — do the two arms agree
    on the ORDERING of artifacts by fit? — so that the local arm's cheap readings can be trusted
    at Gate 2's volume. If the arms disagree on ordering, the hybrid design is unsound and Gate
    0 §4's cost analysis has to be redone.
    """

    arm = "api"

    def __init__(self, model: str = API_MODEL, *, effort: str = API_EFFORT) -> None:
        self.model = model
        self.effort = effort

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading) -> ProbeResult:
        import anthropic  # lazily, per the note in LocalClient

        if os.environ.get("SOUNDING_LINE_NO_EGRESS"):
            raise RuntimeError(
                "SOUNDING_LINE_NO_EGRESS is set; the API arm is disabled. Use --arm local."
            )

        client = anthropic.Anthropic()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "output_format": schema,
            "output_config": {"effort": self.effort},
        }
        _assert_no_tools(**kwargs)

        t0 = time.perf_counter()
        response = client.messages.parse(**kwargs)
        latency = time.perf_counter() - t0

        # Safety classifiers can decline; a declined request returns HTTP 200 with
        # stop_reason "refusal" and possibly empty content. Checked BEFORE reading the parse,
        # because indexing into content on a refusal is the standard way this breaks.
        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise ProbeRefusal(
                f"{self.model} declined this artifact (category={category!r}). "
                f"Recorded as an outcome; not retried."
            )

        parsed = response.parsed_output
        raw = json.dumps(parsed.model_dump(mode="json"), sort_keys=True)
        return ProbeResult(
            reading=reading,
            model=self.model,
            arm=self.arm,
            prompt_sha256=_sha(system + "\n" + prompt),
            response_sha256=_sha(raw),
            latency_s=latency,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_input_tokens": getattr(
                    response.usage, "cache_read_input_tokens", None),
            },
        )


def make_client(arm: str, **kwargs: Any) -> ProbeClient:
    if arm == "local":
        return LocalClient(**kwargs)
    if arm == "api":
        return ApiClient(**kwargs)
    raise ValueError(f"unknown arm {arm!r}; expected 'local' or 'api'")
