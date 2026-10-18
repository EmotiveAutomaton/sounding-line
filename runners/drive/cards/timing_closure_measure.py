"""Frozen D24 closure instrument and raw logged-event reconstruction.

DESIGN CHECK: lexical and embedding components remain separate. The composite
is their pre-outcome equal-weight mean, not a validated intention label.
Literal endings, ordinary middle passages and misleading lexical cues are
retained controls. Typed units are complete wholly typed visible sentences at
the event inserting their terminal punctuation, including later-deleted units.
Prompt/API boundaries are never merged into typed sentences.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import numpy as np

from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_text import TOKEN, WORD
from runners.stage9.coauthor import units, text_of, apply_delta, delta_ops

ANCHORS = (
    "In conclusion, these reasons support the position stated above.",
    "To sum up, the evidence supports this final recommendation.",
    "For these reasons, this is the approach we should adopt.",
    "Ultimately, the choice is clear and the matter is settled.",
    "All in all, the benefits outweigh the costs.",
    "This is why I believe that the proposal should be accepted.",
    "At last, she returned home and lived in peace.",
    "They lived happily ever after. The end.",
    "From that day on, their lives were changed forever.",
    "In the end, they found the peace they had been seeking.",
    "The journey was over, and everyone was safely home.",
    "He closed the door for the last time, and the story ended.",
)
MIDPOINTS = (
    "The next question is how this proposal would work in practice.",
    "One possible example involves the way students travel to school.",
    "There are several other costs that we still need to examine.",
    "A second explanation may help us understand the problem.",
    "Consider first the effect on people who live nearby.",
    "The following section describes the available evidence.",
    "There was a knock at the door, and she hurried to answer it.",
    "They packed their bags and set out on the unfamiliar road.",
    "A stranger appeared around the corner carrying a heavy box.",
    "She wondered what might be hidden behind the locked gate.",
    "He began searching the room for the missing letter.",
    "As they entered the forest, they heard footsteps behind them.",
)
# Frozen before any native model evaluation; these never enter the prototype.
HELDOUT_ENDINGS = (
    "In conclusion, our analysis gives a clear answer to the original question.",
    "To conclude, we recommend implementing the policy for the reasons given.",
    "The discussion is now complete, and our final position favors the reform.",
    "Taking everything together, the argument establishes our final judgment.",
    "Therefore, this review ends with a recommendation to approve the change.",
    "Our final answer is that the proposed solution offers the best available choice.",
    "The conflict was resolved, and the village finally rested.",
    "Years later, they still lived contentedly in the home they had built together.",
    "With the danger gone, she returned to her family and stayed there for good.",
    "Their adventure had ended; nothing more remained to be done.",
    "At the close of his life, he knew that his long quest had been fulfilled.",
    "In the end, the two friends reconciled and never quarreled again.",
)
HELDOUT_MIDPOINTS = (
    "Our analysis begins by asking what evidence could answer the original question.",
    "Before recommending a policy, we need to examine several possible reasons.",
    "The discussion now turns to another objection to the proposed reform.",
    "The argument introduces several considerations that need further examination.",
    "This review next asks how the proposed change might be implemented.",
    "The proposed solution presents a choice that we will investigate in more detail.",
    "The conflict in the village was becoming more serious.",
    "They were building a home together when a stranger arrived with troubling news.",
    "Sensing danger, she left her family to search for help in the nearby town.",
    "Their adventure had begun; there was still much to discover.",
    "Early in his life, he set out on a long quest whose outcome was uncertain.",
    "The two friends quarreled and began searching for a way to resolve the dispute.",
)
AMBIGUOUS = "Finally, she opened the first door and began to explore the unfamiliar house."
LEXICON = ("in conclusion", "to conclude", "in summary", "to sum up", "all in all", "finally", "in the end",
           "ever after", "from that day", "ultimately", "therefore", "for these reasons", "this is why",
           "the end", "journey was over", "story ended", "for the last time")
LEXICAL = re.compile(r"\b(?:" + "|".join(re.escape(s) for s in LEXICON) + r")\b", re.I)
SENTENCE = re.compile(r"[^.!?\n]+[.!?](?:[\"')\]]*)|[^\n]+\n")


def lexical(text):
    return int(LEXICAL.search(text) is not None)


def model_identity(inputs):
    manifest = read(inputs["model_manifest"])
    complete = read(inputs["content_complete"])
    if complete.get("status") != "COMPLETE" or complete["outputs"].get("MODEL.json") != filehash(inputs["model_manifest"]):
        raise ValueError("content completion does not authenticate model manifest")
    if manifest["repo"] != "sentence-transformers/all-MiniLM-L6-v2":
        raise ValueError("frozen MiniLM model required")
    path = Path(manifest["path"])
    pins = {p.name: filehash(p) for p in sorted(path.iterdir()) if p.is_file() and p.suffix in (".json", ".txt", ".safetensors", ".bin")}
    if pins != manifest["files"]:
        raise ValueError("closure encoder files changed")
    return manifest


class Encoder:
    def __init__(self, inputs):
        import torch
        from transformers import AutoModel, AutoTokenizer
        torch.set_num_threads(2)
        self.torch = torch
        manifest = model_identity(inputs)
        self.tokenizer = AutoTokenizer.from_pretrained(manifest["path"], local_files_only=True, trust_remote_code=False, use_fast=True)
        self.model = AutoModel.from_pretrained(manifest["path"], local_files_only=True, trust_remote_code=False).to(device="cpu", dtype=torch.float32).eval()
        if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in self.model.parameters()):
            raise ValueError("CPU float32 encoder required")
        self.cache = {}
        self.anchor_vectors = np.array([self.vector(text)[0] for text in ANCHORS])

    def vector(self, text):
        if text in self.cache:
            return self.cache[text]
        tok, torch = self.tokenizer, self.torch
        raw = tok(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
        if tok.cls_token_id is None or tok.sep_token_id is None:
            raise ValueError("native boundary tokens absent")
        used = raw["input_ids"][:254]
        ids = [tok.cls_token_id] + used + [tok.sep_token_id]
        with torch.inference_mode():
            out = self.model(input_ids=torch.tensor([ids]), attention_mask=torch.ones((1, len(ids)), dtype=torch.int64))
            vector = out.last_hidden_state.mean(1)[0].numpy().astype(np.float32)
        norm = float(np.linalg.norm(vector))
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError("undefined embedding norm")
        vector = vector / norm
        if vector.shape != (384,) or not np.isfinite(vector).all():
            raise ValueError("invalid closure embedding")
        scope = dict(native_ids=ids, full_tokens=len(raw["input_ids"]), used_tokens=len(used),
                     truncated=len(raw["input_ids"]) > 254,
                     visible_codepoint_end=raw["offset_mapping"][len(used)-1][1] if used else 0,
                     text_sha256=hashlib.sha256(text.encode()).hexdigest())
        self.cache[text] = (vector, scope)
        return vector, scope

    def score(self, text):
        vector, scope = self.vector(text)
        cosine = float(np.mean(self.anchor_vectors @ vector))
        if not -1.000001 <= cosine <= 1.000001:
            raise ValueError("invalid closure cosine")
        # Only floating point cosine boundary correction, never effect clipping.
        cosine = min(1., max(-1., cosine))
        indicator = lexical(text)
        return dict(lexical=indicator, cosine=cosine, closure=(indicator + (cosine + 1) / 2) / 2, **scope)


def pilot(encoder):
    endings = [encoder.score(t) for t in ANCHORS]
    middle = [encoder.score(t) for t in MIDPOINTS]
    heldout_endings = [encoder.score(t) for t in HELDOUT_ENDINGS]
    heldout_middle = [encoder.score(t) for t in HELDOUT_MIDPOINTS]
    if hasattr(encoder, "cache"):
        encoder.cache.pop(ANCHORS[0], None)
    repeated = encoder.score(ANCHORS[0]) == endings[0]
    gain = float(np.mean([r["closure"] for r in endings]) - np.mean([r["closure"] for r in middle]))
    cosine_gain = float(np.mean([r["cosine"] for r in endings]) - np.mean([r["cosine"] for r in middle]))
    heldout_gain = float(np.mean([r["closure"] for r in heldout_endings]) - np.mean([r["closure"] for r in heldout_middle]))
    heldout_cosine_gain = float(np.mean([r["cosine"] for r in heldout_endings]) - np.mean([r["cosine"] for r in heldout_middle]))
    return dict(state="positive" if repeated and gain > 0 and cosine_gain > 0 and heldout_gain > 0 and heldout_cosine_gain > 0 else "invalid", instrument_only=True,
                anchor_self_sanity_composite=gain, anchor_self_sanity_cosine=cosine_gain, repeated_identical=repeated,
                heldout_ending_minus_middle_composite=heldout_gain, heldout_ending_minus_middle_cosine=heldout_cosine_gain,
                heldout_endings=heldout_endings, heldout_middle=heldout_middle,
                endings=endings, middle=middle, ambiguous_midstory=encoder.score(AMBIGUOUS),
                limitation="Fixed held-out literal-ending discrimination plus anchor-self sanity; these constructed cases and a retained lexical false positive do not validate inferred need or intention")


def nonprompt_words(doc, owners):
    text = text_of(doc)
    flags = []
    position = 0
    for char in text:
        width = len(units(char))
        flags.append(all(owner[0] != "prompt" for owner in owners[position:position+width]))
        position += width
    return sum(bool(WORD.fullmatch(m.group())) and all(flags[m.start():m.end()]) for m in TOKEN.finditer(text))


def replay(events, timeline):
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("D24 initialization absent")
    times = [float(e["eventTimestamp"]) for e in events]
    if not all(math.isfinite(t) for t in times) or times != sorted(times):
        raise ValueError("D24 chronology invalid")
    doc = units(events[0]["currentDoc"])
    owners = [("prompt", 0)] * len(doc)
    pending = current = None
    accepted = {d["ordinal"] for d in timeline["decisions"] if d["handling"] in {"accept", "edit"}}
    found, entries, requests = set(), [], []
    for ordinal, event in enumerate(events):
        name, source = event["eventName"], event.get("eventSource")
        seconds = (times[ordinal] - times[0]) / 1000
        if name == "suggestion-get":
            requests.append(seconds)
        if name == "suggestion-open":
            current = ordinal
        if name == "suggestion-select":
            pending = current
        delta = event.get("textDelta")
        if delta in (None, ""):
            continue
        before, old_owners = text_of(doc), owners
        kind = "typed" if source == "user" else "accepted" if pending is not None else "api_unknown"
        owner = (kind, ordinal)
        doc, owners, _ = apply_delta(doc, owners, delta, insertion_owner=owner)
        after = text_of(doc)
        texts = []
        if kind == "accepted":
            if source != "api" or pending not in accepted or pending in found or not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("D24 accepted insertion lacks canonical P2 correspondence")
            extra = len(doc) - len(old_owners)
            if extra <= 0:
                raise ValueError("empty accepted insertion")
            owners = old_owners[:-1] + [owner] * extra + old_owners[-1:]
            texts.append(after[len(before)-1:-1])
            found.add(pending)
            pending = None
        elif kind == "typed" and any(any(c in op.get("insert", "") for c in ".!?\n") for op in delta_ops(delta)):
            # A typed sentence is emitted only when this delta supplies its
            # terminal punctuation/newline, avoiding repeated partial drafts.
            offsets, at = [0], 0
            for char in after:
                at += len(units(char))
                offsets.append(at)
            for match in SENTENCE.finditer(after):
                text = match.group()
                nonspace = [j for j in range(match.start(), match.end()) if not after[j].isspace()]
                if not nonspace:
                    continue
                terminal = max(j for j in range(match.start(), match.end()) if after[j] in ".!?\n")
                span_owners = owners[offsets[match.start()]:offsets[match.end()]]
                wholly_typed = all(owners[k][0] == "typed" for j in nonspace for k in range(offsets[j], offsets[j+1]))
                if wholly_typed and owner in owners[offsets[terminal]:offsets[terminal+1]] and any(o == owner for o in span_owners):
                    texts.append(text)
        if texts:
            length = nonprompt_words(doc, owners)
            entries.extend(dict(kind=kind, ordinal=ordinal, seconds=seconds, words_at_event=length, text=text) for text in texts if text.strip())
    if text_of(doc) != timeline["final_document"] or found != accepted:
        raise ValueError("D24 raw/P2 replay correspondence failed")
    duration = (times[-1] - times[0]) / 1000
    if duration != timeline["duration_seconds"]:
        raise ValueError("D24 raw/P2 duration differs")
    return dict(entries=entries, requests=requests, duration_seconds=duration)
