import copy
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from runners.drive.cards import events_d32_examination as card
from runners.drive.cards.events_p5 import read, write, filehash


def fixture_rows(effect=1):
    offers, menus = [], []
    for w in range(6):
        for outside in (0, 1):
            for j in range(8):
                key = f"w{w}-g{outside}-n{j}"
                h = bool(1-outside) if effect == 1 else bool(outside) if effect == -1 else j % 2 == 0
                offers.append(dict(writer=f"w{w}", session=f"s{w}", key=key, position=1, outside=outside, accepted=0))
                menus.append(dict(writer=f"w{w}", session=f"s{w}", key=key, menu_size=2,
                    hovered=[False,h], navigated=[False,False], targeted=[False,h],
                    default_all=[True,h], default_argumentative=[False,h], domain="creative",
                    selected=None, dwell_seconds=2., dwell_observed=True, hover_target_complete=True))
    return offers, menus


@pytest.mark.parametrize("effect,state", [(0,"null"),(1,"positive"),(-1,"negative")])
def test_exact_null_planted_and_reverse(effect, state):
    rows, audit = card.join(*fixture_rows(effect))
    result = card.summary(rows, audit)
    assert result["primary"]["effect"] == effect
    assert result["primary"]["ci95"] == [effect,effect]
    assert result["primary"]["state"] == state
    assert result["primary"]["p_approx"] is None
    assert result["specifications"]["hovered"]["effect"] == -effect
    assert result["support"]["declined_inside"] == result["support"]["declined_outside"] == 48


def test_bootstrap_order_invariance_and_equal_writer_weight():
    offers, menus = fixture_rows(0)
    rows, _ = card.join(offers, menus)
    # Change one writer, preserving unequal opportunities: writer weights stay equal.
    for row in rows:
        if row["writer"] == "w0":
            row.update(hovered=not bool(row["outside"]), targeted=not bool(row["outside"]),
                       default_all=not bool(row["outside"]), default_argumentative=not bool(row["outside"]))
    rows += [dict(r, key=r["key"]+"extra") for r in rows if r["writer"] == "w0"]
    result = card.statistics(rows)
    assert result["contrasts"]["primary"]["effect"] == pytest.approx(1/6)
    assert card.statistics(list(reversed(rows))) == result
    assert card.statistics(list(reversed(rows)), True) == card.statistics(rows, True)


def test_censoring_unknown_targets_keyboard_and_default():
    offers, menus = fixture_rows(1)
    menus[0]["dwell_observed"] = False
    menus[1]["hover_target_complete"] = False
    menus[2].update(dwell_observed=False, hover_target_complete=False)
    rows, audit = card.join(offers, menus)
    assert audit["excluded_unknown_union"] == 3
    assert audit["declined_censored_duration"] == audit["declined_missing_hover_target"] == 2
    r = dict(rows[-1], hovered=False, targeted=True, default_all=True, default_argumentative=True)
    v = card.indicators(r)
    assert v["hover_only_short"] and not v["explicit_targets_short"] and not v["primary"]
    r.update(targeted=False, default_argumentative=False)  # hypothetical default first only
    assert card.indicators(r)["explicit_targets_short"] and not card.indicators(r)["primary"]
    r.update(default_all=False, dwell_seconds=2.000001)
    assert not card.indicators(r)["primary"] and card.indicators(r)["short_5s"]
    r["dwell_seconds"] = 2.
    assert card.indicators(r)["primary"] and not card.indicators(r)["short_1s"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "writer", "accepted", "target", "duration", "position"])
def test_malformed_joins_refuse(mutation):
    offers, menus = fixture_rows()
    if mutation == "missing": menus.pop(0)
    if mutation == "duplicate": offers.append(copy.deepcopy(offers[0]))
    if mutation == "writer": offers[0]["writer"] = "other"
    if mutation == "accepted": offers[0]["accepted"] = 1
    if mutation == "target": menus[0]["targeted"][1] = False
    if mutation == "duration": menus[0]["dwell_seconds"] = float("nan")
    if mutation == "position": offers[0]["position"] = 99
    with pytest.raises(ValueError): card.join(offers, menus)


def test_sparse_support_fails_instead_of_null():
    rows, _ = card.join(*fixture_rows())
    with pytest.raises(ValueError, match="paired writers"):
        card.statistics([r for r in rows if r["writer"] in ("w0","w1")])


def fixture_source(tmp_path):
    offers, menus = fixture_rows()
    inputs = {}
    for name, module, config, output, data in (
        ("d32", "events_d32", dict(bootstrap=2000, seed=20261017, clusters=[50,20,100]), "ROWS_k50.json", offers),
        ("d6", "events_d6", dict(bootstrap=2000, seed=20261017), "ROWS.json", menus)):
        root = tmp_path / name
        write(root / "PLAN.json", dict(module="runners.drive.cards."+module, config=config))
        write(root / "output" / output, data)
        if name == "d6": write(root / "output/INTERFACE_AUDIT.json", dict(fixture=True))
        write(root / "COMPLETE.json", dict(status="COMPLETE", fresh_process_verified=True,
            outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob("*.json")}))
        inputs[name+"_completion"] = str(root / "COMPLETE.json")
    return inputs


def test_serialized_resume_reentry_replay_and_tamper(tmp_path):
    inputs = fixture_source(tmp_path); output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", dict(reason="fixture"))
    assert card.execute(output, inputs, card.CONFIG)["status"] == "yielded"
    part = output / "parts/00.json"; before = part.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, card.CONFIG)
    assert part.read_bytes() == before
    assert card.verify(output, inputs, card.CONFIG)["verified"]
    hashes = {str(p):filehash(p) for p in output.rglob("*.json")}
    assert card.execute(output, inputs, card.CONFIG) == result
    assert {str(p):filehash(p) for p in output.rglob("*.json")} == hashes
    changed = read(output / "ROWS.json"); changed[0]["outside"] = 1
    (output / "ROWS.json").write_text(json.dumps(changed), encoding="utf8")
    saved = read(output / "OUTPUT_HASHES.json"); saved["ROWS.json"] = filehash(output / "ROWS.json")
    (output / "OUTPUT_HASHES.json").write_text(json.dumps(saved), encoding="utf8")
    with pytest.raises(ValueError, match="source reconstruction"):
        card.verify(output, inputs, card.CONFIG)


def test_source_mutation_and_config_refused(tmp_path):
    inputs = fixture_source(tmp_path)
    with pytest.raises(ValueError, match="config"):
        card.source(inputs, dict(card.CONFIG, short_seconds=3.))
    source = Path(inputs["d6_completion"]).parent / "output/ROWS.json"
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="completion binding"):
        card.source(inputs, card.CONFIG)


def test_actual_counted_runtime_and_fresh_process(tmp_path):
    inputs = fixture_source(tmp_path / "sources"); root = tmp_path / "runtime"
    write(root / "PLAN.json", dict(card="D32-examination-fixture", module=card.__name__, inputs=inputs,
        config=card.CONFIG, pins={v:filehash(v) for v in inputs.values()},
        forecast_cpu_seconds=600, max_wall_seconds=180, max_output_bytes=256*1024**2, smoke=True))
    log = root / "runtime.log"
    with log.open("w") as stream:
        proc = subprocess.Popen([sys.executable,"-X","utf8","-B","-m",
            "runners.drive.cards.batch_runtime_v2","run",str(root)], stdout=stream, stderr=stream)
        try:
            deadline = time.monotonic()+40
            while not (root / "OWNER.json").exists():
                if proc.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError("smoke handshake failed: "+log.read_text())
                time.sleep(.1)
            write(root / "MONITOR_READY.json", dict(owner_sha256=filehash(root / "OWNER.json")))
            assert proc.wait(timeout=180) == 0, log.read_text()
            assert read(root / "COMPLETE.json")["fresh_process_verified"]
            assert read(root / "VERIFIED.json")["verified"]
            lease = Path(read(root / "ADMISSION.json")["lease"])
            assert not lease.exists()
        finally:
            if proc.poll() is None:
                proc.terminate(); proc.wait(timeout=30)
