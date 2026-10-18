import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import numpy as np
import pytest
from runners.drive.cards import events_d14 as card
from runners.drive.cards import events_d14_features as features
from runners.drive.cards import events_d14_stats as stats


def known_rows(effect=.6, writers=4):
    rows = []
    for w in range(writers):
        for x in (0., 1.):
            probability = .5 + effect * (x - .5)
            for j in range(10):
                rows.append(dict(writer=f"w{w}", session=f"s{w}", key=f"m{w}-{x}-{j}", position=0,
                    topic_drift=x, protected=int(j < round(10 * probability)),
                    disturbance=dict(candidate_characters=10)))
    return rows


@pytest.mark.parametrize("effect", [0., .6, -.6])
def test_known_probability_slopes_and_bootstrap(effect):
    rows = known_rows(effect)
    moments = stats.sufficient(rows, np.zeros((len(rows), 1)))
    point, certificate = stats.fit_draw(moments)
    assert point == pytest.approx(effect, abs=1e-12)
    assert certificate["normal_equation_gap"] < 1e-10
    sample = [stats.fit_draw(moments, np.array([2, 0, 1, 1]))[0]] * 2000
    assert stats.summarize(point, sample)["state"] == ("null" if effect == 0 else "positive" if effect > 0 else "negative")


def test_identification_guard_and_nuisance_adjustment():
    rows = known_rows(.6)
    nuisance = np.array([[r["topic_drift"]] for r in rows])
    with pytest.raises(ValueError, match="unidentified"):
        stats.fit_draw(stats.sufficient(rows, nuisance))
    # Add a separate exact binary covariate whose known coefficient is .6.
    expanded = []
    controls = []
    for r in rows:
        for x in (0., 1.):
            expanded.append(dict(r, key=r["key"] + str(x), topic_drift=x))
            controls.append([r["topic_drift"]])
    point, _ = stats.fit_draw(stats.sufficient(expanded, controls))
    assert point == pytest.approx(0., abs=1e-12)


def test_menu_replication_does_not_reweight_dismissal():
    rows = known_rows(.6)
    before = stats.fit_draw(stats.sufficient(rows, np.zeros((len(rows), 1))))[0]
    repeated = [dict(r, position=i) for r in rows for i in range(5 if r["protected"] else 1)]
    after = stats.fit_draw(stats.sufficient(repeated, np.zeros((len(repeated), 1))))[0]
    assert after == pytest.approx(before, abs=1e-12)


def test_pilot_is_exact_ceiling_tenth_and_order_invariant():
    writers = [f"w{i}" for i in range(71)]
    selected = features.pilot_writers(writers, 20261017)
    assert len(selected) == 8
    assert selected == features.pilot_writers(reversed(writers), 20261017)
    assert features.paragraph("old paragraph\n\nLatest paragraph.\n ") == ("Latest paragraph.", 15, 32)


class FakeDoc(list):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.ents = []


class FakeNLP:
    def pipe(self, texts, **kwargs):
        return iter(FakeDoc(text) for text in texts)


class FakeEncoder:
    def __init__(self, *args):
        pass

    def encode(self, texts):
        vectors = np.zeros((len(texts), 384), np.float32)
        vectors[:, 0] = 1
        return vectors, [dict(full_tokens=1, used_tokens=1, truncated=False, first_native_token=0,
                              codepoint_start=0, codepoint_end=len(text)) for text in texts]


def sessions_fixture(writers=20):
    sessions, records, p8 = [], [], []
    vectors = np.zeros((4, 384), np.float32)
    vectors[0, 0] = 1
    vectors[1, 1] = 1
    vectors[2, 0] = -1
    vectors[3, 2] = 1
    for w in range(writers):
        menu_rows = []
        for i, handling in enumerate(("accept", "edit", "dismiss", "ignore")):
            key = f"w{w}-m{i}"
            row = dict(key=key, writer=f"w{w}", session=f"s{w}", prompt="p", document="Old.\nParagraph.",
                menu=["First", "Second", "Third"], inserted="Second" if handling in ("accept", "edit") else "",
                handling=handling, open_at=100 * w + 10 * i, resolved_at=100 * w + 10 * i + 1,
                session_time=100 * w, session_end=100 * w + 99, decision_index=i)
            menu_rows.append(row)
            records.append(dict(key=key, writer=f"w{w}", session=f"s{w}", context=0, options=[1, 2, 3],
                                cosine=[0., -1., 0.], scalars=[[5, 1, 1., 0], [6, 1, 1., 1], [5, 1, 1., 2]]))
            p8.extend(dict(key=key, position=j, log_positive_score=float(j - 4)) for j in range(3))
        sessions.append(dict(writer=f"w{w}", session=f"s{w}", timestamp=100 * w, end_at=100 * w + 99, rows=menu_rows))
    return sessions, records, vectors, p8


def test_extraction_selected_support_all_offers_and_source_join():
    sessions, records, vectors, _ = sessions_fixture(1)
    result = features.extract_writer(sessions, records, vectors, FakeEncoder(), FakeNLP())
    assert len(result["rows"]) == 5  # one accept, one edit, three dismissed
    assert len(result["offered_disturbances"]) == 12
    assert result["rows"][0]["protected"] == 0
    assert result["rows"][0]["topic_drift"] == 2
    assert result["audit"]["ignored_menus"] == 1
    sessions[0]["rows"][0]["menu"][0] = "Second"
    result = features.extract_writer(sessions, records, vectors, FakeEncoder(), FakeNLP())
    assert result["audit"]["ambiguous_selected_menus"] == 1
    assert len(result["rows"]) == 4


def test_nuisance_exact_d1_features_include_p8():
    sessions, records, vectors, p8 = sessions_fixture(2)
    rows = features.extract_writer(sessions, records, vectors, FakeEncoder(), FakeNLP())["rows"]
    matrix, projection = features.nuisance_matrix(rows, sessions, records, vectors, p8, 20261017)
    original_rows, base, scalar, embeddings = features.prefix_features(sessions, records, vectors, p8)
    expected = np.c_[base, scalar]
    lookup = {r["key"]: i for i, r in enumerate(original_rows)}
    assert np.array_equal(matrix[:, :expected.shape[1]], expected[[lookup[r["key"]] for r in rows]])
    assert scalar[0, -4:].tolist() == [0., -3., pytest.approx(np.std([-4, -3, -2])), -2.]
    assert projection["fit_menu_keys"] == [r["key"] for r in original_rows]


def test_paragraph_encoder_tail_view_and_padding():
    import torch
    torch.set_num_threads(2)
    class Tokenizer:
        cls_token_id, sep_token_id, pad_token_id = 1000, 1001, 0
        def __call__(self, text, **kwargs):
            n = int(text)
            return dict(input_ids=list(range(1, n + 1)), offset_mapping=[(i, i + 1) for i in range(n)])
    captured = []
    class Model:
        def __call__(self, input_ids, attention_mask):
            captured.extend(input_ids[i, attention_mask[i].bool()].tolist() for i in range(len(input_ids)))
            return SimpleNamespace(last_hidden_state=torch.ones((*input_ids.shape, 384)))
    encoder = object.__new__(features.ParagraphEncoder)
    encoder.tokenizer, encoder.torch, encoder.model, encoder.batch_size = Tokenizer(), torch, Model(), 16
    vectors, scopes = encoder.encode(["300", "4"])
    assert captured[0] == [1000] + list(range(47, 301)) + [1001]
    assert captured[1] == [1000, 1, 2, 3, 4, 1001]
    assert scopes[0]["full_tokens"] == 300 and scopes[0]["truncated"]
    assert scopes[0]["codepoint_start"] == 46
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf8")


def handler_inputs(tmp_path):
    sessions, records, vectors, p8 = sessions_fixture()
    paths = {key: str(tmp_path / (key + ".json")) for key in card.BASE_INPUTS - {"spacy_model", "content_vectors"}}
    paths["content_vectors"] = str(tmp_path / "content_vectors.npy")
    paths["spacy_model"] = str(tmp_path / "spacy")
    Path(paths["spacy_model"]).mkdir()
    (Path(paths["spacy_model"]) / "config.cfg").write_text("fixture", encoding="utf8")
    for key, value in (("sessions", sessions), ("content_records", records), ("content_model", {}), ("p8_verified", {"verified": True})):
        write(Path(paths[key]), value)
    np.save(paths["content_vectors"], vectors)
    Path(paths["p8_rows"]).write_text("\n".join(json.dumps(r) for r in p8), encoding="utf8")
    write(Path(paths["p8_summary"]), dict(status="complete", table_sha256=card.filehash(paths["p8_rows"])))
    write(Path(paths["content_complete"]), dict(status="COMPLETE", outputs={Path(paths[k]).name: card.filehash(paths[k])
          for k in ("content_records", "content_vectors", "content_model")}))
    return paths


def test_actual_pilot_main_resume_and_fresh_verifier(tmp_path, monkeypatch):
    inputs = handler_inputs(tmp_path)
    config = dict(phase="pilot", threads=2, batch_size=16, bootstrap=2000, seed=20261017, pca_dimensions=16)
    monkeypatch.setattr(card, "input_pins", lambda inp: {str(Path(v)): card.filehash(v) for k, v in inp.items() if k != "spacy_model"})
    monkeypatch.setattr(features, "ParagraphEncoder", FakeEncoder)
    import spacy
    monkeypatch.setattr(spacy, "load", lambda _: FakeNLP())
    # Independently test real feature assembly above; handler fixture uses the
    # known-answer predictor to cover all bootstrap/pilot paths cheaply.
    monkeypatch.setattr(features, "nuisance_matrix", lambda rows, *args: (np.zeros((len(rows), 1)), {}))
    original = features.extract_writer
    calls = []
    output = tmp_path / "pilot"
    def extract(own, *args):
        calls.append(own[0]["writer"])
        result = original(own, *args)
        result["rows"] = [dict(r, writer=own[0]["writer"], session=own[0]["session"]) for r in known_rows(.6, 1)]
        if len(calls) == 1:
            write(output / "YIELD_REQUEST.json", {})
        return result
    monkeypatch.setattr(features, "extract_writer", extract)
    yielded = card.execute(output, inputs, config)
    assert yielded["status"] == "yielded"
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, config)
    assert result["execution_only"] and len(result["selected_writers"]) == 2
    tenth = card.read(output / "FIRST_TENTH.json")
    assert tenth["forecast_cpu_seconds"] == result["forecast_cpu_seconds"] == 1080
    assert tenth["selected_writers"] == 2 and tenth["full_writers"] == 20
    assert tenth["projected_cpu_seconds"] == pytest.approx(tenth["elapsed_seconds"] * 2)
    assert tenth["projected_main_extraction_seconds"] == pytest.approx(tenth["elapsed_seconds"] * 20)
    assert result["projected_cpu_seconds"] == pytest.approx(20 * (result["extraction_seconds"] + result["bootstrap_seconds"] + result["preprocessing_seconds"]))
    assert result["verification_allowance_multiplier"] == 2
    assert len(calls) == 2
    assert result["primary"]["effect"] == pytest.approx(.6)
    verified = card.verify(output, inputs, config)
    verified_path = tmp_path / "PILOT_VERIFIED.json"
    write(verified_path, verified)
    args = tmp_path / "verify-args.json"
    write(args, dict(output=str(output), inputs=inputs, config=config))
    script = "import json,sys; from pathlib import Path; from runners.drive.cards.events_d14 import verify; p=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(p['output']),p['inputs'],p['config'])))"
    check = subprocess.run([sys.executable, "-B", "-c", script, str(args)], env=dict(os.environ, PYTHONHASHSEED="913"),
                           capture_output=True, text=True, check=True)
    assert json.loads(check.stdout)["verified"]
    main_inputs = dict(inputs, pilot_summary=str(output / "SUMMARY.json"), pilot_verified=str(verified_path))
    main = card.execute(tmp_path / "main", main_inputs, dict(config, phase="main"))
    assert not main["execution_only"]
    assert main["forecast_cpu_seconds"] == 10800
    assert len(calls) == 20  # pilot writers' extraction reused exactly once
    assert main["primary"]["effect"] == pytest.approx(.6)
    assert card.verify(tmp_path / "main", main_inputs, dict(config, phase="main"))["verified"]
    with pytest.raises(ValueError, match="completed output"):
        card.execute(tmp_path / "main", main_inputs, dict(config, phase="main"))
    Path(inputs["p8_rows"]).write_text("changed", encoding="utf8")
    with pytest.raises(ValueError, match="input changed"):
        card.verify(tmp_path / "main", main_inputs, dict(config, phase="main"))


def test_checkpoint_mutation_refused(tmp_path):
    path = tmp_path / "saved.json"
    card.save(path, dict(value=1))
    path.write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="hash differs"):
        card.load(path)
