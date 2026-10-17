"""Local pinned reader catalogue and exact menu scoring, no remote model code.

DESIGN CHECK: LESSONS 3-5. NULL: changed tokenizer/weights, overflow, partial
residency or nonfinite likelihood refuses, never becomes a score. ALTERNATIVE:
cached-prefix and direct teacher forcing agree; token losses sum to the same
full UTF-8 item loss. Whole-context overflow is explicit, never truncation.
"""
import copy,json,math,time
from pathlib import Path
from runners.stage14.common import REPO,read,freeze,filehash,digest

MODELS={
    'qwen500':('Qwen/Qwen2.5-0.5B','060db6499f32faf8b98477b0a26969ef7d8b9987'),
    'smol360':('HuggingFaceTB/SmolLM2-360M','f8027fd0eaeea54caa13c31d31b9fdc459c38b49'),
    'pythia410':('EleutherAI/pythia-410m','9879c9b5f8bea9051dcb0e68dff21493d67e9d4f'),
    'pythia1400':('EleutherAI/pythia-1.4b','fedc38a16eea3bd36a96b906d78d11d2ce18ed79'),
}
CATALOGUE=REPO/'results/phase_2_4_stage_15/raw/drive-models-v1'
COMMON_WINDOW=2048


def local_catalogue():
    from huggingface_hub.constants import HF_HUB_CACHE
    out={}
    for key,(repo,rev) in MODELS.items():
        root=Path(HF_HUB_CACHE)/('models--'+repo.replace('/','--'))/'snapshots'/rev
        if not (root/'model.safetensors').is_file() or not (root/'tokenizer.json').is_file():raise ValueError('required cached weights/tokenizer missing: '+repo)
        files={p.name:filehash(p) for p in root.iterdir() if p.is_file() and (p.suffix=='.json' or p.suffix=='.safetensors')}
        out[key]=dict(repo=repo,revision=rev,path=str(root),files=files,config=read(root/'config.json'))
    return out


def verify_model(entry):
    root=Path(entry['path'])
    for name,h in entry['files'].items():
        if filehash(root/name)!=h:raise ValueError('reader identity changed: '+name)
    return root


def contexts(tok,brief,document):
    # Explicit delimiters, no attempt to imply natural unseparated tokenization.
    draft=document[len(brief):] if document.startswith(brief) else document
    prompt='Task context:\n'+brief+'\nDraft:\n'
    suffix=tok.encode(draft,add_special_tokens=False)[-100:]
    return dict(c0='',c1=prompt,c2=prompt+tok.decode(suffix,skip_special_tokens=False),c3=prompt+draft+'\nContinuation:\n')


def pack(tok,context,target):
    context_ids=tok.encode(context,add_special_tokens=False)
    # Every continuation has an explicit conditioning token, including c0.
    bos=tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id
    if bos is None:raise ValueError('missing unconditional conditioning token')
    prefix=[bos]+context_ids
    encoded=tok(target,add_special_tokens=False,return_offsets_mapping=True)
    ids=encoded['input_ids'];offsets=encoded['offset_mapping']
    if not ids or not len(target.encode('utf8')):return dict(eligible=False,reason='empty target')
    if len(prefix)+len(ids)>COMMON_WINDOW:return dict(eligible=False,reason='whole context plus target exceeds common 2048-token window',prefix_tokens=len(prefix),target_tokens=len(ids))
    return dict(eligible=True,prefix=prefix,target=ids,offsets=offsets,utf8_bytes=len(target.encode('utf8')))


def score_menu(model,tok,context,targets,torch):
    packed=[pack(tok,context,t) for t in targets];eligible=[x for x in packed if x['eligible']]
    if not eligible:return packed
    prefix=eligible[0]['prefix']
    if any(x['prefix']!=prefix for x in eligible):raise ValueError('prefix mismatch')
    if any(p.device.type!='cuda' for p in model.parameters()):raise ValueError('reader not fully resident on GPU')
    with torch.inference_mode():
        out=model(input_ids=torch.tensor([prefix],device='cuda'),use_cache=True)
        first=out.logits[:,-1,:].float();cache=out.past_key_values;result=[]
        for x in packed:
            if not x['eligible']:result.append(x);continue
            ids=x['target'];pieces=[first]
            if len(ids)>1:
                branch=model(input_ids=torch.tensor([ids[:-1]],device='cuda'),past_key_values=copy.deepcopy(cache),use_cache=False)
                pieces.append(branch.logits[0].float())
            logits=torch.cat(pieces,dim=0)
            labels=torch.tensor(ids,device='cuda');losses=torch.nn.functional.cross_entropy(logits,labels,reduction='none')
            if not torch.isfinite(losses).all():raise ValueError('nonfinite teacher-forced loss')
            values=losses.cpu().tolist();total=float(sum(values))
            result.append(dict(eligible=True,native_token_ids=ids,native_token_nll=values,
                codepoint_offsets=x['offsets'],prefix_tokens=len(prefix),target_tokens=len(ids),
                total_nll=total,mean_token_nll=total/len(ids),nll_per_utf8_byte=total/x['utf8_bytes'],utf8_bytes=x['utf8_bytes']))
            del logits,labels,losses
        return result


def catalogue():
    """Only source acquisition; no inference, including on the missing size arm."""
    from huggingface_hub import HfApi,snapshot_download
    from runners.next_round.queue import require_resources,resource_snapshot
    from runners.stage14.common import now,atomic
    require_resources(resource_snapshot());CATALOGUE.mkdir(parents=True,exist_ok=True)
    with (CATALOGUE/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    try:
        from runners.stage9.process_identity import native_identity
        freeze(CATALOGUE/'OWNER.json',dict(at=now(),native=native_identity()))
        out=local_catalogue();repo='EleutherAI/pythia-1b';info=HfApi(token=False).model_info(repo,files_metadata=True)
        revision=info.sha
        if len(revision)!=40:raise ValueError('unresolved model commit')
        expected=[s for s in info.siblings if Path(s.rfilename).suffix in ('.json','.safetensors')]
        if not expected or any(type(s.size)!=int for s in expected) or sum(s.size for s in expected)>5*1024**3:raise ValueError('unbounded model download')
        freeze(CATALOGUE/'DOWNLOAD.json',dict(repo=repo,revision=revision,allowed=['*.json','*.safetensors'],
            expected_files={s.rfilename:s.size for s in expected},maximum_expected_bytes=5*1024**3))
        root=Path(snapshot_download(repo,revision=revision,token=False,local_dir=CATALOGUE/'pythia1b',allow_patterns=['*.json','*.safetensors'],max_workers=1))
        files={p.name:filehash(p) for p in root.iterdir() if p.is_file() and p.suffix in ('.json','.safetensors')}
        if sum(p.stat().st_size for p in root.iterdir() if p.is_file())>5*1024**3:raise ValueError('model download byte ceiling')
        out['pythia1000']=dict(repo=repo,revision=revision,path=str(root.resolve()),files=files,config=read(root/'config.json'))
        freeze(CATALOGUE/'MODELS.json',out)
        freeze(CATALOGUE/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={'MODELS.json':filehash(CATALOGUE/'MODELS.json'),'DOWNLOAD.json':filehash(CATALOGUE/'DOWNLOAD.json')},model_inference=False,scientific_admission=False))
    except BaseException as exc:
        freeze(CATALOGUE/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc)));raise


if __name__=='__main__':catalogue()
