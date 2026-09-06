"""S4/S5: inventory preserved measurements; never rescore or mutate a stage.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3, 4, 5 (candidate coverage, target fills, source identity,
known answers); CONTROLS sections 5, 6. Gates: no scientific gate. Missing historical
evidence is reported explicitly; inventory coverage never implies measurement validity.
bands: descriptive counts only. Model and paid calls: none.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ARMS = {'DIR', 'DIRS', 'DIR0', 'HDIR', 'CDIR', 'SDIR', 'PULL', 'LAWR', 'RESR'}

def audit(repo: Path, out: Path):
    repo, out = repo.resolve(), out.resolve()
    for stage in (7, 8):
        if out.is_relative_to(repo / f'results/phase_2_4_stage_{stage}'):
            raise ValueError('derived output cannot be in an original stage')
    inputs, groups, gaps = {}, {}, []
    def read(p):
        p = p.resolve()
        if not p.is_relative_to(repo):
            raise ValueError(f'evidence outside repository: {p}')
        data = p.read_bytes()
        inputs[p.relative_to(repo).as_posix()] = hashlib.sha256(data).hexdigest()
        return data.decode('utf-8')
    def add(stage, cell, arm, model, rev, code, target, count, declared, source):
        helper = 'likelihood_any' if (arm == 'HDIR' and target == 'change_point') or (arm in {'DIR', 'DIRS', 'DIR0'} and target in {'next_action','next_type','changed_context'}) or (arm in {'PULL','LAWR','RESR'} and count > 6) else 'likelihood'
        key = (stage, cell, arm, model, rev, code, target, helper, declared, source)
        g = groups.setdefault(key, Counter()); g[count] += 1
    for stage in (7,8):
        root = repo / f'results/phase_2_4_stage_{stage}'
        manifest = json.loads(read(root/'QUEUE_MANIFEST.json'))
        expected = json.loads(read(root/'EXPECTED_CELLS.json'))['cells']
        declared = defaultdict(set)
        for e in expected: declared[(e['question'],e['arm'])].update(e.get('targets',[]))
        for cell in sorted(manifest):
            path = root/cell/'cases.jsonl'
            if not path.exists(): continue
            for line_no, line in enumerate(read(path).splitlines(),1):
                r = json.loads(line); arm=r.get('arm')
                if arm not in ARMS: continue
                base=(stage, cell, arm, str(r.get('model_id')),str(r.get('model_revision')),str(r.get('code_hash')))
                ref=r.get('pred_ref')
                if ref:
                    # Historical paths may belong to another clone; resolve only their stage suffix.
                    suffix=str(ref).replace('\\','/').split(f'results/phase_2_4_stage_{stage}/')[-1]
                    p=root/suffix
                    if not p.exists():
                        gaps.append({'cell':cell,'stage':stage,'arm':arm,'line':line_no,'missing_prediction':suffix});continue
                    pred=json.loads(read(p))
                    for target, dist in pred.get('targets',{}).items():
                        if arm in {'PULL','LAWR','RESR'} and target != arm.lower():continue
                        count=len(dist) if isinstance(dist,dict) else 2 if target=='stop' else None
                        if count is None:continue
                        d=declared.get((r.get('card',cell.split('/')[0]),arm),set())
                        alias={'lawr':'law','resr':'residue'}.get(target,target)
                        declared_state='declared' if alias in d else 'not_declared_or_manifest_missing'
                        if stage==8 and arm=='DIR0':
                            asked={'next_action','stop'} if cell=='E05' else {'next_action'} if cell=='X05' else {'next_action','stop','changed_context'} if cell in {'I04','I05'} else set()
                            declared_state='source_confirmed_asked' if target in asked else 'source_confirmed_fill' if cell in {'E05','X05','I04','I05'} else declared_state
                        if stage==7 and arm=='DIRS' and cell=='K16':declared_state='source_confirmed_asked'
                        add(*base,target,count,declared_state,'saved_prediction')
                elif arm in {'CDIR','SDIR'}:
                    add(*base,'decision' if arm=='CDIR' else 'next_category',4 if arm=='CDIR' else 3,'source_fixed', 'source_constant_per_aggregate_case')
                else:gaps.append({'stage':stage,'cell':cell,'arm':arm,'line':line_no,'missing_prediction_ref':True})
        # Keep imported source identity separate from historical row code hashes.
    for folder in ('runners/stage7/reader','runners/stage8/reader'):
        for p in sorted((repo/folder).glob('*.py')):read(p)
    for name in ('runners/stage7/engine_supplied.py','runners/stage7/engine_prospective.py','runners/stage8/engines.py','runners/stage8/attacks.py'):read(repo/name)
    rows=[]
    for key,counts in sorted(groups.items()):
        stage,cell,arm,model,rev,code,target,helper,declared,source=key
        if declared=='source_confirmed_fill':helper='uniform_fill_not_model_call'
        rows.append(dict(stage=stage,cell=cell,arm=arm,model=model,revision=rev,row_code_hash=code,target=target,helper=helper,declared=declared,count_source=source,candidate_counts=dict(sorted(counts.items())),grouped_rows=sum(n for k,n in counts.items() if k>6 and helper=='likelihood_any'),group_truncation_exposed_rows=sum(n for k,n in counts.items() if k>12 and helper=='likelihood_any')))
    result={'version':'readout-dependency-20260906.1','science_rescored':False,'rows':rows,'gaps':gaps,'limits':['Candidate counts are observed returned supports; unasked targets can be fills, as explicitly labeled.','Declared manifest targets are not proof of actual historical calls.','Raw component validity/top-logprob omissions were not retained; uniform output cannot diagnose their cause.','Source files read now identify the audited implementation, not missing historical capsule closures.','CDIR/SDIR counts are fixed source cardinalities for aggregated cases, not inferred per-event scores.']}
    repairs=json.loads(read(repo/'results/phase_2_4_stage_8/REPAIRS.json'))
    amendments=[]
    consequence={
      'validity1':('construction amendment','outcomes inspected before purpose cells; original construction changed'),
      'validity1b':('execution repair','failed training/filter outputs informed repair'),
      'e04repair':('measurement amendment','failed generations and feasibility judgments informed changed ruler'),
      'solform':('comparator execution repair','observed uniform SOL comparator informed repair'),
      'oom503':('incomplete coverage repair','observed endpoint failures and fragment outcomes informed repair'),
      'ordertol':('criterion amendment','YES: observed total-variation 0.0013 preceded 1e-6 to 0.01 tolerance change'),
      'ledger':('accounting repair','observed missing ledger entries informed merge/backfill'),
      'admission':('claim-grade correction','observed incorrect readmission informed composite gate enforcement')}
    for item in repairs['resets']:
        original=repo/'results/phase_2_4_stage_8'/item['cell']/item['preserved']/'verdict.json'
        current=repo/'results/phase_2_4_stage_8'/item['cell']/'verdict.json'
        old=json.loads(read(original)) if original.exists() else None
        now=json.loads(read(current)) if current.exists() else None
        kind,informed=consequence[item['tag']]
        amendments.append(dict(item,classification=kind,outcome_informed=informed,original_result=old.get('outcome') if old else item['before']['outcome'],original_verdict_retained=original.exists(),repaired_result=now.get('outcome') if now else None,original_rule='total variation <= 1e-6' if item['tag']=='ordertol' else 'see retained attempt and repair diagnosis',changed_rule='total variation <= 0.01' if item['tag']=='ordertol' else item['why'],retained_and_rerun_rows=item['why'],affected_claim=item['cell'],independent_verification='Independent numerical fixtures required; amended pass is not fresh confirmation' if item['tag']=='ordertol' else 'Original outcome preserved; deterministic administrative fixtures do not confirm scientific effects'))
    amendments.append({'cell':'G01','classification':'proposal readout amendment','original_rule':'adapted weights for purpose proposal','changed_rule':'base weights for purpose proposal','outcome_informed':True,'diagnosis':repairs['G01'],'original_result':'missed 0.5 bar per REPAIRS; separate original verdict not identified here','retained_and_rerun_rows':'Only documented registry history is asserted; no reconstructed raw attempt','affected_claim':'purpose proposal and downstream use; diagnosis only','independent_verification':'Later expansion is not untouched confirmation of readout choice'})
    out.mkdir(parents=True,exist_ok=True)
    for name,obj in [('DEPENDENCIES.json',result),('AMENDMENTS.json',{'version':'stage8-amendment-audit-20260906.1','thresholds_changed_now':False,'entries':amendments}),('INPUT_HASHES.json',inputs)]:
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'inventory_rows':len(rows),'input_files':len(inputs),'missing_evidence':len(gaps),'amendments':len(amendments),'output':str(out)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();audit(a.repo,a.out)
