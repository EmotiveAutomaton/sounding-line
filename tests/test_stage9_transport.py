"""Bounded transport changes must reach the actual choice request and stay scoped."""
import json
import hashlib
import importlib.util
import sys,types
import pytest
from runners.stage9 import package_calibration as calibration,features
from runners.stage9.common import REPO,digest
from runners import readout_repair


@pytest.fixture
def reader(monkeypatch):
    # Match the runtime's copied sibling modules without adding a nonexistent
    # runners.stage9.readout production module or changing installed source.
    name='_s9_transport_reader_fixture'
    package=types.ModuleType(name);package.__path__=[]
    for key,module in [(name,package),(name+'.readout',readout_repair),(name+'.features',features)]:
        monkeypatch.setitem(sys.modules,key,module)
    spec=importlib.util.spec_from_file_location(name+'.worker',REPO/'runners/stage9/reader.py')
    module=importlib.util.module_from_spec(spec);monkeypatch.setitem(sys.modules,spec.name,module)
    spec.loader.exec_module(module);return module


def test_cpu_deadline_reaches_wire_without_changing_readout(monkeypatch,reader):
    evidence={'prefix':'public prefix','options':{'second':'STOP','first':'WRITE'}}
    package={'device':'cpu','precision':'float32','model':'fixture','revision':'fixture',
        'adapter_sha256':'fixture','scorer_sha256':'fixture'}
    captured=[]
    class Response:
        def __init__(self,payload):self.payload=payload
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):
            sha=lambda text:hashlib.sha256(text.encode()).hexdigest()
            components=[{'option_id':k,'valid':True,'logprob':-1. if k=='first' else -2.,
                'prefix_sha256':sha(self.payload['prefix']),'continuation_sha256':sha(v),
                'semantics':'sum_log_probability','identity':self.payload['identity']}
                for k,v in self.payload['options'].items()]
            return json.dumps({'valid':True,'identity':self.payload['identity'],
                'components':components}).encode()
    class Opener:
        def open(self,request,timeout):
            payload=json.loads(request.data)
            captured.append({'timeout':timeout,'payload':payload,'url':request.full_url})
            return Response(payload)
    monkeypatch.setenv('S7_ENDPOINT','http://127.0.0.1:1')
    monkeypatch.setenv('S7_TOKEN','fixture-only')
    monkeypatch.setattr(reader.urllib.request,'build_opener',lambda *args:Opener())
    old=reader.run(calibration.call_task(package,evidence,'actual-package-precision-v1'),evidence)
    new=reader.run(calibration.call_task(package,evidence),evidence)
    assert old==new and old['valid'] is True
    assert old['probs']['first']>old['probs']['second']
    assert [r['timeout'] for r in captured]==[600,1800]
    assert captured[0]['payload']==captured[1]['payload']
    assert captured[0]['url']=='http://127.0.0.1:1/infer'


def test_deadline_refuses_unbounded_or_wrong_operation_before_request(monkeypatch,reader):
    evidence={'prefix':'p','options':{'a':'STOP'}}
    identity={'device':'cpu','precision':'float32','information_sha256':digest(evidence)}
    monkeypatch.setattr(reader,'request',lambda *args,**kwargs:pytest.fail('invalid envelope reached model service'))
    for value in (0,-1,1801,1800.,True,'1800',None):
        with pytest.raises(ValueError):reader.run({'operation':'choice','identity':identity,'request_timeout_seconds':value},evidence)
    for change in ({'device':'cuda'},{'precision':'float16'}):
        with pytest.raises(ValueError):reader.run({'operation':'choice','identity':{**identity,**change},'request_timeout_seconds':1800},evidence)
    with pytest.raises(ValueError):reader.run({'operation':'generate','identity':identity,'request_timeout_seconds':1800},evidence)
    assert reader.request_timeout({'operation':'generate','identity':identity})==600


def test_calibration_version_binds_transport_and_preserves_old_calls():
    v2={'operation':'actual-package-precision-v2','transport_seconds':dict(calibration.TRANSPORT_SECONDS)}
    calibration.check_transport(v2)
    calibration.check_transport({'operation':'actual-package-precision-v1'})
    for field in calibration.TRANSPORT_SECONDS:
        for bad in (0,3600,float(calibration.TRANSPORT_SECONDS[field])):
            with pytest.raises(ValueError):calibration.check_transport({**v2,'transport_seconds':{**v2['transport_seconds'],field:bad}})
    for bad in ({'operation':'actual-package-precision-v2'},
                {'operation':'actual-package-precision-v1','transport_seconds':dict(calibration.TRANSPORT_SECONDS)},
                {'operation':'future'}):
        with pytest.raises(ValueError):calibration.check_transport(bad)
    evidence={'prefix':'p','options':{'a':'STOP'}}
    cpu={'device':'cpu','precision':'float32'};gpu={'device':'cuda','precision':'float16'}
    assert calibration.call_task(cpu,evidence,'actual-package-precision-v1')=={'operation':'choice','identity':{**cpu,'information_sha256':digest(evidence)}}
    assert 'request_timeout_seconds' not in calibration.call_task(gpu,evidence)
