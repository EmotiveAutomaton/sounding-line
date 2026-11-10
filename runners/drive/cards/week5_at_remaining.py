"""AT2 selected-reader at-typing remainder, with full prospective population."""
from pathlib import Path
from .week5_at_source import authenticate
from .week5_at_scoring import ENGINE_MODELS
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


def produce(output,inputs,config,verifying=False):
    if set(inputs)!={'source_root','selection_root'} or config!={}:raise ValueError('Exact selected-reader remainder inputs required')
    source=authenticate(inputs['source_root'])/'output';selection=authenticate(inputs['selection_root'])/'output'
    result=read(selection/'RESULT.json')
    if result.get('card')!='AT2' or result.get('screening_only') or not result.get('selection_admissible'):
        raise ValueError('Complete primary final-context model selection required')
    models=sorted(set([result['selected_model'],*ENGINE_MODELS]));root=Path(output);root.mkdir(parents=True,exist_ok=True)
    batches=[]
    for n,item in enumerate(read(source/'INDEX.json')):
        path=source/item['file']
        if filehash(path)!=item['sha256']:raise ValueError('AT source changed')
        rows=[r for r in gzread(path)['rows'] if not r['at_typing_frozen20']]
        for offset in range(0,len(rows),256):
            name=f'batches/at_typing-{n:04d}-{offset//256:04d}.json.gz';value=rows[offset:offset+256]
            if verifying:
                if gzread(root/name)!=value:raise ValueError('Remaining at-typing source replay differs')
            else:gzip_equal(root/name,value)
            batches.append(dict(file=name,words=len(value),sha256=filehash(root/name),models=models,context='at_typing'))
    summary=dict(models=models,batches=len(batches),words=sum(b['words'] for b in batches),selection_sha256=filehash(selection/'RESULT.json'))
    if verifying:
        if read(root/'BATCHES.json')!=batches or read(root/'SUMMARY.json')!=summary:raise ValueError('Remaining at-typing roster differs')
        return dict(verified=True,complete_remaining_source=True)
    write_equal(root/'BATCHES.json',batches);write_equal(root/'SUMMARY.json',summary);return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
