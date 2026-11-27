"""Run the verified TP72 reader under the Week 8 sealed contract.

DESIGN CHECK (LESSONS §§3–5). On invented speech, reversing target and rater
must fail; removing one of twelve trait respondents must suppress the fine form.
Independent runs must return identical rows, intervals, controls and membership
counts. On insufficient support the existing disclosure rule withholds the form.
"""
import csv
import importlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week7_tmp1_shell as shell
from runners.drive.sealed import week8_tp72_receiver as receive
from runners.drive.sealed import week8_tmp3_receiver as speech


def original_speech(example):
    """Recreate reciprocal original-format questionnaires and time-ordered turns."""
    people = {s.speaker: s for s in example}
    roster = {}
    for row in example:
        roster.setdefault(row.conversation, []).append(row.speaker)
    survey, turns = [], []
    for meeting, pair in roster.items():
        if len(pair) != 2:
            raise ValueError('A constructed conversation must have two speakers')
        records = [('boundary', 'before')]
        for who, partner in (pair, pair[::-1]):
            person, other = people[who], people[partner]
            fields = dict(conversation_id=meeting, user_id=who, partner_id=partner)
            fields.update({k: person.outcomes[k] for k in speech.OWN})
            for trait in speech.TRAITS:
                fields['my_'+trait] = person.outcomes['self_'+trait]
                fields['your_'+trait] = other.outcomes['partner_'+trait]
            survey.append(fields)
            records.extend((who, text) for text in person.turns)
        records.append(('boundary','after'))
        turns.extend(dict(conversation_id=meeting, turn_id=i, speaker=s, utterance=t)
                     for i,(s,t) in enumerate(records))
    projected, exclusions = speech.project(survey, turns)
    if exclusions or len(projected) != len(example):
        raise ValueError('The original-format invented conversations failed their join')
    for row in projected:
        expected = people[row.speaker]
        if row.outcomes != expected.outcomes or tuple(row.turns) != tuple(expected.turns):
            raise ValueError('Speaker or partner projection disagrees with the invented truth')
    return projected


def write_release(out, tables, contract):
    with TemporaryDirectory() as tmp:
        staging = Path(tmp)
        for name, rows in tables.items():
            with (staging/name).open('x', newline='', encoding='utf8') as f:
                writer = csv.DictWriter(f, fieldnames=contract[name][0], lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
        shell.check_tables(staging, contract)
        for table in sorted(staging.iterdir()):
            with (out/table.name).open('xb') as dest:
                dest.write(table.read_bytes())


def run(root, out, config):
    mode = config['mode']
    if config['target']:
        shell.check_image()
    expected = {'fixture': {'payload'}, 'history': {'projection','payload'},
                'conversation': {'projection','payload'}}[mode]
    if root.is_symlink() or {p.name for p in root.iterdir()} != expected:
        raise SealedFailure(21,'Source layout differs from the mount receipt')
    payload = root/'payload'
    shell.verify_bundle(payload, config['payload'])
    sys.path.insert(0,str(payload))
    try:
        names = ['panels','history','conversation','rehearse72','made']
        modules = {name: importlib.import_module(name) for name in names}
        if any(Path(m.__file__).resolve().parent != payload.resolve() for m in modules.values()):
            raise SealedFailure(21,'The loaded reader differs from the mounted bundle')
        panels = modules['panels']
        contract = panels.contracts(panels.CONVERSATION if mode != 'history' else panels.HISTORY)
        first = None
        for _ in range(2):
            with TemporaryDirectory() as work:
                scratch = Path(work)
                frozen = panels.Frozen()
                if mode == 'fixture':
                    from runners.drive.sealed.week8_tp72_fixture import exercise
                    tables = exercise(scratch,modules,frozen)
                elif mode == 'history':
                    from runners.drive.sealed import week8_tmp2_source as source
                    source.verify(root/'projection',config['files'])
                    tables = receive.history(root/'projection',config['files'],scratch,modules['history'],
                                             frozen,contract,lambda: None,[])
                else:
                    from runners.drive.sealed.week8_tp72_prior import conversation_rosters
                    speakers, _ = speech.in_seal(root/'projection')
                    universe, known = conversation_rosters(root/'projection',config['prior'])
                    tables = receive.conversation(speakers,scratch,modules['conversation'],frozen,
                                                  contract,lambda: None,universe,known)
            if first is None:
                first = tables
            elif tables != first:
                raise SealedFailure(14,'Independent reader replay differs')
        write_release(out,first,contract)
    finally:
        sys.path.remove(str(payload))
