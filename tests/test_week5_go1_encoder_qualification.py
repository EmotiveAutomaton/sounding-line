"""Refusal checks for the real-encoder qualification; no pretrained model here."""
import numpy as np
import pytest
from runners.drive.cards import week5_go1_encoder_qualification as q


def valid():
    a = np.zeros((len(q.TEXTS),384),dtype=np.float32)
    for i in range(len(a)): a[i,i] = 1
    a[2] = a[1]
    return a


def test_valid_reference():
    q.validate(valid(),valid())


@pytest.mark.parametrize('fault',['shape','dtype','nan','norm','duplicate','constant','reference'])
def test_refusal(fault):
    a=valid(); expected=a.copy()
    if fault=='shape': a=a[:2]
    elif fault=='dtype': a=a.astype(np.float64)
    elif fault=='nan': a[0,0]=np.nan
    elif fault=='norm': a[0,0]=2
    elif fault=='duplicate': a[2]=a[0]
    elif fault=='constant': a[:]=a[0]
    elif fault=='reference': expected[0]=a[3]
    with pytest.raises(ValueError): q.validate(a,expected)


def test_refusal_cannot_silently_pass():
    with pytest.raises(AssertionError): q.refused(lambda:None)


def test_no_corpus_inputs(tmp_path):
    with pytest.raises(ValueError): q.calculate(tmp_path,{'documents':'forbidden'}, {})
