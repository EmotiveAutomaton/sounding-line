"""Strict source labels and continuous released-edit boundaries for ScholaWrite.

DESIGN CHECK: LESSONS sections 2-5, L68/L82/L86/L173 corrections; H08/I02/X03.
NULL: a wrong label, time tie, long gap or discontinuous visible text cannot become
a valid next-edit case. ALTERNATIVE: exact after/before equality and positive time
within 30 minutes establish the next RELEASED edit within a project/author stream.
Filtered source events may intervene; this is not the next raw physical keystroke.
Labels are annotator-assigned spans, not the writer's own report. Project-scoped
author IDs cannot establish global identity. No source text/IDs in public receipts.
Bands: validated released successor or explicit exclusion, no fallback category.
"""
from collections import Counter, defaultdict
import hashlib
import time

from runners.stage9.common import REPO, ROOT, canonical, closure, digest, freeze, read

CATEGORIES = ('PLANNING','IMPLEMENTATION','REVISION')
LOCATIONS = ('first_quarter','second_quarter','third_quarter','last_quarter','no_change')
LABEL_MAP = {
    'Idea Generation':'PLANNING','Idea Organization':'PLANNING','Section Planning':'PLANNING',
    'Text Production':'IMPLEMENTATION','Object Insertion':'IMPLEMENTATION','Cross-reference':'IMPLEMENTATION',
    'Citation Integration':'IMPLEMENTATION','Macro Insertion':'IMPLEMENTATION',
    'Clarity':'REVISION','Coherence':'REVISION','Structural':'REVISION','Linguistic Style':'REVISION',
    'Visual Formatting':'REVISION','Fluency':'REVISION','Scientific Accuracy':'REVISION'}
SOURCE_COUNTS = {'Text Production':35323,'Clarity':7096,'Idea Generation':4325,'Object Insertion':2814,
                 'Structural':2269,'Coherence':2004,'Visual Formatting':1952,'Section Planning':1324,
                 'Cross-reference':1016,'Linguistic Style':962,'Fluency':863,'Citation Integration':667,
                 'Scientific Accuracy':443,'Idea Organization':310,'Macro Insertion':136}


def validate(row):
    if not {'project','author','timestamp','before text','after text','label','high-level'} <= set(row):
        raise ValueError('missing canonical source fields')
    if row['label'] not in LABEL_MAP or LABEL_MAP[row['label']] != row['high-level']:
        raise ValueError('unknown or contradictory source label')
    if not isinstance(row['before text'],str) or not isinstance(row['after text'],str):
        raise ValueError('nontext editor state')
    if not isinstance(row['timestamp'],int) or isinstance(row['timestamp'],bool):
        raise ValueError('invalid timestamp')


def boundary(previous, following):
    if following is None: return 'end of released author stream'
    if (previous['project'],previous['author']) != (following['project'],following['author']):
        return 'different project or source-scoped author'
    if previous.get('timestamp_count',1) != 1 or following.get('timestamp_count',1) != 1:
        return 'edge incident to ambiguous timestamp block'
    delta = following['timestamp']-previous['timestamp']
    if delta <= 0: return 'ambiguous or reversed timestamp'
    if delta > 1800000: return 'over thirty-minute gap'
    if previous['after text'] != following['before text']: return 'discontinuous visible editor text'
    return None


def location(before, after):
    if before == after:return 'no_change'
    first = next((i for i,(a,b) in enumerate(zip(before,after)) if a!=b), min(len(before),len(after)))
    return LOCATIONS[min(3,4*first//max(1,len(before)))]


def visible(record, texts, view):
    if not record['usable']:raise ValueError('no validated released successor')
    if view == 'artifact':return {'document':texts[record['after']]}
    if view == 'record':
        return {'document':texts[record['after']], 'previous_document':texts[record['before']],
                'previous_category':record['category'], 'previous_location':record['location']}
    raise ValueError('unregistered next-edit view')


def raw_inputs():
    """Original released-row closure and preparation contract, without writes."""
    source=REPO/'results/scholawrite/dataset'
    identity={'source_files':closure([source/'all_sorted',source/'dataset_dict.json']),
              'code':closure([REPO/'runners/stage9'/n for n in ('scholawrite.py','common.py')]),
              'source_card':'https://huggingface.co/datasets/minnesotanlp/scholawrite',
              'source_card_checked':'2026-09-07', 'labels':'paper-author annotators assign consecutive spans; not writer-stated intention',
              'source_filtering':'artifact/multilabel/large-difference events removed by publisher',
              'view':'visible editor text, not necessarily a whole manuscript; first changed character in that view',
              'grouping':'whole project primary; author identifier scoped to project only',
              'exposure':'previously evaluated in full; no untouched reserve',
              'rights':'in-hand authorized gated research use; Apache2 metadata plus custom terms: no redistribution or reverse identification; aggregate output only'}
    return source,identity


def reconstruct(source):
    """Rebuild every released row/project and exclusion using the original rules."""
    from datasets import load_from_disk
    ds=load_from_disk(str(source));rows=ds['all_sorted'];groups=defaultdict(list);labels=Counter();high=Counter()
    for ordinal,row in enumerate(rows):
        validate(row);labels[row['label']]+=1;high[row['high-level']]+=1
        groups[(row['project'],row['author'])].append(row|{'ordinal':ordinal})
    if dict(labels)!=SOURCE_COUNTS or len(rows)!=61504:raise ValueError('source counts mismatch')
    if {k:len(ds[k]) for k in ds}!={'train':49212,'test':12292,'test_small':3238,'all_sorted':61504}:
        raise ValueError('released split counts mismatch')
    projects=defaultdict(lambda:{'texts':{},'records':[]});exclusions=Counter();categories=Counter();places=Counter();sessions=set()
    for (project,author),stream in sorted(groups.items()):
        stream.sort(key=lambda r:(r['timestamp'],r['ordinal']))
        timestamp_counts=Counter(row['timestamp'] for row in stream)
        for row in stream:row['timestamp_count']=timestamp_counts[row['timestamp']]
        project_key=digest({'scholawrite_project':project});author_key=digest({'scholawrite_project':project,'author':author})
        target=projects[project_key];session=0
        for i,row in enumerate(stream):
            if i and boundary(stream[i-1],row) is not None:session+=1
            session_key=digest({'author':author_key,'contiguous_segment':session});sessions.add(session_key)
            following=stream[i+1] if i+1<len(stream) else None;reason=boundary(row,following)
            before=digest(row['before text']);after=digest(row['after text'])
            target['texts'][before]=row['before text'];target['texts'][after]=row['after text']
            record={'key':digest({'source_row':row['ordinal']}),'source_ordinal':row['ordinal'],
                    'unit':project_key,'author':author_key,'session':session_key,'before':before,'after':after,
                    'category':row['high-level'],'fine_label':row['label'],'location':location(row['before text'],row['after text']),
                    'usable':reason is None,'exclusion':reason,'next_category':None,'next_location':None,'next_fine_label':None,
                    'next_source_ordinal':None,'gap_ms':following['timestamp']-row['timestamp'] if following else None}
            if reason is None:
                record.update({'next_category':following['high-level'],'next_fine_label':following['label'],
                               'next_location':location(following['before text'],following['after text']),
                               'next_source_ordinal':following['ordinal']})
                categories[record['next_category']]+=1;places[record['next_location']]+=1
            else:exclusions[reason]+=1
            target['records'].append(record)
    ledger=[]
    for project, payload in projects.items():
        sha=hashlib.sha256((canonical(payload)+'\n').encode('utf-8')).hexdigest()
        ledger.append({'unit':project,'path':'projects/'+project+'.json','sha256':sha,
                       'attempted':len(payload['records']),'usable':sum(r['usable'] for r in payload['records']),
                       'authors':len({r['author'] for r in payload['records']}),
                       'sessions':len({r['session'] for r in payload['records']})})
    result={'source_rows':len(rows),'attempted_next_boundaries':len(rows),'usable_next_boundaries':sum(categories.values()),
            'exclusions':dict(exclusions),'projects':len(projects),'project_scoped_author_ids':len(groups),
            'numeric_author_id_values':len({a for p,a in groups}),'global_people_count':'not inferable from project-scoped IDs',
            'contiguous_segments':len(sessions),'source_classes':dict(labels),'source_categories':dict(high),
            'target_categories':dict(categories),'target_locations':dict(places),'source_counts_match':True,
            'reserve_groups':0,'label_provenance':'annotator-assigned spans','scope':'next released edit of the same source-scoped author, with exact editor-text continuity'}
    if sum(exclusions.values())+sum(categories.values())!=len(rows):raise ValueError('attempt ledger does not reconcile')
    return dict(projects),ledger,result


def prepare():
    started=time.time();output=ROOT/'private/prepared/scholawrite-v2'
    source,identity=raw_inputs();freeze(output/'IDENTITY.json',identity)
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    projects,ledger,summary=reconstruct(source)
    for project,payload in projects.items():
        freeze(output/'projects'/(project+'.json'),payload)
    freeze(output/'LEDGER.json',ledger)
    result={'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,**summary}
    freeze(output/'COMPLETE.json',result);freeze(ROOT/'intake/SCHOLAWRITE_PREPARATION_V2.json',result)
    return result


if __name__=='__main__':
    print(prepare())
