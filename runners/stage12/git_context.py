"""A source-bound Git operation consumer and a separate exact replay fixture.

DESIGN CHECK: LESSONS 2-5. NULL: matching endpoint bytes do not identify rename,
copy or delete/recreate history. ALTERNATIVE: explicit parent deltas and recorded
paths recover file operations; a commit message remains reported context, not
cognitive authorship. Known replay truth is separate from real repository data.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from .common import REPO,read,freeze,filehash,native_command,digest
import json

def git(args,cwd=REPO):
    return native_command(['git','-c','core.autocrlf=false','-c','pack.threads=1',*args],cwd=cwd,timeout=60)

def changed(parent,commit,cwd=REPO):
    text=git(['diff-tree','--no-commit-id','--name-status','-r','-M','-C','--find-copies-harder',parent,commit],cwd).decode('utf-8')
    return [dict(status=parts[0],paths=parts[1:]) for line in text.splitlines() if (parts:=line.split('\t'))]

def blob(commit,path,cwd=REPO):
    return git(['show',commit+':'+path],cwd)

def fixture(root):
    root.mkdir(parents=True,exist_ok=False);git(['init','--initial-branch=main'],root)
    def commit(message):
        git(['add','--all'],root)
        git(['-c','user.name=Stage12 controlled fixture','-c','user.email=fixture@invalid',
             'commit','-m',message,'--no-gpg-sign'],root)
        return git(['rev-parse','HEAD'],root).decode().strip()
    for i in range(8):(root/f'unit{i}.txt').write_text(''.join(f'unit {i} line {j}\n' for j in range(30)),encoding='utf-8')
    first=commit('Construct the eight source units')
    for i in range(4):
        p=root/f'unit{i}.txt';p.write_text(p.read_text()+'new supported line\n',encoding='utf-8')
    second=commit('Append recorded material to four units')
    (root/'unit4.txt').rename(root/'renamed4.txt')
    (root/'copy5.txt').write_bytes((root/'unit5.txt').read_bytes())
    (root/'unit6.txt').unlink()
    (root/'new.txt').write_text('new independent unit\n',encoding='utf-8')
    third=commit('Rename, copy, delete and create; no mental-state claim')
    rows=changed(first,second,root)+changed(second,third,root)
    # Eight initial creations plus eight subsequent opportunities.
    known=[dict(status='A',paths=[f'unit{i}.txt']) for i in range(8)]+rows
    if len(known)!=16:raise ValueError('fixture operation denominator changed')
    statuses=sorted(r['status'][0] for r in rows)
    if statuses!=sorted(['M']*4+['R','C','D','A']):raise ValueError('Git did not recover the planted file operations')
    # Replay each version from its tree and verify Git's own blob identity using
    # an independent byte construction. SHA-1 here is the native Git object ID.
    checks=[]
    for commit_id in (first,second,third):
        for line in git(['ls-tree','-r',commit_id],root).decode().splitlines():
            metadata,name=line.split('\t');expected=metadata.split()[2];data=blob(commit_id,name,root)
            checks.append(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected)
    if not all(checks):raise ValueError('byte-level Git replay failed')
    return dict(commits=[first,second,third],opportunities=known,blob_replays=len(checks),
        endpoint_alias=dict(first='rename the file',second='delete then create identical bytes',
                            consequence='same endpoint; history necessary to identify the recorded operation'),
        controls=dict(blob_reconstruction=True,rename_copy_delete_distinguished=True,endpoint_cannot_identify_history=True))

def run(out,card,pulse,raw):
    rows=[]
    for commit in card['candidate_ids']:
        parents=git(['rev-list','--parents','-n','1',commit]).decode().strip().split()[1:]
        if not parents:continue
        message=git(['show','-s','--format=%B',commit]).decode('utf-8',errors='strict')
        for parent in parents:
            for operation in changed(parent,commit):
                if len(rows)>=card['opportunities']:break
                rows.append(dict(commit=commit,parent=parent,merge_parents=len(parents),operation=operation,
                    stated_context=message,context_status='reported; adoption and attention unobserved',
                    endpoint_only='history ambiguous',diff_condition='recorded paths and byte changes',
                    message_condition='same observed operation plus stated context; no upgraded causal attribution'))
        pulse(completed=len(rows),total=card['opportunities'])
        if len(rows)>=card['opportunities']:break
    if len(rows)!=card['opportunities']:raise ValueError('frozen owned-history opportunity population is incomplete')
    checked=fixture(out/'controlled-git')
    freeze(out/'OWNED_HISTORY.json',rows);freeze(out/'CONTROLLED_REPLAY.json',checked)
    return dict(status='complete',kind='infrastructure',owned_operation_opportunities=len(rows),
        fixture_opportunities=len(checked['opportunities']),fixture_blob_replays=checked['blob_replays'],
        views=['endpoint','parent-diff','parent-diff-plus-stated-message'],
        target='recorded file operations and context; neural interpretation remains a separate contrast',
        controls=checked['controls'],files={n:filehash(out/n) for n in ('OWNED_HISTORY.json','CONTROLLED_REPLAY.json')})


def merge_fixture(root):
    """Actual two-parent merge, partial history and distinct author/committer."""
    checked=fixture(root);base=checked['commits'][-1]
    git(['checkout','-b','side'],root)
    (root/'side.txt').write_text('side contribution\n',encoding='utf-8')
    def commit(message):
        git(['add','--all'],root)
        git(['-c','user.name=Fixture integrator','-c','user.email=integrator@invalid',
             'commit','--author=Fixture author <author@invalid>','--no-gpg-sign','-m',message],root)
        return git(['rev-parse','HEAD'],root).decode().strip()
    side=commit('Side source record')
    git(['checkout','main'],root)
    (root/'main.txt').write_text('main contribution\n',encoding='utf-8');main=commit('Main source record')
    git(['-c','user.name=Fixture integrator','-c','user.email=integrator@invalid',
         'merge','--no-ff','--no-gpg-sign','side','-m','Integrate both parents'],root)
    merge=git(['rev-parse','HEAD'],root).decode().strip()
    parents=git(['rev-list','--parents','-n','1',merge],root).decode().split()[1:]
    if parents!=[main,side]:raise ValueError('merge parents lost')
    deltas={p:changed(p,merge,root) for p in parents}
    if deltas[main]!=[dict(status='A',paths=['side.txt'])] or deltas[side]!=[dict(status='A',paths=['main.txt'])]:
        raise ValueError('merge parent-relative truth failed')
    identity=git(['show','-s','--format=%an|%cn',side],root).decode().strip()
    if identity!='Fixture author|Fixture integrator':raise ValueError('author/committer roles conflated')
    partial=root.parent/(root.name+'-shallow')
    git(['clone','--depth','1','--no-local',root.resolve().as_uri(),str(partial)],root.parent)
    shallow=git(['rev-parse','--is-shallow-repository'],partial).decode().strip()=='true'
    visible=git(['rev-list','--parents','-n','1','HEAD'],partial).decode().split()
    if not shallow or len(visible)!=1:raise ValueError('missing-parent fixture not actually shallow')
    raw_parents=[x[7:] for x in git(['cat-file','-p','HEAD'],partial).decode().splitlines() if x.startswith('parent ')]
    if raw_parents!=parents:raise ValueError('retained parent identities differ')
    return dict(base=base,parents=parents,parent_diffs=deltas,visible_commit_count=1,
        missing_parent_history=raw_parents,history_status='unavailable, not absent operations',
        controls=dict(two_parent_merge=True,parent_relative_diffs=True,author_committer_separate=True,actual_shallow_missing_history=True))


def compile_reader(out,card,pulse,raw):
    from .local_api import request
    reference=fixture(out/'controlled-git');merge=merge_fixture(out/'merge-git')
    root=out/'controlled-git';commits=reference['commits'];rows=[];targets=[];cheap=[]
    labels=['create','modify','delete','rename','copy','unknown'];names=dict(A='create',M='modify',D='delete',R='rename',C='copy')
    opportunities=[]
    for index,c in enumerate(commits):
        parent=commits[index-1] if index else None
        changes=reference['opportunities'][:8] if parent is None else changed(parent,c,root)
        for change in changes:opportunities.append((parent,c,change))
    for index,(parent,commit,operation) in enumerate(opportunities):
        status=names[operation['status'][0]];paths=operation['paths'];current=paths[-1]
        endpoint=None if status=='delete' else blob(commit,current,root).decode('utf-8')
        delta=dict(parent=parent,commit=commit,recorded_change=operation)
        message=git(['show','-s','--format=%B',commit],root).decode().strip()
        for view in ('endpoint','endpoint-diff','endpoint-diff-message'):
            evidence=dict(current_path=current,current_bytes=endpoint)
            if view!='endpoint':evidence['parent_relative_record']=delta
            if view=='endpoint-diff-message':evidence['stated_message']=message
            baseline=[float(x==(status if view!='endpoint' else 'unknown')) for x in labels]
            cheap.append(dict(source_id=str(index),view=view,probabilities=baseline,method='recorded-diff alignment or unknown without history'))
            for method in ('direct','coherent-account'):
                ident=digest(['Git',index,view,method]);text=json.dumps(dict(evidence=evidence,labels=labels,
                    question='Recover the recorded file operation. Current bytes can be compatible with multiple histories. The message is reported context, not mental ground truth.'))
                rows.append(dict(id=ident,source_id=str(index),method=method,direction=view,request=request(text,len(labels),'forecast' if method=='direct' else 'account')))
                targets.append(dict(id=ident,target=[float(x==status) for x in labels],target_role='recorded file operation'))
        pulse(phase='Git-reader-compilation',completed=index+1,total=len(opportunities))
    freeze(out/'REQUESTS.json',rows);freeze(out/'EVALUATOR_ONLY.json',targets);freeze(out/'CHEAP_BASELINE.json',cheap)
    freeze(out/'CONTROLLED_MERGE.json',merge)
    return dict(status='complete',kind='infrastructure',source_opportunities=len(opportunities),requests=len(rows),
        scope='controlled Git operation interpretation; parent diffs define recorded rename/copy conventions; real owned-history evidence is retained separately',
        controls=dict(reference['controls'],**merge['controls'],all_views_and_readers=True,endpoint_ambiguity_retained=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json','CHEAP_BASELINE.json','CONTROLLED_MERGE.json')})
