import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week5_in_back_half as m
from runners.drive.cards import week5_in_back_half_fixture as f


def test_complete_handlers_pause_resume_and_independent_replay(tmp_path):
    assert f.execute(tmp_path, {}, {})["passed"]
    assert f.verify(tmp_path, {}, {})["verified"]


def test_signed_null_cluster_ols_matches_direct_and_sensitivity(tmp_path):
    rng = np.random.default_rng(171)
    x = np.column_stack((np.ones(96), rng.normal(size=(96, 2))))
    clusters = np.repeat(np.arange(32), 3)
    for sign in (-1, 0, 1):
        y = 2 + .35 * sign * x[:, 1] + .2 * x[:, 2]
        points, samples, stats = m.model_bank({"slope": (x, y, clusters, np.array([[0, 1, 0]]))},
            tmp_path / str(sign), str(sign), "known", 2000, 999, {})
        r = m.component(points, samples, "slope", clusters=stats["slope"][3])
        assert abs(r["estimate"] - .35 * sign) < 1e-12
        assert r["outcome"] == ("supports" if sign == 1 else "against")
        values = [v["slope"][0] for v in samples]
        assert r["bootstrap_se"] == float(np.std(values, ddof=1))
        assert r["sees"] == 2.8 * r["bootstrap_se"]
        assert r["supports_at"] == .1 + r["sees"]


def test_profile_partition_and_joint_not_separate_models():
    all_items = [k for profile in m.PROFILES.values() for k in profile]
    for name, profile in m.UNIQUE.items():
        assert all(all_items.count(k) == 1 and m.PROFILES[name][k] == sign for k, sign in profile.items())
    assert not set(m.STYLE) & set(all_items)
    assert len(m.STYLE) == 6
    assert set(m.NAMED + m.OTHER_STANCE + m.EVENT + m.UNCLASSED) == set(m.old.APPRAISALS)


def test_reader_panels_exclude_self_and_holdout_is_exact(tmp_path):
    sources, _ = f.source(tmp_path)
    g, v = pd.read_parquet(sources["generation"]), pd.read_parquet(sources["validation"])
    frame, x, y, excess = m.in7_arrays(g, v)
    assert len(frame) == 192 and set(frame.emotion) == {"joy", "boredom", "surprise"}
    # Exact hand calculation: target 3, readers 1..5 -> 1.2 - 2.0 = -0.8.
    text = frame.text.iloc[0]
    g.loc[g.text_id.eq(text), m.old.APPRAISALS] = 3.
    for number, ix in enumerate(v.index[v.text_id.eq(text)], 1):
        v.loc[ix, m.old.APPRAISALS] = float(number)
    frame, _, _, excess = m.in7_arrays(g, v)
    assert np.allclose(excess[frame.text.eq(text).to_numpy()], -.8, atol=1e-14)
    with pytest.raises(ValueError, match="five-reader"):
        m.panels(g, v.iloc[1:])


def test_in6_uses_writer_clusters_and_standardized_known_slope(tmp_path):
    sources, _ = f.source(tmp_path)
    g, v = pd.read_parquet(sources["generation"]), pd.read_parquet(sources["validation"])
    models, _, _ = m.in6_designs(g, v)
    x, _, clusters, c = models["primary"]
    assert len(np.unique(clusters)) == 32 and all("writer" in k for k in clusters)
    text_order = [text for label in m.MAPPED for text in sorted(v.loc[v.original_emotion.eq(label), "text_id"].unique())]
    for text, predictor in zip(text_order, x[:, 4]):
        g.loc[g.text_id.eq(text), "intensity"] = 3 + .3 * predictor
    models, _, _ = m.in6_designs(g, v)
    x, y, _, c = models["primary"]
    assert abs(float((c @ np.linalg.lstsq(x, y, rcond=None)[0])[0]) - 1) < 1e-12


def test_transmission_uses_all_eight_stance_items_and_fisher_z():
    rng = np.random.default_rng(145)
    x = rng.normal(size=(300, 21))
    y = .25 * x + rng.normal(size=x.shape)
    for name in m.NAMED + m.OTHER_STANCE:
        col = m.old.APPRAISALS.index(name)
        y[:, col] = x[:, col] + .2 * rng.normal(size=len(x))
    excess = np.zeros_like(x)
    excess[:, [m.old.APPRAISALS.index(k) for k in m.NAMED]] = .4
    a = m.in7_statistics(x, y, excess, np.array(["positive"] * len(x)))
    assert abs(a["named_minus_event"] - .4) < 1e-14
    direct = {name: np.arctanh(np.corrcoef(x[:, i], y[:, i])[0, 1]) for i, name in enumerate(m.old.APPRAISALS)}
    expected = np.mean([direct[k] for k in m.EVENT]) - np.mean([direct[k] for k in m.NAMED + m.OTHER_STANCE])
    assert abs(a["transmission_event_minus_stance_z"] - expected) < 1e-12 and expected < 0


def test_changed_source_changed_checkpoint_and_human_draw_refusal(tmp_path):
    sources, pins = f.source(tmp_path / "data")
    settings = f.configuration("IN6", pins, draws=40)
    m.execute(tmp_path / "run", sources, {**settings, "max_new_blocks": 1})
    block = next((tmp_path / "run" / "checkpoints").rglob("00000-00032.json"))
    value = json.loads(block.read_text("utf8")); value["values"][0]["primary"][0] += .1
    block.write_bytes(m.canonical(value))
    with pytest.raises(ValueError, match="provenance"):
        m.execute(tmp_path / "run", sources, settings)
    with pytest.raises(ValueError, match="cannot relax"):
        m.load_inputs(sources, {**settings, "constructed_fixture": False})
    with pytest.raises(ValueError, match="pin mismatch"):
        m.load_inputs(sources, {**settings, "fixture_source_pins": {**pins, "generation": "0" * 64}})


def test_below_floor_and_no_fabricated_correlations():
    a = m.estimate(.5, [.49, .5, .51] * 700, clusters=1)
    assert "outcome" not in a and a["interpretation"] == "below floor, descriptive"
    b = m.estimate(None, [None] * 2000)
    assert b["status"] == "design cannot test"
    assert m.correlation_z(np.ones((30, 2)), np.ones((30, 2))) == [None, None]
