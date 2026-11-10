"""Unchanged AT2 statistics with complete float64 selected-reader provenance."""
from pathlib import Path
from . import week5_at_analysis as original
from . import week5_at_collect_v4 as collector
from .week5_at_source import authenticate
from .week5_at_scoring import digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC
from .timing_census import read,filehash
from .timing_p6 import write_equal


def prepare(inputs,config):
    if set(inputs)!={'collection_root'} or config.get('card')!='AT2':raise ValueError('Complete AT2 collection required')
    root=authenticate(inputs['collection_root']);plan=read(root/'PLAN.json');out=root/'output'
    if plan['module']!='runners.drive.cards.week5_at_collect_v4' or read(out/'NUMERICAL_SPEC.json')!=NUMERICAL_SPEC:
        raise ValueError('Complete common-precision collection required')
    collector.validate(plan['inputs'],plan['config'])
    summary=read(out/'SUMMARY.json')
    if sorted(config['models'])!=summary['models'] or config.get('context','final')!=plan['config'].get('context','final') or config.get('context_length',1024)!=plan['config'].get('context_length',1024):
        raise ValueError('Analysis does not match complete collected bank')
    bank=read(plan['inputs']['bank_manifest']);manifests={}
    for model,paths in sorted(bank.items()):
        candidates=[]
        for path in paths.values():
            scoreplan=read(Path(path)/'PLAN.json');candidates.append(read(scoreplan['inputs']['model_manifest']))
        if len({digest(m) for m in candidates})!=1:raise ValueError('Mixed model manifest within collected bank')
        manifests[model]=candidates[0]
    return root,manifests


def run(output,inputs,config,verifying=False):
    root,manifests=prepare(inputs,config);out=Path(output)
    result=(original.verify if verifying else original.execute)(out,dict(rows=str(root/'output/ROWS.json.gz')),config)
    selected=read(out/'RESULT.json')['selected_model'];manifest=manifests[selected]
    binding=dict(model=selected,revision=manifest['revision'],manifest_sha256=digest(manifest),numerical_spec=NUMERICAL_SPEC,
                 complete_collection_sha256=filehash(root/'COMPLETE.json'),context=config.get('context','final'),context_length=config.get('context_length',1024))
    if verifying:
        if read(out/'READER_BINDING.json')!=binding:raise ValueError('Selected reader provenance replay differs')
    else:write_equal(out/'READER_BINDING.json',binding)
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
