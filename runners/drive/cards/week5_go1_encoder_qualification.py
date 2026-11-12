"""Qualify GO1's unchanged real encoder and authenticated checkpoint path.

DESIGN CHECK: LESSONS 3-5 reread. Constructed strings only, no goal outcomes.
Identity repeats and independent full-token reconstruction must agree; malformed
vectors, changed manifests/bindings and changed sealed bytes must refuse. A
truncated multi-chunk reference must disagree. No scientific effect gate or
threshold is changed. Failure retains this attempt and blocks corpus encoding.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import numpy as np
from . import week5_go as core
from . import week5_go_readers as readers
from . import week5_go1_pipeline_v2 as pipeline
from .week5_qualification_io import publication, write_json

TEXTS = ('', 'A person chooses an answer.', 'A person chooses an answer.',
         'Une personne choisit une r\u00e9ponse. \u4e00\u4e2a\u4eba\u9009\u62e9\u4e00\u4e2a\u56de\u7b54\u3002',
         'A person chooses an answer. ' * 80 + 'A different ending about mountains and rivers.')


def validate(values, expected=None):
    if values.shape != (len(TEXTS), 384) or values.dtype != np.float32 or not np.isfinite(values).all():
        raise ValueError('encoder shape, dtype or finiteness differs')
    if not np.allclose(np.linalg.norm(values, axis=1), 1, rtol=0, atol=1e-6):
        raise ValueError('encoder normalization differs')
    if not np.array_equal(values[1], values[2]):
        raise ValueError('duplicate identity differs')
    if all(np.array_equal(values[0], x) for x in values[1:]):
        raise ValueError('constant encoder output')
    if expected is not None and not np.allclose(values, expected, rtol=0, atol=1e-6):
        raise ValueError('independent full-token reconstruction differs')


def reference(manifest):
    """Independent token partition/pooling, without production embeddings/cache."""
    import torch
    from transformers import AutoModel, AutoTokenizer
    directory = str(Path(manifest).parent)
    tok = AutoTokenizer.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
    model = AutoModel.from_pretrained(directory, local_files_only=True, trust_remote_code=False,
                                     use_safetensors=True).to('cpu').eval()
    torch.set_num_threads(2)
    vectors, counts, first = [], [], None
    with torch.inference_mode():
        for text in TEXTS:
            ids = tok.encode(text, add_special_tokens=False)
            blocks = [ids[i:i+126] for i in range(0, len(ids), 126)] or [[]]
            assert sum(map(len, blocks)) == len(ids)
            pooled = []
            for block in blocks:
                tokens = tok.build_inputs_with_special_tokens(block)
                assert len(tokens) == len(block)+2 and len(tokens) <= 128
                tensor = torch.tensor([tokens], dtype=torch.long)
                state = model(input_ids=tensor, attention_mask=torch.ones_like(tensor)).last_hidden_state[0]
                pooled.append(state.mean(dim=0).numpy())
            mean = np.stack(pooled).mean(axis=0)
            vectors.append(mean / np.linalg.norm(mean))
            counts.append({'tokens': len(ids), 'chunks': len(blocks)})
            first = pooled[0] / np.linalg.norm(pooled[0])
    assert counts[-1]['chunks'] >= 3 and counts[0]['tokens'] == 0
    assert not np.allclose(vectors[-1], first, rtol=0, atol=1e-6), 'truncation control is silent'
    return np.asarray(vectors), counts


def refused(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('corruption was accepted')


def calculate(output, inputs, config):
    if set(inputs) != {'encoder_manifest'} or config != {}:
        raise ValueError('constructed qualification accepts only the frozen encoder manifest')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    manifest = Path(inputs['encoder_manifest'])
    cache = output/'vectors'
    with publication([(core, 'write')]):
        try:
            pipeline.vector_bank(TEXTS, manifest, cache, {'max_new_texts': 2})
        except pipeline.Paused:
            pass
        else:
            raise AssertionError('bounded actual-encoder prefix did not pause')
        assert len(list(cache.glob('*.seal.json'))) == 2
        values = pipeline.vector_bank(TEXTS, manifest, cache, {})
        validate(values)
        saved = readers.embeddings
        try:
            def no_new_calls(*args, **kwargs):
                raise AssertionError('fully cached reentry called the model')
            readers.embeddings = no_new_calls
            assert np.array_equal(values, pipeline.vector_bank(TEXTS, manifest, cache, {}))
        finally:
            readers.embeddings = saved
        expected, counts = reference(manifest)
        validate(values, expected)
        key = hashlib.sha256(TEXTS[0].encode()).hexdigest()
        original = json.loads((cache/(key+'.json')).read_text('utf8'))
        for kind in ('bytes', 'binding'):
            bad = output/('bad-'+kind); bad.mkdir(exist_ok=True)
            value = json.loads(json.dumps(original))
            if kind == 'bytes': value['vector'][0] += .01
            else: value['binding']['manifest_sha256'] = '0'*64
            core.write(bad/(key+'.json'), value)
            seal = core.sha(cache/(key+'.json')) if kind == 'bytes' else core.sha(bad/(key+'.json'))
            core.write(bad/(key+'.seal.json'), {'sha256': seal})
            refused(lambda: pipeline.vector_bank(TEXTS, manifest, bad, {}))
        changed = json.loads(manifest.read_text('utf8')); changed['revision'] = 'not-the-frozen-revision'
        core.write(output/'bad-manifest.json', changed)
        refused(lambda: readers.embeddings(TEXTS, output/'bad-manifest.json'))
    report = dict(constructed_only=True, actual_pretrained_encoder_run=True,
                  corpus_scoring=False, backend='CPU; local files only; two numerical threads',
                  texts_sha256=hashlib.sha256(json.dumps(TEXTS, ensure_ascii=True).encode()).hexdigest(),
                  manifest_sha256=core.sha(manifest), reader_sha256=core.sha(readers.__file__),
                  pipeline_sha256=core.sha(pipeline.__file__), qualification_sha256=core.sha(__file__),
                  packages={p: importlib.metadata.version(p) for p in ('numpy','torch','transformers','tokenizers')},
                  unique_constructed_strings=len(set(TEXTS)), counts=counts,
                  pause_resume_cache_reentry=True, full_token_independent_reference=True,
                  changed_seal_binding_manifest_refused=True, truncation_control_fired=True)
    return values, report


def execute(output, inputs, config):
    output=Path(output); values, report=calculate(output,inputs,config)
    np.save(output/'VECTORS.npy',values,allow_pickle=False)
    write_json(output/'SUMMARY.json', report)
    return report


def verify(output, inputs, config):
    output=Path(output); values, report=calculate(output/'independent-replay',inputs,config)
    if not np.array_equal(np.load(output/'VECTORS.npy',allow_pickle=False),values):
        raise ValueError('fresh native encoder replay differs')
    if json.loads((output/'SUMMARY.json').read_text('utf8')) != report:
        raise ValueError('fresh qualification summary differs')
    return dict(verified=True, actual_encoder_fresh_replay=True, constructed_only=True)
