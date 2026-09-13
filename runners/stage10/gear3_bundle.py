"""Allowlisted, hash-checked cloud inputs, never a working-directory upload.

DESIGN CHECK: LESSONS2-5. Only selected manifests, required Python source and
reviewed public executor code enter. Eval labels, caches, secrets and unrelated
files fail the inventory. Constructed poison files must not be collected.
"""
import ast
import hashlib
import importlib.util
from pathlib import Path
import shutil
from . import gear3_batch as batch,gear3_io as storage,ollama
from .contracts import digest
from .executor import source_identity
from .queue import read


def source_closure(repo):
    pending=['runners.stage10.gear3_worker','runners.stage10.executor_worker'];found={}
    def resolve(name):
        path=repo/Path(*name.split('.'))
        for p in (path.with_suffix('.py'),path/'__init__.py'):
            if p.is_file():return p
        return None
    while pending:
        name=pending.pop();p=resolve(name)
        if p is None or p.relative_to(repo).as_posix() in found:continue
        relative=p.relative_to(repo).as_posix();found[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
        package=name if p.name=='__init__.py' else name.rpartition('.')[0]
        for part in range(1,len(name.split('.'))):
            parent='.'.join(name.split('.')[:part])
            if (repo/Path(*parent.split('.'))/'__init__.py').exists():pending.append(parent)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
            if isinstance(node,ast.Import):pending.extend(n.name for n in node.names)
            elif isinstance(node,ast.ImportFrom):
                base=importlib.util.resolve_name('.'*node.level+(node.module or ''),package) if node.level else node.module
                if base:
                    pending.append(base);pending.extend(base+'.'+n.name for n in node.names if n.name!='*')
    if not {'runners/stage10/gear3_batch.py','runners/stage10/ollama.py','runners/stage10/gear3_io.py'}<=set(found):
        raise ValueError('required execution source closure missing')
    return found


def build(repo,manifests,ghost_root,destination,*,mode,profiles,server_version):
    if mode not in {'cache','science'} or destination.exists():raise ValueError('new bounded input bundle required')
    if mode=='science' and not manifests:raise ValueError('empty scientific invocation')
    closure=source_closure(repo)
    if any(m['source_hashes']!=closure for m in manifests):raise ValueError('manifest does not bind complete execution source closure')
    for m in manifests:batch.validate(m)
    root=destination/'contents';root.mkdir(parents=True)
    for name,expected in closure.items():
        original=repo/name;target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
        raw=original.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('source changed during export')
        target.write_bytes(raw)
    native=source_identity(ghost_root)
    allowed=['ARCHIVE_MEMBER_MANIFEST.json','PUBLIC_MANIFEST.json']+['public/consumer/'+p for p in native['public_sources']]
    for name in allowed:
        source=ghost_root/name;target=root/'ghost-public'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    # No observation files are copied: only selected typed envelopes in blocks.
    names=[]
    for m in manifests:
        name='blocks/'+m['block_id']+'.json';names.append(name);ollama.write_new(root/name,m)
    job={'schema':'gear3.job.1','mode':mode,'blocks':names,'profiles':profiles,'server_version':server_version,
         'block_sha256':{name:digest(m) for name,m in zip(names,manifests)},
         'execution_source_hashes':closure,'native_source_identity':native,
         'scope':'selected public target records and permitted training answers only'}
    ollama.write_new(root/'JOB.json',job)
    observed=storage.inventory(root)
    expected=set(closure)|{'ghost-public/'+x for x in allowed}|set(names)|{'JOB.json'}
    if set(observed)!=expected:raise ValueError('unexpected member in cloud input archive')
    receipt=storage.make_archive(root,destination/'INPUT.zip')
    ollama.write_new(destination/'BUNDLE.json',{'job_sha256':digest(job),'archive':receipt,'source_hashes':closure,
        'blocks':[{'id':m['block_id'],'sha256':digest(m)} for m in manifests],
        'training_labels_permitted':True,'evaluation_targets_exported':False})
    return receipt


def validate_input(bundle,repo,ghost_root):
    import zipfile
    checked=storage.verify_archive(bundle);closure=source_closure(repo);native=source_identity(ghost_root)
    with zipfile.ZipFile(bundle) as z:
        job=__import__('json').loads(z.read('JOB.json'))
        if set(job)!={'schema','mode','blocks','profiles','server_version','block_sha256','execution_source_hashes','native_source_identity','scope'} or job['schema']!='gear3.job.1':
            raise ValueError('unrecognized cloud input job')
        if job['execution_source_hashes']!=closure or job['native_source_identity']!=native:
            raise ValueError('cloud code is not the inspected local/native closure')
        if job['server_version']!='0.32.14' or set(job['profiles'])!=set(batch.PINS):raise ValueError('unfrozen model package')
        for k,v in job['profiles'].items():
            p=ollama.ReaderProfile(**v)
            if p.model!='qwen3.5:'+k or p.model_digest!=batch.PINS[k] or p.server_version!=job['server_version']:
                raise ValueError('reader profile differs from prescribed pin')
        allowed=set(closure)|{'JOB.json','ghost-public/ARCHIVE_MEMBER_MANIFEST.json','ghost-public/PUBLIC_MANIFEST.json'}|set(job['blocks'])|{'ghost-public/public/consumer/'+p for p in native['public_sources']}
        if set(checked['files'])!=allowed:raise ValueError('extra data or missing source in cloud upload')
        if job['mode'] not in {'cache','science'} or (job['mode']=='cache' and job['blocks']) or (job['mode']=='science' and not job['blocks']):raise ValueError('empty or unexpected cloud work')
        if set(job['block_sha256'])!=set(job['blocks']) or len(set(job['blocks']))!=len(job['blocks']):raise ValueError('block identity roster differs')
        for name in job['blocks']:
            m=__import__('json').loads(z.read(name));batch.validate(m)
            if digest(m)!=job['block_sha256'][name] or m['source_hashes']!=closure or m['profiles']!=job['profiles']:
                raise ValueError('frozen block code/profile/content differs')
        for name,expected in closure.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=expected:raise ValueError('bundled source bytes changed')
        public=z.read('ghost-public/PUBLIC_MANIFEST.json')
        original=(ghost_root/'PUBLIC_MANIFEST.json').read_bytes()
        archive=__import__('json').loads(z.read('ghost-public/ARCHIVE_MEMBER_MANIFEST.json'))
        if public!=original or hashlib.sha256(public).hexdigest()!=archive['files']['PUBLIC_MANIFEST.json']['sha256']:
            raise ValueError('native public manifest changed')
        for name,expected in native['public_sources'].items():
            if hashlib.sha256(z.read('ghost-public/public/consumer/'+name)).hexdigest()!=expected:raise ValueError('bundled native bytes changed')
    return job,checked
