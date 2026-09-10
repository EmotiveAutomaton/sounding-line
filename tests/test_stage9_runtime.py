"""Exercise the real isolated process with complete and corrupt transport evidence."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

from runners.stage9.common import digest
from runners.stage9.runtime import execute


def test_real_capsule_denies_existing_files_reads_and_writes(tmp_path):
    outside = tmp_path / 'truth.json'
    outside.write_text('original hidden truth')
    result = execute(None, {'probe': True, 'forbidden_paths': [str(outside)], 'other_port': 65534}, root=tmp_path / 'caps')
    assert result['accepted'], result
    assert outside.read_text() == 'original hidden truth'
    assert result['receipt']['all_raised'] is True


def test_real_capsule_scores_all_options_and_rejects_missing_component(tmp_path):
    corrupt = [False]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert self.headers['Authorization'] == 'Bearer test-only'
            sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
            rows = [{'option_id': k, 'valid': True, 'logprob': -1 if k == 'x64' else -10,
                     'prefix_sha256': sha(request['prefix']), 'continuation_sha256': sha(v),
                     'semantics': 'sum_log_probability', 'identity': request['identity']}
                    for k, v in request['options'].items()]
            if corrupt[0]:
                rows.pop()
            result = json.dumps({'valid': True, 'identity': request['identity'], 'components': rows}).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(result)))
            self.end_headers()
            self.wfile.write(result)
    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    evidence = {'prefix': 'Discarded transport fixture. Next action:', 'options': {'x'+str(i): ' STOP' if i == 64 else ' act '+str(i) for i in range(65)}}
    identity = dict(model='fixture', revision='fixture', adapter_sha256='fixture', scorer_sha256='fixture', information_sha256=digest(evidence))
    task = {'operation': 'choice', 'identity': identity}
    try:
        endpoint = 'http://127.0.0.1:' + str(server.server_port)
        result = execute(evidence, task, endpoint, 'test-only', root=tmp_path / 'caps')
        assert result['accepted'], result
        assert len(result['prediction']['probs']) == 65
        assert result['prediction']['pred'] == 'x64'
        corrupt[0] = True
        invalid = execute(evidence, task, endpoint, 'test-only', root=tmp_path / 'caps')
        assert not invalid['accepted']
        assert invalid['prediction'] is None
        assert 'missing component' in invalid['error']['traceback']
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
