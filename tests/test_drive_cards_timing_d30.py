from runners.drive.cards.timing_d30 import classify_markers, occurrences, analyze, shuffle_marker_labels
import math
import numpy as np


def test_covariation_demands_three_prompts_and_distinguishes_local():
    rows = []
    for writer in ["target", "d1", "d2", "d3"]:
        for prompt in ["a", "b", "c"]:
            counts = {"word:habit": 100 if writer == "target" else 2,
                      "word:local": 100 if writer == "target" and prompt == "a" else 0 if writer == "target" else 10,
                      "word:other": 900}
            for marker, count in counts.items():
                rows.extend(dict(writer=writer, prompt=prompt, marker=marker) for _ in range(count))
    labels, _ = classify_markers(rows)
    assert labels[("target", "word:habit")]["label"] == "pervasive"
    assert labels[("target", "word:local")]["label"] == "local"
    limited = [r for r in rows if r["prompt"] != "c"]
    assert not classify_markers(limited)[0]


def test_bigrams_use_recorded_adjacency_and_first_character_pause():
    words = [dict(index=0, token="blue", is_word=True, previous_typed_token_index=None, length=4, revised=False, pause_seconds=.5),
             dict(index=1, token="sky", is_word=True, previous_typed_token_index=0, length=3, revised=True, pause_seconds=.1),
             dict(index=2, token="blue", is_word=True, previous_typed_token_index=None, length=4, revised=False, pause_seconds=.2)]
    rows = occurrences([dict(session="s", writer="w", prompt="p", words=words)])
    bigrams = [r for r in rows if r["marker"].startswith("bigram:")]
    assert len(bigrams) == 1
    assert bigrams[0]["marker"] == "bigram:blue sky"
    assert bigrams[0]["pause_seconds"] == .5
    assert bigrams[0]["revised"]


def test_zero_prompt_prior_retains_local_zero_rate_coverage():
    rows = []
    for writer in ("target", "d1", "d2", "d3"):
        for prompt in ("a", "b", "c"):
            rows.extend(dict(writer=writer, prompt=prompt, marker="word:other") for _ in range(900))
            if writer == "target" and prompt == "a":
                rows.extend(dict(writer=writer, prompt=prompt, marker="word:rare") for _ in range(100))
    labels, _ = classify_markers(rows)
    assert labels["target", "word:rare"]["label"] == "local"


def test_label_shuffle_preserves_marker_membership_and_marker_class_counts():
    rows = [dict(writer="w", marker=m, label=label) for m, label, n in
            (("a", "local", 20), ("b", "pervasive", 2), ("c", "pervasive", 10)) for _ in range(n)]
    shuffled = shuffle_marker_labels(rows, np.random.default_rng(1))
    per_marker = {m: {label for r, label in zip(rows, shuffled) if r["marker"] == m} for m in ("a", "b", "c")}
    assert all(len(labels) == 1 for labels in per_marker.values())
    assert sorted(next(iter(labels)) for labels in per_marker.values()) == ["local", "pervasive", "pervasive"]


def test_bigram_uses_both_scores_and_full_character_span():
    words = [dict(index=0, token="blue", is_word=True, previous_typed_token_index=None, length=4, revised=False,
                  pause_seconds=.5, seconds=1., duration_seconds=.3, population_surprisal=2.),
             dict(index=1, token="sky", is_word=True, previous_typed_token_index=0, length=3, revised=False,
                  pause_seconds=.1, seconds=1.6, duration_seconds=.2, population_surprisal=3.)]
    pair = next(r for r in occurrences([dict(session="s", writer="w", prompt="p", words=words)]) if r["marker"].startswith("bigram:"))
    assert pair["population_surprisal"] == 5.
    assert math.isclose(pair["duration_seconds"], .8)


def known_rows():
    rng = np.random.default_rng(17)
    rows = []
    for writer in range(4):
        for prompt in range(3):
            counts = {"word:other": 600}
            for owner in range(4):
                counts[f"word:habit{owner}"] = 80 if owner == writer else 2
                counts[f"word:local{owner}"] = (80 if prompt == 0 else 0) if owner == writer else 10
            for marker, count in counts.items():
                own_local = marker == f"word:local{writer}"
                for i in range(count):
                    pause = math.exp((1 if own_local else 0) + rng.normal(0, .03))
                    rows.append(dict(writer=str(writer), prompt=str(prompt), session=f"{writer}-{prompt}", marker=marker,
                                     index=i, ordinal=i, pause_seconds=pause, first_delta_characters=1,
                                     population_surprisal=float(rng.uniform(1, 4)), population_log_frequency=float(rng.normal()),
                                     length=int(rng.integers(2, 8)), sentence_start=i % 5 == 0, after_punctuation=i % 7 == 0,
                                     within_intervals=[.05, .05], duration_seconds=.1,
                                     revised=bool(own_local and i % 3 != 0)))
    return rows


def test_signed_primary_and_revision_fallback_recover_known_opposite_directions():
    rows = known_rows()
    config = dict(card="D30", bootstrap_draws=30, seed=20261017, extension=False)
    pause, _ = analyze(rows, config, "per_character")
    assert pause["effect"] > .9
    assert pause["expected_direction"] == 1
    assert pause["state"] == "positive"
    revision, _ = analyze(rows, config, "invalid")
    assert revision["effect"] < -.5
    assert revision["expected_direction"] == -1
    assert revision["state"] == "positive"
    assert revision["effective_card"] == "D30.v1"


def test_actual_handler_yields_resumes_and_verifies_in_fresh_process(tmp_path):
    import json
    import subprocess
    import sys
    from collections import defaultdict
    from runners.drive.cards.timing_d30 import execute, verify
    from runners.drive.cards.timing_p6 import gzwrite
    from runners.drive.cards.timing_census import write, filehash
    sessions = defaultdict(list)
    for row in known_rows():
        sessions[row["session"]].append(dict(row, token=row["marker"][5:], is_word=True, previous_typed_token_index=None))
    p6, tc = tmp_path / "p6", tmp_path / "tc"
    index = []
    for session, words in sorted(sessions.items()):
        path = p6 / "output" / (session + ".json.gz")
        gzwrite(path, dict(session=session, writer=words[0]["writer"], prompt=words[0]["prompt"], words=words))
        index.append(dict(file=path.name, sha256=filehash(path)))
    write(p6 / "output/P6_INDEX.json", index)
    write(tc / "output/TC_PRIMARY.json", dict(timing_mode="per_character"))
    inputs = {}
    for key, directory, name in (("p6", p6, "P6_INDEX.json"), ("tc", tc, "TC_PRIMARY.json")):
        write(directory / "COMPLETE.json", dict(status="COMPLETE", fresh_process_verified=True,
              outputs={"output/" + name: filehash(directory / "output" / name)}))
        inputs[key + "_completion"] = str(directory / "COMPLETE.json")
    inputs.update(p6_index=str(p6 / "output/P6_INDEX.json"), tc_primary=str(tc / "output/TC_PRIMARY.json"))
    config = dict(card="D30", bootstrap_draws=2000, seed=20261017, extension=False)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", dict(reason="fixture saved-boundary test"))
    assert execute(output, inputs, config)["status"] == "yielded"
    assert not (output / "D30_PRIMARY.json").exists()
    (output / "YIELD_REQUEST.json").unlink()
    result = execute(output, inputs, config)
    assert result["state"] == "positive" and result["effect"] > .9
    write(tmp_path / "plan.json", dict(inputs=inputs, config=config, output=str(output)))
    script = "import json,sys;from pathlib import Path;from runners.drive.cards.timing_d30 import verify;p=json.load(open(sys.argv[1]));r=verify(Path(p['output']),p['inputs'],p['config']);print(json.dumps({'verified':r['verified']}))"
    checked = subprocess.run([sys.executable, "-B", "-c", script, str(tmp_path / "plan.json")], capture_output=True, text=True, check=True)
    assert json.loads(checked.stdout)["verified"]
    snapshots = {p.name: p.read_bytes() for p in output.glob("D30_*.json*")}
    assert execute(output, inputs, config) == result
    assert snapshots == {p.name: p.read_bytes() for p in output.glob("D30_*.json*")}
    # Completion alone cannot admit an altered consumer input.
    (tc / "output/TC_PRIMARY.json").write_text('{"timing_mode":"invalid"}')
    import pytest
    with pytest.raises(ValueError, match="completion binding changed"):
        verify(output, inputs, config)
