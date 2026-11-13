"""Constructed LA3/LA4 source, estimator, actual-handler and replay controls."""
from pathlib import Path
import json
import math
import numpy as np
from . import week5_la_back_half as m
from . import week5_la_back_half_source as s
from .timing_p6 import gzip_equal


def meta(meetings=32):
    out = {}
    for k in range(meetings):
        corpus = "AMI" if k % 2 == 0 else "ICSI"
        name = f"constructed-meeting-{k:03d}"
        speakers = {f"constructed-speaker-{k:03d}-{j}": {"person": f"constructed-person-{j}", "role": ("manager", "designer")[j % 2],
                    "native_language": ("language-a", "language-b")[j // 2], "english_variety": ("variety-a", "variety-b")[j // 2],
                    "region": ("region-a", "region-b")[j % 2]} for j in range(4)}
        out[name] = {"corpus": corpus, "group": name, "series_rank": 0, "order_qualified": True,
                     "start_utc_seconds": k * 86400., "speakers": speakers, "duration": 2000.}
    return out


def pause_source(directory):
    metadata = meta(32)
    acts, laughs, lemmas = [], [], []
    rng = np.random.default_rng(533)
    for meeting, data in metadata.items():
        clock = 10.
        for occurrence in range(6):
            for j, speaker in enumerate(data["speakers"]):
                for case in (True, False):
                    fresh = occurrence < 2
                    loggap = .8 + .35 * fresh + rng.uniform(-.05, .05)
                    clock += math.expm1(loggap)
                    token = chr(97 + j) + chr(97 + occurrence % 2) + ("case" if case else "control")
                    words = ["topic" + token, "detail" + token]
                    key = f"constructed-act-{len(acts):06d}"
                    duration = float(rng.uniform(10., 30.))
                    act = {"id": key, "meeting": meeting, "speaker": speaker, "corpus": data["corpus"],
                           "start": clock, "end": clock + duration, "act_type": "statement" if occurrence % 2 else "suggestion",
                           "words": [{"text": word, "start": clock + i * duration / 2, "end": clock + (i + 1) * duration / 2,
                                      "kind": "word"} for i, word in enumerate(words)]}
                    acts.append(act)
                    lemmas.append({"id": key, "content_lemmas": words})
                    if case:
                        other = list(data["speakers"])[(j + 1) % 4]
                        laughs.append({"meeting": meeting, "speaker": other, "start": clock + duration + .5, "end": clock + duration + .7, "label": "vocal"})
                    clock += duration
    return save(directory, acts, laughs, metadata, lemmas)


def join_source(directory):
    metadata = meta(40)
    acts, laughs = [], []
    rng = np.random.default_rng(544)
    for meeting, data in metadata.items():
        speakers = list(data["speakers"])
        for event in range(24):
            start = 15. + event * 30
            starter = event % 4
            line = (event // 4 + starter) % 4
            word = {"text": "constructed", "start": start - 4, "end": start - 2, "kind": "word"}
            acts.append({"id": f"constructed-line-{meeting}-{event}", "meeting": meeting, "speaker": speakers[line],
                         "corpus": data["corpus"], "start": start - 4, "end": start - 2, "act_type": "statement", "words": [word]})
            laughs.append({"meeting": meeting, "speaker": speakers[starter], "start": start, "end": start + .2, "label": "vocal"})
            for person in range(4):
                if person != starter and rng.random() < (.8 if person // 2 == starter // 2 else .15):
                    laughs.append({"meeting": meeting, "speaker": speakers[person], "start": start + .5, "end": start + .7, "label": "vocal"})
    return save(directory, acts, laughs, metadata, [])


def save(directory, acts, laughs, metadata, lemmas):
    directory.mkdir(parents=True, exist_ok=True)
    values = {"acts": acts, "laughs": laughs, "metadata": metadata, "lemmas": lemmas,
              "speech": m.act_speech(acts)}
    inputs = {}
    for key, value in values.items():
        path = directory / (key + ".json.gz")
        gzip_equal(path, value)
        inputs[key] = str(path)
    pins = {k: s.digest(v) for k, v in inputs.items()}
    return inputs, pins


def execute(output, inputs, config):
    output = Path(output)
    pa, pp = pause_source(output / "pause-source")
    ja, jp = join_source(output / "join-source")
    results = {}
    for phase, data, pins in (("LA3", pa, pp), ("LA4", ja, jp)):
        settings = {"phase": phase, "pins": pins, "constructed_fixture": True, "draws": 32}
        result = m.execute(output / phase, data, settings)
        assert result["complete_card"]
        assert m.verify(output / phase, data, settings)["verified"]
        if phase == "LA3":
            assert not result["fallback"] and result["primary"]["estimate"] > .2
        else:
            assert result["primary"]["coefficients"]["shared_native_language"]["estimate"] > .3
            assert result["starter_spoke_main_effect"]["status"] == "non-identifiable"
        results[phase] = {"verified": True, "result_sha256": s.digest(output / phase / "RESULT.json")}
    settings = {"phase": "LA4", "pins": jp, "constructed_fixture": True, "draws": 32}
    # Three-lemma texture cannot turn itself back into a two-lemma fallback.
    texture = m.execute(output / "LA3-three-lemma", pa,
                        {"phase": "LA3", "pins": pp, "constructed_fixture": True, "draws": 1, "texture": True, "shared": 3})
    assert texture["complete_card"] and texture["case"]["repeat_acts"] == 0 and not texture["fallback"]
    assert m.execute(output / "continuation", ja, {**settings, "max_new_blocks": 1})["status"] == "yielded"
    before = {p.name: s.digest(p) for p in (output / "continuation" / "draws").glob("*.json")}
    assert m.execute(output / "continuation", ja, settings)["complete_card"]
    assert all(s.digest(output / "continuation" / "draws" / n) == v for n, v in before.items())
    assert m.verify(output / "continuation", ja, settings)["verified"]
    result = {"passed": True, "handlers": results, "pause_resume_byte_preservation": True,
              "complete_independent_replay": True, "texture_definition_not_replaced_by_fallback": True,
              "no_real_lemmatizer_loaded": True}
    s.write(output / "FIXTURE.json", result)
    return result


def verify(output, inputs, config):
    actual = execute(Path(output) / "fixture-independent-replay", inputs, config)
    if actual != json.loads((Path(output) / "FIXTURE.json").read_text("utf8")):
        raise ValueError("LA constructed fixture replay differs")
    return {"verified": True, "all_handlers_replayed": True}
