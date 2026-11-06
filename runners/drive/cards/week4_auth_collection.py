"""Authenticated private AUTH rows, with both writer roles; no scientific scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 4-7 reread November 5; AUTH_COLLECTION.md.
NULL and ALTERNATIVE both require exact coverage, source and recorded truth.
Malformed/changed/missing evidence refuses rather than selecting valid survivors.
Reader labels are retained; no AUC, uncertainty or genre contrast is calculated.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
from runners.stage14.common import REPO, read, filehash, digest
from .timing_p6 import write_equal
from . import week4_auth_pairs as pairs


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('fixed mode required')
    return dict(mode=mode, expected_pairs=80 if mode == 'constructed' else 3800,
                expected_writers=4 if mode == 'constructed' else 24,
                expected_excluded=16 if mode == 'constructed' else 200)


def parse_raw(lines, requests, model):
    def unique(items):
        value = {}
        for k, v in items:
            if k in value:
                raise ValueError('duplicate JSON key')
            value[k] = v
        return value
    expected = {r['custom_id'] for r in requests}
    if len(expected) != len(requests):
        raise ValueError('duplicate request')
    labels = {}
    for line in lines:
        row = json.loads(line, object_pairs_hook=unique)
        identity = row['custom_id']
        if identity not in expected or identity in labels:
            raise ValueError('result identity mismatch')
        result = row['result']
        if result['type'] != 'succeeded':
            raise ValueError('unsuccessful response')
        message = result['message']
        content = message['content']
        if (message['model'] != model or message['stop_reason'] != 'end_turn'
                or len(content) != 1 or content[0]['type'] != 'text'):
            raise ValueError('invalid whole response')
        value = json.loads(content[0]['text'], object_pairs_hook=unique)
        if (type(value) is not dict or set(value) != {'score'}
                or type(value['score']) is not int or not 0 <= value['score'] <= 9):
            raise ValueError('invalid integer label')
        labels[identity] = value['score']
    if set(labels) != expected:
        raise ValueError('incomplete response collection')
    return labels


def assemble(sessions, joins, requests, labels, excluded, config):
    """Join by content-bound identity, never by reply order or score value."""
    source = {r['session']: r for r in sessions}
    writers = {r['writer'] for r in sessions}
    if len(source) != len(sessions) or len(writers) != config['expected_writers']:
        raise ValueError('source identity coverage')
    if len(excluded) != config['expected_excluded'] or len(set(excluded)) != len(excluded):
        raise ValueError('used calibration coverage')
    by_pair = {r['item_id']: r for r in requests}
    if (len(by_pair) != len(requests) or len(joins) != config['expected_pairs']
            or len(requests) != len(joins) or len({r['pair_id'] for r in joins}) != len(joins)
            or set(by_pair) != {r['pair_id'] for r in joins}
            or set(labels) != {r['custom_id'] for r in requests}
            or len({r['custom_id'] for r in requests}) != len(requests)):
        raise ValueError('complete one-to-one identity join required')
    if set(by_pair) & set(excluded):
        raise ValueError('calibration reuse')
    rows = []
    blocks = defaultdict(list)
    for pair in sorted(joins, key=lambda r: r['pair_id']):
        a, b = source[pair['left']], source[pair['right']]
        request = by_pair[pair['pair_id']]
        label = labels[request['custom_id']]
        if type(label) is not int or not 0 <= label <= 9:
            raise ValueError('invalid label')
        if (a['session'] == b['session'] or a['genre'] != b['genre']
                or a['genre'] != pair['genre'] or a['prompt'] == b['prompt']
                or pair['prompts'] != [a['prompt'], b['prompt']]
                or type(pair['same_writer']) is not bool
                or pair['same_writer'] != (a['writer'] == b['writer'])):
            raise ValueError('recorded truth, genre or prompt mismatch')
        texts = [a['typed']['text'], b['typed']['text']]
        if (not a['source_exact'] or not b['source_exact'] or pair['texts'] != texts
                or pair['pair_id'] != digest(sorted(texts))
                or any(not t.strip() or len(t.split()) > 400 for t in texts)):
            raise ValueError('exact source text mismatch')
        params = request['params']
        projected = json.loads(params['messages'][0]['content'])
        if (projected != dict(text_a=texts[0], text_b=texts[1])
                or request['custom_id'] != digest(['AUTH', 1, pair['pair_id'], params])):
            raise ValueError('provider projection mismatch')
        row = dict(pair_id=pair['pair_id'], custom_id=request['custom_id'],
                   block=pair['block'], genre=pair['genre'], same_writer=pair['same_writer'],
                   left_session=a['session'], right_session=b['session'],
                   left_writer=a['writer'], right_writer=b['writer'],
                   left_prompt=a['prompt'], right_prompt=b['prompt'],
                   left_words=len(texts[0].split()), right_words=len(texts[1].split()),
                   text_sha256=[digest(t) for t in texts], score=label)
        rows.append(row)
        blocks[row['block']].append(row)
    for block in blocks.values():
        if len(block) != 2 or {r['same_writer'] for r in block} != {False, True}:
            raise ValueError('incomplete matched block')
        for key in ('genre', 'left_session', 'left_writer', 'left_prompt', 'right_prompt'):
            if block[0][key] != block[1][key]:
                raise ValueError('unmatched block')
    counts = Counter((r['genre'], r['same_writer']) for r in rows)
    creative = 24 if config['mode'] == 'constructed' else 1000
    argument = 16 if config['mode'] == 'constructed' else 900
    if counts != {(g, truth): n for g, n in [('creative', creative), ('argumentative', argument)] for truth in (True, False)}:
        raise ValueError('unchanged genre and truth allocation required')
    summary = dict(pairs=len(rows), blocks=len(blocks), excluded_pairs=len(excluded),
                   source_writers=len(writers), by_genre={}, scientific_admission=False,
                   scientific_effect_computed=False, raw_text_in_analysis_rows=False)
    for genre in pairs.GENRES:
        selected = [r for r in rows if r['genre'] == genre]
        both = {r[k] for r in selected for k in ('left_writer', 'right_writer')}
        if both != writers:
            raise ValueError('missing writer across both roles')
        summary['by_genre'][genre] = dict(
            same=counts[(genre, True)], different=counts[(genre, False)],
            both_role_writers=len(both),
            positive_role_writers=len({r['left_writer'] for r in selected if r['same_writer']}),
            sessions=len({r[k] for r in selected for k in ('left_session', 'right_session')}))
    return rows, summary


def fixture():
    sessions = pairs.fixture()
    bank, selection, _ = pairs.draw(sessions, pairs.configuration('constructed'))
    excluded = selection['calibration'] + selection['fresh']
    joins = [r for r in bank if r['pair_id'] not in excluded]
    requests, labels = [], {}
    for i, row in enumerate(joins):
        params = dict(messages=[dict(content=json.dumps(dict(text_a=row['texts'][0], text_b=row['texts'][1])))])
        cid = digest(['AUTH', 1, row['pair_id'], params])
        requests.append(dict(item_id=row['pair_id'], custom_id=cid, params=params))
        labels[cid] = i % 10  # A construction to test the join, never a human model score.
    return sessions, joins, requests, labels, excluded


def load(inputs):
    from runners.drive import week4_auth_main as main
    if set(inputs) != {'main_landing'}:
        raise ValueError('fixed main landing required')
    landing = Path(inputs['main_landing'])
    if landing.resolve() != (REPO/'results/phase_2_4_stage_15/DRIVE/WEEK4_AUTH_MAIN_COMPLETE_20261105.json').resolve():
        raise ValueError('wrong main landing')
    landed = read(landing)
    root = main.ROOT / main.PHASE
    for k in ('full_write_through', 'complete_main_corpus', 'format_passes', 'complete_raw_replay'):
        if landed.get(k) is not True:
            raise ValueError('complete landed main required')
    bindings = {root/'COMPLETE.json': 'complete_sha256', root/'LABELS.json': 'labels_sha256',
                root/'RESULTS.jsonl': 'results_sha256', root/'RECONCILED.json': 'settlement_sha256',
                main.ROOT/'SOURCE.json': 'source_sha256', main.ROOT/'PRIVATE_JOIN.json': 'private_join_sha256'}
    for path, key in bindings.items():
        if filehash(path) != landed[key]:
            raise ValueError('main landing binding changed')
    done = read(root/'COMPLETE.json')
    if not all(done[k] is True for k in ('complete_main_corpus', 'format_passes', 'usage_complete')):
        raise ValueError('invalid main completion')
    for name, hashed in read(root/'RECONCILED.json')['proof'].items():
        if filehash(root/name) != hashed:
            raise ValueError('unreconciled main')
    main.bound_plan(main.PHASE)
    requests = main.selected(main.PHASE)
    labels = parse_raw((root/'RESULTS.jsonl').read_text(encoding='utf8').splitlines(), requests, main.MODEL)
    if labels != read(root/'LABELS.json'):
        raise ValueError('saved labels differ from raw replies')
    joins = read(main.ROOT/'PRIVATE_JOIN.json')
    source_plan = read(main.calibration.PAIRS/'PLAN.json')
    sessions = pairs.load(source_plan['inputs'])
    selection = read(main.calibration.PAIRS/'output/SELECTION.json')
    return sessions, joins, requests, labels, selection['calibration'] + selection['fresh']


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('fixed collection configuration')
    if config['mode'] == 'constructed' and inputs:
        raise ValueError('no external constructed inputs')
    data = fixture() if config['mode'] == 'constructed' else load(inputs)
    if verification:
        data = (list(reversed(data[0])), list(reversed(data[1])), list(reversed(data[2])), data[3], list(reversed(data[4])))
    rows, summary = assemble(*data, config)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [('PRIVATE_ROWS.json', rows), ('SUMMARY.json', summary)]:
        if verification:
            if read(output/name) != value:
                raise ValueError('fresh collection replay differs')
        else:
            write_equal(output/name, value)
    return dict(verified=True, complete_identity_join=True, scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
