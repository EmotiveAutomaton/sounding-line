"""Exact objective curvature, retained-fit parity and actual recovery replay."""
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import menus_d2_certified_solver as s
from runners.drive.cards import menus_d2_canonical as prior
from runners.drive.cards import menus_d2_canonical_recovery as c
from runners.drive.cards.menus_io import read, write, sha256, assert_equal
from tests.test_drive_cards_menus_d2_diagnostic import fixture
from tests.test_drive_cards_d2_canonical import complete_pilot


def problem(seed=71):
    rng = np.random.default_rng(seed)
    matrices = [rng.normal(size=(n, 4)) for n in (2, 3, 5, 2, 7, 4)]
    return s.old.pack(matrices, [0, 1, 2, 0, 3, 1])


def test_hessian_finite_difference_and_positive_curvature():
    data = problem(); beta = np.array([.3, -.2, .6, .1]); penalty = .1
    eps = 1e-5
    numerical = np.column_stack([(s.old.objective(beta+eps*e, data, penalty)[1]
        - s.old.objective(beta-eps*e, data, penalty)[1])/(2*eps) for e in np.eye(4)])
    actual = s.hessian(beta, data, penalty)
    np.testing.assert_allclose(actual, numerical, atol=1e-9, rtol=1e-8)
    assert np.linalg.eigvalsh(actual).min() >= penalty


def test_certified_parity_null_and_planted_refinement():
    with threadpool_limits(limits=1):
        data = problem()
        expected, certificate = s.old.fit(data, .1)
        actual, other = s.fit(data, .1)
        assert np.array_equal(actual, expected) and other == certificate
        balanced = s.old.pack([np.array([[-1.], [1.]])]*100, [0, 1]*50)
        beta, cert = s.refine(balanced, .1, np.array([2.]))
        assert abs(beta[0]) < 1e-7 and cert['gradient_max'] <= 1e-8
        planted = s.old.pack([np.array([[-1.], [1.]])]*100, [1]*90+[0]*10)
        beta, cert = s.refine(planted, .1, np.array([-2.]))
        oracle, _ = s.old.fit(planted, .1)
        np.testing.assert_allclose(beta, oracle, atol=1e-7, rtol=0)
        assert beta[0] > 0 and cert['objective'] <= cert['initial_objective']
        with pytest.raises(ValueError): s.refine(data, 0, np.zeros(4))
        with pytest.raises(ValueError): s.refine(data, .1, np.full(4, np.nan))


def test_actual_fallback_and_unrelated_error_not_swallowed(monkeypatch):
    data = problem(); expected = s.old.fit(data, .1)[0]
    def stopped(*args): raise ValueError('uncertified choice fit: fixture boundary')
    monkeypatch.setattr(s.old, 'fit', stopped)
    beta, certificate = s.fit(data, .1)
    np.testing.assert_allclose(beta, expected, atol=1e-6, rtol=0)
    assert certificate['refinement'] == 'exact_hessian_newton_v1'
    assert certificate['gradient_max'] <= 1e-8
    def invalid(*args): raise ValueError('malformed input')
    monkeypatch.setattr(s.old, 'fit', invalid)
    with pytest.raises(ValueError, match='malformed'): s.fit(data, .1)


def test_complete_recovery_retains_bytes_reentry_fresh_replay_and_tamper(tmp_path):
    inputs = fixture(tmp_path/'source')
    fullinputs = complete_pilot(tmp_path/'pilot', inputs)
    failed = tmp_path/'failed'; output = failed/'output'; output.mkdir(parents=True)
    config = prior.CONFIG | dict(mode='full')
    write(output/'YIELD_REQUEST.json', dict(reason='constructed interruption'))
    assert prior.execute(output, fullinputs, config)['status'] == 'yielded'
    write(failed/'PLAN.json', dict(module='runners.drive.cards.menus_d2_canonical',
        config=config, inputs=fullinputs, pins={}))
    write(failed/'FAILED.json', dict(status='FAILED', synthetic_fixture=True))
    files = {p.relative_to(failed).as_posix():sha256(p) for p in failed.rglob('*') if p.is_file()}
    manifest = tmp_path/'RECOVERY.json'
    write(manifest, dict(root=str(failed), files=files, failed_attempt_seconds=1))
    recovered = tmp_path/'recovered'
    recovery_inputs = fullinputs | dict(recovery_manifest=str(manifest))
    result = c.execute(recovered, recovery_inputs, config)
    assert result['repeated_outcome_control']['total'] == 200
    for rel,h in files.items():
        if rel.startswith('output/recipients/'):
            assert sha256(recovered/Path(rel).relative_to('output')) == h
    before = {p.relative_to(recovered).as_posix():sha256(p) for p in recovered.rglob('*') if p.is_file()}
    assert_equal(c.execute(recovered, recovery_inputs, config), result)
    assert before == {p.relative_to(recovered).as_posix():sha256(p) for p in recovered.rglob('*') if p.is_file()}
    request = tmp_path/'REQUEST.json'
    write(request, dict(output=str(recovered), inputs=recovery_inputs, config=config))
    code = 'import json,sys;from runners.drive.cards.menus_d2_canonical_recovery import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["verified"]'
    env = os.environ.copy(); env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONHASHSEED='617')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=120)
    chosen = next((output/'recipients').rglob('*.json.gz'))
    chosen.write_bytes(chosen.read_bytes()+b' ')
    with pytest.raises(ValueError,match='evidence changed'): c.verify(recovered,recovery_inputs,config)
