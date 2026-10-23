import pytest
from pathlib import Path
from runners.drive.cards import week_genre_features_resume as card
from tests.test_drive_week_genre_features_paths import mixed_fixture
from tests.test_drive_week_genre_compare import write


def fixture(root):
    root=Path(root).resolve();inputs=mixed_fixture(root/'source');run=root/'interrupted'
    result=card.base.execute(run/'output',inputs,card.base.CONFIG)
    write(run/'PLAN.json',dict(module=card.base.__name__,config=card.base.CONFIG,inputs=inputs,
        pins={str(Path(v)):card.filehash(v) for v in inputs.values()}))
    write(run/'RESULT.json',result)
    write(run/'FAILED.json',dict(error="TimeoutError('Combined execution/replay bound exceeded')"))
    write(run/'PROGRESS.json',dict(phase='verify'))
    return dict(interrupted_root=str(run))


def test_byte_exact_checkpoint_and_complete_replay(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output'
    card.execute(out,inputs,card.CONFIG)
    assert card.verify(out,inputs,card.CONFIG)['full_source_reconstruction']
    old=Path(inputs['interrupted_root'])/'output'
    assert all((old/n).read_bytes()==(out/n).read_bytes() for n in card.NAMES)


@pytest.mark.parametrize('mutation',['failed','phase','complete','pins','count'])
def test_ineligible_checkpoint_refused(tmp_path,mutation):
    inputs=fixture(tmp_path/'source');run=Path(inputs['interrupted_root'])
    if mutation=='failed':write(run/'FAILED.json',dict(error='unexpected_failure'))
    if mutation=='phase':write(run/'PROGRESS.json',dict(phase='execute'))
    if mutation=='complete':write(run/'COMPLETE.json',dict(status='COMPLETE'))
    if mutation=='pins':
        p=card.read(run/'PLAN.json');p['pins'][next(iter(p['pins']))]='bad';write(run/'PLAN.json',p)
    if mutation=='count':
        s=card.read(run/'output/SUMMARY.json');s['sessions']=0;write(run/'output/SUMMARY.json',s);write(run/'RESULT.json',s)
    with pytest.raises(ValueError):card.execute(tmp_path/'output',inputs,card.CONFIG)
