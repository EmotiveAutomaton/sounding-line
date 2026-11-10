"""Reviewed v4/v5 AT-FP64-1 collection; exact producer pins remain mandatory.

DESIGN CHECK: LESSONS3--5. No numerical, source, cohort or uncertainty gate
is relaxed. Only the reviewed immutable-cost successor joins the same bank.
"""
from pathlib import Path
from . import week5_at_collect as original
from .week5_at_source import authenticate
from .week5_at_scoring_v4 import score_binding,NUMERICAL_SPEC
from .timing_census import read,filehash
from .timing_p6 import gzread
from .timing_p6 import write_equal
from .batch_runtime import check_files

CORE = {
    "week5_at_scoring.py":"2704c175e0ba4893dadb8df07e4b0550b0e1e1498383148afcb27ad9ad2fcf07",
    "week5_at_scoring_v4.py":"1759d0170c01376c0fcb74303b43c0977a0f47613becd15557698470273af420",
    "week5_at_scoring_v5.py":"f3cffb5b192bf473127de00eb109d2b812be57e54d9147b3ca1270250d10b3b2",
}
PRODUCERS={"runners.drive.cards.week5_at_scoring_v4", "runners.drive.cards.week5_at_scoring_v5"}

def producer(root,plan):
    if plan.get("module") not in PRODUCERS:raise ValueError("Legacy or unknown numerical score handler")
    done=read(root/"COMPLETE.json")
    if done["outputs"].get("PLAN.json")!=filehash(root/"PLAN.json"):
        raise ValueError("Completed producer plan is not authenticated")
    pins={}
    for path,sha in plan["pins"].items():
        key=str(Path(path).resolve()).casefold()
        if key in pins and pins[key]!=sha:raise ValueError("Conflicting producer pin aliases")
        pins[key]=sha
    check_files(plan["pins"])
    required=["week5_at_scoring.py","week5_at_scoring_v4.py"]
    if plan["module"].endswith("_v5"):required.append("week5_at_scoring_v5.py")
    for name in required:
        path=Path(__file__).parent/name
        if filehash(path)!=CORE[name] or pins.get(str(path.resolve()).casefold())!=CORE[name]:
            raise ValueError("Unreviewed or unpinned numerical producer")
    for key in ("rows","model_manifest"):
        path=Path(plan["inputs"][key]).resolve()
        if pins.get(str(path).casefold())!=filehash(path):raise ValueError("Unpinned score input")
    return dict(module=plan["module"],plan_sha256=filehash(root/"PLAN.json"),
                complete_sha256=filehash(root/"COMPLETE.json"),core={k:CORE[k] for k in required})



def validate(inputs,config):
    if set(config)-{'context','context_length'}:raise ValueError('Exact declared collector condition required')
    context=config.get('context','final');length=config.get('context_length',1024)
    if context not in ('final','at_typing') or length not in (64,256,1024):raise ValueError('Unregistered collection context')
    source=authenticate(inputs['source_root'])/'output';bank=read(inputs['bank_manifest'])
    expected={r['file']:r for r in read(source/'BATCHES.json') if r['context']==context}
    if not bank or not expected:raise ValueError('Empty complete bank')
    records=[]
    for model,paths in sorted(bank.items()):
        if set(paths)!=set(expected):raise ValueError('Model bank is incomplete')
        revisions=set()
        for name,path in sorted(paths.items()):
            chunk=source/name
            if filehash(chunk)!=expected[name]['sha256']:raise ValueError('Source chunk changed')
            root=authenticate(path);plan=read(root/'PLAN.json');summary=read(root/'output/SUMMARY.json')
            provenance=producer(root,plan)
            if summary.get('numerical_spec')!=NUMERICAL_SPEC:raise ValueError('Mixed numerical scoring specification')
            # A whole-writer projection may retain an identical original chunk.
            # Reuse is permitted by bytes, never by row keys alone or by a path.
            if filehash(plan['inputs']['rows'])!=filehash(chunk):raise ValueError('Score plan source chunk differs')
            planned=plan['config'];manifest=read(plan['inputs']['model_manifest'])
            if planned.get('context','final')!=context or planned.get('context_length',1024)!=length:
                raise ValueError('Score plan context length differs')
            if summary.get('context')!=context or summary.get('context_length')!=length:
                raise ValueError('Score output context length differs')
            if manifest.get('model')!=model or summary.get('model')!=model or summary.get('model_revision')!=manifest.get('revision') or not manifest.get('revision'):
                raise ValueError('Score model revision differs')
            revisions.add(manifest['revision'])
            records.append(dict(model=model,batch=name,source_sha256=filehash(chunk),manifest_sha256=filehash(plan['inputs']['model_manifest']),**provenance))
            binding=score_binding(gzread(chunk),manifest,context,length)
            if read(root/'output/BINDING.json')!={'sha256':binding}:raise ValueError('Scored rows/model/context binding differs')
        if len(revisions)!=1:raise ValueError('Mixed model revisions in complete bank')
        if len({r['manifest_sha256'] for r in records if r['model']==model})!=1:raise ValueError('Mixed model manifests in complete bank')
    return records


def execute(output,inputs,config):
    producers=validate(inputs,config)
    value=original.execute(output,inputs,config)
    write_equal(Path(output)/'NUMERICAL_SPEC.json',NUMERICAL_SPEC)
    write_equal(Path(output)/'PRODUCER_BINDINGS.json',producers)
    return value


def verify(output,inputs,config):
    producers=validate(inputs,config)
    if read(Path(output)/'PRODUCER_BINDINGS.json')!=producers:raise ValueError('Complete producer provenance changed')
    if read(Path(output)/'NUMERICAL_SPEC.json')!=NUMERICAL_SPEC:raise ValueError('Collection numerical specification changed')
    return original.verify(output,inputs,config)
