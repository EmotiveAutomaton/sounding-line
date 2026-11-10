"""AT float64-only bank collection; rejects legacy and mixed precision banks."""
from pathlib import Path
from . import week5_at_collect as original
from .week5_at_source import authenticate
from .week5_at_scoring_v4 import score_binding,NUMERICAL_SPEC
from .timing_census import read,filehash
from .timing_p6 import gzread
from .timing_p6 import write_equal


def validate(inputs,config):
    if set(config)-{'context','context_length'}:raise ValueError('Exact declared collector condition required')
    context=config.get('context','final');length=config.get('context_length',1024)
    if context not in ('final','at_typing') or length not in (64,256,1024):raise ValueError('Unregistered collection context')
    source=authenticate(inputs['source_root'])/'output';bank=read(inputs['bank_manifest'])
    expected={r['file']:r for r in read(source/'BATCHES.json') if r['context']==context}
    if not bank or not expected:raise ValueError('Empty complete bank')
    for model,paths in sorted(bank.items()):
        if set(paths)!=set(expected):raise ValueError('Model bank is incomplete')
        revisions=set()
        for name,path in sorted(paths.items()):
            chunk=source/name
            if filehash(chunk)!=expected[name]['sha256']:raise ValueError('Source chunk changed')
            root=authenticate(path);plan=read(root/'PLAN.json');summary=read(root/'output/SUMMARY.json')
            if plan['module']!='runners.drive.cards.week5_at_scoring_v4':
                raise ValueError('Legacy or mixed numerical score handler')
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
            binding=score_binding(gzread(chunk),manifest,context,length)
            if read(root/'output/BINDING.json')!={'sha256':binding}:raise ValueError('Scored rows/model/context binding differs')
        if len(revisions)!=1:raise ValueError('Mixed model revisions in complete bank')


def execute(output,inputs,config):
    validate(inputs,config)
    value=original.execute(output,inputs,config)
    write_equal(Path(output)/'NUMERICAL_SPEC.json',NUMERICAL_SPEC)
    return value


def verify(output,inputs,config):
    validate(inputs,config)
    if read(Path(output)/'NUMERICAL_SPEC.json')!=NUMERICAL_SPEC:raise ValueError('Collection numerical specification changed')
    return original.verify(output,inputs,config)
