"""One pinned local model, bounded requests, immutable identity and per-call costs.

DESIGN CHECK: Stage 9 I03/X06/X07; no truncation, uniform fallback or remote models.
NULL: wrong package, incomplete support, nonfinite scores or outside-envelope requests
are errors. ALTERNATIVE: every option receives complete common-prefix likelihoods.
Only the parent operator sees weights. The reader has token-gated loopback access.
"""
import argparse
from contextlib import nullcontext
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import time
import threading

from runners.stage9.common import REPO, closure, digest, file_hash, read, write
from runners.stage9.neural import sequence_scores
from runners.stage9.train import BASES
from runners.stage9.generation_policy import overrides, policy


class Engine:
    def __init__(self, config):
        validate_config(config)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from huggingface_hub import snapshot_download
        from peft import PeftModel
        self.config, self.torch = config, torch
        torch.set_num_threads(6)
        if config['family'] not in BASES or config['precision'] not in ('float16', 'bfloat16', 'float32'):
            raise ValueError('unregistered model family or precision')
        self.base = BASES[config['family']]
        snapshot = Path(snapshot_download(**{'repo_id': self.base['model'], 'revision': self.base['revision'], 'local_files_only': True}))
        # HF cache snapshot entries can be symlinks; their actual bytes are hashed.
        model_files = {p.name: file_hash(p) for p in sorted(snapshot.iterdir()) if p.is_file() and p.suffix in ('.safetensors', '.json', '.txt', '.model')}
        self.tok = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        dtype = getattr(torch, config['precision'])
        self.model = AutoModelForCausalLM.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False, dtype=dtype).to(config['device'])
        adapter_sha = 'base-no-adapter'
        if config.get('adapter'):
            adapter = Path(config['adapter'])
            actual = closure([adapter])
            if actual['sha256'] != config['adapter_sha256']:
                raise ValueError('adapter differs from frozen package')
            self.model = PeftModel.from_pretrained(self.model, str(adapter), local_files_only=True).to(dtype)
            if not any('lora_' in n for n, _ in self.model.named_parameters()):
                raise ValueError('adapter did not load any LoRA weights')
            adapter_sha = actual['sha256']
        self.model.eval()
        sources = closure([REPO / 'runners/stage9' / name for name in
                           ('model_service.py', 'neural.py', 'generation_policy.py', 'common.py', 'train.py')])
        self.generation_policy = policy(config.get('generation', {'do_sample': False}),
                                        self.model.generation_config.to_dict(),
                                        self.tok.eos_token_id, self.tok.pad_token_id)
        import transformers
        import peft
        self.identity = {**self.base, 'adapter_sha256': adapter_sha, 'scorer_sha256': sources['sha256'],
                         'base_files_sha256': digest(model_files), 'base_files': model_files,
                         'precision': config['precision'], 'device': config['device'],
                         'batch_size': config['batch_size'], 'max_context': config['max_context'],
                         'max_support': config['max_support'], 'max_new_tokens': config['max_new_tokens'],
                         'renderer': 'raw text, no chat template, summed continuation likelihood',
                         'long_context_batch_rule': 'serial when prefix exceeds 1024 tokens',
                         'attention_implementation': self.model.config._attn_implementation,
                         'scorer_sources': sources, 'torch': torch.__version__,
                         'generation': self.generation_policy,
                         'transformers': transformers.__version__, 'peft': peft.__version__}

    def infer(self, request):
        identity = request['identity']
        if {k: v for k, v in identity.items() if k != 'information_sha256'} != self.identity:
            raise ValueError('request package differs from resident identity')
        if not isinstance(identity.get('information_sha256'), str) or len(identity['information_sha256']) != 64:
            raise ValueError('missing evidence identity')
        prefix = request['prefix']
        if not isinstance(prefix, str):
            raise ValueError('prefix must be text')
        started = time.monotonic()
        if self.config['device'] == 'cuda':
            self.torch.cuda.synchronize()
        if request['operation'] == 'score':
            options = request['options']
            if not isinstance(options, dict) or not options or any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in options.items()):
                raise ValueError('invalid support')
            keys = sorted(options)
            if len(keys) > self.config['max_support']:
                raise ValueError('support outside frozen envelope')
            # Identical events have one likelihood. Different batch shapes can change
            # reduced-precision arithmetic, so never measure identical bytes twice.
            texts = list(dict.fromkeys(options[k] for k in keys))
            prompt_tokens = len(self.tok(prefix, add_special_tokens=True).input_ids)
            batch = 1 if prompt_tokens > 1024 else self.config['batch_size']
            result = sequence_scores(self.model, self.tok, prefix, texts,
                                     batch, self.config['max_context'], self.config['max_support'])
            by_text = dict(zip(texts, result['logprobs']))
            sha = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
            components = [{'option_id': k, 'logprob': value, 'valid': True, 'identity': identity,
                           'prefix_sha256': sha(prefix), 'continuation_sha256': sha(options[k]),
                           'semantics': 'sum_log_probability'} for k in keys for value in [by_text[options[k]]]]
            response = {'components': components, 'usage': {**{k: v for k, v in result.items() if k != 'logprobs'},
                                                          'offered_options': len(keys), 'unique_continuations': len(texts)}}
        elif request['operation'] == 'generate':
            maximum = request['max_new_tokens']
            if type(maximum) is not int or not 1 <= maximum <= self.config['max_new_tokens']:
                raise ValueError('generation outside frozen envelope')
            inputs = self.tok(prefix, return_tensors='pt', add_special_tokens=True)
            n = inputs.input_ids.shape[1]
            if n == 0 or n + maximum > self.config['max_context']:
                raise ValueError('generation context outside frozen envelope')
            self.torch.manual_seed(request['seed'])
            inputs = {k: v.to(self.config['device']) for k, v in inputs.items()}
            with self.torch.no_grad():
                generation = self.generation_policy['overrides']
                output = self.model.generate(**inputs, max_new_tokens=maximum, **generation)
            tail = output[0, n:].tolist()
            eos = self.generation_policy['effective'].get('eos_token_id')
            eos = eos if isinstance(eos, list) else [eos]
            response = {'text': self.tok.decode(tail, skip_special_tokens=True), 'token_ids': tail,
                        'stop_reason': 'eos' if tail and tail[-1] in eos else 'token_cap',
                        'usage': {'prompt_tokens': n, 'generated_tokens': len(tail), 'generation': generation}}
        else:
            raise ValueError('unsupported model operation')
        if self.config['device'] == 'cuda':
            self.torch.cuda.synchronize()
        return {**response, 'valid': True, 'identity': identity,
                'inference_wall_seconds': time.monotonic() - started}


def validate_config(config):
    if config.get('device') not in ('cpu', 'cuda'):
        raise ValueError('only explicit local CPU or CUDA devices are supported')
    for key, lower, upper in [('batch_size', 1, 4), ('max_context', 2, 8192),
                              ('max_support', 1, 128), ('max_new_tokens', 1, 2048), ('port', 0, 65535)]:
        if type(config.get(key)) is not int or not lower <= config[key] <= upper:
            raise ValueError('invalid frozen bound: ' + key)
    if not isinstance(config.get('token'), str) or len(config['token']) < 32:
        raise ValueError('an owner-created inference token is required')
    if config.get('shutdown_token') == config['token']:
        raise ValueError('reader token cannot authorize owner shutdown')
    generation = config.get('generation', {'do_sample': False})
    overrides(generation)


def serve(config):
    validate_config(config)
    from runners.s5_lib import GpuSession
    output = Path(config['output'])
    output.mkdir(parents=True, exist_ok=True)
    with GpuSession('s9_inference_' + output.name) if config['device'] == 'cuda' else nullcontext():
        engine = Engine(config)
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                result, status = {}, 200
                try:
                    if self.path == '/shutdown' and config.get('shutdown_token') and hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + config['shutdown_token']):
                        self.send_response(200)
                        self.send_header('Content-Length', '0')
                        self.end_headers()
                        threading.Thread(target=server.shutdown, daemon=True).start()
                        return
                    if self.path != '/infer' or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + config['token']):
                        raise ValueError('unauthorized endpoint')
                    size = int(self.headers.get('Content-Length', '0'))
                    if not 0 < size <= 2 * 1024**2 or self.headers.get('Transfer-Encoding'):
                        raise ValueError('invalid bounded request length')
                    self.connection.settimeout(600)
                    body = self.rfile.read(size)
                    if len(body) != size:
                        raise ValueError('incomplete request')
                    request = json.loads(body)
                    result = engine.infer(request)
                    # No prompt text, options or evaluator truth enters the usage ledger.
                    receipt = {'request_sha256': hashlib.sha256(body).hexdigest(), 'at': time.time(),
                               'usage': result['usage'], 'inference_wall_seconds': result['inference_wall_seconds']}
                    with (output / 'USAGE.jsonl').open('a', encoding='utf-8', newline='\n') as out:
                        out.write(json.dumps(receipt, sort_keys=True) + '\n')
                except Exception as exc:
                    result, status = {'valid': False, 'error': type(exc).__name__ + ': ' + str(exc)}, 422
                    with (output / 'ERRORS.jsonl').open('a', encoding='utf-8', newline='\n') as out:
                        out.write(json.dumps({**result, 'at': time.time()}) + '\n')
                payload = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        server = HTTPServer(('127.0.0.1', config['port']), Handler)
        write(output / 'READY.json', {'identity': engine.identity, 'pid': os.getpid(), 'at': time.time(),
                                      'endpoint': 'http://127.0.0.1:' + str(server.server_port)})
        try:
            server.serve_forever()
        finally:
            server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path, help='private reviewed local package and bearer-token configuration')
    serve(read(parser.parse_args().config))
