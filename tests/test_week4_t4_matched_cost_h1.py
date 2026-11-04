import copy
import json
import numpy as np
import pytest
from runners.drive.cards import week4_t4_inputs as source
from runners.drive.cards import week4_t4_matched_cost as original
from runners.drive.cards import week4_t4_matched_cost_h1 as cost
from runners.drive.cards import week4_t4_kernel_h1 as kernel
from runners.stage14.common import filehash


def test_generated_targets_and_original_fit_certificate():
    packed = source.assemble(source.fixture(), 2, 3)
    changed = copy.deepcopy(packed)
    changed['train']['y'] = [5]*len(changed['train']['y'])
    for law in (False, True):
        data = original.generated(packed, 20261102, law)
        other = original.generated(changed, 20261102, law)
        assert all(np.array_equal(data[k], other[k]) for k in data)
        for individual in (False, True):
            result = kernel.fit(data, individual)
            assert result['reference_projected_gradient'] <= 1e-5
            assert abs(result['reference_objective']-result['objective']) <= 1e-9


def test_complete_native_replay_and_changed_fit_refusal(tmp_path):
    config = cost.configuration('constructed')
    cost.execute(tmp_path, {}, config)
    assert cost.verify(tmp_path, {}, config)['complete_generated_fit_replay']
    rows = json.loads((tmp_path/'PRIVATE_FITS.json').read_text())
    rows[0]['shared']['theta'][0] += .01
    (tmp_path/'PRIVATE_FITS.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='replay'):
        cost.verify(tmp_path, {}, config)


def test_completed_producers_and_failed_or_altered_bank(tmp_path):
    rows = []
    fixture = source.fixture()
    for writer in range(25):
        for half, start in (('train', 0), ('test', 100)):
            for i in range(24):
                row = copy.deepcopy(fixture[i % 4])
                row.update(key=f'{writer}-{half}-{i}', writer=str(writer),
                           session=f'{writer}-{half}', half=half, open_at=start+i)
                rows.append(row)
    packed = source.assemble(rows)
    roots = {key: tmp_path/key for key in ('inputs', 'bank', 'kernel')}
    for root in roots.values():
        (root/'output').mkdir(parents=True)
    def freeze(root, names):
        (root/'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE',
            fresh_process_verified=True, outputs={n: filehash(root/n) for n in names})))
    source.gzip_equal(roots['inputs']/'output/PRIVATE_DATA.json.gz', packed)
    (roots['inputs']/'output/SUMMARY.json').write_text(json.dumps(dict(packed['summary'], mode='full')))
    freeze(roots['inputs'], ['output/PRIVATE_DATA.json.gz', 'output/SUMMARY.json'])
    for name in ('bank', 'kernel'):
        (roots[name]/'output/SUMMARY.json').write_text(json.dumps(dict(complete_bank=True, bank_gate=True, worlds=40)))
    freeze(roots['bank'], ['output/SUMMARY.json'])
    (roots['kernel']/'PLAN.json').write_text(json.dumps(dict(module='runners.drive.cards.week4_t4_kernel_h1', config=kernel.configuration('full'))))
    freeze(roots['kernel'], ['PLAN.json', 'output/SUMMARY.json'])
    inputs = {key+'_completion': str(root/'COMPLETE.json') for key, root in roots.items()}
    assert cost.load(inputs) == packed
    (roots['kernel']/'output/SUMMARY.json').write_text(json.dumps(dict(complete_bank=True, bank_gate=False, worlds=40)))
    freeze(roots['kernel'], ['PLAN.json', 'output/SUMMARY.json'])
    with pytest.raises(ValueError, match='recovery validation'):
        cost.load(inputs)
    (roots['kernel']/'output/SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        cost.load(inputs)
