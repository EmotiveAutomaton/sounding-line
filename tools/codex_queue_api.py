"""Bounded native queue transport for one existing owner. Never starts a turn.

Uses installed experimental thread/queue API. Receipts prove acceptance only.
Ambiguous sends require reconciliation; never retry through a different backend.
"""
from __future__ import annotations
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid


class Client:
    def __init__(self, executable, repo, state):
        self.messages = queue.Queue()
        self.counter = 0
        Path(state).mkdir(parents=True, exist_ok=True)
        self.errors = (Path(state)/'queue-api-stderr.log').open('a', encoding='utf8')
        self.proc = None
        try:
            self.proc = subprocess.Popen([executable, 'app-server'], cwd=repo,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.errors,
                text=True, encoding='utf8', creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            threading.Thread(target=self.read, daemon=True).start()
            self.call('initialize', {'clientInfo':{'name':'soundingline_queue','version':'1'},
                'capabilities':{'experimentalApi':True}})
            self.send({'method':'initialized'})
        except BaseException:
            self.close()
            raise

    def read(self):
        try:
            for line in self.proc.stdout:
                try: self.messages.put(json.loads(line))
                except ValueError: continue
        finally:
            self.messages.put(None)

    def send(self, message):
        self.proc.stdin.write(json.dumps(message)+'\n'); self.proc.stdin.flush()

    def call(self, method, params):
        self.counter += 1
        self.send({'id':self.counter,'method':method,'params':params})
        deadline = time.monotonic()+30
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError('native API response deadline')
            try: message=self.messages.get(timeout=remaining)
            except queue.Empty: raise TimeoutError('native API response deadline') from None
            if message is None: raise OSError('native API closed; inspect private stderr')
            if message.get('id')==self.counter:
                if 'error' in message: raise RuntimeError('native queue API rejected request: '+str(message['error'].get('code')))
                return message['result']

    def close(self):
        if self.proc is not None:
            if self.proc.stdin and not self.proc.stdin.closed:
                try: self.proc.stdin.close()
                except OSError: pass
            try: self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.terminate(); self.proc.wait(timeout=5)
        self.errors.close()


def inventory(client, owner):
    uuid.UUID(owner)
    rows=[]; cursor=None; seen=set()
    for _ in range(10):
        params={'threadId':owner,'limit':100}
        if cursor: params['cursor']=cursor
        page=client.call('thread/queue/list',params)
        rows.extend(page['data']); cursor=page.get('nextCursor')
        if not cursor: return rows
        if cursor in seen: raise ValueError('native queue cursor repeated')
        seen.add(cursor)
    raise ValueError('native queue inventory exceeds bounded inspection')


def enqueue(client, owner, text, event_ids, cancelled=lambda:False):
    if not event_ids: raise ValueError('empty operational event batch')
    request_id=str(uuid.uuid5(uuid.UUID(owner),'sounding-line:'+','.join(sorted(event_ids))))
    expected=[{'type':'text','text':text,'text_elements':[]}]
    matches=[r for r in inventory(client,owner) if r.get('clientUserMessageId')==request_id]
    if len(matches)>1: raise ValueError('duplicate native submission identities')
    if matches:
        result=matches[0]
    else:
        if cancelled(): raise RuntimeError('cancelled before native enqueue')
        result=client.call('thread/queue/add',{'threadId':owner,'input':expected,'clientUserMessageId':request_id})['queuedSubmission']
    if result.get('clientUserMessageId')!=request_id or result.get('input')!=expected:
        raise ValueError('native submission receipt differs from request')
    uuid.UUID(result['id'])
    return result['id']


def deliver(executable, repo, state, owner, text, event_ids):
    client=Client(executable,repo,state)
    try:
        return enqueue(client,owner,text,event_ids,lambda:(Path(state)/'watch.cancel').exists())
    finally:
        client.close()
