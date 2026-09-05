"""T03: the catalog cards in docs/TOOLS.md, one per repository and corpus: what it is, what
human input it holds (maker-stated, reader-inferred, both), size, license, fetch status,
loader status, the published baseline reproduced, and the Stage 9 question it could serve.
Written idempotently under one marked section so a rerun replaces the block.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (a deliverable file written by a cell is written whole under a
  marker, never appended twice).
gates: T03: NULL is any manifested corpus or clone without a card (fails DOWN);
  ALTERNATIVE: one card each. bands: exhaustive.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage8.testbed.clones import CLONES                                   # noqa: E402
from runners.stage8.testbed.corpora import CORPORA                                 # noqa: E402
from soundingline.stage8 import now_iso, read_registry                            # noqa: E402

TOOLS = REPO / "docs" / "TOOLS.md"
START = "<!-- STAGE8_TESTBED_CATALOG_START -->"
END = "<!-- STAGE8_TESTBED_CATALOG_END -->"

STAGE9_Q = {
    "MMToM-QA": "a fine-tuned small model as the action-likelihood estimator inside the realizer (the reader as the likelihood, the program as the posterior)",
    "muma-tom": "the multi-agent form of the same, for mixed-control records",
    "Hypothetical-Minds": "natural-language hypothesis refinement against the joint reader's proposal breadth limit",
    "InversePlanning.jl": "the exact known-law comparator, if a Julia runtime is installed",
    "LaBToM.jl": "epistemic language as a belief factor proposal grammar",
    "CLIPS.jl": "instructions as strong evidence, against the artifact-only regime",
    "acting-as-inverse-inverse-planning": "the bard: a maker shaping a reader's inference, the audience factor made active",
    "gpudrive-CoDec": "recoverable attention as the subjective action set's formal object",
    "BPL": "process from a static artifact in a medium where the maker's share is concentrated (the artful gradient's far end)",
    "timecraft": "process reconstruction trained on real time lapses: a natural process record outside text",
    "inverse_painting": "the same, a second program",
    "world-model-evaluation": "the compression and distinction metrics as expertise-gate rulers",
    "verbalized-sampling": "the one-call distribution readout's own calibration fixtures",
    "iterater": "intention labels as purpose truth on real revisions",
    "newsedits": "the prospective update task as a real-record expertise gate",
    "thought-tracing": "Stage 7's particle arm, re-pinned",
    "AutoToM": "Stage 7's expansion arm, re-pinned",
}
STAGE9_C = {
    "argrewrite_v2": "reader-inferred purposes against maker-stated ones where both exist",
    "newsedits_2": "the real-record ceiling for the expertise gate (predict the next edit)",
    "arxivedits": "purpose recall on real revisions with clean intention truth",
    "iterater": "the same, a second corpus",
    "genius_expertise": "crowd inference against the maker's own statement on the same lines (the human bridge)",
    "woolf_online": "one maker across drafts: accumulation on a real series",
    "shelley_godwin": "the same, a second edition",
    "commitbench": "stated proximal goals at scale in code, a domain caveat on the card",
    "coauthor": "already measured (Stage 7 P13)",
    "scholawrite": "already measured (Stage 7 P14)",
}


def render() -> str:
    src = (read_registry("TESTBED_SOURCES") or {}).get("clones") or {}
    cm = read_registry("CORPUS_MANIFESTS") or {}
    tb = read_registry("TESTBED") or {}
    fx = tb.get("fixtures") or {}
    sm = tb.get("smoke") or {}
    bl = tb.get("baselines") or {}
    lines = [START, "", f"### Stage 8 testbed catalog (written {now_iso()} by T03; one card per repository and corpus)", "",
             "| repository | operation worth borrowing | head | license | files | the Stage 9 question |", "|---|---|---|---|---|---|"]
    for name, spec in CLONES.items():
        rec = (src.get(name) or {}).get("receipt") or {}
        lines.append(f"| {name} | {spec['card']} | {(rec.get('head') or 'not cloned')[:10]} | {rec.get('license_first_line', 'not cloned')} | {rec.get('files_on_disk', '')} | {STAGE9_Q.get(name, '')} |")
    lines += ["", "*Table: the sibling programs cloned read-only into the sibling reference workspace (shallow, blob-limited); head is the pinned commit; none is on any capsule path.*", "",
              "| corpus | human input | fetch status | loader | published baseline | the Stage 9 question |", "|---|---|---|---|---|---|"]
    for name, spec in CORPORA.items():
        st = (cm.get("items") or {}).get(name, "not fetched")
        f = fx.get(name) or {}
        loader = "fixture PASS" if f.get("pass") else ("in hand: " + str(sm.get(name)) if f.get("pass") is None else "fixture FAIL")
        b = bl.get(name) or {}
        lines.append(f"| {name} | {spec['human_input']} | {st} | {loader} | {b.get('status', '')} {('(' + str(b.get('reproduced')) + ')') if b.get('reproduced') is not None else ''} | {STAGE9_C.get(name, '')} |")
    lines += ["", "*Table: the human-input corpora as manifests (hashes, URLs, lengths, license hints in corpora/manifests/stage8_testbed.json; text in the gitignored store; bulk data never re-hosted); no analysis of these corpora ran this stage beyond the loader fixtures and the counts.*", "", END]
    return "\n".join(lines)


def write_cards() -> dict:
    text = TOOLS.read_text(encoding="utf-8")
    block = render()
    if START in text and END in text:
        pre = text.split(START)[0]
        post = text.split(END)[1]
        new = pre + block + post
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    TOOLS.write_text(new, encoding="utf-8", newline="\n")
    n_cards = len(CLONES) + len(CORPORA)
    return {"cards": n_cards, "path": str(TOOLS)}
