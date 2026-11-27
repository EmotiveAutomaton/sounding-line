"""Original-format invented inputs for the two TP72 receiver paths."""
from datetime import date, timedelta
import csv
import hashlib
import io
from zipfile import ZipFile, ZIP_DEFLATED

from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week8_tmp2_source as source
from runners.drive.sealed import week8_tp72_receiver as receiver
from runners.drive.sealed.week8_tp72_job import original_speech


def archive(root, role, fields, rows):
    path = root/('pandora_'+role+'.zip')
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(fields)
    writer.writerows(rows)
    data = buffer.getvalue().encode('utf8')
    with ZipFile(path,'w',ZIP_DEFLATED) as dest:
        dest.writestr(source.HEADERS[role],data)
    return dict(name=path.name,bytes=path.stat().st_size,expanded=len(data),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def histories(root, made):
    original = root/'invented'
    made.make(original)
    with (original/'traits.csv').open(newline='') as stream:
        header, *records = csv.reader(stream)
    profiles = [[name,*[100*float(v) for v in scores]] for name,*scores in records]
    for i in range(12):
        profiles.extend([[f'absent{i}',40,50,60,70,80],[f'missing{i}','',50,60,70,80]])
    rows = []
    with (original/'comments.csv').open(newline='') as stream:
        for r in csv.DictReader(stream):
            text, group = (r['text']+' ')*2, r['community']
            if r['id'].startswith('excluded-'):
                text,group = 'Openness 80 and Neuroticism 60','collection'
            rows.append((r['author'],text,group,r['day'],r['id']))
    for i in range(48):
        rows.append((f'person{i}','I took the MBTI yesterday.','fiction','2000-01-01',f'drop-{i}'))
    markup = '<'+' '.join(['example']*60)+'>'
    for i in range(32,48):
        for day in range(18,126):
            rows.append((f'person{i}',markup,'fiction',str(date(2000,1,1)+timedelta(days=day)),f'{i}-{day}'))
    dest = root/'archives'
    dest.mkdir()
    pins = dict(profiles=archive(dest,'profiles',header,profiles),
                comments=archive(dest,'comments',source.COMMENT_COLS,rows))
    source.verify(dest,pins)
    return dest,pins


def exercise(work,m,frozen):
    panels = m['panels']
    archives,pins = histories(work,m['made'])
    remembered = {}
    class CheckedHistory:
        @staticmethod
        def history(*args, excluded, dropped):
            if 'collection' not in excluded or dropped != {f'drop-{i}' for i in range(48)}:
                raise ValueError('Constructed exclusions differ from the original records')
            return m['history'].history(*args,excluded=excluded,dropped=dropped)
    history = receiver.history(archives,pins,work,CheckedHistory,frozen,
                               panels.contracts(panels.HISTORY),lambda: None,[])
    if set(history) != receiver.HISTORY:
        raise ValueError('The two constructed history cohorts must release all nine tables')
    for name, rows in history.items():
        n = 48 if name in ('traits.csv','contrast.csv','channels.csv') else 32
        if not rows or any(int(r['n'])!=n or int(r['isoN'])!=200 or int(r['rotN'])!=200 for r in rows):
            raise ValueError('History support or matched controls failed')
    sample = original_speech(m['rehearse72'].invented_speech())
    contract = panels.contracts(panels.CONVERSATION)
    class CheckedConversation:
        @staticmethod
        def conversation(speakers,dest,engine,check,observe):
            def capture(name,labels,people):
                remembered[name,tuple(labels)]=people
                observe(name,labels,people)
            return m['conversation'].conversation(speakers,dest,engine,check,capture)
    for label, subset in [('small',sample[:2]),('twelve',sample)]:
        scratch = work/label
        scratch.mkdir()
        universe = frozenset(s.speaker for s in subset)
        try:
            result = receiver.conversation(subset,scratch,CheckedConversation,frozen,contract,lambda: None,universe,[])
        except SealedFailure as exc:
            if label=='small' and exc.code==12:
                continue
            raise
        if label=='small':
            raise ValueError('Two invented people produced a releasable row')
        if set(result)!={'conversation_affect.csv'} or {len(p) for p in remembered.values()}!={11,12}:
            raise ValueError('Missing-trait complement failed the constructed release check')
        return result
