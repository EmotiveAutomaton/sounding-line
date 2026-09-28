"""Separately frozen development corrections; original attempts remain immutable.

DESIGN CHECK: LESSONS 3-5. NULL: absent operation payloads, collapsed treatments,
over-budget memories, invalid probabilities or failed known answers refuse admission.
ALTERNATIVE: meaningful source payloads survive the actual tokenizer and the original
Qwen admission gate passes without normalizing replies. Development only; this module
does not authorize reserve replay or restore untouched status to exposed records.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
from .common import freeze, digest
from . import context, gpu

PROBABILITY_INSTRUCTIONS = (
    '\nJSON fields: handling, facts, goal_support, unknown_history. Each fact has '
    'slot, actor, operation, relation, exact_spans. Handling and each categorical '
    'fact array must contain probabilities between 0 and 1 summing to 1, in the '
    'listed category order; never category indices. For example, a four-category '
    'uncertain distribution is [0.25,0.25,0.25,0.25]. Goal support is four independent '
    'probabilities; unknown_history is one probability. No prose or extra keys.\n'
)
_original_request = gpu.request
_original_intervention = context.intervention


def request(evidence, arm):
    result = deepcopy(_original_request(evidence, arm))
    text = result['messages'][1]['content']
    result['messages'][1]['content'] = text.replace('\nEVIDENCE:\n', PROBABILITY_INSTRUCTIONS+'\nEVIDENCE:\n', 1)
    if len(result['messages'][1]['content'].encode('utf-8')) > 5300:
        raise ValueError('corrected interface exceeds original byte budget')
    return result


def fixture(row):
    result = deepcopy(row)
    if result.get('control') == 'observed-adoption':
        # Scorer metadata only. D and all reader-visible evidence remain identical.
        result['views']['A'] = {'endpoint': result['views']['D']['endpoint']}
    return result


def memory(tok, row, training, mode):
    previous, ids = _original_intervention(row, training, mode)
    if previous is None or mode not in ('raw-retrieval', 'linked-memory', 'duplicated', 'independent'):
        return previous, ids
    by = {r['key']: r for r in training}
    chosen = [by[k] for k in ids]
    def raw_record(r):
        # Same 12-token endpoint excerpt in the single and repeated record.
        tail = tok.decode(tok.encode(r['views']['A']['endpoint'], add_special_tokens=False)[-12:])
        return 'recorded_handling='+r['target']['handling']+'; endpoint_tail='+json.dumps(tail, ensure_ascii=False)
    if mode == 'linked-memory':
        active = [f for f in chosen[0]['target']['facts'] if f['operation'] != 'absent']
        if not active:
            raise ValueError('linked memory has no recorded operations')
        content = 'Recorded operations (slot: actor operation relation spans): '+ '; '.join(
            f['slot']+': '+f['actor']+' '+f['operation']+' '+f['relation']+' '+json.dumps(f['exact_spans'], separators=(',', ':'))
            for f in active)
        tail = tok.decode(tok.encode(chosen[0]['views']['A']['endpoint'], add_special_tokens=False)[-12:])
        content += '; endpoint_tail='+json.dumps(tail, ensure_ascii=False)
    else:
        records = [raw_record(r) for r in chosen[:(2 if mode == 'independent' else 1)]]
        if mode == 'duplicated': records *= 2
        content = '\n'.join(records)
    tokens = tok.encode(content, add_special_tokens=False)
    if len(tokens) > 100:
        raise ValueError('complete corrected memory exceeds original 100-token budget')
    if tok.decode(tokens) != content:
        raise ValueError('memory changes under tokenizer round trip')
    return content, ids[:(2 if mode == 'independent' else 1)]


def realization(rows, training, tok):
    if not rows or any(r['partition'] != 'development' for r in rows):
        raise ValueError('memory correction requires nonempty development-only rows')
    checks=[]; errors=[]
    for row in rows:
        rendered={}
        for mode in context.MODES:
            try:
                text, ids = memory(tok, row, training, mode)
                if text is None:
                    checks.append(dict(key=row['key'],mode=mode,unavailable=True)); continue
                actual = tok.decode(tok.encode(text, add_special_tokens=False)[:100])
                if mode in ('raw-retrieval','linked-memory','duplicated','independent') and actual != text:
                    raise ValueError('payload erased by actual projection')
                for view in ('A','C'):
                    e=context.evidence(row,view)
                    base=tok.decode(tok.encode(json.dumps(e,ensure_ascii=False),add_special_tokens=False)[:260])
                    labels=list(context.ACTIONS)+['unknown']
                    if mode=='missing-candidate':labels.pop(int(digest(row['key'])[:8],16)%4)
                    prompt='Evidence from a completed writing episode: '+base+'\nContext/memory: '+actual+'\nPossible recorded actions: '+', '.join(labels)+'.\nRecorded action:'
                    if len(tok.encode(prompt,add_special_tokens=False))>512:
                        raise ValueError('corrected complete prompt exceeds original prefix budget')
                    checks.append(dict(key=row['key'],view=view,mode=mode,prompt_sha256=digest(prompt)))
                rendered[mode] = actual
                checks.append(dict(key=row['key'],mode=mode,tokens=len(tok.encode(actual,add_special_tokens=False)),sha256=digest(actual),source_ids=ids))
            except ValueError as exc:
                errors.append(dict(key=row['key'],mode=mode,error=str(exc)))
        if all(m in rendered for m in ('raw-retrieval','linked-memory','duplicated')):
            a,b,c=[rendered[m] for m in ('raw-retrieval','linked-memory','duplicated')]
            if len({a,b,c}) != 3 or c != a+'\n'+a or 'Recorded operations' not in b:
                errors.append(dict(key=row['key'],error='treatment meaning or duplicate realization failed'))
    return dict(admitted=not errors,checks=checks,errors=errors,development_rows=len(rows),
                scope='input realization only; unequal token lengths remain; original reserve exposure retained')


@contextmanager
def qwen_interface():
    prior=gpu.request; gpu.request=request
    try: yield
    finally: gpu.request=prior


def handle(card,out,raw,tick):
    from .common import read
    args=card['args']
    if card['action']=='qwen-development-repair':
        from .worker import handle as original_handle
        with qwen_interface():
            return original_handle(dict(card,action='qwen-admission'),out,raw,tick)
    if card['action'] in ('memory-development-admission','memory-development-batch'):
        from .detectors import cached_model
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(cached_model('openai-community/gpt2-medium'),local_files_only=True)
        result=realization(read(raw/args['rows']),read(raw/args['training']),tok)
        freeze(out/'ADMISSION.json',result)
        if card['action']=='memory-development-admission':return result
        if not result['admitted']:raise ValueError('development realization failed')
        prior=context.intervention
        context.intervention=lambda row,training,mode:memory(tok,row,training,mode)
        try:
            result=context.run(read(raw/args['rows']),read(raw/args['training']),out,raw,tick=tick)
        finally:context.intervention=prior
        analysis=context.summarize(result['rows'])
        analysis['scope']='development-only corrected rendering; unequal prompt lengths; no held-out memory benefit claim'
        freeze(out/'ANALYSIS.json',analysis)
        return result
    raise ValueError('unknown bounded development correction')
