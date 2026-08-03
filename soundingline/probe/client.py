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
# Pinned and verified installed, 2026-08-02. 6.6GB of weights on a 12GB card leaves enough KV
# cache for a full artifact plus the family plus the loop state, which is the binding constraint
# here rather than parameter count.
#
# Two sourcing notes, both recorded because both cost time:
#   * `qwen3.5:9b-q4` — the tag named in the research pass — DOES NOT EXIST. Ollama's web tag
#     listing displays quantisation variants that are not published as pullable manifests, and
#     `ollama pull` answers "file does not exist". The real tag is unsuffixed.
#   * a stray `qwen3:8b` sat here briefly after a partial edit. Any run recorded against that
#     string is invalid; none was.
LOCAL_MODEL = "qwen3.5:9b"

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

    def read_text(self, system: str, prompt: str) -> str: ...


# ---------------------------------------------------------------------------------------------

class LocalClient:
    """A-5 local arm. Carries convergence-sampling volume.

    Ollama's `format` parameter takes a JSON schema and constrains decoding to it, which is the
    same guarantee the API arm gets from `messages.parse()`. `keep_alive` holds the model in
    VRAM across the k samples of one artifact — on 12GB that is the difference between a
    convergence run and a slideshow.
    """

    arm = "local"

    # Pinned to loopback explicitly rather than inherited from OLLAMA_HOST.
    #
    # This is a security decision, not a workaround. OLLAMA_HOST is an ambient environment
    # variable that anything on the machine can set, and the probe is the process that reads
    # adversarial text — a probe whose model endpoint is settable by the environment is a probe
    # whose output can be redirected without touching this repository. EGRESS_ALLOWLIST says the
    # local arm reaches loopback; this is where that is enforced rather than assumed.
    #
    # It also happens to fix a real failure: this machine has OLLAMA_HOST=0.0.0.0, a *bind*
    # address. The client dutifully tried to *connect* to 0.0.0.0 and failed.
    HOST = "http://127.0.0.1:11434"

    def __init__(self, model: str = LOCAL_MODEL, *, seed: int | None = None,
                 num_ctx: int = 16384, host: str = HOST) -> None:
        self.model = model
        self.seed = seed
        self.num_ctx = num_ctx
        self.host = host

    def read_text(self, system: str, prompt: str) -> str:
        """Wholly unconstrained prose. No `format`, no schema, no grammar.

        Exists so the free-form arm's reasoning step is genuinely unconstrained. Routing it
        through a one-string schema would impose the format tax on the baseline while the
        bounded arm reasons freely — manufacturing the very advantage the ablation is supposed
        to measure.
        """
        import ollama

        client = ollama.Client(host=self.host)
        options: dict[str, Any] = {"num_ctx": self.num_ctx, "num_predict": 1600}
        if self.seed is not None:
            options["seed"] = self.seed
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
            "options": options,
            "keep_alive": "10m",
            "think": False,
        }
        _assert_no_tools(**kwargs)
        return (client.chat(**kwargs)["message"].get("content") or "").strip()

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading, *, two_stage: bool = True) -> ProbeResult:
        """Two calls: reason in prose, then coerce to schema.

        `two_stage=False` reproduces the old single-call path and exists only so the format tax
        can be MEASURED rather than asserted. It is not a supported production mode.
        """
        import ollama  # imported lazily: the analysis package must import with no client present

        from soundingline.probe import render

        client = ollama.Client(host=self.host)
        options: dict[str, Any] = {"num_ctx": self.num_ctx}
        if self.seed is not None:
            options["seed"] = self.seed

        t0 = time.perf_counter()
        reasoning = ""

        if two_stage:
            # ── Stage 1: unconstrained prose. No `format`, so nothing competes with reasoning.
            r1 = client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt + render.reason_suffix()},
                ],
                options={**options, "num_predict": 1600},
                keep_alive="10m",
                think=False,
            )
            reasoning = (r1["message"].get("content") or "").strip()
            if not reasoning:
                raise ValueError("stage 1 returned no reasoning; nothing to coerce")
            coerce_messages = [
                {"role": "system", "content": render.coerce_system()},
                {"role": "user", "content": render.coerce(reasoning)},
            ]
        else:
            coerce_messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]

        # ── Stage 2: constrained. The grammar now only has to transcribe, not reason.
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": coerce_messages,
            "format": json_schema(schema),
            # Explicit ceiling on the coercion call. Without it a sample truncated mid-object
            # while enumerating decisions, and a truncated JSON payload is a lost reading rather
            # than a short one.
            "options": {**options, "num_predict": 3000},
            "keep_alive": "10m",
            "think": False,
        }
        _assert_no_tools(**kwargs)
        r2 = client.chat(**kwargs)
        latency = time.perf_counter() - t0

        raw = r2["message"]["content"]
        return ProbeResult(
            parsed=schema.model_validate_json(raw),
            model=self.model,
            arm=self.arm,
            prompt_sha256=_sha(system + "\n" + prompt),
            response_sha256=_sha(raw),
            latency_s=latency,
            usage={
                "reasoning_chars": len(reasoning),
                "two_stage": two_stage,
                "eval_count": r2.get("eval_count"),
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

    def read_text(self, system: str, prompt: str) -> str:
        """Wholly unconstrained prose. See LocalClient.read_text for why this exists."""
        import anthropic

        client = anthropic.Anthropic()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": self.effort},
        }
        _assert_no_tools(**kwargs)
        r = client.messages.create(**kwargs)
        if r.stop_reason == "refusal":
            raise ProbeRefusal(f"{self.model} declined this artifact.")
        return "".join(b.text for b in r.content if b.type == "text").strip()

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading, *, two_stage: bool = True) -> ProbeResult:
        """Same two-stage shape as the local arm. Identical treatment is the point.

        A5's reference arm only bounds the local arm if it is doing the same thing. Giving the
        API arm a single constrained call while the local arm reasons first would make any
        difference between them uninterpretable — model capability and execution strategy would
        be confounded.
        """
        import anthropic

        from soundingline.probe import render

        if os.environ.get("SOUNDING_LINE_NO_EGRESS"):
            raise RuntimeError(
                "SOUNDING_LINE_NO_EGRESS is set; the API arm is disabled. Use --arm local."
            )

        client = anthropic.Anthropic()
        t0 = time.perf_counter()
        reasoning = ""

        if two_stage:
            r1 = client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": prompt + render.reason_suffix()}],
                output_config={"effort": self.effort},
            )
            if r1.stop_reason == "refusal":
                raise ProbeRefusal(
                    f"{self.model} declined this artifact "
                    f"(category={getattr(r1.stop_details, 'category', None)!r})."
                )
            reasoning = "".join(b.text for b in r1.content if b.type == "text").strip()
            if not reasoning:
                raise ValueError("stage 1 returned no reasoning; nothing to coerce")
            coerce_system, coerce_user = render.coerce_system(), render.coerce(reasoning)
        else:
            coerce_system, coerce_user = system, prompt

        # `output_config.format` with the SAME explicit schema the local arm compiles, rather
        # than `messages.parse(output_format=...)`. Pydantic renders the distributions as open
        # objects, and on the first live call Claude returned `{}` for both — schema-valid,
        # measurement-empty. The explicit form names every family value and requires all of them.
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": coerce_system,
            "messages": [{"role": "user", "content": coerce_user}],
            "output_config": {
                "format": {"type": "json_schema", "schema": json_schema(schema)},
            },
        }
        _assert_no_tools(**kwargs)
        r2 = client.messages.create(**kwargs)
        latency = time.perf_counter() - t0

        if r2.stop_reason == "refusal":
            raise ProbeRefusal(
                f"{self.model} declined at the coercion step "
                f"(category={getattr(r2.stop_details, 'category', None)!r})."
            )

        raw = next(b.text for b in r2.content if b.type == "text")
        return ProbeResult(
            parsed=schema.model_validate_json(raw),
            model=self.model,
            arm=self.arm,
            prompt_sha256=_sha(system + chr(10) + prompt),
            response_sha256=_sha(raw),
            latency_s=latency,
            usage={
                "reasoning_chars": len(reasoning),
                "input_tokens": r2.usage.input_tokens,
                "output_tokens": r2.usage.output_tokens,
            },
        )


def make_client(arm: str, **kwargs: Any) -> ProbeClient:
    if arm == "local":
        return LocalClient(**kwargs)
    if arm == "api":
        return ApiClient(**kwargs)
    raise ValueError(f"unknown arm {arm!r}; expected 'local' or 'api'")
