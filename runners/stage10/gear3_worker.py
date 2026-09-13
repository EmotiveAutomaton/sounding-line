"""Bounded remote worker, invoked only by the campaign branch of gear3.py.

DESIGN CHECK: LESSONS3-5. Original expiration survives preemption; a durable
STARTED without terminal status refuses replay. Every model request is committed
before dispatch; all outputs and failures are exported. No private evaluator or
local GPU lock is used. A refused/invalid route remains an observed failure.
"""
import json
import os
from pathlib import Path
import subprocess
import shutil
import threading
import time
import uuid
import urllib.request
from . import gear3_batch as batch,ollama
from .contracts import digest
from .gear3_io import durable_attempts,make_archive,verify_archive
from .queue import read


def run(volume,reservation,bundle_path,mode):
    root=Path('/campaign');invocation=reservation['invocation_id']
    if not invocation or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in invocation):
        raise ValueError('unsafe invocation identifier')
    output=root/'attempts'/invocation;expires=reservation['expires_at']
    volume.reload()
    output.mkdir(parents=True,exist_ok=True)
    if (output/'TERMINAL.json').exists():
        # A provider replay returns existing transport identity, not another run.
        terminal=read(output/'TERMINAL.json')
        if terminal['reservation_sha256']!=digest(reservation):raise ValueError('terminal reservation changed')
        return terminal
    if (output/'STARTED.json').exists():
        # A preempted worker may have sent a request without receiving its reply.
        # Preserve the attempt; recovery is a separate charged controller action.
        raise RuntimeError('preempted/uncertain invocation retained; automatic replay refused')
    if time.time()>=expires-15:raise TimeoutError('original reservation expired before startup')
    source=Path('/repo');bundle=root/bundle_path
    archive=verify_archive(bundle,source)
    job=read(source/'JOB.json')
    if job['mode']!=mode or mode not in {'cache','science'}:raise ValueError('cloud job mode changed')
    if reservation.get('recovery_of'):
        prior=root/'attempts'/reservation['recovery_of']
        if not prior.is_dir():raise ValueError('recorded prior attempt is unavailable')
        if (prior/'blocks').exists():shutil.copytree(prior/'blocks',output/'blocks')
        if any(not p.with_name('ATTEMPT.json').exists() for p in (output/'blocks').rglob('REQUEST.json')):
            raise ValueError('prior request outcome uncertain; no repeated inference allowed')
    started=time.time();server=None;monitor_thread=None;stop=threading.Event();peak={'observed_gpu_memory_mib':0,'samples':0}
    # Scalar GPU observations only; all model text remains in the private archive.
    def monitor():
        while not stop.wait(2):
            try:
                p=subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
                if p.returncode==0:
                    peak['observed_gpu_memory_mib']=max(peak['observed_gpu_memory_mib'],int(p.stdout.strip().splitlines()[0]));peak['samples']+=1
            except (OSError,ValueError,subprocess.TimeoutExpired):pass
    status='FAILED';error=None;models=[]
    with durable_attempts(output,reservation,volume.commit):
        ollama.write_new(output/'STARTED.json',{'at':ollama.now(),'reservation':reservation,'input_archive':archive,'mode':mode,
            'container_id':os.environ.get('MODAL_TASK_ID'),'pid':os.getpid(),'attempt_nonce':uuid.uuid4().hex})
        try:
            env={**os.environ,'OLLAMA_MODELS':str(root/'models'),'OLLAMA_HOST':'127.0.0.1:11434',
                'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_CONTEXT_LENGTH':'16384'}
            with (output/'ollama.log').open('x',encoding='utf8') as log:
                server=subprocess.Popen(['ollama','serve'],env=env,stdout=log,stderr=subprocess.STDOUT)
                deadline=min(expires-15,time.time()+60)
                while time.time()<deadline:
                    if server.poll() is not None:raise RuntimeError('pinned model server exited during startup')
                    try:
                        if ollama.api('/api/version')['version']!=job['server_version']:raise ValueError('cloud server version mismatch')
                        break
                    except urllib.error.URLError:time.sleep(.25)
                else:raise TimeoutError('bounded server startup expired')
                if mode=='cache':
                    for key in ('9b','27b'):
                        profile=ollama.ReaderProfile(**job['profiles'][key])
                        remaining=int(expires-time.time()-20)
                        if remaining<1:raise TimeoutError('no model-cache time remains')
                        with (output/(key+'-pull.log')).open('x',encoding='utf8') as log:
                            p=subprocess.run(['ollama','pull',profile.model],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                        if p.returncode:raise RuntimeError('pinned model download failed')
                        identity=ollama.identity(profile=profile);models.append(identity)
                        ollama.write_new(output/(key+'-CACHE.json'),identity)
                        volume.commit()
                else:
                    monitor_thread=threading.Thread(target=monitor,daemon=True);monitor_thread.start()
                    active=None;loads=0
                    def before_model(profile):
                        nonlocal active,loads
                        if active is not None:
                            response=ollama.api('/api/generate',{'model':active.model,'keep_alive':0,'stream':False})
                            ollama.write_new(output/f'unload-{loads:03d}.json',response)
                        identity=ollama.identity(profile=profile);loads+=1
                        ollama.write_new(output/f'model-{loads:03d}.json',identity)
                        request={'model':profile.model,'keep_alive':-1,'stream':False,
                                 'options':{'num_ctx':16384,'num_thread':2}}
                        ollama.write_new(output/f'load-{loads:03d}-request.json',request)
                        response=ollama.api('/api/generate',request)
                        ollama.write_new(output/f'load-{loads:03d}-raw.json',response)
                        running=ollama.api('/api/ps');ollama.write_new(output/f'load-{loads:03d}-memory.json',running)
                        if len(running.get('models',[]))!=1 or running['models'][0]['digest']!=profile.model_digest:
                            raise ValueError('wrong or multiple loaded model packages')
                        active=profile;models.append(identity)
                    for name in job['blocks']:
                        manifest=read(source/name)
                        batch.run_block(manifest,output/'blocks'/manifest['block_id'],
                                        ghost_root=source/'ghost-public',before_model=before_model)
                    status='COMPLETE'
                status='COMPLETE'
        except Exception as exc:
            error={'type':type(exc).__name__,'message':str(exc)}
            ollama.write_new(output/'ERROR.json',error)
        finally:
            stop.set()
            if monitor_thread is not None:monitor_thread.join(timeout=4)
            if server is not None:
                server.terminate()
                try:server.wait(timeout=5)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
            terminal={'status':status,'at':ollama.now(),'mode':mode,'reservation_sha256':digest(reservation),
                'duration_seconds':time.time()-started,'original_expires_at':expires,'error':error,'model_identities':models,
                'gpu_observation':peak,'owner_ended':True,'source_archive_sha256':archive['archive_sha256'],
                'archive_path':'exports/'+invocation+'.zip','billing':'service time only; provider invoice remains separate'}
            ollama.write_new(output/'TERMINAL.json',terminal)
    # The archive is outside the attempt tree; it contains TERMINAL and all logs.
    export=root/terminal['archive_path'];export.parent.mkdir(parents=True,exist_ok=True)
    make_archive(output,export);volume.commit()
    return terminal
