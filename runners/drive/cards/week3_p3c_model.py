"""Pinned public P3c checkpoint intake, with no model execution.

DESIGN CHECK: LESSONS 3-5 read 2026-10-27. Null and alternative share
identical source admission. Missing files, gated/wrong revisions and hash or
size mismatches refuse; successful download does not validate predictions.
"""
import hashlib
from pathlib import Path
from runners.stage14.common import read, filehash, freeze

MODEL = 'wanyu/IteraTeR-ROBERTA-Intention-Classifier'
REVISION = 'd9e6e6ee893e9f36cbba8047b838ccbfea1c1c32'
FILES = ('README.md','config.json','merges.txt','pytorch_model.bin',
         'special_tokens_map.json','tokenizer_config.json','vocab.json')


def expected(metadata):
    if metadata['sha'] != REVISION or metadata['id'] != MODEL or metadata['private'] or metadata['gated'] is not False:
        raise ValueError('pinned public model required')
    rows={r['rfilename']:r for r in metadata['siblings']}
    if len(rows)!=len(metadata['siblings']) or not set(FILES)<=rows.keys():
        raise ValueError('complete unique model files required')
    if sum(rows[n]['size'] for n in FILES)>2*1024**3:
        raise ValueError('two-GiB intake ceiling')
    return rows


def inventory(path, metadata):
    rows=expected(metadata);out={}
    for name in FILES:
        p=Path(path)/name;r=rows[name]
        if not p.is_file() or p.stat().st_size != r['size'] or r['size']<=0:
            raise ValueError('model file size differs: '+name)
        h=filehash(p)
        if 'lfs' in r:
            if h!=r['lfs']['sha256'] or p.stat().st_size!=r['lfs']['size']:
                raise ValueError('model LFS hash differs: '+name)
        else:
            git=hashlib.sha1(b'blob '+str(r['size']).encode()+b'\0'+p.read_bytes()).hexdigest()
            if git!=r['blobId']:raise ValueError('model Git blob differs: '+name)
        out[name]=dict(bytes=r['size'],sha256=h)
    return out


def run(output,inputs,config,verification=False):
    if config!={'version':1}:raise ValueError('frozen intake config required')
    if set(inputs)!={'metadata','official_license','official_readme','source_gate','agent_labels'}:
        raise ValueError('explicit provenance and blind-label bindings required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding={k:filehash(v) for k,v in inputs.items()}
    meta=read(inputs['metadata']);expected(meta)
    if not read(inputs['source_gate'])['full_write_through'] or not read(inputs['agent_labels'])['agent_made'] or read(inputs['agent_labels'])['predictions_seen']:
        raise ValueError('prepared sources and frozen blind labels required')
    license_text=Path(inputs['official_license']).read_text(encoding='utf8')
    publisher=Path(inputs['official_readme']).read_text(encoding='utf8')
    if 'Apache License' not in license_text or 'Version 2.0' not in license_text or MODEL not in publisher:
        raise ValueError('publisher notices required')
    if (output/'SUMMARY.json').exists():
        result=read(output/'SUMMARY.json')
        if result['inputs']!=binding:raise ValueError('intake binding differs')
    elif verification:
        raise ValueError('missing complete intake')
    else:
        from huggingface_hub import snapshot_download
        snapshot_download(repo_id=MODEL,revision=REVISION,token=False,local_dir=output/'model',
            allow_patterns=list(FILES),max_workers=1)
        result=dict(model=MODEL,revision=REVISION,inputs=binding,files=inventory(output/'model',meta),
            model_executed=False,corpus_inference=False,provider_spend_cents=0,
            notices='Official linked implementation Apache-2.0; HF model card has no separate license field; local research intake, no redistribution')
        freeze(output/'SUMMARY.json',result)
    if inventory(output/'model',meta)!=result['files']:raise ValueError('saved model inventory differs')
    if verification:return dict(verified=True,full_download_byte_inventory=True,model_executed=False)
    return dict(status='complete',model_executed=False,files=len(result['files']))


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
