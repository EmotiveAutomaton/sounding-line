"""Constructed-only LA5 source formulas and complete numerical consumer checks."""
from contextlib import contextmanager
from pathlib import Path
import copy
import numpy as np
from . import week5_la5_v1 as study


def meeting():
    name = 'constructed-meeting'; people = ('A', 'B', 'C', 'D')
    meta = {'corpus': 'AMI', 'duration': 600., 'speakers': {p: {'person': p, 'role': 'projectmanager' if p == 'A' else None} for p in people}}
    acts = [{'id': 'constructed-act-'+str(i), 'meeting': name, 'speaker': 'A', 'start': t, 'end': t+1,
             'words': [{'kind': 'word', 'laugh': False} for _ in range(3)]} for i, t in enumerate((100., 300.))]
    laughs = [{'meeting': name, 'speaker': p, 'start': t, 'end': t+.2, 'label': 'vocal'}
              for p, t in [('B', 101.5), ('C', 102.), ('B', 301.5), ('C', 302.), ('A', 303.)]]
    speech = []
    for t, counts in [(60., [4, 3, 2, 1]), (120., [2, 4, 3, 1]), (260., [2, 4, 3, 1]), (320., [4, 3, 2, 1])]:
        for person, count in zip(people, counts, strict=True):
            speech.extend({'meeting': name, 'speaker': person, 'start': t+i*.01, 'end': t+i*.01+.005} for i in range(count))
    for act in acts:
        speech.extend({'meeting': name, 'speaker': 'A', 'start': act['start']+.1+i*.1,
                       'end': act['start']+.15+i*.1} for i in range(3))
    return acts, laughs, speech, {name: meta}


def two_meetings():
    acts, laughs, speech, metadata = meeting(); source = [acts, laughs, speech]; result = [[], [], []]; meta = {}
    for number in range(2):
        name = 'constructed-meeting-'+str(number)
        for incoming, outgoing in zip(source, result, strict=True):
            for original in incoming:
                row = copy.deepcopy(original); row['meeting'] = name
                if 'id' in row:
                    row['id'] += '-'+str(number)
                outgoing.append(row)
        meta[name] = copy.deepcopy(next(iter(metadata.values())))
    return *result, meta


@contextmanager
def source_boundary():
    original = study.load_source; data = two_meetings()
    try:
        identity = {'constructed': study.digest(data), 'implementation': study.dependencies()}
        study.load_source = lambda inputs: (*data, identity)
        yield
    finally:
        study.load_source = original


def projection_chain(output):
    output = Path(output); small = {'phase': 'LA5-prepare', 'max_new_draws': 1, 'max_wall_seconds': 160}
    large = {**small, 'max_new_draws': 10}
    with source_boundary():
        assert study.execute(output, {}, small)['status'] == 'yielded'
        complete = study.execute(output, {}, large)
        assert complete['complete_preparation'] is True
        paused = study.verify(output, {}, small)
        assert paused['status'] == 'yielded' and paused['verified'] is False
        assert study.verify(output, {}, large)['verified'] is True
    rows = study.seal.read(output/'EVENTS.json')['rows']
    assert len(rows) == 4 and all(r['model_eligible'] for r in rows)
    return {'passed': True, 'events': 4, 'all_source_fields_independently_replayed': True}


def model_rows(effect=0.):
    rng = np.random.default_rng(131350); rows = []
    for corpus in ('AMI', 'ICSI'):
        for m in range(20):
            for person in range(4):
                for event in range(10):
                    not_joined = event % 2 == 0
                    start = float(rng.uniform(100, 1000)); words = int(rng.integers(3, 24)); laughers = int(rng.integers(2, 5))
                    outcome = .2 + effect*not_joined + .003*start/60 + .001*words + .002*laughers + .01*person + .001*m
                    rows.append({'act': f'constructed-{corpus}-{m}-{person}-{event}', 'meeting': f'{corpus}-{m:02}',
                        'speaker': f'{corpus}-{m}-{person}', 'person': f'{corpus}-person-{person}', 'corpus': corpus,
                        'role': 'projectmanager' if corpus == 'AMI' else None, 'act_start': start, 'act_words': words,
                        'other_laughers': laughers, 'joined': not not_joined, 'outcome': outcome, 'model_eligible': True})
    return rows


@contextmanager
def table_boundary(rows):
    original = study.load_prepared
    try:
        identity = {'constructed': study.digest(rows), 'implementation': study.dependencies()}
        study.load_prepared = lambda inputs: (rows, identity)
        yield
    finally:
        study.load_prepared = original


def null_chain(output):
    output = Path(output); rows = model_rows()
    small = {'phase': 'LA5', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 160}
    large = {**small, 'max_new_draws': 10000}
    with table_boundary(rows):
        assert study.execute(output, {}, small)['status'] == 'yielded'
        complete = study.execute(output, {}, large)
        assert complete['complete_card'] is True
        paused = study.verify(output, {}, small)
        assert paused['status'] == 'yielded' and paused['verified'] is False
        verified = study.verify(output, {}, large)
        assert verified['verified'] is True
    assert complete['primary']['outcome'] == 'band-null'
    for panel in [complete['primary'], *complete['secondary'].values()]:
        assert panel['draws'] == 2000 and abs(panel['estimate']) < 1e-9
    proof = {'passed': True, 'all_2000_draw_panels': ['AMI', 'ICSI', 'AMI-role-0'],
        'execute_and_independent_verify_pause_reentry': True, 'source_substitution': 'constructed prepared numerical event table',
        'record_kind': 'run', 'theory_tags': ['H14-mockery'], 'by_construction': True, 'activation': []}
    study.io.write_json(output/'FIXTURE.json', proof)
    return proof
