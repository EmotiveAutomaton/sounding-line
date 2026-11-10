"""Complete native S3 source, encoder, collection and numerical controls."""
from pathlib import Path
import argparse,json,subprocess,sys
from . import week5_bk_s3_source as source,week5_bk_s3_encode as encoder,week5_bk_s3_analysis as analysis
from .week4_revision_utf16_h1 import apply_delta,text_of
from .timing_p6 import write_equal,gzip_equal
from .timing_census import filehash,read

def events_fixture():
    doc='A story about birds.\n';events=[dict(eventName='system-initialize',eventTimestamp=0,eventSource='api',currentDoc=doc)]
    def change(ops,t):
        nonlocal doc
        events.append(dict(eventName='text-change',eventTimestamp=t*1000,eventSource='user',textDelta={'ops':ops}))
        value,_,_=apply_delta(source.units(doc),[None]*len(source.units(doc)),{'ops':ops});doc=text_of(value)
    change([{'retain':len(source.units(doc))},{'insert':'Blue birds sing.\nBright birds rest.\nFinal birds fly.'}],1)
    change([{'retain':len(source.units(doc[:doc.index('birds sing')]))},{'insert':'tiny '}],10)
    change([{'retain':len(source.units(doc[:doc.index('birds fly')]))},{'insert':'tiny '}],11)
    change([{'retain':len(source.units(doc))},{'insert':' Future words cannot score prior alignment.'}],80)
    events.append(dict(eventName='system-finish',eventTimestamp=100000,eventSource='api'))
    return events

def world(sign):
    rows=[]
    for w in range(30):
        for i in range(12):
            for nonlocal_ in (False,True):
                value=.2*sign if nonlocal_ else -.2*sign
                rows.append(dict(writer=f'constructed-{w}',session=f'constructed-{w}',ordinal=2*i+int(nonlocal_),genre='creative',
                    size=5,decile=1,nonlocal_edit=nonlocal_,position=.1+.03*(i%4) if nonlocal_ else .8,
                    remaining=500+(i%5)*3 if nonlocal_ else 490, scores={cell:value for cell in analysis.CELLS}))
    return rows

def complete(root,names):
    write_equal(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,constructed=True,
          outputs={'output/'+name:filehash(root/'output'/name) for name in names}))

def verify_all(output,manifest):
    sourceproof=source.verify(output/'source/output',dict(constructed_source=str(output/'SOURCE_FIXTURE.json')),dict(card='BK-S3-source',mode='constructed'))
    encodeproof=encoder.verify(output/'encoder/output',dict(source_completion=str(output/'source/COMPLETE.json'),encoder_manifest=manifest),dict(card='BK-S3-encoder',phase='score',start=0,stop=2))
    collectproof=encoder.verify(output/'collection/output',dict(source_completion=str(output/'source/COMPLETE.json'),scored_completions=[str(output/'encoder/COMPLETE.json')]),dict(card='BK-S3-encoder',phase='collect'))
    models={name:analysis.verify(output/name/'analysis',dict(scored_completion=str(output/name/'prepared/COMPLETE.json')),dict(card='BK-S3',cell='primary',draws=2000,permutations=200)) for name in ('positive','negative','null')}
    return dict(source=sourceproof,encoder=encodeproof,collection=collectproof,models=models)

def run(output,manifest):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);events=events_fixture()
    write_equal(output/'SOURCE_FIXTURE.json',dict(constructed=True,events=events,reference=source.prior.extract(events)))
    source.execute(output/'source/output',dict(constructed_source=str(output/'SOURCE_FIXTURE.json')),dict(card='BK-S3-source',mode='constructed'))
    complete(output/'source',['PRIVATE_EVENTS.json.gz','SUMMARY.json'])
    assert read(output/'source/output/SUMMARY.json')['pairs']==1
    encoder.execute(output/'encoder/output',dict(source_completion=str(output/'source/COMPLETE.json'),encoder_manifest=manifest),dict(card='BK-S3-encoder',phase='score',start=0,stop=2))
    complete(output/'encoder',['PRIVATE_SCORED.json.gz','SUMMARY.json'])
    encoder.execute(output/'collection/output',dict(source_completion=str(output/'source/COMPLETE.json'),scored_completions=[str(output/'encoder/COMPLETE.json')]),dict(card='BK-S3-encoder',phase='collect'))
    for name,sign in [('positive',1),('negative',-1),('null',0)]:
        gzip_equal(output/name/'prepared/output/PRIVATE_SCORED.json.gz',world(sign));complete(output/name/'prepared',['PRIVATE_SCORED.json.gz'])
        analysis.execute(output/name/'analysis',dict(scored_completion=str(output/name/'prepared/COMPLETE.json')),dict(card='BK-S3',cell='primary',draws=2000,permutations=200))
        result=read(output/name/'analysis/SCIENCE.json');assert abs(result['point']['effect']-.4*sign)<1e-9
        assert result['direction']=={1:'positive',-1:'negative',0:'inconclusive'}[sign]
        assert result['reference']['invalid_draws']==0 and result['support_gate']
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_s3_fixture','--verify','--output',str(output),'--encoder-manifest',manifest],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    receipt=dict(passed=True,constructed=True,human_execution=False,all2000bootstrap_and200permutations=True,real_encoder=True,fresh_process=json.loads(child.stdout),
                 source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_s3_source.py','week5_bk_s3_analysis.py','week5_bk_s3_encode.py','week5_bk_s3_fixture.py')})
    write_equal(output/'COMPLETE.json',receipt);return dict(passed=True,real_encoder=True,full_fresh_replay=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--encoder-manifest',required=True);p.add_argument('--verify',action='store_true');args=p.parse_args()
    result=verify_all(args.output,args.encoder_manifest) if args.verify else run(args.output,args.encoder_manifest)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
