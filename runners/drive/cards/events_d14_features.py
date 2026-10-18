"""Frozen local D14 disturbances; no P3 labels or P4 fitted outputs."""
import hashlib
import re
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.decomposition import PCA
from .events_p5 import Encoder, filehash
from .menus_p4 import prefix_features


def paragraph(document):
    """Last nonempty newline-delimited paragraph; no invented earlier text."""
    chunks = list(re.finditer(r"[^\r\n]+", document))
    for match in reversed(chunks):
        if match.group().strip():
            return match.group(), match.start(), match.end()
    return "", 0, 0


def pilot_writers(writers, seed):
    writers = sorted(set(writers))
    order = sorted(writers, key=lambda w: (hashlib.sha256(f"{seed}:{w}".encode()).hexdigest(), w))
    return order[:max(1, (len(order) + 9) // 10)]


def spacy_pins(path):
    root = Path(path)
    return {str(p): filehash(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


class ParagraphEncoder(Encoder):
    """Frozen MiniLM; tokenize full paragraph, retain its last 254 native tokens."""
    def encode(self, texts):
        tok, torch = self.tokenizer, self.torch
        vectors, scopes = [], []
        for start in range(0, len(texts), self.batch_size):
            ids = []
            for text in texts[start:start + self.batch_size]:
                encoded = tok(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
                raw, offsets = encoded["input_ids"], encoded["offset_mapping"]
                first = max(0, len(raw) - 254)
                ids.append([tok.cls_token_id] + raw[first:] + [tok.sep_token_id])
                scopes.append(dict(full_tokens=len(raw), used_tokens=min(254, len(raw)), truncated=len(raw) > 254,
                    first_native_token=first, codepoint_start=offsets[first][0] if raw else 0,
                    codepoint_end=offsets[-1][1] if raw else 0))
            width = max(map(len, ids))
            mask = torch.tensor([[1] * len(row) + [0] * (width - len(row)) for row in ids])
            tokens = torch.tensor([row + [tok.pad_token_id] * (width - len(row)) for row in ids])
            with torch.inference_mode():
                hidden = self.model(input_ids=tokens, attention_mask=mask).last_hidden_state
                arr = ((hidden * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)).numpy().astype(np.float32)
            arr /= np.maximum(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12)
            if arr.shape != (len(ids), 384) or not np.isfinite(arr).all():
                raise ValueError("invalid paragraph vectors")
            vectors.extend(arr)
        return np.asarray(vectors, np.float32).reshape((-1, 384)), scopes


def linguistic(doc):
    finite = [t for t in doc if "Fin" in t.morph.get("VerbForm")]
    persons = [t for t in doc if t.pos_ == "PRON" and t.morph.get("Person")]
    nfinite, nperson = max(1, len(finite)), max(1, len(persons))
    return dict(finite_verbs=len(finite), past_share=sum("Past" in t.morph.get("Tense") for t in finite) / nfinite,
        present_share=sum("Pres" in t.morph.get("Tense") for t in finite) / nfinite,
        first_person_share=sum("1" in t.morph.get("Person") for t in persons) / nperson,
        second_person_share=sum("2" in t.morph.get("Person") for t in persons) / nperson,
        third_person_share=sum("3" in t.morph.get("Person") for t in persons) / nperson,
        person_tokens=len(persons), entities=sorted({e.text.casefold() for e in doc.ents}),
        quoted=bool(re.search(r'["“”]', doc.text)), characters=len(doc.text), words=sum(not t.is_space for t in doc))


def extract_writer(sessions, records, vectors, encoder, nlp):
    records = {r["key"]: r for r in records}
    menus = sorted((r for s in sessions for r in s["rows"]), key=lambda r: (r["open_at"], r["key"]))
    paragraphs = [paragraph(r["document"]) for r in menus]
    encoded, scopes = encoder.encode([p[0] for p in paragraphs])
    texts = []
    for row, (text, _, _) in zip(menus, paragraphs):
        texts.extend([text] + row["menu"])
    docs = iter(nlp.pipe(texts, batch_size=32, n_process=1))
    rows, audit, paragraph_vectors, offered = [], Counter(), [], []
    for menu, context, scope, para in zip(menus, encoded, scopes, paragraphs):
        feature = records[menu["key"]]
        if feature["writer"] != menu["writer"] or feature["session"] != menu["session"] or len(feature["options"]) != len(menu["menu"]):
            raise ValueError("content source join differs")
        baseline = linguistic(next(docs))
        parsed = [linguistic(next(docs)) for _ in menu["menu"]]
        audit["menus"] += 1
        audit["truncated_paragraphs"] += scope["truncated"]
        paragraph_vectors.append(dict(key=menu["key"], vector=context.tolist(), scope=scope,
                                      start_codepoint=para[1], end_codepoint=para[2]))
        candidates = []
        for slot, candidate in enumerate(parsed):
            cosine = float(context @ vectors[feature["options"][slot]])
            if not math_finite_cosine(cosine):
                raise ValueError("invalid topic cosine")
            disturbance = {k: candidate[k] - baseline[k] for k in
                ("past_share", "present_share", "first_person_share", "second_person_share", "third_person_share")}
            disturbance.update(dialogue_introduced=candidate["quoted"] and not baseline["quoted"],
                new_entity=bool(set(candidate["entities"]) - set(baseline["entities"])),
                candidate_characters=candidate["characters"], candidate_words=candidate["words"])
            candidates.append(dict(key=menu["key"], writer=menu["writer"], session=menu["session"], position=slot,
                topic_drift=1 - cosine if para[0].strip() else None, disturbance=disturbance,
                paragraph_truncated=scope["truncated"]))
        offered.extend(candidates)
        if not para[0].strip():
            audit["empty_preceding_paragraph"] += 1
            continue
        if menu["handling"] == "ignore":
            audit["ignored_menus"] += 1
            continue
        if menu["handling"] in ("accept", "edit"):
            chosen = [i for i, text in enumerate(menu["menu"]) if text == menu["inserted"]]
            if len(chosen) != 1:
                audit["ambiguous_selected_menus"] += 1
                continue
            eligible = chosen
            audit["unchosen_offers_without_observed_handling"] += len(menu["menu"]) - 1
        elif menu["handling"] == "dismiss":
            eligible = range(len(menu["menu"]))
        else:
            raise ValueError("unknown handling")
        for slot in eligible:
            rows.append(dict(**candidates[slot], protected=int(menu["handling"] in ("dismiss", "edit")), handling=menu["handling"]))
    return dict(rows=rows, audit=dict(audit), paragraphs=paragraph_vectors, offered_disturbances=offered,
        not_measured=["sentiment change: no frozen validated local classifier", "formality change: no frozen validated local classifier"])


def math_finite_cosine(value):
    return bool(np.isfinite(value) and -1.00001 <= value <= 1.00001)


def nuisance_matrix(rows, sessions, records, vectors, p8_rows, seed, pca_dimensions=16):
    """Exact frozen D1 feature assembly, without depending on any fitted P4 output."""
    allowed = {r["key"] for s in sessions for r in s["rows"]}
    d1_rows, base, scalar, embedding = prefix_features(sessions, [r for r in records if r["key"] in allowed], vectors,
                                                      [r for r in p8_rows if r["key"] in allowed])
    if len(d1_rows) < 2:
        raise ValueError("insufficient menus for content projection")
    dimensions = min(pca_dimensions, len(d1_rows) - 1, embedding.shape[1])
    pca = PCA(n_components=dimensions, svd_solver="randomized", random_state=seed)
    components = pca.fit_transform(embedding)
    matrix = np.c_[base, scalar, components]
    lookup = {r["key"]: i for i, r in enumerate(d1_rows)}
    output = []
    for row in rows:
        # Individual offer position/length supplement D1's prechoice menu features.
        output.append(np.r_[matrix[lookup[row["key"]]], np.eye(5)[row["position"]] if row["position"] < 5 else np.zeros(5),
                              row["position"] >= 5, np.log1p(row["disturbance"]["candidate_characters"])])
    return np.asarray(output, float), dict(dimensions=dimensions, components=pca.components_.tolist(),
        mean=pca.mean_.tolist(), fit_menu_keys=[r["key"] for r in d1_rows],
        baseline="Exact menus_p4.prefix_features with authenticated P8 scores; no fitted P4 models or labels",
        outcome_use="PCA uses predictors only; lawful resolved earlier handling enters D1 prefix features")
