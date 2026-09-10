import copy
import math

import pytest

from runners.stage9.comparison_analysis import contrast,select_rival


def rows(prefix='d'):
    return [{'unit':prefix+str(i),'domain':'essay' if i%2 else 'workshop','valid':True,
             'truth':'a' if i%2 else 'b',
             'predictions':{'generic':{'a':.5,'b':.5},
                            'signal':{'a':.8 if i%2 else .2,'b':.2 if i%2 else .8},
                            'wrong':{'a':.2 if i%2 else .8,'b':.8 if i%2 else .2}}} for i in range(12)]


def test_known_gain_null_and_wrong_conditioning_bands():
    data=rows()
    units=[r['unit'] for r in data]
    result=contrast(data,units,left='signal',right='generic',draws=100)
    assert result['overall']['mean']==pytest.approx(math.log(1.6))
    assert result['overall']['disposition']=='SUPPORT CANDIDATE'
    assert set(result['strata']['domain'])=={'essay','workshop'}
    bad=contrast(data,units,left='wrong',right='generic',draws=100)
    assert bad['overall']['disposition']=='COUNTEREVIDENCE'
    for row in data:row['predictions']['signal']=row['predictions']['generic']
    null=contrast(data,units,left='signal',right='generic',draws=100)
    assert null['overall']['mean']==0 and null['overall']['disposition']=='PRACTICALLY SMALL'


def test_rival_is_selected_once_and_cannot_reuse_development():
    data=rows();units=[r['unit'] for r in data]
    package='a'*64
    selected=select_rival(data,units,['generic','signal','wrong'],role='development',package_sha256=package)
    assert selected['selected']=='signal'
    with pytest.raises(ValueError,match='development selection units'):
        contrast(data,units,left='generic',right='signal',selection=selected,package_sha256=package,draws=100)
    future=rows('new');newunits=[r['unit'] for r in future]
    assert contrast(future,newunits,left='generic',right='signal',selection=selected,
                    package_sha256=package,draws=100)['overall']['disposition']=='COUNTEREVIDENCE'
    with pytest.raises(ValueError,match='another contrast'):
        contrast(future,newunits,left='signal',right='generic',selection=selected,package_sha256=package,draws=100)


def test_invalid_missing_and_zero_forecasts_cannot_be_dropped():
    data=rows();units=[r['unit'] for r in data]
    with pytest.raises(ValueError,match='incomplete'):
        contrast(data[:-1],units,left='signal',right='generic',draws=100)
    data[0]['valid']=False
    with pytest.raises(ValueError,match='invalid component'):
        contrast(data,units,left='signal',right='generic',draws=100)
    data[0]['valid']=True
    data[0]['predictions']['signal']={'a':1.,'b':0.}
    result=contrast(data,units,left='signal',right='generic',draws=100)
    assert result['overall']['finite_estimate'] is False
    assert result['overall']['disposition']=='DESCRIPTIVE'
    assert result['excluded_targets']==0 and result['complete_independent_units']==12
