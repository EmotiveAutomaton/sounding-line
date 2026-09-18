"""Attach a separately retained human-log audit without modifying frozen forecasts."""
import argparse
from runners.stage11.core import PRIVATE, read, freeze, digest, canonical
from runners.stage11.viewer import TEMPLATE


def build_review(root=PRIVATE):
    original = read(root/'VIEWER_CASES.json')
    review = read(root/'MANUAL_CASE_REVIEW.json')
    if review['viewer_digest'] != digest(original):
        raise ValueError('review belongs to different cases')
    assert len(review['cases']) == len(original['cases'])
    for case, annotations in zip(original['cases'], review['cases']):
        assert case['name'] == annotations['name']
        for view, notes in annotations['views'].items():
            events = (case['forecasts'][view]['account'] or {}).get('events', [])
            assert len(notes) == len(events)
            for event, audit, note in zip(events, case['audit'][view], notes):
                assert note['event_digest'] == digest(event)
                assert note['record_relation'] in ('supported','contradicted','unresolved')
                audit.update(note)
        case['review_summary'] = annotations['summary']
    original['rule'] += ' Separate operator audit: retained source events and document changes; support badges concern the named operation, never the whole narrative. Review and endorsement remain unknown.'
    freeze(root/'REVIEWED_VIEWER_CASES.json', original)
    template = TEMPLATE.replace(
        "node('span',audit.record_relation,'badge '+audit.record_relation)",
        "node('span','Operation: '+audit.record_relation,'badge '+audit.record_relation)")
    template = template.replace(
        "if(revealed){box.append(",
        "if(revealed){box.append(node('p',audit.reason,'small'),node('p','Links: '+audit.links,'small'));box.append(")
    template = template.replace(
        "if(revealed)el('truth').append(",
        "if(revealed)el('truth').append(node('p',c.review_summary),")
    content = template.replace('__DATA__',canonical(original).replace('<','\\u003c'))
    path = root/'contribution-map-reviewed.html'
    if path.exists() and path.read_text(encoding='utf-8') != content:
        raise ValueError('reviewed viewer changed')
    path.write_text(content,encoding='utf-8',newline='\n')
    return dict(cases=len(original['cases']),path=str(path),review_digest=digest(review))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=type(PRIVATE),default=PRIVATE)
    print(build_review(parser.parse_args().root))
