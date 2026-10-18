import gzip
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import timing_d30_crossed as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_stats import sufficient, fit
from tests.test_drive_cards_timing_d30_specification import fixture_sources


def constructed(signal=1):
    x, y, writers, markers = [], [], [], []
    for w in range(8):
        for m in range(10):
            for r in range(6):
                nuisance = math.sin(m + r//2)
                x.append([r % 2, nuisance])
                y.append(signal * (r % 2) + .2*w - .1*m + .3*nuisance + .01*((w*m+r//2)%7))
                writers.append(str(w)); markers.append(str(m))
    return dict(x=x, y=y, writers=writers, markers=markers)


def test_sparse_reml_equals_direct_dense_covariance():
    matrix = constructed()
    ix = [i for i, (w, m) in enumerate(zip(matrix["writers"], matrix["markers"])) if int(w) < 4 and int(m) < 4]
    matrix = {k: [v[i] for i in ix] for k, v in matrix.items()}
    prepared = card.prepare(**matrix)
    ratios = [.2, .5]
    actual = card.evaluate(prepared, ratios)
    x = np.asarray(matrix["x"])
    a = np.column_stack([x/x.std(0), np.ones(len(x))])
    zw = np.array([[w == str(j) for j in range(4)] for w in matrix["writers"]], float)
    zm = np.array([[m == str(j) for j in range(4)] for m in matrix["markers"]], float)
    covariance = np.eye(len(x)) + ratios[0]*(zw @ zw.T) + ratios[1]*(zm @ zm.T)
    inverse_x = np.linalg.solve(covariance, a)
    inverse_y = np.linalg.solve(covariance, matrix["y"])
    information = a.T @ inverse_x
    beta = np.linalg.solve(information, a.T @ inverse_y)
    y = np.array(matrix["y"])
    rss = y @ inverse_y - (a.T @ inverse_y) @ beta
    df = len(x)-a.shape[1]
    expected = np.linalg.slogdet(covariance)[1] + np.linalg.slogdet(information)[1] + df*np.log(rss/df)
    assert actual["effect"] == pytest.approx(beta[0]/x[:, 0].std(), abs=1e-10)
    assert actual["objective"] == pytest.approx(expected, abs=1e-8)


@pytest.mark.parametrize("signal", [1, 0, -1])
def test_known_sign_and_copy_identity(signal):
    matrix = constructed(signal)
    answer = card.fit(**matrix)
    assert answer["converged"]
    assert answer["effect"] == pytest.approx(signal, abs=1e-7)
    duplicated = card.resample(matrix, [0, 0, 1, 2, 3, 4, 5, 6])
    assert len(set(duplicated["writers"])) == 8
    assert len(set(duplicated["markers"])) == 10
    assert duplicated["markers"][:60] == duplicated["markers"][60:120]


def serialized_sources(path, signal):
    inputs = fixture_sources(path)
    for name, extension in (("primary", False), ("extension", True)):
        root = Path(inputs[name+"_completion"]).parent
        saved = gzread(root / "output/D30_INTERMEDIATES.json.gz")
        for row in saved["rows"]:
            log_pause = math.log(row["pause_seconds"])
            if signal == 0:
                log_pause -= int(row["marker"] == "word:local" + row["writer"])
            elif signal == -1:
                log_pause = -log_pause
            row["pause_seconds"] = math.exp(log_pause)
        matrix, markers = card.specification.designs(saved["rows"], "per_character")
        with gzip.open(root / "output/D30_INTERMEDIATES.json.gz", "wt", encoding="utf-8") as stream:
            json.dump(saved, stream)
        baseline = dict(effect=fit(sufficient(matrix["designs"][int(extension)], matrix["y"], matrix["writers"], True))[0],
                        observations=len(matrix["y"]), writers=len(set(matrix["writers"])))
        (root / "output/D30_PRIMARY.json").write_text(json.dumps(baseline), encoding="utf-8")
        complete = read(root / "COMPLETE.json")
        complete["outputs"] = {p.relative_to(root).as_posix():filehash(p) for p in root.rglob("*") if p.is_file() and p.name != "COMPLETE.json"}
        (root / "COMPLETE.json").write_text(json.dumps(complete), encoding="utf-8")
    return inputs


@pytest.mark.parametrize("signal", [1, 0, -1])
def test_actual_serialized_pilot_and_fresh_process(tmp_path, signal):
    inputs = serialized_sources(tmp_path / "sources", signal)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {})
    assert card.execute(output, inputs, card.CONFIG)["status"] == "yielded"
    checkpoint = output / "fits/fit-00.json"
    retained = checkpoint.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, card.CONFIG)
    assert checkpoint.read_bytes() == retained
    assert result["instrument_only"] and not result["scientific_main_admitted"]
    assert result["fits"][0]["effect"] == pytest.approx(signal, abs=.02)
    manifest = tmp_path / "verify.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=card.CONFIG))
    code = "import json,sys; from pathlib import Path; from runners.drive.cards.timing_d30_crossed import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result


def test_invalid_design_and_config(tmp_path):
    matrix = constructed()
    matrix["x"] = [[1, 0] for _ in matrix["x"]]
    with pytest.raises(ValueError, match="no variation"):
        card.fit(**matrix)
    with pytest.raises(ValueError, match="configuration"):
        card.source({}, dict(card.CONFIG, bootstrap_pilot_draws=True))
