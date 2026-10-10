"""SL10 gold denominator and conservative paper exposure census.

DESIGN CHECK: LESSONS 2-5. NULL: unknown archive coverage cannot certify freshness.
ALTERNATIVE: released denominators and positive prior-preparation witnesses agree.
Silver is never promoted to gold. No requests or psychological inference occur.
"""
from .common import REPO,read,filehash,freeze
from runners.stage12.aries import jsonl

def run(card,out,raw,tick):
    root=REPO/'results/phase_2_4_stage_12/raw/inputs/aries-v1'
    for r in read(root/'FETCH.json'):
        if filehash(root/r['name'])!=r['sha256']:raise ValueError('source drift')
    labels=jsonl(root/'edit_labels_test.jsonl');papers={r['doc_id'] for r in labels}
    edits={(r['doc_id'],e) for r in labels for e in r['positive_edits']}
    linked=sum(bool(r['positive_edits']) for r in labels)
    if (len(papers),len(labels),len(edits))!=(42,196,131):raise ValueError('gold denominator drift')
    # Paper prose states 85; this pinned release has 87 positive-label comments.
    # Preserve and expose the discrepancy; do not silently redefine its target.
    witnesses={p:[] for p in papers};pins={};inspected=0
    for stage in ('12','13'):
        for path in (REPO/f'results/phase_2_4_stage_{stage}/raw').rglob('SOURCE_ROWS.json'):
            value=read(path)
            if not isinstance(value,list):continue
            present={r.get('doc') for r in value if isinstance(r,dict)} & papers
            if present:
                rel=str(path.relative_to(REPO)).replace('\\','/');pins[rel]=filehash(path)
                for p in present:witnesses[p].append(rel)
            inspected+=1
    freeze(out/'PAPER_LEDGER.json',[dict(paper=p,status='PRIOR_SOURCE_PREPARATION_WITNESSED' if witnesses[p] else 'UNKNOWN_NOT_CERTIFIED_FRESH',witnesses=witnesses[p]) for p in sorted(papers)])
    freeze(out/'SOURCE_PINS.json',pins)
    freeze(out/'SUMMARY.json',dict(gold_papers=42,gold_comments=196,positive_edits=131,comments_with_positive_labels=linked,paper_reported_text_linked_comments=85,linked_comment_discrepancy_unresolved=linked!=85,prior_prepared_papers=sum(bool(v) for v in witnesses.values()),unknown_papers=sum(not v for v in witnesses.values()),certified_unexposed_gold_papers=0,source_ledgers_inspected=inspected,H05_disposition='descriptive only until a complete exposure exclusion audit certifies at least 20 untouched gold papers',silver='training or separately labelled evaluation only'))
