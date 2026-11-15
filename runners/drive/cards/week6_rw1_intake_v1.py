"""RW1 candidate marker and receipt gate, without corpus IO or human outcomes.

DESIGN CHECK: LESSONS 2,3. Constructed lexical checks cannot satisfy the required
two independent builders' 200-sentence instrument check. Missing, overlapping or
single-builder records stay held. One marker revision is the packet's maximum.
"""
import hashlib
import json
import re

VERSION = 'RW1-plan-candidate-v1'
FIRST_PERSON = r"(?:i|we)"
PLAN = re.compile(
    r"\b(?:" + FIRST_PERSON + r"\s+(?:will\b|(?:am|are)\s+going\s+to\b|plan\s+to\b|"
    r"decided\s+to\b|intend\s+to\b|have\s+arranged\b)|"
    r"(?:i|we)['’]ll\b|i['’]m\s+going\s+to\b|we['’]re\s+going\s+to\b|"
    r"(?:i|we)['’]ve\s+arranged\b)", re.I)


def plan_candidate(sentence):
    """Literal list candidate, not a qualified semantic plan annotation.

    Negated, hypothetical, quoted and non-agentive future phrases are deliberately
    left for the independent check; no result-informed rule revision is allowed.
    """
    if not isinstance(sentence, str):
        raise ValueError('Sentence text required')
    return PLAN.search(sentence) is not None


def manifest_digest(sentences):
    """Bind ordered opaque IDs and sentence bytes; never emit the sentence text."""
    if len(sentences) != 200 or len({r['id'] for r in sentences}) != 200:
        raise ValueError('Exactly two hundred unique sentences required')
    serial = [{'id': r['id'], 'sha256': hashlib.sha256(r['text'].encode('utf8')).hexdigest()} for r in sentences]
    return hashlib.sha256(json.dumps(serial, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def qualification(sentences, builder_a, builder_b, *, revision=0):
    """Verify receipt completeness, not the truth of a claimed independence attestation.

    Owners must authenticate builder identities and isolated annotation provenance.
    Report both list-versus-hand agreements and hand-versus-hand agreement; all
    three must meet the packet threshold before an owner may admit the marker.
    """
    if revision not in (0, 1):
        raise ValueError('At most one marker-list revision is permitted')
    binding = manifest_digest(sentences)
    receipts = [builder_a, builder_b]
    if (not builder_a.get('builder_id') or not builder_b.get('builder_id')
            or builder_a['builder_id'] == builder_b['builder_id']):
        raise ValueError('Two distinct builder identities required')
    expected = [r['id'] for r in sentences]
    for receipt in receipts:
        if receipt.get('manifest_sha256') != binding or receipt.get('marker_version') != VERSION:
            raise ValueError('Annotation source or candidate marker changed')
        if receipt.get('independently_annotated') is not True:
            raise ValueError('Independent-annotation attestation required')
        if receipt.get('revision') != revision or not receipt.get('provenance_sha256'):
            raise ValueError('Frozen revision and annotation provenance hash required')
        rows = receipt.get('annotations', [])
        if [r['id'] for r in rows] != expected:
            raise ValueError('Every ordered sentence requires one annotation from each builder')
        if any(type(r.get('by_list')) is not bool or type(r.get('by_hand')) is not bool for r in rows):
            raise ValueError('Boolean list and hand annotations required')
        if any(r['by_list'] != plan_candidate(s['text']) for r, s in zip(rows, sentences, strict=True)):
            raise ValueError('Builder list annotations differ from the pinned candidate implementation')
    agreements = [sum(r['by_list'] == r['by_hand'] for r in receipt['annotations']) / 200 for receipt in receipts]
    between = sum(a['by_hand'] == b['by_hand'] for a, b in zip(builder_a['annotations'], builder_b['annotations'], strict=True)) / 200
    passed = min(*agreements, between) >= .80
    return {'status': 'reviewable' if passed else 'one_revision_available' if revision == 0 else 'instrument_failed',
            'source_manifest_sha256': binding, 'marker_version': VERSION, 'revision': revision,
            'sentences': 200, 'list_hand_agreements': agreements, 'hand_hand_agreement': between,
            'threshold': .80, 'owner_identity_and_provenance_review_required': True,
            'production_admitted': False, 'human_outcomes_computed': False}
