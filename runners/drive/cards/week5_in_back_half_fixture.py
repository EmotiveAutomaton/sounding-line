"""Constructed, all-handler and refusal fixture for IN5--IN7. No corpus access."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import week5_in_back_half as m


def source(directory):
    rng = np.random.default_rng(11571)
    generation, validation = [], []
    for prompt in m.MAPPED + ("joy", "boredom", "surprise"):
        for i in range(64):
            text = f"constructed-{prompt}-{i:03d}"
            ratings = rng.uniform(1.3, 4.7, len(m.old.APPRAISALS))
            row = dict(zip(m.old.APPRAISALS, ratings))
            row.update(text_id=text, prolific_id=f"constructed-writer-{i // 2:02d}", emotion=prompt,
                       intensity=float(rng.uniform(1.4, 4.6)), confidence=float(rng.uniform(1.4, 4.6)), word_count=20)
            generation.append(row)
            for r in range(5):
                values = np.clip(.5 * ratings + .5 * rng.uniform(1, 5, len(ratings)), 1, 5)
                rr = dict(zip(m.old.APPRAISALS, values))
                rr.update(text_id=text, prolific_id=f"constructed-reader-{r}", original_emotion=prompt,
                          intensity=float(rng.uniform(1.2, 4.8)), confidence=3.)
                validation.append(rr)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {"generation": directory / "generation.parquet", "validation": directory / "validation.parquet"}
    pd.DataFrame(generation).to_parquet(paths["generation"], index=False)
    pd.DataFrame(validation).to_parquet(paths["validation"], index=False)
    return {k: str(v) for k, v in paths.items()}, {k: m.old.digest(v) for k, v in paths.items()}


def configuration(phase, pins, draws=64, texture_draws=16):
    return {"phase": phase, "constructed_fixture": True, "fixture_source_pins": pins,
            "draws": draws, "texture_draws": texture_draws}


def execute(output: Path, inputs: dict, config: dict):
    output = Path(output)
    sources, pins = source(output / "constructed-source")
    receipts = {}
    for phase in ("IN5", "IN6", "IN7"):
        settings = configuration(phase, pins)
        result = m.execute(output / phase, sources, settings)
        verified = m.verify(output / phase, sources, settings)
        assert result["complete_card"] and verified["verified"]
        receipts[phase] = {"complete": True, "verified": True, "result_sha256": m.old.digest(output / phase / "RESULT.json")}
    in5 = json.loads((output / "IN5" / "RESULT.json").read_text("utf8"))
    assert len(in5["map"]) == 48 and len(in5["joint_item_models"]["fear"]) == 7
    assert all(row["by_construction"] == name.startswith("full/") for name, row in in5["map"].items())
    in6 = json.loads((output / "IN6" / "RESULT.json").read_text("utf8"))
    assert in6["texts"] == 256 and in6["primary"]["clusters"] == 32
    assert in6["secondary"]["same_rater"]["by_construction"]
    in7 = json.loads((output / "IN7" / "RESULT.json").read_text("utf8"))
    assert in7["texts"] == 192 and not set(in7["prompt_counts"]) & set(m.MAPPED)
    assert len(in7["per_item"]) == 21
    # Exercise real checkpoint pause/continuation, then fresh whole-handler replay.
    settings = configuration("IN6", pins)
    paused = m.execute(output / "continuation", sources, {**settings, "max_new_blocks": 1})
    assert paused["status"] == "yielded"
    before = {str(p.relative_to(output / "continuation")): m.old.digest(p) for p in (output / "continuation" / "checkpoints").rglob("*.json")}
    resumed = m.execute(output / "continuation", sources, settings)
    assert resumed == json.loads((output / "IN6" / "RESULT.json").read_text("utf8"))
    assert all(m.old.digest(output / "continuation" / p) == value for p, value in before.items())
    assert m.verify(output / "continuation", sources, settings)["verified"]
    result = {"passed": True, "handlers": receipts, "paired_maps_and_joint_items": True,
              "writer_cluster_join": True, "untouched_prompt_partition": True,
              "sealed_pause_resume_and_full_independent_replay": True}
    m.sealed(output / "FIXTURE.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict):
    expected = json.loads((Path(output) / "FIXTURE.json").read_text("utf8"))
    actual = execute(Path(output) / "fixture-independent-replay", inputs, config)
    if actual != expected:
        raise ValueError("constructed IN extension fixture replay differs")
    return {"verified": True, "all_three_handlers_replayed": True}
