"""Rutledge source-support repair; original MD-source attempt remains immutable.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. No effect is estimated here.
Exact duplicate task arrays can identify a task, but conflicting tasks at one
attempt counter cannot. Neither null nor alternative outcomes alter eligibility.
Ambiguous repeat histories and missing clocks are counted, never fabricated.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from .week5_md import HEADER, MAT_SHA, ZIP_SHA, save_json, sha, validate_play


def resolve(subject: dict) -> tuple[list[np.ndarray], list[int], list[float], bool, dict]:
    if list(subject['dataHdr']) != HEADER:
        raise ValueError('task schema mismatch')
    raw = subject['data']
    plays = [raw] if getattr(raw, 'shape', None) == (30, 15) else list(raw)
    counters = np.atleast_1d(subject['timesPlayed']).astype(float)
    days = np.atleast_1d(subject['dayNumber']).astype(float)
    tod = np.atleast_1d(subject['timeOfDay']).astype(float)
    if not len(plays) == len(counters) == len(days) == len(tod) == int(subject['nPlays']):
        raise ValueError('play cardinality mismatch')
    if not np.isfinite(counters).all() or (counters < 1).any() or (counters != np.floor(counters)).any():
        raise ValueError('unsupported counter value')
    for play in plays:
        validate_play(np.asarray(play, float))
    audit = Counter(raw_plays=len(plays), nonfinite_clock_plays=int((~np.isfinite(days+tod)).sum()))
    retained, kept_counter, kept_day = [], [], []
    repeat_eligible = bool(np.isfinite(days+tod).all())
    for value in sorted(set(counters)):
        indices = np.flatnonzero(counters == value)
        if len(indices) > 1:
            repeat_eligible = False
            audit['duplicate_counter_groups'] += 1
            equal = all(np.array_equal(plays[indices[0]], plays[i], equal_nan=True) for i in indices[1:])
            if not equal:
                audit['conflicting_counter_groups'] += 1
                audit['conflicting_counter_plays_excluded'] += len(indices)
                audit['conflicting_first_groups'] += int(value == 1)
                continue
            audit['identical_counter_groups'] += 1
            audit['identical_copies_collapsed'] += len(indices)-1
        clock = days[indices] + tod[indices]
        # A known task does not establish a calendar time when copied clocks disagree.
        stamp = float(clock[0]) if np.isfinite(clock).all() and np.all(clock == clock[0]) else float('nan')
        audit['retained_missing_clock'] += int(not np.isfinite(stamp))
        retained.append(np.asarray(plays[indices[0]], float))
        kept_counter.append(int(value)); kept_day.append(stamp)
    audit['retained_plays'] = len(retained)
    audit['first_play_retained'] = int(1 in kept_counter)
    audit['first_counter_absent'] = int(1 not in counters)
    audit['repeat_history_ineligible_people'] = int(not repeat_eligible)
    audit['duplicate_counter_people'] = int(len(set(counters)) != len(counters))
    return retained, kept_counter, kept_day, repeat_eligible, dict(audit)


def source_subjects(source: Path, independent: bool = False):
    if sha(source/'Rutledge_risk_and_happiness_task_2023.zip') != ZIP_SHA:
        raise ValueError('archive pin mismatch')
    mat = source/'Rutledge_GBE_risk_data_TOD.mat'
    if sha(mat) != MAT_SHA:
        raise ValueError('extracted member pin mismatch')
    if independent:
        return loadmat(mat, variable_names=['subjData'], struct_as_record=False, squeeze_me=True)['subjData']
    return loadmat(mat, variable_names=['subjData'], simplify_cells=True)['subjData']


def prepare(source: Path, output: Path) -> dict:
    ss = source_subjects(source)
    all_plays, person, counter, day, eligible, first, first_person = [], [], [], [], [], [], []
    audit = Counter(participants=len(ss))
    for ordinal, subject in enumerate(ss):
        ps, cs, ds, repeat_ok, counts = resolve(subject)
        audit.update(counts)
        for play, c, d in zip(ps, cs, ds):
            all_plays.append(play); person.append(ordinal); counter.append(c); day.append(d); eligible.append(repeat_ok)
            if c == 1:
                first.append(play); first_person.append(ordinal)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output/'task.npz', plays=np.asarray(all_plays), person=np.asarray(person),
                        counter=np.asarray(counter), day=np.asarray(day), repeat_eligible=np.asarray(eligible),
                        first=np.asarray(first), first_person=np.asarray(first_person))
    record = {'kind':'source_support_repair', 'version':'MD-source.h1', 'scientific_result':False,
              'archive_sha256':ZIP_SHA, 'mat_sha256':MAT_SHA, 'task_sha256':sha(output/'task.npz'),
              'counts':dict(audit), 'plays':len(all_plays), 'first_plays':len(first),
              'support_policy':'Exact positive attempt 1 only; identical task copies collapsed; conflicting counter groups excluded; any collision or nonfinite clock excludes repeat history.',
              'clock_policy':'Identical copies with disagreeing clocks retain the known task with missing calendar coordinate.',
              'identifier_policy':'Private ordinal cluster only; no source id, demographic or clinical fields retained.'}
    save_json(output/'SOURCE.json', record)
    return record


def verify_projection(source: Path, output: Path) -> dict:
    """Independent object-struct reader and projection implementation; every value."""
    record = json.loads((output/'SOURCE.json').read_text('utf8'))
    if sha(output/'task.npz') != record['task_sha256']:
        raise ValueError('task hash changed')
    with np.load(output/'task.npz', allow_pickle=False) as npz:
        saved = {k:npz[k] for k in npz.files}
    checked = first_checked = 0
    audit = Counter()
    for ordinal, s in enumerate(source_subjects(source, independent=True)):
        audit['participants'] += 1
        if list(s.dataHdr) != HEADER:
            raise ValueError('independent schema mismatch')
        ps = [s.data] if getattr(s.data, 'shape', None) == (30,15) else list(s.data)
        cs = np.atleast_1d(s.timesPlayed); ds = np.atleast_1d(s.dayNumber)+np.atleast_1d(s.timeOfDay)
        groups = {}
        for index, c in enumerate(cs):
            groups.setdefault(int(c), []).append(index)
        collision = len(groups) != len(cs)
        repeat_ok = not collision and bool(np.isfinite(ds).all())
        audit.update(raw_plays=len(ps), nonfinite_clock_plays=int((~np.isfinite(ds)).sum()),
                     first_counter_absent=int(1 not in groups), duplicate_counter_people=int(collision),
                     repeat_history_ineligible_people=int(not repeat_ok))
        for c, ii in sorted(groups.items()):
            if len(ii) > 1:
                audit['duplicate_counter_groups'] += 1
                if any(not np.array_equal(ps[ii[0]],ps[i],equal_nan=True) for i in ii):
                    audit.update(conflicting_counter_groups=1, conflicting_counter_plays_excluded=len(ii), conflicting_first_groups=int(c==1))
                    continue
                audit.update(identical_counter_groups=1, identical_copies_collapsed=len(ii)-1)
            clock = ds[ii]
            d = clock[0] if np.isfinite(clock).all() and (clock == clock[0]).all() else np.nan
            audit['retained_missing_clock'] += int(not np.isfinite(d)); audit['retained_plays'] += 1
            if not np.array_equal(saved['plays'][checked],ps[ii[0]],equal_nan=True):
                raise ValueError('numeric task mismatch')
            if saved['person'][checked] != ordinal or saved['counter'][checked] != c or saved['repeat_eligible'][checked] != repeat_ok:
                raise ValueError('support metadata mismatch')
            if not np.array_equal(saved['day'][checked],d,equal_nan=True):
                raise ValueError('calendar projection mismatch')
            if c == 1:
                audit['first_play_retained'] += 1
                if saved['first_person'][first_checked] != ordinal or not np.array_equal(saved['first'][first_checked],ps[ii[0]],equal_nan=True):
                    raise ValueError('first task mismatch')
                first_checked += 1
            checked += 1
    if checked != len(saved['plays']) or first_checked != len(saved['first']) or dict(audit) != record['counts']:
        raise ValueError('projection count mismatch')
    result = {'verified':True, 'all_numeric_values':True, 'plays_checked':checked,
              'first_plays_checked':first_checked, 'task_sha256':record['task_sha256'], 'counts_reconciled':True}
    save_json(output/'VERIFIED.json', result)
    return result


def fixture() -> dict:
    # This fixture constructs only task arrays; it contains no human observations.
    play = np.zeros((30,15)); play[:,0] = np.arange(1,31); play[:,9] = np.nan
    play[[0,3,5,8,11,13,16,18,21,24,26,29],9] = 50
    def subject(ps,cs,days):
        return dict(dataHdr=HEADER,data=ps,timesPlayed=cs,dayNumber=days,timeOfDay=np.zeros(len(cs)),nPlays=len(cs))
    equal = resolve(subject([play,play.copy()],[1,1],[0,1]))
    assert len(equal[0]) == 1 and equal[1] == [1] and np.isnan(equal[2][0]) and not equal[3]
    changed = play.copy(); changed[:,1] = 1-changed[:,1]
    conflict = resolve(subject([play,changed],[1,1],[0,1]))
    assert not conflict[0] and conflict[4]['conflicting_first_groups'] == 1
    later = resolve(subject([play],[3],[2]))
    assert later[1] == [3] and later[4]['first_play_retained'] == 0
    missing = resolve(subject([play],[1],[np.nan]))
    assert missing[1] == [1] and not missing[3]
    return {'passed':True,'identical_task_clock_ambiguity':True,'conflicting_first_excluded':True,
            'later_play_not_first':True,'missing_clock_not_invented':True}


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config.get('phase','prepare') == 'prepare':
        return prepare(Path(inputs['source']),output)
    if config.get('phase') == 'fixture':
        result=fixture();save_json(output/'FIXTURE.json',result);return result
    raise ValueError('unsupported phase')


def verify(output: Path, inputs: dict, config: dict) -> dict:
    if config.get('phase','prepare') == 'prepare':
        return verify_projection(Path(inputs['source']),output)
    if config.get('phase') == 'fixture':
        if fixture() != json.loads((output/'FIXTURE.json').read_text('utf8')):
            raise ValueError('fixture replay mismatch')
        return {'verified':True,'fixture_replayed':True}
    raise ValueError('unsupported phase')
