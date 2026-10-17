"""Pure aggregate source shape from the completed revision metadata snapshot.

DESIGN CHECK: LESSONS 2-5. NULL: missing/duplicate/reordered input refuses;
immediate duplicate hash cannot become a revert. ALTERNATIVE: known return to
an older hash is counted, with hidden identifiers and summary uncertainty explicit.
"""
import re
from collections import Counter
from runners.stage14.common import REPO,read,freeze,pins,check_pins,filehash,now

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-wiki-reference-v1'
SOURCE=REPO/'results/phase_2_4_stage_15/raw/drive-wikipedia-intake-v1'

def article_counts(rows):
    counts=Counter();editors=Counter();seen_ids=set();hashes=set();last=None;last_time=None
    for row in rows:
        if row['revid'] in seen_ids:raise ValueError('duplicate revision')
        seen_ids.add(row['revid']);counts['revisions']+=1
        if last_time is not None and row['timestamp']<last_time:raise ValueError('nonchronological revision')
        last_time=row['timestamp'];user=row.get('userid');name=row.get('user')
        if user:editors['id:'+str(user)]+=1
        elif name:editors['anonymous:'+name]+=1
        else:counts['hidden_editor']+=1
        sha=row.get('sha1')
        if sha:
            if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('invalid content SHA-1')
            counts['immediate_noop']+=int(sha==last)
            counts['identity_revert']+=int(sha in hashes and sha!=last)
            hashes.add(sha);last=sha
        else:counts['hidden_sha1']+=1;last=None
        tags=row.get('tags',[]);counts['tagged_reverted_revision']+=int('mw-reverted' in tags)
        if 'comment' not in row:counts['hidden_comment']+=1;continue
        comment=row['comment'].strip();counts['nonempty_summary']+=int(bool(comment))
        body=re.sub(r'^/\*.*?\*/\s*','',comment)
        auto=bool(set(tags)&{'mw-rollback','mw-undo'}) or bool(re.match(r'^(Undid revision|Reverted edits|Reverted revision|Automatic|Robot)\b',body,re.I))
        counts['nonautomatic_summary_heuristic']+=int(bool(body) and not auto)
    return counts,editors

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('existing reference attempt')
    complete=read(SOURCE/'COMPLETE.json')
    for name,sha in complete['outputs'].items():
        if filehash(SOURCE/name)!=sha:raise ValueError('intake output changed')
    src=[REPO/'runners/drive/wiki_reference.py',REPO/'tests/test_drive_wiki_reference.py',
        REPO/'docs/design/stage-15/drive/WIKIPEDIA_REFERENCE.md',SOURCE/'COMPLETE.json']
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(src),snapshot_outputs=complete['outputs'],provider_calls=0,scientific_admission=False))

def run():
    plan=read(ROOT/'PLAN.json');check_pins(plan['pins'])
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    for name,sha in plan['snapshot_outputs'].items():
        if filehash(SOURCE/name)!=sha:raise ValueError('snapshot changed')
    index=read(SOURCE/'INDEX.json');total=Counter();editors=Counter();per_article=[];anchors=[]
    for a in index['articles']:
        rows=[]
        for i in range(a['batches']):
            page=read(SOURCE/'responses'/f"{a['article']:03}-{i:04}.json")['query']['pages'][0]
            if page['pageid']!=a['pageid']:raise ValueError('article changed')
            rows+=page.get('revisions',[])
        if len(rows)!=a['revisions']:raise ValueError('revision count differs')
        c,e=article_counts(rows);total.update(c);editors.update(e);per_article.append(len(e))
        last=next((r for r in reversed(rows) if r.get('sha1')),None)
        anchors.append(dict(pageid=a['pageid'],title=a['title'],latest_visible_revision=last['revid'] if last else None,sha1=last['sha1'] if last else None))
    if total['revisions']!=index['revisions']:raise ValueError('total revisions differ')
    aggregate=dict(editors=len(editors),edits_per_editor=sorted(editors.values()),editors_per_article=per_article,
        summary_coverage=total['nonautomatic_summary_heuristic']/total['revisions'],revert_fraction=total['identity_revert']/total['revisions'])
    anchor=anchors[0]
    if anchor['title']!='Empathy' or not anchor['sha1']:raise ValueError('source anchor absent')
    freeze(ROOT/'T3_SOURCE.json',dict(aggregates=aggregate,counts=dict(total),articles=len(anchors),article_anchors=anchors,
        source_window_ended_at=index['source_window_ended_at'],intake_terminal_sha256=filehash(SOURCE/'COMPLETE.json'),
        request_outputs_sha256=plan['snapshot_outputs'],source_identity_kind='Wikipedia committed content SHA-1, not Git',
        summary_semantics='fixed nonautomatic-summary heuristic; raw coverage and hidden counts retained',
        full_text_history_ready=False,scientific_admission=False))
    freeze(ROOT/'T3.json',dict(source=dict(revision=anchor['sha1'],sha256=filehash(ROOT/'T3_SOURCE.json'),
        citation=f"Wikipedia API revision snapshot; Empathy anchor https://en.wikipedia.org/w/index.php?oldid={anchor['latest_visible_revision']}; content SHA-1, not Git; full 105-article snapshot bound in T3_SOURCE.json"),aggregates=aggregate))
    freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.name:filehash(p) for p in ROOT.glob('*.json')},
        scientific_admission=False,source_identity_review_required=True))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
