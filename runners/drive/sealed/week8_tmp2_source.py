"""Apply amendment DJ inside the seal. Only the named aggregate counts may leave."""
import csv
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import heapq
import io
import itertools
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables
from runners.drive.sealed.week7_tmp1_shell import check_image
from independent_release import Entry, decide

TRAITS=('Openness','Extraversion','Agreeableness','Conscientiousness','Neuroticism')
TYPES=tuple(''.join(p) for p in itertools.product('ei','ns','tf','jp'))
NAMES=('mbti','myers','enneagram','socionics','personality','bigfive','big5','typology','jung','keirsey','hexaco',*TYPES)
BY_NAME=re.compile('|'.join(NAMES),re.I)
SCORE_WORDS=re.compile(r'\b('+'|'.join(TRAITS)+r')\b(?=[\s\S]{0,40}\d)',re.I)
TEST_NAMES=re.compile(r'\b(?:personality\s+(?:test|inventory|questionnaire|assessment)s?|16personalities|16\s*pf|'
    r'myers[\s–-]*briggs|mbti|big[ -]?(?:5|five)|five[ -]factor\s+(?:inventory|test|questionnaire)|'
    r'bfi(?:[ -]?2)?|neo[ -]?(?:pi|ffi)(?:[ -]?r)?|ipip(?:[ -]?(?:neo|50|100|120|300))?|'
    r'hexaco|enneagram|keirsey|mmpi(?:[ -]?2)?|socionics|jung\s+typology)\b',re.I)
WORDS=re.compile(r"[^\W_]+(?:['’][^\W_]+)*",re.UNICODE)
MISSING={'','na','n/a','nan','null','none'}
HEADERS={'profiles':'author_profiles.csv','comments':'all_comments_since_2015.csv'}
COMMENT_COLS=('author','body','subreddit','created_utc','id')


def reporting(body):
    return len({m.group(1).casefold() for m in SCORE_WORDS.finditer(body)})>=2


def verify(root,pins):
    if root.is_symlink() or not root.is_dir() or {p.name for p in root.iterdir()}!={s['name'] for s in pins.values()}:
        raise SealedFailure(21,'Archive roster differs')
    for role,s in pins.items():
        p=root/s['name']
        if p.is_symlink() or not p.is_file() or p.stat().st_size!=s['bytes']:
            raise SealedFailure(21,'Archive size differs')
        h=hashlib.sha256()
        with p.open('rb') as stream:
            for chunk in iter(lambda:stream.read(4<<20),b''):
                h.update(chunk)
        if h.hexdigest()!=s['sha256']:raise SealedFailure(21,'Archive digest differs')
        with ZipFile(p) as archive:
            infos=archive.infolist()
            if len(infos)!=1 or infos[0].filename!=HEADERS[role] or infos[0].file_size!=s['expanded'] or infos[0].flag_bits&1:
                raise SealedFailure(21,'Original CSV member differs')


@contextmanager
def selected(root,pins,role,columns):
    import pyarrow as pa
    import pyarrow.csv as pc
    with ZipFile(root/pins[role]['name']) as archive:
        with archive.open(HEADERS[role]) as raw:
            header=next(csv.reader([raw.readline(1<<20).decode('utf-8-sig')],strict=True))
        def bind(wanted):
            names=[h for h in header if (h.casefold()==wanted.casefold() if wanted in TRAITS else h==wanted)]
            if len(names)!=1:raise SealedFailure(22,'Ambiguous or absent column')
            return names[0]
        real=[bind(k) for k in columns]
        with archive.open(HEADERS[role]) as raw:
            opts=pc.ConvertOptions(include_columns=real,column_types={k:pa.string() for k in real},strings_can_be_null=False)
            stream=pc.open_csv(raw,read_options=pc.ReadOptions(use_threads=False,block_size=4<<20),
                parse_options=pc.ParseOptions(newlines_in_values=True),convert_options=opts)
            try:
                yield (row for batch in stream for row in zip(*(c.to_pylist() for c in batch.columns)))
            finally:
                stream.close()


def profiles(root,pins):
    totals=[0]*5
    above=[0]*5
    complete={}
    people=set()
    with selected(root,pins,'profiles',('author',*TRAITS)) as rows:
        for author,*scores in rows:
            if not author.strip() or author in people:raise SealedFailure(22,'Incomplete or ambiguous author key')
            people.add(author)
            vector=[]
            for i,raw in enumerate(scores):
                if raw.strip().casefold() in MISSING:
                    vector.append(None)
                    continue
                try:v=float(raw)
                except ValueError:raise SealedFailure(24,'Unbound trait value') from None
                if not math.isfinite(v) or not 0<=v<=100:raise SealedFailure(24,'Trait range failed')
                totals[i]+=1
                above[i]+=int(v>1)
                vector.append(v)
            if None not in vector:complete[author]=vector
    if any(n==0 or 10*k<n for n,k in zip(totals,above)):
        raise SealedFailure(24,'Trait scale range check failed')
    return people,complete


def timestamp(value):
    try:
        if re.fullmatch(r'\d+(?:\.0+)?',value):
            return int(float(value))
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError,OverflowError):
        raise SealedFailure(22,'Unbound comment clock') from None


def check_fields(author,community,ident):
    if not author or not community or not ident or author.casefold() in {'[deleted]','[removed]'}:
        raise SealedFailure(22,'Unidentified source record')


def filter_histories(root,pins,scratch,projection=None):
    import sqlite3
    all_profiles,scored=profiles(root,pins)
    universe=set(all_profiles)
    reported_groups=set()
    named_groups=set()
    named_people=set()
    reporting_people=set()
    # Count comment identities once inside the private scratch space.
    conn=sqlite3.connect(str(scratch/'comments.sqlite'))
    try:
        conn.execute('PRAGMA journal_mode=OFF')
        conn.execute('PRAGMA synchronous=OFF')
        conn.execute('CREATE TABLE ids (id TEXT PRIMARY KEY) WITHOUT ROWID')
        pending=[]
        with selected(root,pins,'comments',('author','subreddit','id','body')) as rows:
            for author,community,ident,body in rows:
                community=community.strip().casefold()
                check_fields(author,community,ident)
                universe.add(author)
                pending.append((ident,))
                if len(pending)>=8192:
                    conn.executemany('INSERT INTO ids VALUES (?)',pending)
                    pending.clear()
                if BY_NAME.search(community):
                    named_groups.add(community)
                    named_people.add(author)
                if author in scored and reporting(body):
                    reported_groups.add(community)
                    reporting_people.add(author)
        if pending:conn.executemany('INSERT INTO ids VALUES (?)',pending)
        conn.commit()
    except sqlite3.IntegrityError:
        raise SealedFailure(22,'Duplicate comment key') from None
    finally:
        conn.close()
    excluded=reported_groups|named_groups
    latest={}
    dropped=0
    dropped_authors=set()
    with selected(root,pins,'comments',COMMENT_COLS) as rows:
        for author,body,community,created,ident in rows:
            if community.strip().casefold() in excluded:
                continue
            if TEST_NAMES.search(body) or reporting(body):
                dropped+=1
                dropped_authors.add(author)
                continue
            if author not in scored or body.strip().casefold() in ('','[deleted]','[removed]'):
                continue
            key=(timestamp(created),ident)
            heap=latest.setdefault(author,[])
            if len(heap)>=1000 and key<=heap[0][:2]:continue
            words=sum(1 for _ in WORDS.finditer(body))
            if not words:continue
            item=(*key,words)
            if len(heap)<1000:heapq.heappush(heap,item)
            else:heapq.heapreplace(heap,item)
    kept={a:h for a,h in latest.items() if len(h)>=100 and sum(it[2] for it in h)>=5000}
    if projection is not None:
        projection.mkdir()
        with (projection/'traits.csv').open('w',encoding='utf8',newline='') as out:
            w=csv.writer(out);w.writerow(('author',*TRAITS))
            for a in sorted(kept):w.writerow((a,*scored[a]))
        (projection/'excluded_communities.json').write_text(json.dumps(sorted(excluded)),'utf8')
        selected_ids={it[1] for h in kept.values() for it in h}
        with (projection/'comments.csv').open('w',encoding='utf8',newline='') as out:
            w=csv.writer(out);w.writerow(('author','id','day','community','text'))
            with selected(root,pins,'comments',COMMENT_COLS) as rows:
                for author,body,community,created,ident in rows:
                    if ident in selected_ids:
                        if author not in kept or community.strip().casefold() in excluded:raise SealedFailure(14,'Projection differs')
                        day=datetime.fromtimestamp(timestamp(created),timezone.utc).date().isoformat()
                        w.writerow((author,ident,day,community,body))
                        selected_ids.remove(ident)
        if selected_ids:raise SealedFailure(14,'Projected history mismatch')
    components=[(len(scored),frozenset(scored)),(len(kept),frozenset(kept)),
                (len(reported_groups),frozenset(reporting_people)),(len(named_groups),frozenset(named_people)),
                (dropped,frozenset(dropped_authors))]
    return universe,components


def count_table(universe,components):
    # Priority is the order fixed in DJ. Compare every independently exposed
    # count, including different units in the same row. Each n counts people.
    candidates=[]
    for k,(value,people) in enumerate(components,1):
        if min(value,len(people))<11:continue
        if k>2 and abs(value-len(people))<11:continue
        candidates.append(Entry(dict(measure=k,count=value,n=len(people)),people))
    permitted,_=decide([(1,'counts',candidates)],universe)
    kept=[]
    earlier=[]
    for row in permitted.get('counts',[]):
        current={row['count'],row['n']}
        if all(abs(a-b)>=11 for a in current for b in earlier):
            kept.append(row)
            earlier.extend(current)
    if not kept:raise SealedFailure(12,'Counts withheld')
    return {'counts':kept}


def run(root,out,config):
    from tempfile import TemporaryDirectory
    if config['real_image']:check_image()
    pins=config['files']
    verify(root,pins)
    def read_once():
        with TemporaryDirectory(prefix='tmp2-counts-') as tmp:
            return count_table(*filter_histories(root,pins,Path(tmp)))
    first=read_once()
    if first!=read_once():raise SealedFailure(14,'Independent count replay differs')
    write_tables(out,first)
