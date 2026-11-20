import csv
import pytest
from runners.drive.cards.week6_sealed_support_v1 import (
    write_tables, unique_people, ReadBudget, SealedFailure, force_threads)


def test_counts_people_not_repeated_rows(tmp_path):
    assert unique_people([1]*100 + [2]*100) == 2
    with pytest.raises(SealedFailure): write_tables(tmp_path, {'status':[dict(n=2, state='present')]})
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(SealedFailure): unique_people(None)


@pytest.mark.parametrize('n', [11.0, 11.9, True, -1, None])
def test_not_integer_counts_rejected(tmp_path, n):
    with pytest.raises(SealedFailure): write_tables(tmp_path, {'status':[dict(n=n)]})


def test_suppression_and_csv_integer_boundary(tmp_path):
    receipt = write_tables(tmp_path, {'status':[dict(n=10, state='small'), dict(n=11, state='present')]})
    assert receipt['dropped'] == {'status': 1}
    with (tmp_path/'status.csv').open() as f:
        assert list(csv.DictReader(f)) == [dict(n='11', state='present')]


def test_row_and_byte_caps_refuse_before_any_file(tmp_path):
    for rows in ([dict(n=11)]*2001, [dict(n=11, value='x'*262144)]):
        with pytest.raises(SealedFailure): write_tables(tmp_path, {'status':rows})
        assert list(tmp_path.iterdir()) == []


def test_read_budget_counts_repeat_reads_and_refuses_outside(tmp_path):
    root = tmp_path/'data'; root.mkdir()
    p = root/'test.csv'; p.write_bytes(b'0123456789')
    b = ReadBudget(root, maximum=20)
    assert b.reserve(p, passes=2) == p
    with pytest.raises(SealedFailure): b.reserve(p)
    outside = tmp_path/'outside'; outside.write_text('x')
    with pytest.raises(SealedFailure): b.reserve(outside)


def test_thread_limit_overrides_inherited_environment(monkeypatch):
    import os
    monkeypatch.setenv('OPENBLAS_NUM_THREADS', '32')
    for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','CUDA_VISIBLE_DEVICES'):
        monkeypatch.setenv(name, os.environ.get(name, ''))
    force_threads(2)
    assert os.environ['OPENBLAS_NUM_THREADS'] == '2'
    with pytest.raises(ValueError): force_threads(5)
