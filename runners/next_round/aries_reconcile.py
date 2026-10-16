"""R5 descriptive denominator audit; no inference or fresh-data admission.

DESIGN CHECK: LESSONS 2-5 read 2026-10-14. NULL: absent/duplicated records,
invalid paragraph indices or changed source pins refuse reconciliation.
ALTERNATIVE: count raw labels and explicitly named canonical filters separately.
Never tune a filter to force the paper count, or treat unlabelled as negative.
"""
import json
from pathlib import Path
import tarfile

from runners.stage14.common import REPO, read, freeze, filehash, now
from runners.stage12.aries import jsonl, paragraph_text


def flags(before, after, source_indices):
    return dict(raw=True, nonidentical=before != after,
                canonical_min100=len(before + after) >= 100 and before != after,
                source_diff=bool(source_indices) and before != after,
                full_addition=not source_indices)


def run():
    source = REPO / 'results/phase_2_4_stage_12/raw/inputs/aries-v1'
    out = REPO / 'results/phase_2_4_stage_15/raw/r5-denominators-v1'
    out.mkdir(parents=True, exist_ok=False)
    pins = {r['name']: r['sha256'] for r in read(source / 'FETCH.json')}
    if any(filehash(source / k) != v for k, v in pins.items()):
        raise ValueError('source drift')
    labels = jsonl(source / 'edit_labels_test.jsonl')
    keys = {(r['doc_id'], r['comment_id']) for r in labels}
    if len(keys) != len(labels):
        raise ValueError('duplicate paper/comment identity')
    papers = {r['doc_id'] for r in labels}
    edits = {r['doc_id']: r for r in jsonl(source / 'paper_edits.jsonl') if r['doc_id'] in papers}
    if set(edits) != papers:
        raise ValueError('missing paper edits')
    needed = {r[k] for r in edits.values() for k in ('source_pdf_id', 'target_pdf_id')}
    documents = {}
    with tarfile.open(source / 's2orc.tar.gz', 'r:gz') as archive:
        for member in archive:
            key = Path(member.name).stem
            if key in needed and member.isfile():
                if member.size > 8 * 1024**2 or key in documents:
                    raise ValueError('oversize or duplicate canonical document')
                with archive.extractfile(member) as f:
                    documents[key] = json.load(f)
    if set(documents) != needed:
        raise ValueError('missing canonical version')
    ledger = []
    for label in labels:
        record = edits[label['doc_id']]
        by = {e['edit_id']: e for e in record['edits']}
        if len(by) != len(record['edits']):
            raise ValueError('duplicate edit id')
        details = []
        for eid in label['positive_edits']:
            e = by[eid]
            before = paragraph_text(documents[record['source_pdf_id']], e['source_idxs'])
            after = paragraph_text(documents[record['target_pdf_id']], e['target_idxs'])
            details.append(dict(edit_id=eid, source_characters=len(before), target_characters=len(after),
                                flags=flags(before, after, e['source_idxs'])))
        ledger.append(dict(paper=label['doc_id'], comment=label['comment_id'], edits=details))
    names = ('raw', 'nonidentical', 'canonical_min100', 'source_diff', 'full_addition')
    counts = {name: sum(any(e['flags'][name] for e in r['edits']) for r in ledger) for name in names}
    unique = {(r['paper'], e['edit_id']) for r in ledger for e in r['edits']}
    if (len(papers), len(labels), len(unique), counts['raw']) != (42, 196, 131, 87):
        raise ValueError('released gold denominators changed')
    summary = dict(at=now(), papers=len(papers), comments=len(labels), unique_positive_edits=len(unique),
                   linked_comments_by_explicit_filter=counts, paper_section_4_3=85,
                   scope='Descriptive paper clusters; no causal or private-goal inference.',
                   filter_note='Canonical minimum uses source plus target length, not either paragraph alone.',
                   exact_85_filters=[k for k, v in counts.items() if v == 85],
                   freshness='Unchanged: no untouched paper is certified by this audit.',
                   paper_url='https://arxiv.org/html/2306.12587v2',
                   source_pins=pins, runner_sha256=filehash(Path(__file__)))
    freeze(out / 'COMMENT_LEDGER.json', ledger)
    freeze(out / 'SUMMARY.json', summary)
    freeze(out / 'COMPLETE.json', dict(status='COMPLETE', at=now(), outputs={n: filehash(out/n) for n in ('SUMMARY.json', 'COMMENT_LEDGER.json')}))
    print(json.dumps({k: summary[k] for k in ('papers','comments','unique_positive_edits','linked_comments_by_explicit_filter','exact_85_filters')}))


if __name__ == '__main__':
    run()
