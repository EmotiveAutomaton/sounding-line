"""Pinned public CPU encoder intake for CA1; no participant data leaves the host.

DESIGN CHECK: LESSONS 4-5. Immutable revision and every retained file hash
are required. A readable model name is not a download receipt. Only the
declared safetensors and tokenizer/configuration files may enter this capsule.
No training, inference on corpus data, paid request, or GPU use occurs here.
"""
from pathlib import Path

from .menus_io import assert_equal, input_hashes, read, write, sha256
from .week3_choice_intake import ENCODER

FILES = ("README.md", "config.json", "config_sentence_transformers.json", "modules.json",
         "1_Pooling/config.json", "model.safetensors", "sentence_bert_config.json",
         "sentencepiece.bpe.model", "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json")


def inventory(root):
    result = {}
    for name in FILES:
        path = Path(root) / name
        if not path.is_file() or path.stat().st_size == 0: raise ValueError("encoder capsule missing " + name)
        result[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    if sum(v["bytes"] for v in result.values()) > 1_000_000_000: raise ValueError("encoder exceeds frozen one-billion-byte ceiling")
    return result


def execute(output, inputs, config):
    from huggingface_hub import snapshot_download
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if config.get("encoder", ENCODER) != ENCODER: raise ValueError("encoder revision changed")
    snapshot_download(repo_id=ENCODER["model"], revision=ENCODER["revision"], local_dir=output / "model",
                      allow_patterns=list(FILES), max_workers=1)
    result = {"card": "CA1-model-intake", "encoder": ENCODER, "files": inventory(output / "model"),
              "input_hashes": input_hashes(inputs), "corpus_inference": False, "provider_spend_cents": 0}
    write(output / "SUMMARY.json", result)
    return result


def verify(output, inputs, config):
    result = read(Path(output) / "SUMMARY.json")
    if result["encoder"] != ENCODER: raise ValueError("encoder identity changed")
    assert_equal(inventory(Path(output) / "model"), result["files"])
    assert_equal(input_hashes(inputs), result["input_hashes"])
    return {"verified": True, "full_download_byte_inventory": True}
