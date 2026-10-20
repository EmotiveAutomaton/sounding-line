import numpy as np
import pytest
import sys
from types import SimpleNamespace

from runners.drive.cards import timing_d36 as module
from runners.drive.cards.timing_d36 import analyze, correlation, mismatches, native_mean, reduce_reread, split_jokes, verify
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzwrite
from runners.drive.cards.timing_stats import bind


def fixture():
    rng = np.random.default_rng(17)
    rates = rng.normal(size=40)
    features = [dict(joke_id=str(i), rate=rate, punchline_surprisal=float(rng.uniform(2, 7)), punchline_tokens=int(rng.integers(5, 25)))
                for i, rate in enumerate(rates)]
    ratings = 2 * rates[None, :] + rng.normal(size=(120, 1)) + rng.normal(size=(120, 40))
    ratings[rng.uniform(size=ratings.shape) < .1] = np.nan
    return features, ratings


def test_sentence_boundary_and_fixed_mismatch_control():
    jokes, excluded = split_jokes([dict(joke_id="a", text="Dr. Smith arrives. The door laughs."),
                                  dict(joke_id="b", text="A car arrives. It parks upside down."),
                                  dict(joke_id="c", text="One sentence.")])
    assert jokes[0]["setup"] == "Dr. Smith arrives. "
    assert jokes[0]["punchline"] == "The door laughs."
    assert excluded == [dict(joke_id="c", reason="one sentence")]
    assert mismatches(jokes, 20261017) == {0: 1, 1: 0}
    with pytest.raises(ValueError, match="identical"):
        mismatches([jokes[0], dict(jokes[0], joke_id="d")], 20261017)


def test_resolution_gain_is_difference_of_gains_and_native_losses_are_verified():
    score = lambda value: dict(surprisal_nats=value, native_token_nll=[value / 2, value / 2], native_token_ids=[1, 2])
    record = dict(joke_id="a", mismatch_joke_id="b", setup_alone_mean=8., punchline_tokens=2,
                  punchline_surprisal=4., true=[score(2.), score(4.)], mismatch=[score(5.), score(7.)])
    result = reduce_reread(record)
    assert result["resolution_gain"] == (8 - 3) - (8 - 6) == 3
    assert result["rate"] == 1.5
    record["true"][0]["native_token_nll"][0] = 99
    with pytest.raises(ValueError, match="sum"):
        native_mean(record["true"])


def test_rater_primary_and_separately_labeled_joke_controls_recover_planted_signal():
    features, ratings = fixture()
    result = analyze(features, ratings, dict(seed=20261017, bootstrap_draws=200, extension=False))
    assert result["state"] == "positive" and result["effect"] > .95
    assert result["bootstrap_se"] > 0 and result["wald_p_two_sided"] < .01
    assert "conditional" in result["interval_population"]
    assert result["joke_bootstrap_sensitivity"]["state"] == "descriptive"
    assert abs(result["joke_permutation_control"]["mean_correlation"]) < .05
    assert result["joke_permutation_control"]["two_sided_p"] < .01
    # Noise cannot exclude zero; the packet calls a positive noisy point marginal.
    rates = np.array([r["rate"] for r in features])
    rng = np.random.default_rng(39)
    null_ratings = rng.normal(size=ratings.shape)
    null_result = analyze(features, null_ratings, dict(seed=20261017, bootstrap_draws=200, extension=False))
    assert null_result["state"] in {"null", "marginal"} and null_result["ci_low"] < 0 < null_result["ci_high"]
    assert correlation(rates, rates, rates[:, None]) is None


def test_partial_correlation_controls_surprise_and_length_and_invalid_support_is_explicit():
    features, ratings = fixture()
    covariates = np.array([[r["punchline_surprisal"], r["punchline_tokens"]] for r in features])
    confounded = ratings + 4 * covariates[:, 0] + 2 * covariates[:, 1]
    result = analyze(features, confounded, dict(seed=20261017, bootstrap_draws=200, extension=True))
    assert result["effect"] > .95 and result["state"] == "positive"
    assert analyze(features, ratings[:, :-1], dict(extension=False))["state"] == "invalid"
    ratings[:, 0] = np.nan
    assert analyze(features, ratings, dict(extension=False))["state"] == "invalid"


def test_fresh_verifier_reduces_saved_native_arrays_and_refuses_mutation(tmp_path):
    features, ratings = fixture()
    records = []
    reduced = []
    for feature in features:
        score = lambda value: dict(surprisal_nats=value, native_token_nll=[value], native_token_ids=[1])
        record = dict(joke_id=feature["joke_id"], mismatch_joke_id="donor", setup_alone_mean=8.,
                      punchline_tokens=1, punchline_surprisal=feature["punchline_surprisal"],
                      true=[score(5.)], mismatch=[score(5. + feature["rate"])])
        dest = tmp_path / "rereads" / (feature["joke_id"] + ".json.gz")
        gzwrite(dest, record)
        reduced.append(reduce_reread(record))
        records.append(dict(file=dest.relative_to(tmp_path).as_posix(), sha256=filehash(dest)))
    config = dict(seed=20261017, bootstrap_draws=30, extension=False)
    result = analyze(reduced, ratings, config)
    result.update(excluded_one_sentence_jokes=0, excluded_unrated_eligible_jokes=0, total_source_unrated_jokes=0,
                  rating_eligibility=module.RATING_POPULATION)
    write(tmp_path / "D36_FEATURES.json", reduced)
    write(tmp_path / "D36_REREADS.json", records)
    write(tmp_path / "D36_EXCLUSIONS.json", [])
    write(tmp_path / "D36_RATING_SUPPORT.json", [dict(joke_id=f["joke_id"], observed_ratings=int(np.isfinite(ratings[:, i]).sum())) for i, f in enumerate(features)])
    write(tmp_path / "D36_PRIMARY.json", result)
    np.savez_compressed(tmp_path / "D36_RATINGS.npz", ratings=ratings)
    bind(tmp_path, {}, config, ["D36_FEATURES.json", "D36_REREADS.json", "D36_EXCLUSIONS.json", "D36_PRIMARY.json", "D36_RATINGS.npz", "D36_RATING_SUPPORT.json"])
    assert verify(tmp_path, {}, config)["verified"]
    (tmp_path / records[0]["file"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="native reread changed"):
        verify(tmp_path, {}, config)


def test_bootstrap_checkpoint_restores_exact_rng_and_draws():
    features, ratings = fixture()
    config = dict(seed=20261017, bootstrap_draws=200, extension=False)
    saved = []
    def checkpoint(record):
        saved.append(record)
        raise module.CooperativeYield()
    with pytest.raises(module.CooperativeYield):
        analyze(features, ratings, config, on_checkpoint=checkpoint)
    assert len(saved[0]["rater_samples"]) == 20
    assert analyze(features, ratings, config, resume=saved[0]) == analyze(features, ratings, config)


def test_whole_handler_fake_reader_yields_resumes_and_verifies_without_corpus(tmp_path, monkeypatch):
    # This is synthetic storage/integration evidence, never model/scientific evidence.
    texts = [dict(joke_id=str(i), text=f"Person {i} enters. Answer number {i + 10}.") for i in range(8)]
    texts += [dict(joke_id=str(i), text=f"Single sentence {i}.") for i in range(8, 150)]
    texts_path = tmp_path / "texts.json"
    write(texts_path, texts)
    frozen = tmp_path / "fake-model.txt"
    frozen.write_text("synthetic source", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    write(manifest, dict(model_path="synthetic", tokenizer_path="synthetic", files={str(frozen): filehash(frozen)}))
    p7 = tmp_path / "p7"
    index = []
    for joke in texts:
        words = [dict(start=m.start(), end=m.end(), is_word=bool(module.WORD.fullmatch(m.group())), surprisal_nats=3.)
                 for m in module.TOKEN.finditer(joke["text"])]
        dest = p7 / "jokes" / (joke["joke_id"] + ".json.gz")
        gzwrite(dest, dict(words=words))
        index.append(dict(joke_id=joke["joke_id"], domain="jester", file=dest.relative_to(p7).as_posix(), sha256=filehash(dest)))
    write(p7 / "P7_INDEX.json", index)
    write(p7 / "P7_PRIMARY.json", dict(pilot_only=False))
    write(p7 / "TIMING_BINDINGS.json", dict(inputs=dict(jester_texts=filehash(texts_path), model_manifest=filehash(manifest))))
    rating_path = tmp_path / "ratings.npz"
    source_ratings = np.random.default_rng(5).uniform(-8, 8, size=(24, 150))
    source_ratings[:, :2] = np.nan
    source_ratings[:, 8:16] = np.nan
    np.savez_compressed(rating_path, ratings=source_ratings, joke_ids=np.array([str(i) for i in range(150)]))
    class FakeModel:
        config = SimpleNamespace(model_type="gpt2", n_layer=24, n_embd=1024)
        def cpu(self): return self
        def eval(self): return self
    class FakeScorer:
        calls = 0
        def __init__(self, *args): pass
        def score(self, prefix, target):
            FakeScorer.calls += 1
            value = 3 + sum(map(ord, prefix)) % 97 / 100
            return dict(surprisal_nats=value, native_token_nll=[value], native_token_ids=[1], prefix_tokens_dropped=0)
    tokenizer = lambda text, **kwargs: dict(input_ids=list(range(len(text.split()))))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(set_num_threads=lambda _: None, float32="synthetic"))
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **kw: tokenizer),
        AutoModelForCausalLM=SimpleNamespace(from_pretrained=lambda *a, **kw: FakeModel())))
    monkeypatch.setattr(module, "CachedScorer", FakeScorer)
    inputs = dict(p7_index=str(p7 / "P7_INDEX.json"), jester_texts=str(texts_path), jester_ratings=str(rating_path), model_manifest=str(manifest))
    config = dict(extension=False, seed=20261017, bootstrap_draws=2000)
    output = tmp_path / "run"
    write(output / "YIELD_REQUEST.json", {})
    assert module.execute(output, inputs, config)["status"] == "yielded"
    first_calls = FakeScorer.calls
    (output / "YIELD_REQUEST.json").unlink()
    result = module.execute(output, inputs, config)
    assert result["excluded_one_sentence_jokes"] == 142
    assert result["excluded_unrated_eligible_jokes"] == 2 and result["total_source_unrated_jokes"] == 10
    assert FakeScorer.calls == first_calls * 8
    assert module.verify(output, inputs, config)["verified"]
    assert module.execute(output, inputs, config) == result
    assert FakeScorer.calls == first_calls * 8
