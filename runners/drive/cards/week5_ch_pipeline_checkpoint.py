"""Private transactional helpers for prospective CH pipeline successors.

DESIGN CHECK: LESSONS 3-5. Frozen inputs and scientific configuration bind each
checkpoint. Only a sealed new-attempt copy is reusable; owner requests are
operational and never evidence of a finished source population.
"""
from pathlib import Path
import hashlib,json,time
from .week5_ch_source import digest,write_json
from .week5_ch_engine_bounded import requested


def binding(inputs,config,implementation):
    quantum=config.get('max_new_draws')
    if quantum is not None and (type(quantum) is not int or quantum<1):raise ValueError('Positive integral operational quantum required')
    return dict(inputs=inputs,config={k:v for k,v in config.items() if k!='max_new_draws'},
                implementation=dict(implementation,checkpoint_helper=digest(__file__)))


class YieldRequested(Exception):pass


def require(root):
    if requested(Path(root)):
        raise YieldRequested('Owner request at source authentication boundary')


def file_digest(path,check=None):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            if check is not None:check()
            chunk=stream.read(8*1024**2)
            if not chunk:break
            h.update(chunk)
    return h.hexdigest()


def checked(spec,check=None):
    path=Path(spec['path'])
    if file_digest(path,check)!=spec['sha256']:raise ValueError('Pinned input changed')
    return path


def copied(path,root,check=None):
    path=Path(path);root=Path(root)
    record=root.parent/'RESUMED_FROM.json'
    if not record.exists():raise ValueError('Checkpoint needs a new sealed runtime attempt')
    expected=json.loads(record.read_text(encoding='utf8'))['copied']
    if expected.get(path.relative_to(root).as_posix())!=file_digest(path,check):raise ValueError('Copied checkpoint hash differs')


def get(con,key):
    row=con.execute('SELECT value FROM _week5_runtime WHERE key=?',(key,)).fetchone()
    return None if row is None else json.loads(row[0])


def put(con,key,value):
    con.execute('INSERT OR REPLACE INTO _week5_runtime VALUES(?,?)',(key,json.dumps(value,sort_keys=True)))


def initialize(con,identity,state):
    con.execute('CREATE TABLE IF NOT EXISTS _week5_runtime(key TEXT PRIMARY KEY,value TEXT)')
    old=get(con,'binding')
    if old is not None and old!=identity:raise ValueError('Changed checkpoint contract')
    if old is None:put(con,'binding',identity);put(con,'state',state);con.commit()
    return get(con,'state')


class Control:
    def __init__(self,output,request_root,config,operation):
        self.output=Path(output);self.root=Path(request_root);self.operation=operation
        self.started=time.process_time();self.new=0
        self.quantum=config.get('max_new_draws') if operation=='execute' else None
    def stop(self):return requested(self.root) or (self.quantum is not None and self.new>=self.quantum)
    def tick(self,amount,done,total):
        self.new+=amount
        value=dict(operation=self.operation,completed=done,total=total,new_this_invocation=self.new,
                   invocation_cpu_seconds=time.process_time()-self.started,complete=False)
        write_json(self.output/'PROGRESS.json',value,mutable=True)
        if total and done>=max(1,(total+19)//20) and self.new and not (self.output/'PILOT.json').exists():
            write_json(self.output/'PILOT.json',dict(value,basis='recorded source-row transaction; decompression and setup charged; not final science',
                       forecast_same_phase_cpu_seconds=value['invocation_cpu_seconds']*total/self.new))
    def yielded(self,done,total):
        return dict(status='yielded',reason='Owner request or CH source checkpoint quantum',
                    phase=self.operation,completed=done,total=total)


def seal(output,identity,files,check=None):
    write_json(Path(output)/'SOURCE_SEAL.json',dict(binding=identity,files={n:file_digest(Path(output)/n,check) for n in files}))


def sealed(output,identity,check=None):
    path=Path(output)/'SOURCE_SEAL.json'
    if not path.exists():return False
    value=json.loads(path.read_text(encoding='utf8'))
    if value['binding']!=identity or any(file_digest(Path(output)/n,check)!=h for n,h in value['files'].items()):raise ValueError('Sealed source changed')
    return True


def guarded(function,output,inputs,config):
    try:return function(output,inputs,config)
    except YieldRequested:
        return dict(status='yielded',reason='Owner request during complete file authentication/finalization; no partial hash accepted',
                    phase='authentication_or_finalization',verification_prefix_credited=False)
