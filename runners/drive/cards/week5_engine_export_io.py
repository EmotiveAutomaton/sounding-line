"""Shared local-only engine export boundaries; no model or source acquisition."""
from pathlib import Path
import json
import shutil
from . import week5_qualification_io as io


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def complete(root,module):
    root=Path(root).resolve();done=read(root/'COMPLETE.json')
    if done.get('status')!='COMPLETE' or done.get('fresh_process_verified') is not True:
        raise ValueError('Complete independently verified export dependency required')
    if any((root/name).exists() for name in ('PAUSED.json','FAILED.json')):
        raise ValueError('Ambiguous dependency terminal')
    for name,expected in done['outputs'].items():
        path=root/name;path.resolve().relative_to(root)
        if path.is_symlink() or io.sha(path)!=expected:raise ValueError('Dependency output changed')
    plan=read(root/'PLAN.json')
    if plan.get('module')!=module or read(root/'VERIFIED.json').get('verified') is not True:
        raise ValueError('Dependency producer or independent verification differs')
    for name in ('PLAN.json','VERIFIED.json'):
        if done['outputs'].get(name)!=io.sha(root/name):raise ValueError('Dependency native metadata is not sealed')
    return root,plan,done


def checkpoint(path,value):
    path=Path(path);io.write_json(path,value);io.write_json(path.with_suffix('.seal.json'),{'sha256':io.sha(path)})


def state(path,binding,initial):
    path=Path(path)
    if not path.exists():return {'binding':binding,**initial}
    if io.sha(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('Export checkpoint changed')
    value=read(path)
    if value['binding']!=binding:raise ValueError('Export checkpoint source/semantic binding changed')
    return value


def replay_bundle(left,right):
    left,right=Path(left),Path(right)
    names=lambda root:{p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    expected=names(left)
    if expected!=names(right) or not expected:raise ValueError('Complete export replay inventory differs')
    if any(io.sha(left/name)!=io.sha(right/name) for name in expected):raise ValueError('Every export field must independently replay')


def materialize(run_root,destination,*,card,module,producer_sha256):
    if card not in ('EX2','EX3'):raise ValueError('Uncommissioned export route')
    repo=Path(__file__).resolve().parents[3]
    allowed=repo/'corpora/store/exports/engine_bench_20261111'/card
    destination=Path(destination).resolve()
    if destination!=allowed.resolve() or destination.exists():raise ValueError('Only the new named local ignored export is allowed')
    root,plan,done=complete(run_root,module)
    result=read(root/'output/RESULT.json')
    if result.get('complete_export') is not True or result.get('card')!=card:
        raise ValueError('Partial or unsupported export cannot be copied')
    bundle=root/'output/bundle';manifest=read(bundle/'MANIFEST.json')
    if manifest.get('card')!=card or manifest['source_binding'].get('module_sha256')!=producer_sha256:
        raise ValueError('Export source/producer identity differs')
    expected=set(manifest['files'])|{'MANIFEST.json'}
    actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if expected!=actual:raise ValueError('Export bundle has unexpected members')
    for name in expected:
        path=bundle/name;path.resolve().relative_to(bundle.resolve())
        if path.is_symlink():raise ValueError('Export symlink refused')
        if name!='MANIFEST.json' and io.sha(path)!=manifest['files'][name]:raise ValueError('Export member differs')
    destination.mkdir(parents=True)
    for name in sorted(expected):
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(bundle/name,path)
        if io.sha(path)!=io.sha(bundle/name):raise ValueError('Local export copy differs')
    return {'card':card,'destination':destination.relative_to(repo).as_posix(),
            'files':{name:io.sha(destination/name) for name in sorted(expected)}}
