"""One bounded ARIES request-to-edit adapter, using the released annotations.

DESIGN CHECK: LESSONS 2-5. NULL: an unlinked edit is unknown, not a negative;
empty predictions cannot recover useful edits. ALTERNATIVE: an annotation
licenses correspondence to an external review request, never author adoption.
Canonical schema and paragraph concatenation were read from allenai/aries
scripts/train_revision_alignment.py and aries/alignment/doc_edits.py; back
matter is concatenated as in aries/util/s2orc.py. Source SHA256s are retained.
This does not reproduce the paper's trained aligners or published scores.
"""
import json
import re
import tarfile
from collections import defaultdict
from pathlib import Path
from .common import read,freeze,filehash,digest
from .local_api import request


def jsonl(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x]


def relation(label,edit):
    if edit in label['positive_edits']:return 'linked'
    if edit in label['negative_edits']:return 'not-linked'
    return 'unlabelled'


def paragraph_text(document,indices):
    parsed=document['pdf_parse'];body=parsed['body_text']+parsed['back_matter']
    if any(type(i) is not int or i<0 or i>=len(body) for i in indices):raise ValueError('paragraph index outside canonical merged body')
    return '\n'.join(body[i]['text'] for i in indices)


def lexical(a,b):
    x=set(re.findall(r'\w+',a.lower()));y=set(re.findall(r'\w+',b.lower()))
    return len(x&y)/len(x|y) if x|y else 0.


def compile(out,card,pulse,raw):
    root=Path(card['source_root']);fetch=read(root/'FETCH.json')
    for r in fetch:
        if filehash(root/r['name'])!=r['sha256']:raise ValueError('ARIES source changed')
    labels=jsonl(root/'edit_labels_test.jsonl');docs={r['doc_id'] for r in labels}
    positives={(r['doc_id'],i) for r in labels for i in r['positive_edits']}
    if (len(docs),len(labels),len(positives))!=(42,196,131):raise ValueError('published annotation denominator mismatch')
    # Select documents before looking at prediction results; no request text is
    # sent to a provider during preparation. Full annotation counts stay visible.
    eligible_docs={r['doc_id'] for r in labels if r['positive_edits']}
    chosen=card.get('paper_ids',sorted(eligible_docs,key=lambda x:digest(['S12-ARIES',120921,x]))[:4])
    if len(set(chosen))!=len(chosen) or not set(chosen)<=eligible_docs:
        raise ValueError('invalid frozen paper roster')
    edits={r['doc_id']:r for r in jsonl(root/'paper_edits.jsonl') if r['doc_id'] in chosen}
    comments={(r['doc_id'],r['comment_id']):r for r in jsonl(root/'review_comments.jsonl') if r['doc_id'] in chosen}
    needed={r[k] for r in edits.values() for k in ('source_pdf_id','target_pdf_id')};documents={}
    with tarfile.open(root/'s2orc.tar.gz','r:gz') as archive:
        for member in archive:
            name=Path(member.name).stem
            if name in needed and member.isfile():
                if member.size>8*1024*1024 or name in documents:raise ValueError('oversize or duplicate paper parse')
                documents[name]=json.load(archive.extractfile(member))
    if set(documents)!=needed:raise ValueError('missing canonical paper versions')
    rows=[];requests=[];targets=[];exclusions=[]
    for doc in chosen:
        record=edits[doc];source=documents[record['source_pdf_id']];target=documents[record['target_pdf_id']]
        by={r['edit_id']:r for r in record['edits']}
        if len(by)!=len(record['edits']):raise ValueError('duplicate edit ids')
        own=sorted([r for r in labels if r['doc_id']==doc and r['positive_edits']],key=lambda r:digest([r['comment_id'],120921]))[:2]
        if 'selected_comments' in card:
            own=[r for r in labels if r['doc_id']==doc and r['comment_id']==card['selected_comments'][doc]]
            if len(own)!=1:raise ValueError('frozen comment missing or duplicated')
        for label in own:
            comment=comments[(doc,label['comment_id'])]
            # Explicit positives and explicit negatives only. Other edit links
            # remain unknown even though the upstream training sampler uses them.
            candidates=sorted(set(label['positive_edits']+label['negative_edits']),key=lambda i:digest([doc,label['comment_id'],i,120921]))
            eligible=[]
            for eid in candidates:
                edit=by[eid];before=paragraph_text(source,edit['source_idxs']);after=paragraph_text(target,edit['target_idxs'])
                context=dict(review_request=comment['comment'],request_context=comment['comment_context'],before=before,after=after)
                if len(json.dumps(context,ensure_ascii=True).encode())>4200:
                    exclusions.append(dict(doc=doc,comment=label['comment_id'],edit=eid,reason='frozen input-length eligibility'));continue
                eligible.append((eid,context))
            positive=[r for r in eligible if relation(label,r[0])=='linked'][:card.get('pairs_per_class',2)]
            negative=[r for r in eligible if relation(label,r[0])=='not-linked'][:card.get('pairs_per_class',2)]
            if not positive or not negative:
                exclusions.append(dict(doc=doc,comment=label['comment_id'],reason='both annotated classes required for diagnostic selection'));continue
            for eid,context in positive+negative:
                key=digest([doc,label['comment_id'],eid]);truth=relation(label,eid)
                rows.append(dict(id=key,doc=doc,comment=label['comment_id'],edit=eid,public=context,
                    target_role='C_ext',author_adoption='unobserved',lexical_overlap=lexical(context['review_request'],context['after'])))
                for direction in ('reverse-request-correspondence','forward-edit-correspondence'):
                    for method in ('direct','coherent-account'):
                        ident=digest([key,direction,method]);question=(
                            'Does this recorded delta respond to the supplied external reviewer request? The author mental goal is unknown.' if direction.startswith('reverse') else
                            'Given the external reviewer request and original passage, is the supplied revised passage a corresponding edit? This tests conditional correspondence, not recovery of a private goal.')
                        text=json.dumps(dict(evidence=context,question=question,labels=['not-linked','linked']),ensure_ascii=True)
                        req=request(text,2,'forecast' if method=='direct' else 'account')
                        requests.append(dict(id=ident,source_id=key,doc=doc,method=method,direction=direction,request=req))
                        targets.append(dict(id=ident,target=[float(truth=='not-linked'),float(truth=='linked')],target_role='C_ext',annotation_source='released test annotation; not psychological truth'))
        pulse(phase='ARIES-source-adapter',completed=len(rows))
    if not rows or {tuple(r['target']) for r in targets}!={(1.,0.),(0.,1.)}:raise ValueError('ARIES diagnostic has no class dynamic range')
    freeze(out/'SOURCE_ROWS.json',rows);freeze(out/'REQUESTS.json',requests);freeze(out/'EVALUATOR_ONLY.json',targets);freeze(out/'EXCLUSIONS.json',exclusions)
    return dict(status='complete',kind='infrastructure',released_papers=42,released_comments=196,released_positive_edits=131,
        selected_papers=len(chosen),eligible_pairs=len(rows),requests=len(requests),excluded_input_pairs=len(exclusions),
        independence='paper descriptive groups; author components unavailable; comments and edits are not independent people',
        scope='annotation-balanced diagnostic, not natural prevalence or confirmatory accuracy; both directional views classify the same supplied pair, no novel-edit generation claim',
        controls=dict(released_totals_reconciled=True,back_matter_fused=True,many_to_many_indices_preserved=True,unlinked_not_negative=True,no_private_goal_label=True,positive_negative_dynamic_range=True),
        files={n:filehash(out/n) for n in ('SOURCE_ROWS.json','REQUESTS.json','EVALUATOR_ONLY.json','EXCLUSIONS.json')})
