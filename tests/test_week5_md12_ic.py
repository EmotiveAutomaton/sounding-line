import numpy as np
import pytest
from runners.drive.cards import week5_md12_ic as ic


def test_signed_fit_and_zero_reference_are_reachable():
    rng=np.random.default_rng(91);x=rng.normal(size=(30,12,7));x-=x[:,:10].mean(axis=1)[:,None,:]
    for sign in [-1,1]:
        y=x[:,:,:4]@np.array([.3,.2,-.1,.01])+sign*.03*x[:,:,4]
        bank=[ic.md.stats(x,y)]*len(ic.md.GAMMAS)
        gain,coefficient,gamma=ic.estimate(bank,'MD1.ic',1)
        assert abs(coefficient-sign*.03)<1e-10 and abs(gain-1)<1e-9
        y=x[:,:,:4]@np.array([.3,.2,-.1,.01])+sign*.01*x[:,:,5]
        result=ic.estimate([ic.md.stats(x,y)]*len(ic.md.GAMMAS),'MD2.ic',1)
        assert abs(result[0]-sign*.01)<1e-10
    with pytest.raises(ValueError):ic.estimate([ic.md.stats(x,np.zeros((30,12)))]*len(ic.md.GAMMAS),'MD1.ic',1)


def test_oracle_dose_fixed_without_recovery_search():
    rng=np.random.default_rng(74);x=rng.normal(size=(40,12,7));x-=x[:,:10].mean(axis=1)[:,None,:]
    y=x[:,:,0]+.5*x[:,:,4]+rng.normal(size=(40,12))
    worlds,dose=ic.planted_worlds([x]*len(ic.md.GAMMAS),y,0,'MD1.ic')
    a=dose['coefficient_magnitude'];energy=a*a*dose['heldout_residual_level_energy'];noise=dose['heldout_noise_energy']
    assert abs(energy/(energy+noise)-.01)<1e-14
    assert np.allclose((worlds[0][1]+worlds[2][1])/2,worlds[1][1])
    assert dose['recovered_gain_is_not_oracle_gain']
