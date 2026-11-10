"""Bounded native queue transport for one existing owner. Never starts a turn.

Uses installed experimental thread/queue API. Receipts prove acceptance only.
Ambiguous sends require reconciliation; never retry through a different backend.
"""
from __future__ import annotations
import json
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import uuid

WAKE_PREFIX = 'Sounding Line operational wake.'


class QueueBusy(RuntimeError):
    """An existing operational submission must drain before another is added."""


def request_identity(owner, event_ids):
    return str(uuid.uuid5(uuid.UUID(owner), 'sounding-line:' + ','.join(sorted(event_ids))))


def wake_text(row):
    parts = row.get('input', [])
    if len(parts) == 1 and parts[0].get('type') == 'text':
        text = parts[0].get('text', '')
        if text.startswith(WAKE_PREFIX):
            return text
    return None


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
    request_id=request_identity(owner,event_ids)
    expected=[{'type':'text','text':text,'text_elements':[]}]
    rows=inventory(client,owner)
    matches=[r for r in rows if r.get('clientUserMessageId')==request_id]
    if len(matches)>1: raise ValueError('duplicate native submission identities')
    if matches:
        result=matches[0]
    else:
        if any(wake_text(r) is not None for r in rows):
            raise QueueBusy('an operational wake is already pending in the native queue')
        if cancelled(): raise RuntimeError('cancelled before native enqueue')
        result=client.call('thread/queue/add',{'threadId':owner,'input':expected,'clientUserMessageId':request_id})['queuedSubmission']
    if result.get('clientUserMessageId')!=request_id or result.get('input')!=expected:
        raise ValueError('native submission receipt differs from request')
    uuid.UUID(result['id'])
    return result['id']


def reconcile(client, owner, known, render):
    """Retire only exact, fully ACKed watcher submissions; never ACK a result."""
    present=[]; retired=[]; unrecognized=[]
    for row in inventory(client,owner):
        text=wake_text(row)
        if text is None: continue
        ids=re.findall(r'^- ([0-9a-f]{24}):',text,re.M)
        if (not ids or len(ids)!=len(set(ids)) or any(e not in known for e in ids)
                or row.get('clientUserMessageId')!=request_identity(owner,ids)
                or text!=render([known[e] for e in ids])):
            unrecognized.append(row['id']); continue
        item={'queue_id':row['id'],'event_ids':ids}
        if not all(known[e]['acknowledged'] is not None for e in ids):
            present.append(item); continue
        # Recheck exact bytes immediately before deleting; user submissions are never touched.
        fresh=[r for r in inventory(client,owner) if r['id']==row['id']]
        if fresh and fresh!=[row]: raise ValueError('native wake changed before retirement')
        if fresh:
            result=client.call('thread/queue/delete',
                {'threadId':owner,'queuedSubmissionId':row['id']})
            if not isinstance(result.get('deleted'),bool):
                raise ValueError('invalid native retirement receipt')
            if any(r['id']==row['id'] for r in inventory(client,owner)):
                raise ValueError('native wake still present after retirement')
        retired.append(item)
    return {'present':present,'retired':retired,'unrecognized_wakes':unrecognized}


def reconcile_owner(executable, repo, state, owner, known, render):
    client=Client(executable,repo,state)
    try:
        return reconcile(client,owner,known,render)
    finally:
        client.close()


def deliver(executable, repo, state, owner, text, event_ids):
    client=Client(executable,repo,state)
    try:
        return enqueue(client,owner,text,event_ids,lambda:(Path(state)/'watch.cancel').exists())
    finally:
        client.close()
