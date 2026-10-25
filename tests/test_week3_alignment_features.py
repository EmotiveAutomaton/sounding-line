"""Completed-source CPU feature consumer, pilot selection and fresh replay."""
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_alignment_features as card, week3_alignment_inputs as prep
from runners.drive.cards import week3_alignment_model as model
from runners.drive.cards.menus_io import write, sha256
from tests.test_week3_alignment_inputs import fixture as input_fixture
from tests.test_week3_alignment_model import fake_download


def complete(root):
    write(root / "COMPLETE.json", {"status": "COMPLETE", "fresh_process_verified": True,
          "outputs": {"output/SUMMARY.json": sha256(root / "output/SUMMARY.json")}})


def fixture(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    inputs = input_fixture(root / "source"); prep_root = root / "prepared"
    prep.execute(prep_root / "output", inputs, {"fixture": True}); complete(prep_root)
    model_root = root / "model"; model_out = model_root / "output"
    fake_download(revision=model.ENCODER["revision"], allow_patterns=list(model.FILES), max_workers=1, local_dir=model_out / "model")
    write(model_out / "SUMMARY.json", {"card": "CA1-model-intake", "encoder": model.ENCODER,
          "files": model.inventory(model_out / "model"), "input_hashes": {}, "corpus_inference": False, "provider_spend_cents": 0})
    complete(model_root)
    return {"prepared_summary": str(prep_root / "output/SUMMARY.json"), "prepared_complete": str(prep_root / "COMPLETE.json"),
            "model_summary": str(model_out / "SUMMARY.json"), "model_complete": str(model_root / "COMPLETE.json")}


def test_pilot_samples_comparisons_without_choice_use():
    rows = [{"candidates": [4 * i + j for j in range(4)], "prompt": str(i % 10), "choice": 0} for i in range(100)]
    splits = {"prompt_text_indices": {str(i): 400 + i for i in range(10)}}
    selected, ids, prompts = card.select_ids(rows, splits, "pilot", card.SEED)
    assert len(selected) == 10
    for r in rows: r["choice"] = 3
    assert card.select_ids(rows, splits, "pilot", card.SEED) == (selected, ids, prompts)


def test_actual_fixture_handler_fresh_replay_and_reentry(tmp_path):
    inputs = fixture(tmp_path / "fixture"); output = tmp_path / "out"; config = {"mode": "fixture"}
    result = card.execute(output, inputs, config)
    assert result["execution_only"] is True and result["comparisons"] == 100
    assert card.verify(output, inputs, config)["verified"]
    assert card.execute(output, inputs, config) == result
    vectors = np.load(output / "EMBEDDINGS.npy")
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1., atol=1e-6)


def test_saved_boundary_yield_and_resume(tmp_path):
    inputs = fixture(tmp_path / "fixture"); output = tmp_path / "out"; output.mkdir(); config = {"mode": "fixture"}
    write(output / "YIELD_REQUEST.json", {"reason": "fixture"})
    assert card.execute(output, inputs, config)["status"] == "yielded"
    assert not (output / "SUMMARY.json").exists()
    (output / "YIELD_REQUEST.json").unlink()
    card.execute(output, inputs, config)
    assert card.verify(output, inputs, config)["verified"]


def test_changed_chunk_refused(tmp_path):
    inputs = fixture(tmp_path / "fixture"); output = tmp_path / "out"; config = {"mode": "fixture"}
    card.execute(output, inputs, config)
    path = output / "chunks/00000.npy"; values = np.load(path); values[0, 0] += .1; np.save(path, values)
    with pytest.raises(ValueError, match="checkpoint changed"):
        card.execute(output, inputs, config)
    with pytest.raises(ValueError, match="replay differs"):
        card.verify(output, inputs, config)


def test_uncompleted_source_refused(tmp_path):
    inputs = fixture(tmp_path / "fixture")
    path = Path(inputs["prepared_complete"]); value = json.loads(path.read_text()); value["fresh_process_verified"] = False
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="fresh completion"):
        card.execute(tmp_path / "out", inputs, {"mode": "fixture"})


def test_main_requires_full_cluster_support(tmp_path):
    inputs = fixture(tmp_path / "fixture")
    with pytest.raises(ValueError, match="50 prompts"):
        card.execute(tmp_path / "out", inputs, {"mode": "full"})
