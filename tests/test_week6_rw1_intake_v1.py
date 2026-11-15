"""Constructed marker receipt checks are not actual builder qualification."""
import copy
import pytest
from runners.drive.cards import week6_rw1_intake_v1 as rw


@pytest.mark.parametrize('text', ['I will call.', 'We are going to meet.', 'I plan to leave.',
    'We decided to wait.', 'I intend to return.', 'We have arranged dinner.', "I'll call.", "I'm going to walk."])
def test_literal_first_person_list(text):
    assert rw.plan_candidate(text)


@pytest.mark.parametrize('text', ['She will leave.', 'The plan is uncertain.', 'Yesterday we walked.', 'I am worried.'])
def test_nonmarkers(text):
    assert not rw.plan_candidate(text)


def receipts():
    sentences = [{'id': str(i), 'text': 'I will call.' if i % 2 else 'Clouds pass.'} for i in range(200)]
    base = {'manifest_sha256': rw.manifest_digest(sentences), 'marker_version': rw.VERSION,
            'revision': 0, 'independently_annotated': True, 'provenance_sha256': 'constructed-proof-only',
            'annotations': [{'id': r['id'], 'by_list': rw.plan_candidate(r['text']),
                             'by_hand': rw.plan_candidate(r['text'])} for r in sentences]}
    return sentences, dict(copy.deepcopy(base), builder_id='constructed-A'), dict(copy.deepcopy(base), builder_id='constructed-B')


def test_two_receipts_are_reviewable_but_not_admitted():
    sentences, a, b = receipts()
    result = rw.qualification(sentences, a, b)
    assert result['status'] == 'reviewable'
    assert result['owner_identity_and_provenance_review_required'] and not result['production_admitted']
    b['builder_id'] = a['builder_id']
    with pytest.raises(ValueError, match='distinct'):
        rw.qualification(sentences, a, b)


def test_missing_annotation_or_changed_sentence_cannot_pass():
    sentences, a, b = receipts()
    b['annotations'].pop()
    with pytest.raises(ValueError, match='Every ordered'):
        rw.qualification(sentences, a, b)
    sentences, a, b = receipts(); sentences[0]['text'] = 'Changed.'
    with pytest.raises(ValueError, match='source'):
        rw.qualification(sentences, a, b)


def test_disagreement_can_fail_and_only_one_revision_is_available():
    sentences, a, b = receipts()
    for row in b['annotations'][:41]:
        row['by_hand'] = not row['by_hand']
    assert rw.qualification(sentences, a, b)['status'] == 'one_revision_available'
    a['revision'] = b['revision'] = 1
    assert rw.qualification(sentences, a, b, revision=1)['status'] == 'instrument_failed'
    with pytest.raises(ValueError, match='one marker-list revision'):
        rw.qualification(sentences, a, b, revision=2)
