"""Constructed complete-handler rehearsals for GO2 and GO3; no human results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import week5_go as core


def goal_history(output, manifest):
    from . import week5_go_history as go
    for sign in [-1, 0, 1]:
        old='The goal is to protect forests and preserve animal habitats.'
        new='The goal is to reduce payment latency in electronic bank transfers.'
        before, after=(old,new) if sign==1 else (new,old) if sign==-1 else (old,old)
        anchors=[{'author':str(i),'document':str(i),'old_goal':old,'new_goal':new,
                  'before':[before]*3,'after':[after]*3,'three_each':True} for i in range(120)]
        path=output/str(sign);path.mkdir(parents=True,exist_ok=True)
        core.write(path/'anchors.json',{'anchors':anchors})
        inputs={'anchors':str(path/'anchors.json'),'encoder_manifest':str(manifest)}
        config={'phase':'GO2','draws':2000}
        result=go.execute(path/'output',inputs,config)
        assert go.verify(path/'output',inputs,config)['verified']
        assert result['window']=='three before/three after' and result['draws']==2000
        assert abs(result['after_minus_before'])<1e-12 if sign==0 else sign*result['after_minus_before']>.02
    receipt={'passed':True,'constructed_only':True,'actual_pinned_encoder':True,
             'signed_null_complete_execute_verify':True,'draws':2000,
             'module_sha256':core.sha(Path(go.__file__))}
    core.write(output/'FIXTURE.json',receipt);return receipt


def revision_classifier(output):
    from . import week5_go3_analysis as go
    from .week5_go_revisions import PRIMARY
    for world in ['signal','no_signal']:
        records=[]
        for user in range(40):
            for label in range(5):
                for repetition in range(5):
                    row={'editor':str(user),'post':f'{user}-{repetition}',
                         'stamp':str(repetition),'site':'constructed','reason':PRIMARY[label],
                         'type':5,'self_edit':True,'owner_known':True}
                    for j in range(14):row['diff_'+str(j)]=float(j==label) if world=='signal' else 0.
                    records.append(row)
        path=output/world;path.mkdir(parents=True,exist_ok=True)
        pd.DataFrame(records).to_parquet(path/'features.parquet',index=False)
        inputs={'features':str(path/'features.parquet')};config={'phase':'GO3','draws':2000,'self_only':True}
        result=go.execute(path/'output',inputs,config)
        assert go.verify(path/'output',inputs,config)['verified']
        assert result['draws']==2000 and result['folds']==5
        if world=='signal':assert result['interval'][0]>.05
        else:assert result['interval'][1]<.05
    receipt={'passed':True,'constructed_only':True,'actual_oof_complete_execute_verify':True,
             'signal_and_no_signal':True,'draws':2000,'module_sha256':core.sha(Path(go.__file__))}
    core.write(output/'FIXTURE.json',receipt);return receipt


def revision_habits(output):
    from . import week5_go3_analysis as go
    from .week5_go_revisions import PRIMARY
    for world in ['personal','context_only']:
        records=[]
        for user in range(48):
            # A repeatable probability vector encoded exactly as twenty edits per
            # shared post. Same-post donors see the same population in both halves.
            count=np.random.default_rng(101+user).multinomial(20,np.random.default_rng(201+user).dirichlet(np.ones(5)))
            if world=='context_only':count=np.array([4]*5)
            for post in range(4):
                for label,n in enumerate(count):
                    for _ in range(n):records.append({'editor':str(user),'post':str(post),'stamp':str(post),'site':'constructed','reason':PRIMARY[label]})
        result=go.habits(pd.DataFrame(records),2000,1000)
        assert result['status']=='ok' and result['paired_draws']==2000
        assert result['passes'] if world=='personal' else not result['passes']
        if world=='context_only':assert abs(result['real_accuracy']-1/30)<1e-12 and abs(result['context_accuracy']-1/30)<1e-12
        core.write(output/(world+'.json'),result)
    receipt={'passed':True,'constructed_only':True,'three_role_personal_context_worlds':True,
             'conditional_permutations':1000,'draws':2000,'module_sha256':core.sha(Path(go.__file__))}
    core.write(output/'FIXTURE.json',receipt);return receipt


def reader_pipeline(output,manifest):
    from . import week5_go1_pipeline as go
    rows=[{'repository':'eips','type':'Standards Track','category':'Core','author':str(i),'document':str(i),
           'motivation':f'unique goal {i}','rest':f'unique goal {i}','specification':f'unique goal {i}','rationale':f'reason {i}'} for i in range(60)]
    core.write(output/'documents.json',{'documents':rows});inputs={'documents':str(output/'documents.json'),'encoder_manifest':str(manifest)}
    config={'phase':'GO1-score','reader':'encoder','max_new_texts':1}
    assert go.execute(output/'encoder',inputs,config)['status']=='yielded'
    config.pop('max_new_texts');assert go.execute(output/'encoder',inputs,config)['rows']==60
    assert go.verify(output/'encoder',inputs,config)['verified']
    config={'phase':'GO1-score','reader':'tfidf'};go.execute(output/'tfidf',inputs,config);assert go.verify(output/'tfidf',inputs,config)['verified']
    roster=json.loads((output/'tfidf/ALLOCATION.json').read_text('utf8'))['allocation']
    for sign in [-1,0,1]:
        directories={}
        for reader in ['tfidf','encoder','language_model']:
            p=output/f'known-{sign}'/reader;p.mkdir(parents=True,exist_ok=True);scores=np.zeros((len(roster),50))
            for i,a in enumerate(roster):
                good=(i%2==0) if reader=='tfidf' else (True if sign>0 else False if sign<0 else i%2==0)
                scores[i,a['truth_position'] if good else (a['truth_position']+1)%50]=1
            np.save(p/'scores.npy',scores);core.write(p/'ALLOCATION.json',{'allocation':roster});core.write(p/'ROWS.json',{'documents':rows})
            core.write(p/'SCORED.json',{'scores_sha256':core.sha(p/'scores.npy'),'allocation_sha256':core.sha(p/'ALLOCATION.json'),'rows_sha256':core.sha(p/'ROWS.json'),'constructed_bank':True});directories[reader]=str(p)
        out=output/f'collect-{sign}';config={'phase':'GO1-collect','draws':2000}
        result=go.execute(out,{**inputs,'readers':directories},config);assert go.verify(out,{**inputs,'readers':directories},config)['verified']
        assert abs(result['gain_over_lexical']['language_model']['estimate']-.5*sign)<1e-12
    receipt={'passed':True,'constructed_only':True,'actual_encoder_tfidf_execute_verify':True,'sealed_vector_pause_resume':True,
             'signed_null_complete_collection_2000':True,'language_model_bank':'constructed numerical fixture; selected LM remains AT2-dependent','module_sha256':core.sha(go.__file__)}
    core.write(output/'FIXTURE.json',receipt);return receipt
