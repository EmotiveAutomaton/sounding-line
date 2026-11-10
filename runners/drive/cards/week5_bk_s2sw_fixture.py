"""Actual native S2.sw source, checkpoint and complete numerical fixtures."""
from pathlib import Path
import argparse, copy, json, shutil, subprocess, sys, time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_s2sw_source as source
from . import week5_bk_s2sw_analysis as analysis
from .week5_bk_s4k_fixture import seal
from .week5_bk_klicke_intake import read, write, digest
from .batch_runtime import REPO


def row(before,after,stamp,author='constructed',label='Text Production',project='constructed'):
    from runners.stage9.scholawrite import LABEL_MAP
    return dict(project=project,author=author,timestamp=stamp,**{'before text':before,'after text':after},label=label,**{'high-level':LABEL_MAP[label]})


def source_rows(authors=6):
    all_rows=[]
    for author in range(authors):
        rng=np.random.default_rng(20261102+author);current='';stamp=1000;marks=[]
        def add(after,gap=None,label='Text Production'):
            nonlocal current,stamp
            if gap is None:gap=int(1000*np.exp(rng.normal(-.1,1.1)))
            stamp+=gap;all_rows.append(row(current,after,stamp,str(author),label,str(author//2)));current=after
        for i in range(60):
            token=f'unit{i:03d}';marks.append(token)
            add(current+token+' ')
            mean=(-1.2,0.,1.2)[i%3]
            add(current+'begins ',int(1000*np.exp(rng.normal(mean,.65))))
            add(current+'here. ',int(1000*np.exp(rng.normal(mean,.65))))
            add(current)
        for i,token in enumerate(marks):
            if i%4 in (0,1):add(current.replace(token,token.upper(),1),None,'Clarity')
        add(current,150000)
    return all_rows


def numerical_records(kind='positive',authors=8):
    result=[]
    for a in range(authors):
        units=[]
        for flow in (0,1):
            success=10 if kind=='null' else 12+a%4 if flow else 4-a%4
            if kind=='negative':success=20-success
            for j in range(20):
                future=[dict(ordinal=flow*100+j,lag_seconds=180 if j%2 else 60,label='Clarity',
                    visible_sentence_nonlocal=True,visible_paragraph_nonlocal=True)] if j<success else []
                units.append(dict(timing_state='eligible released-change proxy',class_='flow_proxy' if flow else 'hesitant_proxy',
                    observed_later_rows=2,remaining_seconds=300,session=str(a),later_edits=future,
                    controls={k:0. for k in source.CONTROL_NAMES}))
                units[-1]['class']=units[-1].pop('class_')
        result.append(dict(author=str(a),project=str(a//2),units=units))
    return result


def checks():
    rows=[row('', 'A\U0001f600',1000),row('A\U0001f600','A\U0001f600 beta.',1500),row('A\U0001f600 beta.','A\U0001f600 beta.',1600),
          row('A\U0001f600 beta.','A\U0001f600 beta. Next sentence.',1800),row('A\U0001f600 beta. Next sentence.','Changed. Next sentence.',3000,'constructed','Clarity'),
          row('Changed. Next sentence.','Gone. Next sentence.',4000,'constructed','Coherence'),row('Gone. Next sentence.',' Next sentence.',5000,'constructed','Structural')]
    for i,r in enumerate(rows):r.update(ordinal=i,timestamp_count=1)
    units=source.project_segment(rows,'a','p',0,'end',lambda:None)
    assert len(units)==2 and units[0]['text']=='A\U0001f600 beta.' and units[0]['gaps_seconds']==[.5]
    assert [r['ordinal'] for r in units[0]['later_edits']]==[4,5,6]
    assert units[0]['later_edits'][0]['visible_sentence_nonlocal']
    assert units[1]['later_edits']==[]
    mutated=copy.deepcopy(rows)
    for r in mutated:r['label']='Idea Generation';r['high-level']='PLANNING'
    changed=source.project_segment(mutated,'a','p',0,'end')
    assert [(u['ordinals'],u['gaps_seconds'],[v['ordinal'] for v in u['later_edits']]) for u in changed]==[(u['ordinals'],u['gaps_seconds'],[v['ordinal'] for v in u['later_edits']]) for u in units]
    # Pure insertion exactly on a completed span boundary cannot revise it.
    assert not any(r['ordinal']==3 for r in units[0]['later_edits'])
    broken=copy.deepcopy(rows);broken[3]['before text']='different view'
    assert source.segment_rows(broken)[1]['discontinuous visible editor text']>=1
    tie=copy.deepcopy(rows);tie[1]['timestamp_count']=2
    assert source.segment_rows(tie)[1]['edge incident to ambiguous timestamp block']==2
    from runners.stage9.scholawrite import boundary
    a=row('','text',0);b=row('text','text more',1800000)
    assert boundary(a,b) is None;b['timestamp']+=1;assert boundary(a,b)=='over thirty-minute gap'
    single=source.project_author('p','a',[dict(row('','only',1000),ordinal=0,timestamp_count=1)])
    assert single['units'][0]['observed_later_rows']==0 and single['units'][0]['hesitancy'] is None
    values={}
    for kind in ('positive','negative','null'):
        _,bundle,summary=analysis.initial(numerical_records(kind),'overlap')
        values[kind]=summary['conditional_estimate']['effect']
        # Dense writer-intercept GLS with fixed arbitrary positive variance.
        z=bundle['z'];g=bundle['g'];design=np.column_stack([z,np.eye(len(bundle['writers']))[g]])
        covariance=np.eye(len(g))+.7*(g[:,None]==g[None,:])
        beta=np.linalg.solve(design.T@np.linalg.solve(covariance,design),design.T@np.linalg.solve(covariance,bundle['y']))
        assert np.isclose(beta[0]/bundle['scale'][0],values[kind],atol=1e-12)
    assert abs(values['positive']-.55)<1e-12 and abs(values['negative']+.55)<1e-12 and abs(values['null'])<1e-12
    alias=numerical_records()
    for author in alias:
        for u in author['units']:u['controls']['log_words']=int(u['class']=='flow_proxy')
    _,bundle,summary=analysis.initial(alias,'overlap');assert bundle is None and 'aliased' in summary['reason']
    return dict(unicode_and_deletion_lineage=True,annotation_independent=True,boundary_insertion_not_revision=True,
        discontinuity_and_ambiguous_edges_censored=True,thirty_minute_boundary_exact=True,last_span_censored=True,
        signed_and_null_arithmetic=True,dense_gls_oracle=True,aliased_predictor_refused=True)


def fresh(root,phase):
    run=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,'--output',str(root),'--replay',phase],capture_output=True,text=True)
    if run.returncode:raise RuntimeError(run.stderr[-3000:])
    result=json.loads(run.stdout);cost=result.pop('_process_cpu_seconds');write(root/'costs'/(phase+'.json'),dict(cpu_seconds=cost));return result


def run(root):
    root.mkdir(parents=True,exist_ok=False);start=time.process_time()
    with threadpool_limits(limits=1):known=checks()
    write(root/'raw/rows.json',source_rows());(root/'raw/salt.bin').write_bytes(bytes(range(32)))
    inputs=dict(fixture=str(root/'raw/rows.json'),identity_salt=str(root/'raw/salt.bin'))
    config=dict(card='BK-S2.sw-source',mode='constructed',max_new_draws=1)
    first=source.execute(root/'pause',inputs,config);assert first['status']=='yielded' and first['new_authors']==1
    before={p.relative_to(root/'pause').as_posix():digest(p) for p in (root/'pause').rglob('*') if p.is_file()}
    shutil.copytree(root/'pause',root/'source/output');last=source.execute(root/'source/output',inputs,dict(config,max_new_draws=6));assert last['new_authors']==5
    write(root/'source/REPLAY.json',dict(inputs=inputs,config=config))
    proof=fresh(root,'source');assert proof['new_authors']==6;seal(root/'source','runners.drive.cards.week5_bk_s2sw_source',inputs,config,proof)
    assert before=={p.relative_to(root/'pause').as_posix():digest(p) for p in (root/'pause').rglob('*') if p.is_file()}
    for cell in analysis.CELLS:
        ai=dict(source_complete=str(root/'source/COMPLETE.json'));ac=dict(card='BK-S2.sw',cell=cell,mode='constructed',max_new_draws=110 if cell=='overlap' else 20)
        attempt=root/cell;first=analysis.execute(attempt,ai,ac)
        if cell=='overlap':assert first['status']=='yielded' and first['new_draws']==110
        if first['status']=='yielded':analysis.execute(attempt,ai,dict(ac,max_new_draws=2200))
        write(attempt/'REPLAY.json',dict(inputs=ai,config=ac));proof=fresh(root,cell)
        assert proof['all_draws_recomputed'] and proof['new_draws']==(2200 if cell=='overlap' else 400)
        assert read(attempt/'SUMMARY.json')['support_gate'] is False
    # Native execute and verify owner-yield paths, plus immutable-source refusal.
    for phase in ('source','overlap'):
        base=root/phase/('output' if phase=='source' else '');target=root/('yield-'+phase);shutil.copytree(base,target)
        write(target/'YIELD_REQUEST.json',dict(reason='constructed owner request'))
        data=read(root/phase/'REPLAY.json');module=source if phase=='source' else analysis
        assert module.execute(target,data['inputs'],data['config'])['status']=='yielded'
        assert module.verify(target,data['inputs'],data['config'])['status']=='yielded'
    false=root/'tampered';shutil.copytree(root/'source/output',false);path=false/'authors/000.json.gz';changed=read(path);changed['rows']+=1;path.unlink();write(path,changed)
    try:source.verify(false,inputs,config)
    except ValueError:pass
    else:raise AssertionError('Changed author projection passed')
    changed_inputs=dict(inputs,identity_salt=str(root/'raw/other-salt.bin'))
    Path(changed_inputs['identity_salt']).write_bytes(bytes(reversed(range(32))))
    try:source.execute(root/'pause',changed_inputs,config)
    except ValueError:pass
    else:raise AssertionError('Changed source identity input passed')
    false=root/'tampered-draw';shutil.copytree(root/'overlap',false)
    path=false/'draws/00000.json';changed=read(path);changed['value']+=.1;path.unlink();write(path,changed)
    data=read(root/'overlap/REPLAY.json')
    try:analysis.verify(false,data['inputs'],data['config'])
    except ValueError:pass
    else:raise AssertionError('Changed numerical draw passed')
    known.update(actual_source_pause_resume=True,fresh_complete_source=True,complete_primary_and_four_companions=True,
        fresh_all_numerical_draws=True,owner_execute_and_verify_yield=True,tampered_source_refused=True,
        changed_source_inputs_refused=True,tampered_draw_refused=True,predecessor_unchanged=True)
    proof=dict(passed=True,constructed=True,checks=known,cpu_seconds=time.process_time()-start+sum(read(p)['cpu_seconds'] for p in (root/'costs').glob('*.json')),
        source_sha256={str(Path(m.__file__).relative_to(REPO)):digest(m.__file__) for m in (source,analysis)},fixture_sha256=digest(__file__))
    write(root/'FIXTURE.json',proof);return dict(passed=True,proof=str(root/'FIXTURE.json'),cpu_seconds=proof['cpu_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--replay');a=p.parse_args()
    if a.replay:
        data=read(a.output/a.replay/'REPLAY.json');module=source if a.replay=='source' else analysis
        path=a.output/a.replay/('output' if a.replay=='source' else '')
        result=module.verify(path,data['inputs'],data['config']);result['_process_cpu_seconds']=time.process_time();print(json.dumps(result))
    else:
        try:print(json.dumps(run(a.output.resolve())))
        except BaseException as error:
            if a.output.exists():write(a.output/'FAILED_FIXTURE.json',dict(error_type=type(error).__name__,
                parent_process_cpu_seconds=time.process_time(),fixture_sha256=digest(__file__)))
            raise
