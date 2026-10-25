"""The encoder network intake fetches only the frozen public capsule."""
from pathlib import Path
import sys
import types

import pytest

from runners.drive.cards import week3_alignment_model as card


def fake_download(**kwargs):
    assert kwargs["revision"] == card.ENCODER["revision"]
    assert kwargs["allow_patterns"] == list(card.FILES)
    assert kwargs["max_workers"] == 1
    for name in card.FILES:
        path = Path(kwargs["local_dir"]) / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("fixture " + name).encode())


def test_actual_handler_and_mutated_download_refusal(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "huggingface_hub", types.SimpleNamespace(snapshot_download=fake_download))
    result = card.execute(tmp_path, {}, {})
    assert result["corpus_inference"] is False
    assert card.verify(tmp_path, {}, {})["verified"]
    (tmp_path / "model/model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(tmp_path, {}, {})


def test_missing_model_refused(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        card.inventory(tmp_path)


def test_moving_revision_refused_before_network(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "huggingface_hub", types.SimpleNamespace(snapshot_download=lambda **kw: pytest.fail("network reached")))
    with pytest.raises(ValueError, match="revision"):
        card.execute(tmp_path, {}, {"encoder": {**card.ENCODER, "revision": "main"}})
