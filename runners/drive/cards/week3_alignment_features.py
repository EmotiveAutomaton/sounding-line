"""CA1 pinned CPU embedding pilot/full preparation with deterministic checkpoints.

DESIGN CHECK: LESSONS 3-5. Completed source and model receipts bind every byte.
Only candidate/prompt texts enter embeddings: no identities, choices, explanations
or later context. A pilot selects ten percent of comparisons by fixed seed for
cost only; it cannot become a statistical result. Full production refuses fixture
encoding and insufficient prompt-cluster support. Fresh verification re-encodes
every saved chunk in the same batch layout before admitting the feature table.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

from .menus_io import assert_equal, input_hashes, read, write, sha256
from .batch_runtime import atomic
from .week3_choice_intake import ENCODER
from .week3_alignment_model import inventory

SEED = 20261026


def bind(inputs, prefix):
    path = Path(inputs[prefix + "_summary"]).resolve()
    completion_path = Path(inputs[prefix + "_complete"]).resolve()
    completed = read(completion_path)
    if completed.get("status") != "COMPLETE" or completed.get("fresh_process_verified") is not True:
        raise ValueError(prefix + " fresh completion missing")
    if completed.get("outputs", {}).get(path.relative_to(completion_path.parent).as_posix()) != sha256(path):
        raise ValueError(prefix + " summary not bound by completion")
    return read(path), path.parent


def source(inputs):
    report, root = bind(inputs, "prepared")
    if report.get("card") != "CA1-inputs" or report.get("state") != "inputs_ready": raise ValueError("completed CA1 inputs required")
    for name, expected in report["output_hashes"].items():
        if sha256(root / name) != expected: raise ValueError("private prepared table changed")
    with gzip.open(root / "COMPARISONS.jsonl.gz", "rt", encoding="utf8") as stream:
        rows = [json.loads(line) for line in stream]
    splits = read(root / "SPLITS.json")
    return report, root, rows, splits


def select_ids(rows, splits, mode, seed):
    if not rows: raise ValueError("no prepared comparisons")
    selected = np.arange(len(rows))
    if mode == "pilot":
        selected = np.sort(np.random.default_rng(seed).choice(len(rows), max(1, int(np.ceil(.1 * len(rows)))), replace=False))
    candidates = {i for row in (rows[int(j)] for j in selected) for i in row["candidates"]}
    prompts = {row["prompt"] for row in (rows[int(j)] for j in selected)}
    prompt_ids = {splits["prompt_text_indices"][p] for p in prompts}
    return selected.tolist(), sorted(candidates | prompt_ids), sorted(prompts)


def encoder(inputs, config):
    report, root = bind(inputs, "model")
    if report.get("card") != "CA1-model-intake" or report["encoder"] != ENCODER:
        raise ValueError("pinned CA1 encoder required")
    assert_equal(inventory(root / "model"), report["files"])
    if config.get("mode") == "fixture":
        def fake(texts):
            values = np.array([[int.from_bytes(hashlib.sha256((str(k) + text).encode()).digest()[:4], "big") / 2**32
                               for k in range(384)] for text in texts], dtype=np.float32)
            return values / np.linalg.norm(values, axis=1, keepdims=True)
        return fake
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    model = SentenceTransformer(str(root / "model"), device="cpu", trust_remote_code=False, local_files_only=True)
    if model.get_sentence_embedding_dimension() != 384 or model.max_seq_length != 128:
        raise ValueError("encoder shape/token limit differs from pinned contract")
    def encode(texts):
        values = model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True,
                              normalize_embeddings=True, device="cpu")
        if values.shape != (len(texts), 384) or not np.isfinite(values).all(): raise ValueError("invalid CPU embeddings")
        return np.asarray(values, dtype=np.float32)
    return encode


def run(output, inputs, config, verifying=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    mode = config.get("mode", "full")
    if mode not in ("full", "pilot", "fixture"): raise ValueError("unknown CA1 feature mode")
    seed = int(config.get("seed", SEED)); chunk_size = 512
    binding = {"inputs": input_hashes(inputs), "config": config, "module_sha256": sha256(__file__)}
    if (output / "BINDINGS.json").exists(): assert_equal(binding, read(output / "BINDINGS.json"))
    elif verifying: raise ValueError("feature source binding missing")
    else: write(output / "BINDINGS.json", binding)
    prepared, root, rows, splits = source(inputs)
    selected, ids, prompts = select_ids(rows, splits, mode, seed)
    _, full_ids, _ = select_ids(rows, splits, "full", seed)
    if mode == "full" and len(prompts) < 50: raise ValueError("fewer than 50 prompts for frozen cluster fallback")
    wanted = set(ids); texts = {}
    with gzip.open(root / "TEXTS.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["index"] in wanted:
                if row["index"] in texts or hashlib.sha256(row["text"].encode("utf8")).hexdigest() != row["sha256"]:
                    raise ValueError("duplicate or changed embedding text")
                texts[row["index"]] = row["text"]
    if set(texts) != wanted: raise ValueError("missing selected candidate/prompt text")
    encode = encoder(inputs, config); parts = []; cpu = []; selected_texts = 0
    for number, begin in enumerate(range(0, len(ids), chunk_size)):
        chunk_ids = ids[begin:begin + chunk_size]; path = output / "chunks" / f"{number:05}.npy"
        receipt_path = path.with_suffix(".json")
        if path.exists() and receipt_path.exists() and not verifying:
            receipt = read(receipt_path)
            if receipt["sha256"] != sha256(path) or receipt["text_indices"] != chunk_ids: raise ValueError("embedding checkpoint changed")
            values = np.load(path, allow_pickle=False); charge = receipt["cpu_seconds"]
        else:
            before = time.process_time()
            with threadpool_limits(limits=2): values = encode([texts[i] for i in chunk_ids])
            charge = time.process_time() - before
            if path.exists():
                if not np.array_equal(values, np.load(path, allow_pickle=False)): raise ValueError("fresh CPU embedding replay differs")
            elif verifying: raise ValueError("missing embedding chunk")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream: np.save(stream, values, allow_pickle=False)
            if not verifying:
                write(receipt_path, {"text_indices": chunk_ids, "sha256": sha256(path), "cpu_seconds": charge})
        if values.shape != (len(chunk_ids), 384) or not np.isfinite(values).all(): raise ValueError("checkpoint embedding shape invalid")
        parts.append(values); cpu.append(charge); selected_texts += len(chunk_ids)
        if not verifying:
            atomic(output / "PROGRESS.json", {"phase": "embedding", "texts_completed": selected_texts, "texts_total": len(ids)})
            if (output / "YIELD_REQUEST.json").exists(): return {"status": "yielded", "card": "CA1-features", "texts_completed": selected_texts}
    matrix = np.concatenate(parts); lookup = {v: i for i, v in enumerate(ids)}
    vector_path = output / "EMBEDDINGS.npy"
    if vector_path.exists():
        if not np.array_equal(matrix, np.load(vector_path, allow_pickle=False)): raise ValueError("concatenated embeddings changed")
    elif verifying: raise ValueError("complete embeddings missing")
    else:
        with vector_path.open("xb") as stream: np.save(stream, matrix, allow_pickle=False)
    cluster_count = min(50, len(prompts)) if mode != "full" else 50
    prompt_values = matrix[[lookup[splits["prompt_text_indices"][p]] for p in prompts]]
    with threadpool_limits(limits=2):
        labels = KMeans(n_clusters=cluster_count, random_state=seed, n_init=10, algorithm="lloyd").fit_predict(prompt_values)
    index = {"text_indices": ids, "comparison_indices": selected,
             "prompt_clusters": {p: int(label) for p, label in zip(prompts, labels)}}
    index_path = output / "INDEX.json"
    if index_path.exists(): assert_equal(index, read(index_path))
    elif verifying: raise ValueError("feature index missing")
    else: write(index_path, index)
    result = {"card": "CA1-features", "mode": mode, "execution_only": mode != "full",
              "input_hashes": input_hashes(inputs), "encoder": ENCODER, "texts": len(ids),
              "comparisons": len(selected), "full_comparisons": len(rows), "full_texts": len(full_ids),
              "dimensions": 384, "normalized": True, "maximum_tokens": 128, "prompt_clusters": cluster_count,
              "permutation_route": prepared["permutation_route"],
              "output_hashes": {"EMBEDDINGS.npy": sha256(vector_path), "INDEX.json": sha256(index_path)},
              "scope": "Representation preparation only; no preference reader, value direction or probability test."}
    path = output / "SUMMARY.json"
    if path.exists(): assert_equal(result, read(path))
    elif verifying: raise ValueError("feature summary missing")
    else:
        write(path, result)
        write(output / "TIMING.json", {"encoding_cpu_seconds": float(sum(cpu)), "selected_texts": len(ids),
              "full_text_count": len(full_ids), "full_encoding_cpu_projection": float(sum(cpu) * len(full_ids) / len(ids)),
              "projection_scope": "one encoding pass only; admission must charge execute plus fresh replay, source overhead and later model fitting"})
    return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    run(output, inputs, config, True)
    return {"verified": True, "fresh_all_embeddings_and_clusters": True}
