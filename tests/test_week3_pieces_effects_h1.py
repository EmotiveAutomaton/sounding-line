import ast
import json
from pathlib import Path
import pytest
from runners.drive.cards import week3_pieces_effects_h1_checks as checks
from runners.drive.cards.timing_census import read

def test_complete_known_answer_effects():
    assert len(checks.cases())==7

def test_serialized_replay_and_mutation(tmp_path):
    assert checks.execute(tmp_path,{},checks.CONFIG)['cases']==7
    assert checks.verify(tmp_path,{},checks.CONFIG)['verified']
    x=read(tmp_path/'CASES.json'); x['edited'][0]['accepted_retained_share']=1
    (tmp_path/'CASES.json').write_text(json.dumps(x),encoding='utf8')
    with pytest.raises(ValueError,match='fresh complete effects'): checks.verify(tmp_path,{},checks.CONFIG)

def test_exact_consumer_source_changes_are_only_provenance_import_and_call():
    root=Path('runners/drive/cards')
    s=(root/'week3_pieces_effects.py').read_text(encoding='utf8')
    s=s.replace('"""WB1 occurrence effects and discovery-only classes; completes coverage card.',
                '"""WB1.h1 effects: same windows/contrasts with physical insertion provenance.')
    s=s.replace('from runners.drive.cards.timing_events import source_sessions, accepted_lifetimes',
                'from runners.drive.cards.timing_events import source_sessions\nfrom runners.drive.cards.week3_insertion_provenance_h1 import reconstruct')
    s=s.replace('lifetime = accepted_lifetimes(events, timeline["final_document"])',
                'lifetime = reconstruct(events, timeline)["eligible"]')
    assert ast.dump(ast.parse(s))==ast.dump(ast.parse((root/'week3_pieces_effects_h1.py').read_text(encoding='utf8')))

def test_exact_cost_consumer_changes_only_effects_dependency():
    root=Path('runners/drive/cards');s=(root/'week3_pieces_effects_pilot.py').read_text(encoding='utf8')
    s=s.replace('"""WB1 missing effects/encoder/bootstrap cost probe; never scientific admission.',
                '"""WB1.h1 unchanged effects cost probe using corrected insertion provenance.')
    s=s.replace('from runners.drive.cards import week3_pieces_effects as effects',
                'from runners.drive.cards import week3_pieces_effects_h1 as effects')
    assert ast.dump(ast.parse(s))==ast.dump(ast.parse((root/'week3_pieces_effects_h1_pilot.py').read_text(encoding='utf8')))
