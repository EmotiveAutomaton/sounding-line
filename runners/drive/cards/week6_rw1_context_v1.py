"""Finite prospective time/place marker; semantic qualification stays separate.

DESIGN CHECK: LESSONS 2,3. Known literal positives and negatives are fixtures.
Unmatched plans count as unknown-or-absent, not proved nonspecific. Two builders
must genuinely review the same 200 sentences. Unknown hand labels count as
disagreements; they never shrink the fixed agreement denominator.
"""
import re
from . import week6_rw1_intake_v1 as plan

VERSION = 'RW1-time-place-literal-v1'
TIME_WORDS = ('today', 'tomorrow', 'tonight', 'monday', 'tuesday', 'wednesday',
              'thursday', 'friday', 'saturday', 'sunday')
MONTHS = ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
          'september', 'october', 'november', 'december')
TIME_PHRASES = ('next week', 'next month', 'next year', 'this week', 'this weekend',
                'next weekend', 'in the morning', 'in the afternoon', 'in the evening',
                'at noon', 'at midnight')
PLACE_PHRASES = ('at home', 'stay home', 'go home', 'from home', 'at work', 'to work',
                 'at school', 'to school', 'at university', 'to university',
                 'at hospital', 'to hospital', 'at the hospital', 'to the hospital',
                 'at the shop', 'to the shop', 'at the shops', 'to the shops',
                 'at the supermarket', 'to the supermarket', 'at the park', 'to the park',
                 'at the office', 'to the office', 'in the garden', 'to the garden',
                 'in my garden', 'at my parents', 'to my parents', 'at the bank', 'to the bank')
TIME = re.compile(r'\b(?:' + '|'.join(re.escape(x) for x in (*TIME_WORDS, *TIME_PHRASES))
    + r')\b|\b(?:in|during|by|before|after)\s+(?:' + '|'.join(MONTHS) + r')\b'
    + r'|\b(?:' + '|'.join(MONTHS) + r')\s+\d{1,2}\b'
    + r'|\b\d{1,2}\s+(?:' + '|'.join(MONTHS) + r')\b'
    + r'|\b(?:at|by|before|after)\s+(?:[01]?\d|2[0-3])(?::[0-5]\d)?\s*(?:am|pm)\b'
    + r'|\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', re.I)
PLACE = re.compile(r'\b(?:' + '|'.join(re.escape(x) for x in PLACE_PHRASES) + r')\b', re.I)


def classify(sentence):
    is_plan = plan.plan_candidate(sentence)
    when = is_plan and TIME.search(sentence) is not None
    where = is_plan and PLACE.search(sentence) is not None
    return {'plan': is_plan, 'literal_time': when, 'literal_place': where,
            'literal_named': when or where, 'unknown_or_absent': is_plan and not (when or where)}


def qualification(sentences, forms):
    if len(sentences) != 200 or len(forms) != 2: raise ValueError('Same 200 sentences and two builders required')
    hand = []; agreements = []; unknown = []
    for manual, listed in forms:
        a = [r['time_place_label'] for r in manual['annotations']]
        b = [r['time_place_label'] for r in listed['annotations']]
        if len(a) != 200 or len(b) != 200: raise ValueError('All 200 time/place labels required')
        if any(type(v) is not bool and v != 'unknown' for v in a): raise ValueError('Boolean or unknown hand labels required')
        if any(type(v) is not bool for v in b): raise ValueError('Boolean literal labels required')
        if b != [classify(s['text'])['literal_named'] for s in sentences]:
            raise ValueError('Time/place list labels differ from the pinned rule')
        agreements.append(sum(type(x) is bool and x == y for x, y in zip(a, b, strict=True)) / 200)
        unknown.append(sum(x == 'unknown' for x in a)); hand.append(a)
    between = sum(type(a) is bool and type(b) is bool and a == b for a, b in zip(*hand, strict=True)) / 200
    return {'status': 'reviewable' if min(*agreements, between) >= .80 else 'instrument-unqualified',
        'threshold': .80, 'list_hand_agreements': agreements, 'hand_hand_agreement': between,
        'unknown_hand_counts': unknown, 'hand_positive_counts': [sum(x is True for x in a) for a in hand],
        'literal_positive_count': sum(classify(s['text'])['literal_named'] for s in sentences),
        'literal_unknown_or_absent_plan_count': sum(classify(s['text'])['unknown_or_absent'] for s in sentences),
        'production_admitted': False, 'owner_identity_and_semantic_review_required': True}
