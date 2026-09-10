"""Complete bounded CommitBench records, validated diffs and repository grouping.

DESIGN CHECK: LESSONS 2-5; H06/I02/X01. NULL: a complete API response can contain
an invalid or incomplete unified diff; reject its task use without dropping receipt.
ALTERNATIVE: each text hunk reconciles exact old/new line counts and preserves
context, paths, additions and deletions. Dataset snapshot/ranges must match exactly.
Bands: schema mismatch fails; unsupported diff excludes with a reason; valid records
retain repository/duplicate grouping. No author reconstruction or accumulation.
"""
from collections import Counter
import re
import time
from runners.stage9.common import ROOT,REPO,closure,digest,file_hash,freeze,read

PIN='1500792cd6998308da046ba72b688156b2ffa471'
FIELDS={'hash','diff','message','project','split','diff_languages'}
HUNK=re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)$')


def parse_diff(text):
    """Data-only parser. Never interprets paths as local paths or executes code."""
    if not isinstance(text,str) or not text.startswith('diff --git '):raise ValueError('not unified git diff')
    old=new=0;active=False;hunks=[];paths=[];added=[];removed=[];context=[]
    for line in text.splitlines():
        match=HUNK.match(line)
        if match:
            if old or new:raise ValueError('incomplete preceding hunk')
            old=int(match.group(2) or 1);new=int(match.group(4) or 1);active=True
            hunks.append({'old_start':int(match.group(1)),'old_count':old,'new_start':int(match.group(3)),'new_count':new})
            continue
        if active and (old or new):
            if line.startswith('\\ No newline at end of file'):continue
            if not line or line[0] not in ' +-':raise ValueError('invalid hunk body')
            if line[0] in ' -':old-=1
            if line[0] in ' +':new-=1
            if min(old,new)<0:raise ValueError('hunk exceeds declared range')
            {'+':added,'-':removed,' ':context}[line[0]].append(line[1:]);continue
        if line.startswith('\\ No newline at end of file'):continue
        if line.startswith(('--- ','+++ ')):paths.append(line[4:]);continue
        if line.startswith(('diff --git ','index ','new file mode ','deleted file mode ',
                            'old mode ','new mode ','similarity index ','rename from ','rename to ',
                            'dissimilarity index ','copy from ','copy to ')):continue
        if line.startswith(('Binary files ','GIT binary patch')):raise ValueError('binary change unsupported')
        if line:raise ValueError('unrecognized diff record')
    if old or new:raise ValueError('incomplete final hunk')
    if not hunks:raise ValueError('no textual hunk')
    return {'hunks':hunks,'paths':paths,'added':added,'removed':removed,'context':context}


def validate_page(data,header,offset,total):
    if header.get('X-Revision')!=PIN or data.get('partial') is not False or data.get('num_rows_total')!=total:
        raise ValueError('unverified snapshot or partial dataset')
    if [r['row_idx'] for r in data['rows']]!=list(range(offset,offset+100)):
        raise ValueError('incomplete page range')
    rows=[]
    for r in data['rows']:
        if r['truncated_cells']:raise ValueError('truncated record')
        row=r['row']
        if set(row)!=FIELDS or any(not isinstance(v,str) or not v for v in row.values()):raise ValueError('source row schema')
        if row['split']!='train':raise ValueError('source split changed')
        rows.append(row)
    return rows


def components(rows):
    """Whole repositories joined by exact commit/diff duplicates before splitting."""
    parent={r['project']:r['project'] for r in rows}
    def root(g):
        while parent[g]!=g:parent[g]=parent[parent[g]];g=parent[g]
        return g
    seen={}
    for r in rows:
        for key in [('commit',r['hash']),('diff',digest(r['diff']))]:
            if key in seen:
                a,b=sorted([root(r['project']),root(seen[key])]);parent[b]=a
            else:seen[key]=r['project']
    return {g:root(g) for g in parent}


def visible(row,candidates):
    if len(candidates)!=4 or len(set(candidates))!=4 or any(not isinstance(s,str) or not s for s in candidates):
        raise ValueError('four distinct complete descriptions required')
    return {'diff':row['diff'],'candidate_descriptions':list(candidates)}


def prepare():
    started=time.time();source=read(ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json');out=ROOT/'private/prepared/commitbench-v1'
    if source['pin']!=PIN or source['rows']!=1200:raise ValueError('unexpected source selection')
    all_rows=[]
    for page in source['pages']:
        receipt=page['receipt'];p=ROOT/'private/intake/objects'/receipt['sha256']
        if file_hash(p)!=receipt['sha256'] or not receipt['complete_eof']:raise ValueError('source incomplete or changed')
        all_rows.extend(validate_page(read(p),page['headers'],page['offset'],source['total_source_rows']))
    if len(all_rows)!=1200:raise ValueError('selected source count mismatch')
    groups=components(all_rows);pilot=groups[all_rows[0]['project']]
    identity={'pin':PIN,'source_slice_sha256':file_hash(ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json'),
              'sources':closure([REPO/'runners/stage9'/n for n in ('commitbench.py','common.py')]),
              'split_rule':'digest repository component modulo100:0-59train,60-79development,80-89discovery,90-99reserve; inspected first example component pilot',
              'rights':'CC-BY-NC-4.0 data, private noncommercial research; no identity reconstruction',
              'independent_unit':'repository plus exact-commit/diff-linked components; coauthor ambiguity retained',
              'scope':'released diff to stated complete change description; no transparent-intent or individual-accumulation claim'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    records=[];attempts=[];splits={};seen=set()
    for row in all_rows:
        group=groups[row['project']];unit=digest({'repository-component':group});slot=int(digest({'commitbench-split-v1':group})[:12],16)%100
        split='pilot' if group==pilot else 'train' if slot<60 else 'development' if slot<80 else 'discovery' if slot<90 else 'reserve'
        splits[unit]=split;key=digest({'commit':row['hash'],'project':row['project']});reason=None;parsed=None
        try:parsed=parse_diff(row['diff'])
        except ValueError as exc:reason=str(exc)
        if key in seen:raise ValueError('duplicate exact commit identity')
        seen.add(key);attempts.append({'key':key,'unit':unit,'split':split,'exclusion':reason})
        if reason:continue
        records.append(row|{'key':key,'unit':unit,'split':split,'source_split':row['split'],
                            'parsed':parsed,'languages':row['diff_languages'].split(','),'content_sha256':digest(row['diff'])})
    freeze(out/'ATTEMPTS.json',attempts);freeze(out/'SPLITS.json',splits)
    for lane in ['pilot','train','development','discovery','reserve']:
        freeze(out/lane/'RECORDS.json',[r for r in records if r['split']==lane])
    result={'identity_sha256':digest(identity),'source_count_matches':True,'source_rows':len(all_rows),
            'attempts':len(attempts),'usable':len(records),'excluded':dict(Counter(a['exclusion'] for a in attempts if a['exclusion'])),
            'repositories':len(groups),'repository_components':len(set(groups.values())),
            'splits':{lane:{'attempts':sum(a['split']==lane for a in attempts),'usable':sum(r['split']==lane for r in records),
                            'groups':sum(s==lane for s in splits.values())} for lane in ['pilot','train','development','discovery','reserve']},
            'files':{p.relative_to(out).as_posix():file_hash(p) for p in [out/'ATTEMPTS.json',out/'SPLITS.json']+
                     [out/lane/'RECORDS.json' for lane in ['pilot','train','development','discovery','reserve']]},
            'elapsed_seconds':time.time()-started,'completed_at':time.time(),'baseline_ready':False,
            'scientific_split_accepted':False,'limits':['slice not full repositories','no stable maker identity',
                'released sanitization retained','cross-source closure still required before scientific use']}
    freeze(out/'COMPLETE.json',result);freeze(ROOT/'intake/COMMITBENCH_PREPARATION.json',result)
    return result


if __name__=='__main__':print(prepare())
