"""CA1.s1 representations with the original global prompt reference retained.

DESIGN CHECK: LESSONS 3-5 read 2026-11-04. NULL and ALTERNATIVE share
the original encoder, original prompt clusters and complete selected people.
Missing source authentication, changed arrays or dropped prompts refuse.
Cost prefixes never select the scientific population or score preferences.
"""
from pathlib import Path
from types import FunctionType
import time
from . import week3_alignment_features as original
from .week3_alignment_encoder_smoke import environment
from .menus_io import read, write, assert_equal, sha256
from .timing_p6 import write_equal


def configuration(mode):
    if mode not in ('pilot','full','fixture'):
        raise ValueError('Unknown sample feature mode')
    return dict(mode=mode,seed=original.SEED,variant='CA1.s1',global_prompt_pool=mode!='pilot')


def select_ids(rows,splits,mode,seed):
    selected,ids,prompts=original.select_ids(rows,splits,mode,seed)
    if mode=='pilot':return selected,ids,prompts
    prompts=sorted(splits['prompt_text_indices'])
    ids=sorted(set(ids)|set(splits['prompt_text_indices'].values()))
    return selected,ids,prompts


def source(inputs):
    report,root,rows,splits=original.source(inputs)
    if report.get('variant')!='CA1.s1' or not report.get('sample_scope'):
        raise ValueError('Completed explicit sample source required')
    return report,root,rows,splits


# Reuse the exact original encoding, chunk layouts, clustering and bitwise
# verification. Only source admission and the retained prompt pool differ.
_run=FunctionType(original.run.__code__,dict(original.run.__globals__,
    source=source,select_ids=select_ids,__file__=__file__),original.run.__name__,
    original.run.__defaults__,original.run.__closure__)


def run(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):
        raise ValueError('Frozen sample feature configuration required')
    if config['mode']!='fixture':environment()
    start=time.process_time();result=_run(output,inputs,config,verifying)
    output=Path(output)
    if result.get('status')=='yielded':return result
    scope=dict(variant='CA1.s1',sample_scope=True,original_prompt_reference=config['mode']!='pilot',
               inputs={k:sha256(v) for k,v in inputs.items()},scientific_admission=False)
    if verifying:assert_equal(scope,read(output/'SAMPLE_SCOPE.json'))
    else:write_equal(output/'SAMPLE_SCOPE.json',scope)
    timing=dict(cpu_seconds=time.process_time()-start,texts=result['texts'],full_texts=result['full_texts'])
    timing_path=output/('SAMPLE_VERIFY_TIMING.json' if verifying else 'SAMPLE_EXECUTE_TIMING.json')
    if not timing_path.exists():write(timing_path,timing)
    if verifying and config['mode']=='pilot':
        prior=read(output/'SAMPLE_EXECUTE_TIMING.json')
        # Conservatively scale fixed overhead and the full prompt pool too.
        forecast=3*max(prior['cpu_seconds'],timing['cpu_seconds'])*result['full_texts']/result['texts']
        if not (output/'SAMPLE_FORECAST.json').exists():write(output/'SAMPLE_FORECAST.json',dict(full_encoding_cpu_seconds=forecast,
              engineering_margin=1.5,fresh_replay_included=True,statistical_work_excluded=True))
    return dict(verified=True,fresh_all_embeddings_and_clusters=True,global_prompt_pool=config['mode']!='pilot') if verifying else result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
