"""Native exact binding gate and complete collector handler on constructed rows."""
from pathlib import Path
import json
from . import week5_at_collect_v3 as card
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal
from .week5_at_scoring_v4 import score_binding,NUMERICAL_SPEC


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Binding fixture accepts no human inputs')
    root=Path(output);source=root/'constructed-source';rows=[];batches=[];bank={'constructed-model':{}}
    manifest=dict(model='constructed-model',revision='constructed-revision-1',files={});mp=root/'MANIFEST.json';write_equal(mp,manifest)
    for i in range(2):
        row=dict(row_key=str(i),writer='constructed-writer',session='constructed-session',target='constructed',final_prefix='',at_typing_prefix='',timing_supported=True,population_surprisal=1.,log_frequency=-1.,pause_seconds=1.,fast=.8)
        rows.append(row);name=f'batches/final-0000-{i:04d}.json.gz';p=source/'output'/name;gzip_equal(p,[row])
        batches.append(dict(file=name,context='final',words=1,sha256=filehash(p)))
        scored=root/f'score-{i}';out=scored/'output';bank['constructed-model'][name]=str(scored)
        write_equal(scored/'PLAN.json',dict(module='runners.drive.cards.week5_at_scoring_v4',inputs=dict(rows=str(p),model_manifest=str(mp)),config=dict(context='final',context_length=1024,max_wall_seconds=1200)))
        write_equal(out/'SUMMARY.json',dict(model='constructed-model',model_revision=manifest['revision'],context='final',context_length=1024,words=1,numerical_spec=NUMERICAL_SPEC))
        write_equal(out/'BINDING.json',dict(sha256=score_binding([row],manifest,'final',1024)))
        write_equal(out/'block-00000.json',dict(values=[dict(row_key=str(i),score=dict(surprisal_nats=1.,entropy_nats=1.))]))
        write_equal(out/'INDEX.json',[dict(row_key=str(i),file='block-00000.json',slot=0,sha256=filehash(out/'block-00000.json'))])
    gzip_equal(source/'output/sessions/session-0000.json.gz',dict(rows=rows))
    write_equal(source/'output/INDEX.json',[dict(file='sessions/session-0000.json.gz',sha256=filehash(source/'output/sessions/session-0000.json.gz'))])
    write_equal(source/'output/BATCHES.json',batches);write_equal(root/'BANK.json',bank)
    args=dict(source_root=str(source),bank_manifest=str(root/'BANK.json'));cfg=dict(context='final',context_length=1024)
    old_auth,old_original=card.authenticate,card.original.authenticate
    def fixture_auth(path):
        p=Path(path)
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Only constructed paths allowed')
        return p
    card.authenticate=card.original.authenticate=fixture_auth
    try:
        (card.verify if verifying else card.execute)(root/'collected',args,cfg)
        if len(gzread(root/'collected/ROWS.json.gz'))!=2:raise ValueError('Complete collector coverage failed')
        # Identical whole-writer projection bytes retain exact reusable scores.
        p=root/'score-0/PLAN.json';saved=p.read_bytes();copied=root/'same-source-chunk.json.gz'
        copied.write_bytes(Path(read(p)['inputs']['rows']).read_bytes())
        alternate=read(p);alternate['inputs']['rows']=str(copied)
        p.write_text(json.dumps(alternate)+'\n',encoding='utf8')
        try:card.validate(args,cfg)
        finally:p.write_bytes(saved)
        def refuses(path,changed,reason):
            previous=path.read_bytes();path.write_text(json.dumps(changed)+'\n',encoding='utf8')
            try:
                try:card.validate(args,cfg)
                except ValueError as error:
                    if reason not in str(error):raise
                else:raise ValueError('Invalid binding was accepted')
            finally:path.write_bytes(previous)
        p=root/'score-0/output/SUMMARY.json';refuses(p,dict(read(p),context_length=64),'context length differs')
        p=root/'score-0/output/BINDING.json';refuses(p,dict(sha256='changed'),'binding differs')
        p=root/'score-0/PLAN.json';v=read(p);v['config']['context_length']=64;refuses(p,v,'context length differs')
        p=root/'score-0/output/SUMMARY.json';refuses(p,dict(read(p),model_revision='different'),'revision differs')
        p=root/'score-0/PLAN.json';refuses(p,dict(read(p),module='runners.drive.cards.week5_at_scoring_v3'),'Legacy or mixed numerical')
        p=root/'score-0/output/SUMMARY.json';refuses(p,dict(read(p),numerical_spec=dict(NUMERICAL_SPEC,model_computation='float32')),'Mixed numerical')
        # An internally consistent second revision still cannot join the bank.
        changed=dict(manifest,revision='constructed-revision-2');mp2=root/'MANIFEST-2.json';write_equal(mp2,changed)
        files=[root/'score-1/PLAN.json',root/'score-1/output/SUMMARY.json',root/'score-1/output/BINDING.json'];saved=[p.read_bytes() for p in files]
        try:
            plan=read(files[0]);plan['inputs']['model_manifest']=str(mp2)
            values=[plan,dict(read(files[1]),model_revision=changed['revision']),dict(sha256=score_binding([rows[1]],changed,'final',1024))]
            for p,v in zip(files,values):p.write_text(json.dumps(v)+'\n',encoding='utf8')
            try:card.validate(args,cfg)
            except ValueError as error:
                if 'Mixed model revisions' not in str(error):raise
            else:raise ValueError('Mixed revisions accepted')
        finally:
            for p,b in zip(files,saved):p.write_bytes(b)
    finally:card.authenticate=old_auth;card.original.authenticate=old_original
    receipt=dict(fixture_only=True,actual_complete_collection=True,context_plan_and_output_checked=True,revision_checked=True,
                 mixed_revision_bank_refused=True,mixed_precision_bank_refused=True,exact_scored_source_binding=True,identical_projected_chunk_reusable=True,no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Binding fixture changed')
        return dict(verified=True,complete_binding_and_collector_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
