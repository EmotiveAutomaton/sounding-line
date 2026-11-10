"""Week 5 AT: exact word contexts, CPU causal losses and prefix-cache entropy.

DESIGN CHECK: LESSONS 3--5 and CONTROLS 1--6 reread 2026-11-07.
NULL/ALTERNATIVE: numerical admission is independent of scientific effect.
Fresh forwards must reproduce every checked token loss and first-token entropy
within 1e-4 nats. Altered IDs, offsets, crops, hashes or nonfinite values refuse.
Deleted/revised production occurrences have no invented final-text location.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta
from .timing_text import TOKEN
from .timing_census import filehash, read
from .timing_p6 import gzread, gzip_equal, write_equal, progress

SEED = 20261107
MODELS = (
    'openai-community/gpt2-medium', 'openai-community/gpt2',
    'openai-community/gpt2-large', 'EleutherAI/pythia-70m-deduped',
    'EleutherAI/pythia-160m-deduped', 'EleutherAI/pythia-410m-deduped',
    'EleutherAI/pythia-1b-deduped', 'EleutherAI/pythia-1.4b-deduped',
    'HuggingFaceTB/SmolLM2-360M', 'Qwen/Qwen2.5-0.5B',
)
ENGINE_MODELS = MODELS[-2:]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     ensure_ascii=False).encode()).hexdigest()


def frozen_sessions(identities, fraction=.2):
    """Exactly ceil(20%) sessions selected before model or pause outcomes."""
    identities = sorted(set(identities))
    rng = np.random.default_rng(SEED)
    ix = rng.permutation(len(identities))[:math.ceil(fraction*len(identities))]
    return sorted(identities[i] for i in ix)


def context_rows(events, targets):
    """P7 completion identity mapping, extended to exact final provenance.

    The identity is the tuple of original inserted character IDs, not the word
    spelling. Repeated words and reinserted copies can never acquire a prior
    occurrence's pause. UTF-16 deltas retain the canonical replay convention.
    """
    by_event = defaultdict(list)
    for row in targets:
        by_event[row['completed_ordinal']].append(row)
    doc = units(events[0]['currentDoc'])
    owners, inserted = [-1]*len(doc), []
    mapped, used = {}, set()

    def candidates(document, provenance):
        text = text_of(document)
        offsets = [0]
        for ch in text:
            offsets.append(offsets[-1]+len(units(ch)))
        found = defaultdict(list)
        for m in TOKEN.finditer(text):
            ids = tuple(dict.fromkeys(provenance[offsets[m.start()]:offsets[m.end()]]))
            if not ids or -1 in ids:
                continue
            key = (m.group().casefold(), inserted[ids[0]], len(m.group()))
            found[key].append((ids, text[:m.start()], m.group()))
        return found

    for ordinal, event in enumerate(events):
        before_doc, before_owners = doc, owners
        ops = delta_ops(event.get('textDelta'))
        if ops:
            new_owners, position = [], 0
            for op in ops:
                if 'insert' in op:
                    for ch in op['insert']:
                        identity = -1
                        if event.get('eventSource') == 'user':
                            identity = len(inserted)
                            inserted.append(ordinal)
                        new_owners.extend([identity]*len(units(ch)))
                elif 'retain' in op:
                    new_owners.extend(owners[position:position+op['retain']])
                    position += op['retain']
                else:
                    position += op['delete']
            new_owners.extend(owners[position:])
            doc, _, _ = apply_delta(doc, owners, event.get('textDelta'))
            owners = new_owners
        if ordinal not in by_event:
            continue
        old, new = candidates(before_doc, before_owners), candidates(doc, owners)
        for row in sorted(by_event[ordinal], key=lambda x: x['index']):
            key = (row['token'], row['ordinal'], row['length'])
            options = [v for v in old[key] if v[0] not in used] or [v for v in new[key] if v[0] not in used]
            if not options:
                raise ValueError('No unique production occurrence at completion')
            ids, prefix, target = options[0]
            used.add(ids)
            mapped[row['index']] = dict(index=row['index'], character_ids=ids,
                                       at_typing_prefix=prefix, target=target)
    if set(mapped) != {r['index'] for r in targets}:
        raise ValueError('Incomplete production context coverage')
    final = {ids: (prefix, target) for choices in candidates(doc, owners).values()
             for ids, prefix, target in choices}
    output = []
    for row in targets:
        item = mapped[row['index']]
        where = final.get(item.pop('character_ids'))
        unchanged = where is not None and where[1] == item['target']
        item.update(final_prefix=where[0] if unchanged else None,
                    final_supported=unchanged,
                    final_disposition='exact_survivor' if unchanged else 'deleted_or_modified')
        output.append(item)
    return output


def tokenize_target(tokenizer, prefix, target, context_length):
    encoded = tokenizer(prefix+target, add_special_tokens=False, return_offsets_mapping=True)
    start = tokenizer.bos_token_id
    if start is None:
        start = tokenizer.eos_token_id
    if start is None:
        raise ValueError('Model has no explicit start token')
    raw = [start]+list(encoded['input_ids'])
    dropped = max(0, len(raw)-context_length)
    positions = [i+1-dropped for i, (a,b) in enumerate(encoded['offset_mapping'])
                 if b>len(prefix) and a<len(prefix+target)]
    if not positions or min(positions)<=0:
        raise ValueError('Target does not fit the declared causal context')
    return raw[dropped:], positions, dropped


class CausalScorer:
    """P7 prefix cache, including first-token predictive entropy.

    Loss/entropy at token i is from logits at i-1. Cache reuse backs off one
    token so the first new loss is always computed, never filled from a later
    prediction. Cropped prefixes are treated as new absolute-position contexts.
    """
    def __init__(self, model, tokenizer, torch, context_length=1024):
        self.model, self.tokenizer, self.torch = model, tokenizer, torch
        self.context_length = context_length
        self.cache, self.ids, self.losses, self.entropies = None, [], [], []
        self.forward_tokens = 0

    def _forward(self, ids, cache=None):
        tensor = self.torch.tensor([ids], dtype=self.torch.long, device='cpu')
        with self.torch.inference_mode():
            out = self.model(input_ids=tensor, past_key_values=cache, use_cache=True)
            logp = self.torch.log_softmax(out.logits[0, :-1].float(), dim=-1)
            losses = -logp.gather(1, tensor[0,1:,None]).squeeze(1)
            entropy = -(logp.exp()*logp).sum(-1)
        return out.past_key_values, losses.tolist(), entropy.tolist()

    def score(self, prefix, target):
        ids, positions, dropped = tokenize_target(self.tokenizer,prefix,target,self.context_length)
        common = 0
        for a,b in zip(ids,self.ids):
            if a!=b:
                break
            common += 1
        if common==len(ids) and self.cache is not None:
            if hasattr(self.cache,'crop'):
                self.cache.crop(len(ids))
                losses, entropies = self.losses[:len(ids)], self.entropies[:len(ids)]
            else:
                self.cache, nll, entropy = self._forward(ids)
                losses, entropies = [None]+nll, [None]+entropy
                self.forward_tokens += len(ids)
        else:
            reuse = max(0,common-1)
            if self.cache is not None and reuse and hasattr(self.cache,'crop'):
                self.cache.crop(reuse)
            else:
                self.cache, reuse = None, 0
            self.cache,nll,entropy = self._forward(ids[reuse:], self.cache)
            losses = (self.losses[:reuse+1] if reuse else [None])+nll
            entropies = (self.entropies[:reuse+1] if reuse else [None])+entropy
            self.forward_tokens += len(ids)-reuse
        self.ids,self.losses,self.entropies = ids,losses,entropies
        selected = [losses[i] for i in positions]
        first_entropy = entropies[positions[0]]
        if any(v is None or not math.isfinite(v) or v<0 for v in selected+[first_entropy]):
            raise ValueError('Nonfinite or negative model measurement')
        return dict(native_token_ids=[ids[i] for i in positions], native_token_nll=selected,
                    surprisal_nats=sum(selected), entropy_nats=first_entropy,
                    prefix_tokens_dropped=dropped)

    def direct_check(self,prefix,target,saved):
        fresh = CausalScorer(self.model,self.tokenizer,self.torch,self.context_length).score(prefix,target)
        for key in ('native_token_ids','prefix_tokens_dropped'):
            if fresh[key]!=saved[key]:
                raise ValueError('Fresh-forward identity mismatch')
        error=max(abs(a-b) for a,b in zip(fresh['native_token_nll']+[fresh['entropy_nats']],
                                         saved['native_token_nll']+[saved['entropy_nats']]))
        if error>1e-4 or saved['surprisal_nats']!=sum(saved['native_token_nll']):
            raise ValueError('Fresh-forward numerical mismatch')
        return error


def load_model(manifest):
    if manifest['model'] not in MODELS and manifest['model'] not in (
            'EleutherAI/pythia-410m','EleutherAI/pythia-1.4b'):
        raise ValueError('Uncommissioned model')
    if not manifest.get('revision') or not manifest.get('licence'):
        raise ValueError('Revision and inspected licence required')
    for path,sha in manifest['files'].items():
        if filehash(path)!=sha:
            raise ValueError('Model snapshot changed')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    torch.set_num_threads(2)
    tok=AutoTokenizer.from_pretrained(manifest['tokenizer_path'],local_files_only=True,
                                     trust_remote_code=False,use_fast=True)
    model=AutoModelForCausalLM.from_pretrained(manifest['model_path'],local_files_only=True,
          trust_remote_code=False,use_safetensors=True,dtype=torch.float32).cpu().eval()
    return model,tok,torch


def score_batch(output, rows, manifest, *, context='final', context_length=1024,
                max_wall_seconds=1500, verifying=False):
    """Immutable per-word checkpoints; completion means this entire fixed batch.

    Fresh verifier checks seeded 2% (at least one), identities and all reductions.
    A timeout writes a yield receipt, never a completion. The runtime can resume.
    """
    if context not in ('final','at_typing') or context_length not in (64,256,1024):
        raise ValueError('Unregistered context condition')
    if not rows:
        raise ValueError('Empty scoring batch')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    binding=digest(dict(rows=rows,manifest=manifest,context=context,context_length=context_length))
    write_equal(root/'BINDING.json',dict(sha256=binding))
    model,tok,torch=load_model(manifest)
    scorer=CausalScorer(model,tok,torch,context_length)
    chosen=set(np.random.default_rng(SEED).choice(len(rows),max(1,math.ceil(.02*len(rows))),replace=False)) if rows else set()
    began=time.monotonic();index=[];errors=[]
    for i,row in enumerate(rows):
        prefix=row[context+'_prefix']
        if prefix is None:
            raise ValueError('Unsupported context must be counted before batching')
        path=root/f'word-{i:07d}.json'
        if path.exists():
            saved=read(path)
            if saved['binding']!=binding or saved['row_key']!=row['row_key']:
                raise ValueError('Checkpoint from another scored word')
            ids,positions,dropped=tokenize_target(tok,prefix,row['target'],context_length)
            score=saved['score'];native=score['native_token_nll']
            if (score['native_token_ids']!=[ids[j] for j in positions]
                    or score['prefix_tokens_dropped']!=dropped or len(native)!=len(positions)
                    or any(not math.isfinite(v) or v<0 for v in native+[score['entropy_nats']])
                    or score['surprisal_nats']!=sum(native)):
                raise ValueError('Retained model measurement does not reconstruct')
            if verifying and i in chosen:
                errors.append(scorer.direct_check(prefix,row['target'],saved['score']))
        else:
            if verifying:
                raise ValueError('Verification encountered missing checkpoint')
            saved=dict(binding=binding,row_key=row['row_key'],score=scorer.score(prefix,row['target']))
            write_equal(path,saved)
        index.append(dict(row_key=row['row_key'],file=path.name,sha256=filehash(path)))
        if i%32==0:
            progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'score',words=i+1,total=len(rows)))
        if time.monotonic()-began>=max_wall_seconds and i+1<len(rows):
            return dict(status='yielded',completed=i+1,total=len(rows))
    result=dict(status='complete',words=len(rows),context=context,context_length=context_length,
                model=manifest['model'],model_revision=manifest['revision'],scientific_admission=False)
    if verifying:
        if read(root/'INDEX.json')!=index or read(root/'SUMMARY.json')!=result:
            raise ValueError('Saved batch index or reduction differs')
        return dict(verified=True,fresh_forward_count=len(chosen),max_error=max(errors,default=0.))
    write_equal(root/'INDEX.json',index);write_equal(root/'SUMMARY.json',result)
    return result


def native_fixture(output):
    """Actual CPU model and source-provenance fixture, no research corpus."""
    import torch
    from transformers import GPT2Config,GPT2LMHeadModel
    from .timing_text import replay_words
    class Tokenizer:
        eos_token_id=0
        bos_token_id=0
        def __call__(self,text,**kwargs):
            return dict(input_ids=[ord(c)%31+1 for c in text],
                        offset_mapping=[(i,i+1) for i in range(len(text))])
    torch.set_num_threads(2);torch.manual_seed(4)
    model=GPT2LMHeadModel(GPT2Config(vocab_size=33,n_positions=64,n_embd=16,n_layer=1,n_head=2,bos_token_id=0,eos_token_id=0)).eval()
    scorer=CausalScorer(model,Tokenizer(),torch,64)
    rows=[('a ','b'),('a b ','word'),('a ','b'),('x'*70+' ','long'),('x'*70+' long ','end')]
    errors=[]
    for prefix,target in rows:
        saved=scorer.score(prefix,target)
        errors.append(scorer.direct_check(prefix,target,saved))
    events=[dict(eventName='system-initialize',eventSource='system',eventTimestamp=0,currentDoc=''),
            dict(eventName='text-insert',eventSource='user',eventTimestamp=100,textDelta={'ops':[{'insert':'cat cat '}]}),
            dict(eventName='text-delete',eventSource='user',eventTimestamp=200,textDelta={'ops':[{'delete':4}]})]
    mapped=context_rows(events,replay_words(events)['words'])
    if [r['final_supported'] for r in mapped]!=[False,True] or mapped[1]['final_prefix']!='':
        raise ValueError('Occurrence identity fixture failed')
    result=dict(status='COMPLETE',fixture_only=True,scientific_admission=False,
                actual_device=str(next(model.parameters()).device),actual_threads=torch.get_num_threads(),
                checked_forwards=len(rows),max_error=max(errors),occurrence_identity_pass=True,
                torch_version=torch.__version__)
    write_equal(Path(output)/'FIXTURE.json',result)
    return result


def execute(output,inputs,config):
    return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),**config)


def verify(output,inputs,config):
    return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),verifying=True,**config)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True)
    print(json.dumps(native_fixture(p.parse_args().fixture),sort_keys=True))
