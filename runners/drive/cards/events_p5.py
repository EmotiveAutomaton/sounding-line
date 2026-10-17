"""P5 source extraction and the D4 deterministic split; private intermediates.

DESIGN CHECK: LESSONS 2-5. NULL: identical text has zero change, punctuation
and <=3-character within-word repairs enter housekeeping; unchanged text never
enters content. ALTERNATIVE: distance >=.15 or a finite-verb count change enters
content, unless housekeeping already applies. Overlapping definitions are kept
as flags and housekeeping wins, preventing a one-character typo entering both
comparators. All remaining edits are excluded. Source/final replay disagreement,
bad model identity, nonfinite embeddings or incomplete output are invalid, never
a null. This pass supplies features and split counts, not D4's predictive fit.

Sentence policy: final surviving sentences whose every nonspace character has
writer-typed provenance. Mixed/prompt/API sentences are retained as exclusions.
Edit embeddings use complete affected punctuation-bounded sentence windows;
minimal changed spans and original P2 windows are also retained explicitly.
Every char in the affected sentence is linked to the correction, including
surviving original chars and replacement chars, for D35 exclusion downstream.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

from runners.stage9.coauthor import units, text_of, delta_ops

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BOUNDARY = re.compile(r"[.!?](?:[\"'’”)]*)\s+|\n+")


def filehash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read(path):
    with Path(path).open(encoding="utf8") as f:
        return json.load(f)


def input_bindings(inputs):
    result = {k:filehash(v) for k,v in inputs.items() if Path(v).is_file()}
    spacy_root = Path(inputs["spacy_model"])
    if not spacy_root.is_dir():
        raise ValueError("spaCy input must be its explicit installed model directory")
    result["spacy_files"] = {p.relative_to(spacy_root).as_posix():filehash(p)
        for p in sorted(spacy_root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if not result["spacy_files"]:
        raise ValueError("empty spaCy model")
    return result


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")


def freeze_or_equal(path, value):
    if Path(path).exists():
        if read(path) != value:
            raise ValueError("retained intermediate differs")
    else:
        write(path,value)


def changed_bounds(before, after):
    left = 0
    while left < min(len(before), len(after)) and before[left] == after[left]:
        left += 1
    right = 0
    while right < min(len(before), len(after)) - left and before[-right - 1] == after[-right - 1]:
        right += 1
    return left, len(before) - right, len(after) - right


def sentence_bounds(text):
    start = 0
    for match in BOUNDARY.finditer(text):
        stop = match.end()
        if text[start:stop].strip():
            yield start, stop
        start = stop
    if text[start:].strip():
        yield start, len(text)


def affected_bounds(text, start, end):
    spans = list(sentence_bounds(text))
    chosen = [(a, b) for a, b in spans if a < end and b > start]
    if not chosen:  # An insertion at a boundary belongs to its following sentence.
        chosen = [(a, b) for a, b in spans if a <= start < b]
    if not chosen and spans and start == len(text):
        chosen = [spans[-1]]
    return (chosen[0][0], chosen[-1][1]) if chosen else (start, end)


def levenshtein_bounded(a, b, cap=3):
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        new = [i]
        for j, cb in enumerate(b, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (ca != cb)))
        row = new
    return min(row[-1], cap + 1)


def housekeeping(before, after):
    if before == after:
        return False
    left, old_end, new_end = changed_bounds(before, after)
    old, new = before[left:old_end], after[left:new_end]
    punctuation = bool(old + new) and all(unicodedata.category(c).startswith("P") for c in old + new)
    if punctuation:
        return True
    # A lexical repair changes one nonempty word, preserving the text around it.
    for word in re.finditer(r"\w+(?:['’]\w+)*", before, flags=re.UNICODE):
        a, b = word.span()
        if a <= left <= old_end <= b:
            new_b = b + len(after) - len(before)
            replacement = after[a:new_b]
            if (re.fullmatch(r"\w+(?:['’]\w+)*", replacement, re.UNICODE)
                    and before[:a] == after[:a] and before[b:] == after[new_b:]
                    and levenshtein_bounded(word.group(), replacement) <= 3):
                return True
    return False


def classify(before, after, before_vector, after_vector, before_verbs, after_verbs):
    a, b = np.asarray(before_vector, float), np.asarray(after_vector, float)
    if a.shape != b.shape or a.ndim != 1 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("invalid paired embedding")
    if not np.isclose(np.linalg.norm(a), 1, atol=1e-5) or not np.isclose(np.linalg.norm(b), 1, atol=1e-5):
        raise ValueError("embedding must be normalized")
    if min(before_verbs, after_verbs) < 0:
        raise ValueError("negative finite verb count")
    distance = float(np.clip(1 - a @ b, 0, 2))
    house = housekeeping(before, after)
    content = before != after and (distance >= .15 or before_verbs != after_verbs)
    return dict(split="housekeeping" if house else "content" if content else "excluded",
                housekeeping=house, content_threshold=content, overlap=house and content,
                cosine_distance=distance, finite_verbs_before=before_verbs, finite_verbs_after=after_verbs)


def extract_session(events, timeline):
    """Replay source exactly and retain per-character source/touch links privately."""
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("initialization required")
    times = [float(e["eventTimestamp"]) for e in events]
    if not all(map(math.isfinite, times)) or times != sorted(times):
        raise ValueError("invalid chronology")
    doc = units(events[0]["currentDoc"])
    meta = [("prompt", 0) for _ in doc]
    owners = list(range(len(doc)))
    touches = {}
    current_menu = pending = None
    expected = {e["ordinal"]: e for e in timeline["edits"]}
    if len(expected) != len(timeline["edits"]):
        raise ValueError("duplicate P2 edit ordinal")
    edits = []
    for ordinal, event in enumerate(events):
        name = event["eventName"]
        if name == "suggestion-open":
            current_menu = ordinal
        if name == "suggestion-select":
            pending = current_menu
        delta = event.get("textDelta")
        if delta in (None, ""):
            continue
        before, prior_owners = text_of(doc), owners
        source = event.get("eventSource")
        kind = "typed" if source == "user" else "accepted" if pending is not None else "api_unknown"
        origin_ordinal = pending if kind == "accepted" else ordinal
        out, new_owners, position, inserted_ids = [], [], 0, []
        for op in delta_ops(delta):
            if "insert" in op:
                new = units(op["insert"])
                ids = list(range(len(meta), len(meta) + len(new)))
                meta.extend([(kind, origin_ordinal)] * len(new))
                out.extend(new); new_owners.extend(ids); inserted_ids.extend(ids)
            else:
                count = op.get("retain", op.get("delete"))
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError("invalid UTF-16 boundary")
                if "retain" in op:
                    out.extend(doc[position:position + count]); new_owners.extend(owners[position:position + count])
                position += count
        out.extend(doc[position:]); new_owners.extend(owners[position:])
        doc, owners = out, new_owners
        after = text_of(doc)
        if kind == "accepted":
            if not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("accepted insertion is not canonical append")
            extra = len(doc) - len(prior_owners)
            if extra < 0 or extra != len(inserted_ids):
                raise ValueError("unexpected accepted insertion length")
            owners = prior_owners[:-1] + inserted_ids + prior_owners[-1:]
            pending = None
        if ordinal not in expected:
            continue
        p2 = expected[ordinal]
        left, old_end, new_end = changed_bounds(before, after)
        if source != "user" or (left, old_end, new_end) != (p2["changed_start_codepoint"], p2["before_changed_end"], p2["after_changed_end"]):
            raise ValueError("P2 edit bounds differ")
        if (p2["before"] != before[max(0,left-256):min(len(before),old_end+256)]
                or p2["after"] != after[max(0,left-256):min(len(after),new_end+256)]):
            raise ValueError("P2 edit window differs")
        ba, bb = affected_bounds(before, left, old_end)
        aa, ab = affected_bounds(after, left, new_end)
        # Use the union of both boundary views, aligned through unchanged context.
        # A new full stop must not manufacture a deletion of the following words.
        ba = aa = min(ba, aa)
        tail = min(len(before)-bb, len(after)-ab)
        bb, ab = len(before)-tail, len(after)-tail
        before_ids = prior_owners[len(units(before[:ba])):len(units(before[:bb]))]
        after_ids = owners[len(units(after[:aa])):len(units(after[:ab]))]
        for atom in set(before_ids + after_ids):
            touches.setdefault(atom, set()).add(ordinal)
        deleted_owners = [meta[a][0] for a in prior_owners[len(units(before[:left])):len(units(before[:old_end]))]]
        edits.append(dict(ordinal=ordinal, seconds=(times[ordinal]-times[0])/1000,
            before=before[ba:bb], after=after[aa:ab], before_start=ba, after_start=aa,
            changed_before=before[left:old_end], changed_after=after[left:new_end],
            p2_before=p2["before"], p2_after=p2["after"],
            deleted_origin_counts=dict(Counter(deleted_owners)),
            accepted_owners_touched=p2["accepted_owners_touched"],
            origin="model" if p2["accepted_owners_touched"] else "own" if deleted_owners and set(deleted_owners)=={"typed"} else "other"))
    final = text_of(doc)
    if final != timeline["final_document"] or len(edits) != len(expected):
        raise ValueError("P2 final document or edit coverage differs")
    sentences = []
    for a, b in sentence_bounds(final):
        ids = owners[len(units(final[:a])):len(units(final[:b]))]
        nonspace_ids = []
        cursor = 0
        for c in final[a:b]:
            width = len(units(c))
            if not c.isspace():
                nonspace_ids.extend(ids[cursor:cursor+width])
            cursor += width
        kinds = Counter(meta[i][0] for i in nonspace_ids)
        linked = sorted(set().union(*(touches.get(i, set()) for i in ids))) if ids else []
        sentences.append(dict(text=final[a:b], start_codepoint=a, end_codepoint=b,
            writer_typed=bool(kinds) and set(kinds)=={"typed"}, origin_counts=dict(kinds),
            correction_ordinals=linked,
            first_insertion_ordinal=min((meta[i][1] for i in nonspace_ids), default=None),
            last_insertion_ordinal=max((meta[i][1] for i in nonspace_ids), default=None)))
    return dict(edits=edits, sentences=sentences,
                final_sha256=hashlib.sha256(final.encode()).hexdigest())


def model_identity(path):
    identity = read(path)
    if identity["repo"] != MODEL:
        raise ValueError("P5 must use CONTENT_V2 MiniLM")
    root = Path(identity["path"])
    if root.name != identity["revision"]:
        raise ValueError("model revision differs")
    for rel, expected in identity["files"].items():
        if filehash(root / rel) != expected:
            raise ValueError("model bytes differ")
    return root


class Encoder:
    """Same first-254-token view and CLS/SEP-inclusive pooling as CONTENT_V2."""
    def __init__(self, identity_path, threads, batch_size):
        import torch
        from transformers import AutoModel, AutoTokenizer
        if threads not in (1, 2) or not 1 <= batch_size <= 32:
            raise ValueError("CPU limits differ")
        torch.set_num_threads(threads)
        self.torch, self.batch_size = torch, batch_size
        path = model_identity(identity_path)
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
        self.model = AutoModel.from_pretrained(path, local_files_only=True, trust_remote_code=False).to("cpu").eval()
        if any(p.device.type != "cpu" for p in self.model.parameters()):
            raise ValueError("unexpected device")

    def encode(self, texts):
        tok, torch = self.tokenizer, self.torch
        vectors, scope = [], []
        for start in range(0, len(texts), self.batch_size):
            ids = []
            for text in texts[start:start+self.batch_size]:
                encoded = tok(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
                raw, offsets = encoded["input_ids"], encoded["offset_mapping"]
                ids.append([tok.cls_token_id]+raw[:254]+[tok.sep_token_id])
                scope.append(dict(full_tokens=len(raw), used_tokens=min(len(raw),254), truncated=len(raw)>254,
                                  codepoint_end=offsets[min(len(raw),254)-1][1] if raw else 0))
            width = max(map(len, ids))
            mask = torch.tensor([[1]*len(i)+[0]*(width-len(i)) for i in ids])
            tokens = torch.tensor([i+[tok.pad_token_id]*(width-len(i)) for i in ids])
            with torch.inference_mode():
                states = self.model(input_ids=tokens, attention_mask=mask).last_hidden_state
                pooled = (states*mask.unsqueeze(-1)).sum(1)/mask.sum(1,keepdim=True)
                arr = pooled.numpy().astype(np.float32)
            arr /= np.maximum(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12)
            if arr.shape != (len(ids),384) or not np.isfinite(arr).all():
                raise ValueError("invalid embeddings")
            vectors.extend(arr)
        return np.asarray(vectors,np.float32).reshape((-1,384)), scope


def finite_verbs(doc):
    return sum("Fin" in token.morph.get("VerbForm") for token in doc)


def summary_from_saved(output):
    output = Path(output)
    classes, origins = Counter(), Counter()
    sentences = edits = touched = typed = truncated = overlap = 0
    index = read(output/"SESSION_INDEX.json")
    if len({r["session"] for r in index}) != len(index):
        raise ValueError("repeated saved session")
    for entry in index:
        path = output/entry["file"]
        if filehash(path) != entry["sha256"]:
            raise ValueError("saved session changed")
        with gzip.open(path,"rt",encoding="utf8") as f:
            s = json.load(f)
        v = np.load(output/entry["vectors"],allow_pickle=False)
        if filehash(output/entry["vectors"]) != entry["vectors_sha256"]:
            raise ValueError("saved vectors changed")
        if v.ndim != 2 or v.shape[1] != 384 or not np.isfinite(v).all() or not np.allclose(np.linalg.norm(v,axis=1),1,atol=1e-5):
            raise ValueError("saved vectors invalid")
        for e in s["edits"]:
            rebuilt = classify(e["before"],e["after"],v[e["before_vector"]],v[e["after_vector"]],
                               e["finite_verbs_before"],e["finite_verbs_after"])
            if rebuilt != {k:e[k] for k in rebuilt}:
                raise ValueError("split does not reproduce")
            classes[e["split"]]+=1; origins[e["origin"]]+=1; overlap+=int(e["overlap"])
        content = {e["ordinal"] for e in s["edits"] if e["split"]=="content"}
        for row in s["sentences"]:
            expected = bool(content.intersection(row["correction_ordinals"]))
            if row["content_correction_touched"] != expected:
                raise ValueError("content touch link differs")
            typed += int(row["writer_typed"])
            touched += int(row["writer_typed"] and expected)
        sentences += len(s["sentences"]); edits += len(s["edits"])
        truncated += sum(x["truncated"] for x in s["visibility"])
    return dict(card="P5_D4_SPLIT", sessions=len(index), sentences=sentences, writer_typed_sentences=typed,
                typed_sentences_touched_by_content=touched, edits=edits, split_counts=dict(sorted(classes.items())),
                correction_origins=dict(sorted(origins.items())), threshold_overlaps=overlap, truncated_vectors=truncated,
                descriptive=True, scientific_admission=False, d4_predictive_primary_run=False)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    """Called only by the owner's CPU lease/monitor wrapper; never dispatches itself."""
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    required = {"p2_index", "source_roster", "source_root", "sessions", "content_model", "spacy_model"}
    if set(inputs) != required:
        raise ValueError("explicit input contract differs")
    if set(config)!={"threads","batch_size","expected_sessions","expected_edits"}:
        raise ValueError("freeze the complete P5 config")
    if config["threads"] not in (1,2) or not 1 <= config["batch_size"] <= 32:
        raise ValueError("CPU limits differ")
    if any(type(config[k]) is not int or config[k]<1 for k in ("expected_sessions","expected_edits")):
        raise ValueError("invalid frozen cohort")
    from runners.drive.cards import states  # Common campaign state authority, no private replacement.
    import spacy
    spacy.require_cpu()
    nlp = spacy.load(inputs["spacy_model"], exclude=["ner"])
    encoder = Encoder(inputs["content_model"],config["threads"],config["batch_size"])
    p2_index = read(inputs["p2_index"])
    if len(p2_index) != config["expected_sessions"]:
        raise ValueError("P2 cohort coverage differs")
    roster = {r["session"]:r for r in read(inputs["source_roster"])}
    sessions = {r["session"]:r for r in read(inputs["sessions"])}
    if set(sessions) != {r["session"] for r in p2_index}:
        raise ValueError("session cohort differs")
    binding = input_bindings(inputs)
    run_binding=dict(paths=inputs,sha256=binding,config=config,
        sentence_policy="final surviving fully writer-typed sentences; mixed sentences retained as exclusions",
        edit_scope="full punctuation-bounded affected sentence; P2 256-codepoint windows retained")
    if (output/"INPUTS.json").exists():
        if read(output/"INPUTS.json") != run_binding:
            raise ValueError("resume inputs/config differ")
        if (output/"SUMMARY.json").exists():
            raise ValueError("completed output is verified, never rerun")
    elif any(output.iterdir()):
        raise ValueError("unbound existing output")
    else:
        write(output/"INPUTS.json",run_binding)
    index = []
    source_pins = {}
    saved_elapsed=0.
    for item in sorted(p2_index,key=lambda x:x["session"]):
        unit_started=time.monotonic()
        session = item["session"]
        meta = roster[session]
        source = Path(inputs["source_root"])/meta["path"]
        p2_path = Path(inputs["p2_index"]).parent/item["file"]
        if filehash(source) != meta["source_sha256"] or filehash(p2_path) != item["sha256"]:
            raise ValueError("input session changed")
        source_pins[str(source)]=meta["source_sha256"]
        source_pins[str(p2_path)]=item["sha256"]
        receipt=output/"sessions"/f"{session}.receipt.json"
        if receipt.exists():
            saved=read(receipt)
            if saved["source_sha256"]!=meta["source_sha256"] or saved["p2_sha256"]!=item["sha256"]:
                raise ValueError("checkpoint input changed")
            entry=saved["entry"]
            if filehash(output/entry["file"])!=entry["sha256"] or filehash(output/entry["vectors"])!=entry["vectors_sha256"]:
                raise ValueError("checkpoint changed")
            index.append(entry)
            saved_elapsed+=saved["elapsed_seconds"]
            if (output/"YIELD_REQUEST.json").exists():
                return dict(status="yielded",sessions_saved=len(index),sessions_total=len(p2_index),scientific_admission=False)
            continue
        with source.open(encoding="utf8") as f:
            events = [json.loads(line) for line in f]
        result = extract_session(events,read(p2_path))
        texts, look = [], {}
        def add(text):
            if text not in look:
                look[text]=len(texts); texts.append(text)
            return look[text]
        for e in result["edits"]:
            e["before_vector"],e["after_vector"]=add(e["before"]),add(e["after"])
        for s in result["sentences"]:
            s["vector"]=add(s["text"]) if s["writer_typed"] else None
        vectors, visibility = encoder.encode(texts)
        verbs = [finite_verbs(doc) for doc in nlp.pipe(texts,batch_size=32,n_process=1)]
        for e in result["edits"]:
            i,j=e["before_vector"],e["after_vector"]
            e.update(classify(e["before"],e["after"],vectors[i],vectors[j],verbs[i],verbs[j]))
        content={e["ordinal"] for e in result["edits"] if e["split"]=="content"}
        for s in result["sentences"]:
            s["content_correction_touched"]=bool(content.intersection(s["correction_ordinals"]))
        result.update(session=session,writer=item["writer"],prompt=sessions[session]["prompt"],
            timestamp=sessions[session]["timestamp"],end_at=sessions[session]["end_at"],visibility=visibility,
            source_sha256=meta["source_sha256"],p2_sha256=item["sha256"])
        rel=f"sessions/{session}.json.gz"; vector_rel=f"sessions/{session}.npy"
        (output/"sessions").mkdir(exist_ok=True)
        # An interrupted unit has no receipt. Preserve its incomplete files for
        # inspection; the owner's single repair retry writes a fresh unit pair.
        for path in (output/rel,output/vector_rel):
            if path.exists():
                retained=path.with_name(path.name+".incomplete")
                if retained.exists():
                    raise ValueError("second incomplete unit is not retried")
                path.rename(retained)
        with gzip.open(output/rel,"xt",encoding="utf8",newline="\n") as f:
            json.dump(result,f,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
        np.save(output/vector_rel,vectors,allow_pickle=False)
        entry=dict(session=session,file=rel,sha256=filehash(output/rel),vectors=vector_rel,
                   vectors_sha256=filehash(output/vector_rel))
        elapsed=time.monotonic()-unit_started
        write(receipt,dict(entry=entry,source_sha256=meta["source_sha256"],p2_sha256=item["sha256"],elapsed_seconds=elapsed))
        saved_elapsed+=elapsed
        index.append(entry)
        if len(index)==max(1,math.ceil(.1*len(p2_index))):
            if not (output/"FIRST_TENTH.json").exists():
                write(output/"FIRST_TENTH.json",dict(sessions=len(index),elapsed_seconds=saved_elapsed,
                    projected_seconds=saved_elapsed*len(p2_index)/len(index),forecast_cpu_seconds=3600))
        if (output/"YIELD_REQUEST.json").exists():
            return dict(status="yielded",sessions_saved=len(index),sessions_total=len(p2_index),scientific_admission=False)
    freeze_or_equal(output/"SESSION_INDEX.json",index)
    freeze_or_equal(output/"SOURCE_PINS.json",source_pins)
    summary=summary_from_saved(output)
    if summary["edits"] != config["expected_edits"]:
        raise ValueError("P2 edit census differs")
    if binding != input_bindings(inputs):
        raise ValueError("input changed during extraction")
    write(output/"SUMMARY.json",summary)
    return summary


def verify(output: Path, inputs: dict, config: dict) -> dict:
    binding=read(Path(output)/"INPUTS.json")
    if binding["paths"] != inputs or binding["config"] != config:
        raise ValueError("verification inputs/config differ")
    if binding["sha256"] != input_bindings(inputs):
        raise ValueError("frozen inputs changed")
    model_identity(inputs["content_model"])
    for path,expected in read(Path(output)/"SOURCE_PINS.json").items():
        if filehash(path)!=expected:
            raise ValueError("frozen source changed")
    result=summary_from_saved(output)
    if result != read(Path(output)/"SUMMARY.json"):
        raise ValueError("primary split census differs")
    return dict(verified=True,primary=result)
