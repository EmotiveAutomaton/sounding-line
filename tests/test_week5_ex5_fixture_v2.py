import sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_ex5_v1 as study
from runners.drive.cards import week5_ex5_fixture_v2 as fixture


def test_code_blocks_plain_text_and_codepoint_lengths():
    text, lengths = study.plain('<p>Before &amp; after</p><pre><code>x &lt; y</code></pre><p>tail <code>a+b</code></p>')
    assert text == 'Before & after [CODE_BLOCK:length=5] tail a+b'
    assert lengths == [5]
    with pytest.raises(ValueError):
        study.plain('<pre>unclosed')


def test_etree_and_independent_expat_fields_match():
    row = fixture.xml_row(Id=17, PostTypeId=1, Body='<p>Text & more</p>')
    assert study.parse_row(row) == study.parse_row(row, True)
    with pytest.raises(ValueError):
        study.parse_row(b'<row><nested/></row>')


def test_full_2000_export_immutable_resume_and_every_field_replay(tmp_path):
    assert fixture.chain(tmp_path/'supported')['passed']


def test_insufficient_site_never_substitutes_questions(tmp_path):
    assert fixture.chain(tmp_path/'unsupported', deficient=True)['passed']


def test_eligibility_requires_actual_answers_and_known_other_accepted_owner(tmp_path):
    db, _ = study.open_state(tmp_path, 'constructed'); salt = b'x'*32
    def add(public, kind, owner, parent=None, accepted=None, words=100):
        value = dict(Id=str(public), PostTypeId=str(kind), CreationDate='2020-01-01T00:00:00',
            OwnerUserId=str(owner) if owner is not None else '', Body='<p>'+'x '*words+'</p>')
        if parent is not None:
            value['ParentId'] = str(parent)
        if accepted is not None:
            value['AcceptedAnswerId'] = str(accepted)
        db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', study.project(value, 'writers', public, salt))
    for q, count, answer_owner, words in [(100, 3, 20, 80), (200, 2, 20, 100), (300, 9, 20, 100),
                                          (400, 3, 10, 100), (500, 3, None, 100), (600, 3, 20, 601)]:
        add(q, 1, 10, accepted=q+1, words=words)
        for offset in range(1, count+1):
            add(q+offset, 2, answer_owner if offset == 1 else 25, parent=q)
    chosen, counts = study.select(db, 'writers'); db.close()
    assert [r[2] for r in chosen] == ['100'] and counts['eligible'] == 1
    assert counts['self_accepted'] == 1 and counts['unknown_accepted_or_asker_owner'] == 1
    assert counts['outside_answer_count_band'] == 2 and counts['outside_body_word_band'] == 1


def test_posting_ties_use_public_numeric_id_not_score(tmp_path):
    db, _ = study.open_state(tmp_path, 'constructed')
    rows = [('writers', '1', 1, None, '3', 'question-owner', 99, 'stamp', 'Title', 'body', '[]', 1, 100),
            ('writers', '10', 2, '1', None, 'other', 999, 'same', '', 'a', '[]', 2, 1),
            ('writers', '3', 2, '1', None, 'other', -1, 'same', '', 'b', '[]', 3, 1)]
    db.executemany('INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    value = study.export_question(db, 'writers', '1'); db.close()
    assert [a['answer_id'] for a in value['answers']] == ['3', '10']
    assert value['answers'][0]['accepted'] and value['answers'][0]['final_score'] == -1
    assert value['attribution_url'] == 'https://writing.stackexchange.com/questions/1'


def test_scope_source_mutation_and_identifier_refusals(tmp_path):
    with pytest.raises(ValueError):
        study.authenticate({}, lambda: False)
    with pytest.raises(ValueError):
        study.settings({'per_site': 10})
    with pytest.raises(ValueError):
        study.positive_id('12?user=34')
    infos = fixture.sources(tmp_path/'inputs', per_site=1)
    with fixture.source_boundary(infos):
        assert study.execute(tmp_path/'out', {}, {'max_new_draws': 1})['status'] == 'yielded'
    (tmp_path/'out/posts.sqlite').write_bytes(b'changed')
    with fixture.source_boundary(infos), pytest.raises(ValueError, match='checkpoint differs'):
        study.execute(tmp_path/'out', {}, {'max_new_draws': 1})
