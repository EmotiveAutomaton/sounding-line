import numpy as np
from runners.drive.cards import week5_bk_t4_weights as model
from runners.drive.cards.week5_bk_t4_fixture import fixture_bundle
from runners.drive.cards import week5_bk_t4_texture as texture


def test_identified_gradient_and_coordinates():
    assert all(model.known_answers().values())


def test_unit_directions_cover_negative_weights():
    for v in ([1,0,0,0,0],[-1,0,0,0,0],[0,-1,0,0,0],[0,0,0,0,-1]):
        u,_=model.directions(model.angles_of(v)[None,:])
        assert np.allclose(u[0],v,atol=1e-12)


def test_genre_fallback_preserves_both_halves_and_clusters():
    bundle=fixture_bundle()
    for half in ('train','test'):
        bundle['packed'][half]=dict(bundle['packed'][half],genres=['creative']*36)
    out=texture.genre_bundle(bundle,'creative')
    assert out['texture_scope']['requires_pooled_fallback']
    assert len(out['packed']['writers'])==3
    assert len(out['packed']['train']['w'])==36
