"""Week 5 chess source census and frozen two-stage sampling (private output).

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1,4,6. Selection precedes clock or
evaluation availability. Missing/negative/zero clocks are counted, never filled.
Header identities become campaign-salted hashes before storage. Null and positive
worlds use the same sampler. Round-trip disagreement refuses source admission.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse, gzip, hashlib, hmac, io, json, math, os, re, shutil, sqlite3, time, uuid
import chess, chess.pgn
import numpy as np
import pyarrow as pa

SEED = 20261107
HEADER = re.compile(r'^\[(\w+) "(.*)"\]$')
CLOCK = re.compile(r'\[%clk (\d+):(\d+):(\d+(?:\.\d+)?)\]')
TOKEN = re.compile(r'\{([^}]*)\}|([^\s{}]+)')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''): h.update(block)
    return h.hexdigest()


def write_json(path, value, mutable=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    if path.exists() and not mutable:
        if path.read_bytes() != raw: raise ValueError('Immutable output differs')
    else:
        temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');temporary.write_bytes(raw)
        try:
            for attempt in range(30):
                try:os.replace(temporary,path);break
                except PermissionError:
                    if attempt==29:raise
                    time.sleep(.1)
        finally:
            if temporary.exists():temporary.unlink()


def pseudonym(value, salt):
    if not value or value == '?' or value.lower() == 'anonymous': return None
    return hmac.new(salt, value.casefold().encode(), hashlib.sha256).hexdigest()


def selected_history(player, fraction=.02):
    return player is not None and int(player[:16], 16) < int(fraction * 2**64)


def control(initial, increment):
    expected = initial + 40 * increment
    return 'bullet' if expected < 180 else 'blitz' if expected < 480 else 'rapid' if expected < 1500 else 'classical'


def records(stream):
    lines = []; size = 0
    for line in stream:
        if line.startswith('[Event ') and lines:
            yield '\n'.join(lines); lines = []; size = 0
        size += len(line)
        if size > 1024**2: raise ValueError('PGN game exceeds bounded parser')
        lines.append(line.rstrip('\r\n'))
    if lines: yield '\n'.join(lines)


@contextmanager
def source_stream(path):
    path = Path(path)
    if path.suffix == '.zst':
        with pa.OSFile(str(path),'rb') as raw,pa.CompressedInputStream(raw,'zstd') as binary:
            with io.TextIOWrapper(binary, encoding='utf8') as stream:
                stream._week5_compressed_source=raw
                yield stream
    else:
        with path.open(encoding='utf8') as stream: yield stream


def decode_headers(text, salt):
    headers = {}
    for line in text.splitlines():
        m = HEADER.match(line)
        if m: headers[m[1]] = m[2]
    tc = re.fullmatch(r'(\d+)\+(\d+)', headers.get('TimeControl', ''))
    if not tc or 'rated' not in headers.get('Event', '').lower(): return None, 'unrated_or_unknown_control'
    if headers.get('Variant', 'Standard') not in ('Standard', 'From Position'): return None, 'variant'
    if headers.get('FEN'): return None, 'nonstandard_initial_position'
    initial, increment = map(int, tc.groups())
    if initial <= 0: return None, 'invalid_clock'
    try: ratings = [int(headers[x + 'Elo']) for x in ('White', 'Black')]
    except (KeyError, ValueError): return None, 'missing_rating'
    ids = [pseudonym(headers.get(x), salt) for x in ('White', 'Black')]
    if not all(ids): return None, 'missing_identity'
    try:
        stamp = datetime.strptime(headers['UTCDate'] + ' ' + headers['UTCTime'], '%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
    except (KeyError, ValueError): stamp = None
    try:
        end = datetime.strptime(headers['EndDate'] + ' ' + headers['EndTime'], '%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
    except (KeyError, ValueError): end = None
    changes = []
    for color in ('White', 'Black'):
        try: changes.append(int(headers[color + 'RatingDiff']))
        except (KeyError, ValueError): changes.append(None)
    return dict(players=ids, ratings=ratings, initial=initial, increment=increment,
                time_control=control(initial, increment), start=stamp, end=end,
                rating_changes=changes, result=headers.get('Result', '*')), None


def mainline_tokens(text):
    # Lichess exports main lines; parentheses would introduce ambiguous ply maps.
    moves = ' '.join(line for line in text.splitlines() if not line.startswith('['))
    if '(' in re.sub(r'\{[^}]*\}', '', moves): raise ValueError('Variations in canonical monthly source')
    for match in TOKEN.finditer(moves):
        if match[1] is not None: yield 'comment', match[1]
        else:
            token = re.sub(r'^\d+\.(?:\.\.)?', '', match[2]).rstrip('!?')
            if token and token not in ('1-0','0-1','1/2-1/2','*') and not token.startswith('$'):
                yield 'move', token


def parse_game(text, meta, limit=None):
    board = chess.Board(); output = []; last = [None, None]; counts = Counter()
    for kind, token in mainline_tokens(text):
        if kind == 'comment':
            if not output: continue
            match = CLOCK.search(token)
            if match:
                value = int(match[1])*3600 + int(match[2])*60 + float(match[3])
                output[-1]['clock_after'] = value
            continue
        if limit is not None and len(output) >= limit: break
        move = board.parse_san(token); side = 0 if board.turn else 1
        material = sum(len(board.pieces(piece, color))*weight for piece, weight in ((chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)) for color in (True,False))
        row = dict(ply=len(output)+1, player=meta['players'][side], rating=meta['ratings'][side],
                   side=side, fen=board.fen(), position=' '.join(board.fen().split()[:4]),
                   uci=move.uci(), legal_moves=board.legal_moves.count(), material=material,
                   clock_after=None, clock_before=None, think_time=None)
        output.append(row); board.push(move)
    first = [None,None]
    for row in output:
        side = row['side']; after = row['clock_after']; before = last[side]
        if first[side] is None and after is not None: first[side] = after
        row['clock_before'] = before
        if row['ply'] <= 4: counts['first_two_moves'] += 1
        elif before is None or after is None: counts['missing_clock'] += 1
        else:
            think = before - after + meta['increment']
            if think < 0: counts['negative_think_time'] += 1
            elif think == 0: counts['zero_think_time'] += 1
            else: row['think_time'] = think; counts['positive_think_time'] += 1
        last[side] = after
    return output, dict(counts), first


def roundtrip(text, meta):
    game = chess.pgn.read_game(io.StringIO(text))
    if game is None or game.errors: raise ValueError('Canonical PGN parser refused')
    exported = game.accept(chess.pgn.StringExporter(headers=True, variations=False, comments=True))
    left, counts, first = parse_game(text, meta)
    right, rcounts, rfirst = parse_game(exported, meta)
    if left != right or counts != rcounts or first != rfirst: raise ValueError('PGN round-trip changed features')


def open_database(path):
    con = sqlite3.connect(path)
    con.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
    CREATE TABLE IF NOT EXISTS frame(player TEXT,month TEXT,tc TEXT,band INT,n INT,rating_sum REAL,PRIMARY KEY(player,month,tc,band));
    CREATE TABLE IF NOT EXISTS openings(month TEXT,tc TEXT,position TEXT,move TEXT,n INT,PRIMARY KEY(month,tc,position,move));
    CREATE TABLE IF NOT EXISTS opening_positions(month TEXT,tc TEXT,position TEXT,n INT,PRIMARY KEY(month,tc,position));
    CREATE TABLE IF NOT EXISTS histories(month TEXT,ordinal INT,payload TEXT,PRIMARY KEY(month,ordinal));
    CREATE TABLE IF NOT EXISTS checkpoints(month TEXT PRIMARY KEY,ordinal INT,source TEXT,counts TEXT,complete INT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
    ''')
    return con


def census(source, source_sha, month, salt, database, max_games=None, checkpoint_games=10000,telemetry=None,expected_games=None):
    """Transactional checkpoints permit skipping completed ordinals on restart."""
    con = open_database(database); old = con.execute('SELECT ordinal,source,counts,complete FROM checkpoints WHERE month=?',(month,)).fetchone()
    salt_digest=hashlib.sha256(salt).hexdigest();prior_salt=con.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()
    if prior_salt is not None and prior_salt[0]!=salt_digest:con.close();raise ValueError('Changed campaign salt on checkpoint resume')
    con.execute("INSERT OR IGNORE INTO settings VALUES('salt_sha256',?)",(salt_digest,));con.commit()
    if old and old[1] != source_sha: raise ValueError('Changed month pin')
    if old and old[3]: con.close(); return json.loads(old[2])
    done = old[0] if old else -1; counts = Counter(json.loads(old[2]) if old else {})
    frame = Counter(); ratings = Counter(); book = Counter(); position_counts=Counter();ordinal = done
    cpu_start=time.process_time();wall_start=time.monotonic();source_bytes=Path(source).stat().st_size
    stream=None
    def save(complete):
        con.executemany('INSERT INTO frame VALUES(?,?,?,?,?,?) ON CONFLICT(player,month,tc,band) DO UPDATE SET n=n+excluded.n,rating_sum=rating_sum+excluded.rating_sum', [(*key,n,ratings[key]) for key,n in frame.items()])
        con.executemany('INSERT INTO openings VALUES(?,?,?,?,?) ON CONFLICT(month,tc,position,move) DO UPDATE SET n=n+excluded.n', [(*key,n) for key,n in book.items()])
        con.executemany('INSERT INTO opening_positions VALUES(?,?,?,?) ON CONFLICT(month,tc,position) DO UPDATE SET n=n+excluded.n', [(*key,n) for key,n in position_counts.items()])
        con.execute('INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,?,?)',(month,ordinal,source_sha,json.dumps(dict(counts),sort_keys=True),int(complete)))
        con.commit(); frame.clear(); ratings.clear(); book.clear();position_counts.clear()
        if telemetry is not None and stream is not None:
            raw=getattr(stream,'_week5_compressed_source',None)
            position=raw.tell() if raw is not None else stream.buffer.tell()
            fraction=min(1.,position/source_bytes) if source_bytes else 1.
            progress=dict(month=month,source_sha256=source_sha,source_bytes=source_bytes,compressed_bytes_read=position,
                          completed_game_ordinal=ordinal,expected_games=expected_games,counts=dict(counts),complete=complete,
                          invocation_cpu_seconds=time.process_time()-cpu_start,invocation_wall_seconds=time.monotonic()-wall_start,
                          resumed_after_ordinal=done,byte_fraction=fraction)
            write_json(Path(telemetry)/'PROGRESS.json',progress,mutable=True)
            if done<0 and fraction>=.05 and not (Path(telemetry)/'PILOT.json').exists():
                progress['forecast_cpu_seconds']=progress['invocation_cpu_seconds']/fraction
                progress['pilot_basis']='first completed transaction at >=5% compressed input bytes; read-buffer progress proxy'
                write_json(Path(telemetry)/'PILOT.json',progress)
    try:
        with source_stream(source) as stream:
            for ordinal,text in enumerate(records(stream)):
                if ordinal <= done: continue
                if max_games is not None and ordinal >= max_games:
                    ordinal -= 1;save(False);break
                counts['source_games'] += 1; meta, reason = decode_headers(text,salt)
                if reason: counts[reason] += 1; continue
                historical = any(selected_history(p) for p in meta['players'])
                try:
                    if counts['roundtrip_games'] < 1000: roundtrip(text,meta); counts['roundtrip_games'] += 1
                    rows, dispositions, first = parse_game(text,meta,None if historical else 10)
                except ValueError:
                    counts['parse_failure'] += 1; continue
                counts['rated_games'] += 1
                for player,rating in zip(meta['players'],meta['ratings']):
                    key=(player,month,meta['time_control'],400*(rating//400)); frame[key]+=1; ratings[key]+=rating
                seen = set();seen_positions=set()
                for row in rows[:10]:
                    key=(month,meta['time_control'],row['position'],row['uci'])
                    if key not in seen: book[key]+=1; seen.add(key)
                    position_key=key[:3]
                    if position_key not in seen_positions:position_counts[position_key]+=1;seen_positions.add(position_key)
                if historical:
                    game_id=hashlib.sha256((source_sha+':'+str(ordinal)).encode()).hexdigest()
                    chosen=[p for p in meta['players'] if selected_history(p)]
                    kept=[r for r in rows if r['player'] in chosen]
                    payload=dict(game=game_id,meta=meta,rows=kept,first_clocks=first,dispositions=dispositions)
                    con.execute('INSERT INTO histories VALUES(?,?,?)',(month,ordinal,json.dumps(payload,sort_keys=True)))
                    counts['history_games']+=1; counts['history_moves']+=len(kept)
                if (ordinal+1)%checkpoint_games == 0: save(False)
                if telemetry is not None and ordinal%100==0 and (Path(telemetry)/'YIELD_REQUEST.json').exists():
                    request=json.loads((Path(telemetry)/'YIELD_REQUEST.json').read_text(encoding='utf8'))
                    save(False)
                    return dict(counts,_yield=dict(reason=request.get('reason','supervisor requested yield'),completed_game_ordinal=ordinal))
            else:
                if counts['parse_failure'] > .01*max(1,counts['source_games']): raise ValueError('More than 1% parse failures')
                save(True)
        if counts['parse_failure'] > .01*max(1,counts['source_games']): raise ValueError('More than 1% parse failures')
        return dict(counts)
    except BaseException:
        con.rollback(); raise
    finally:
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)'); con.close()


def choose_players(database, players=10000):
    """Proportional rating-band allocation; salted hash ranks are outcome-blind."""
    con=sqlite3.connect(database)
    if any(not r[0] for r in con.execute('SELECT complete FROM checkpoints')): raise ValueError('Incomplete census cannot define player frame')
    rows=con.execute('SELECT player,month,tc,band,n,rating_sum/n FROM frame WHERE n>=20').fetchall();con.close()
    by_stratum=defaultdict(list)
    # A player appears only once: deterministic priority across all eligible strata.
    unique={}
    for row in rows:
        rank=hashlib.sha256(f'{SEED}:eligibility:{row[0]}:{row[1]}:{row[2]}:{row[3]}'.encode()).hexdigest()
        if row[0] not in unique or rank<unique[row[0]][0]: unique[row[0]]=(rank,row)
    for _,row in unique.values(): by_stratum[(row[1][:4],row[2],row[3])].append(row)
    result=[];counts={}
    for era in ('2017','2026'):
        for tc,weight in [('blitz',.7),('bullet',.1),('rapid',.1),('classical',.1)]:
            strata={k:v for k,v in by_stratum.items() if k[:2]==(era,tc)}
            total=sum(len(v) for v in strata.values());target=min(total,int(players*weight/2))
            exact={k:target*len(v)/max(total,1) for k,v in strata.items()};quota={k:int(v) for k,v in exact.items()}
            for k in sorted(strata,key=lambda k:(-(exact[k]-quota[k]),k))[:target-sum(quota.values())]:quota[k]+=1
            for k in sorted(strata):
                ordered=sorted(strata[k],key=lambda r:hashlib.sha256(f'{SEED}:sample:{r[0]}'.encode()).hexdigest())
                for row in ordered[:quota[k]]: result.append(dict(player=row[0],month=row[1],time_control=row[2],band=row[3],eligible_games=row[4],rating=row[5]))
            counts[era+'-'+tc]=dict(eligible=total,selected=target)
    return sorted(result,key=lambda x:x['player']),counts


def collect_positions(sources, selected, salt, output, moves_per_player=40, games_per_player=10):
    wanted={(r['month'],r['player']):r for r in selected}; candidates=defaultdict(list);counts=Counter()
    for spec in sources:
        month=spec['month']
        with source_stream(spec['path']) as stream:
            for ordinal,text in enumerate(records(stream)):
                meta,reason=decode_headers(text,salt)
                if reason or not any((month,p) in wanted for p in meta['players']):continue
                try:rows,disp,first=parse_game(text,meta)
                except ValueError:counts['parse_failure']+=1;continue
                game=hashlib.sha256((spec['sha256']+':'+str(ordinal)).encode()).hexdigest()
                for player in meta['players']:
                    key=(month,player)
                    if key not in wanted or meta['time_control']!=wanted[key]['time_control']:continue
                    # Retain all moves in the selected game BEFORE availability filtering.
                    moves=[dict(r,game=game,month=month,**{k:meta[k] for k in ('initial','increment','time_control')}) for r in rows if r['player']==player and r['ply']>4]
                    if not moves:counts['games_without_postopening_moves']+=1;continue
                    rank=hashlib.sha256(f'{SEED}:game:{player}:{game}'.encode()).hexdigest()
                    moves=sorted(moves,key=lambda r:hashlib.sha256(f'{SEED}:move:{rank}:{r["ply"]}'.encode()).hexdigest())[:math.ceil(moves_per_player/games_per_player)]
                    candidates[player].append((rank,moves))
                    candidates[player]=sorted(candidates[player],key=lambda x:x[0])[:games_per_player]
    emitted=[]
    for player in sorted(candidates):
        games=candidates[player]; counts['sampled_players']+=1
        if len(games)<games_per_player:counts['below_ten_games_players']+=1
        pools=[moves for game,moves in games]
        for index in range(moves_per_player):
            pool=pools[index%len(pools)];offset=index//len(pools)
            if offset<len(pool):emitted.append(pool[offset])
    with Path(output).open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as binary:
        with io.TextIOWrapper(binary,encoding='utf8',newline='\n') as stream:
            for row in emitted:stream.write(json.dumps(row,sort_keys=True)+'\n')
    counts['sampled_positions']=len(emitted)
    return dict(counts)


def merge_frames(paths, destination):
    """Merge completed independently counted months, refusing overlaps."""
    target=open_database(destination)
    try:
        for index,path in enumerate(paths):
            alias='source'+str(index);target.execute('ATTACH DATABASE ? AS '+alias,(str(Path(path).resolve()),))
            if target.execute(f'SELECT COUNT(*) FROM {alias}.checkpoints WHERE complete!=1').fetchone()[0]:raise ValueError('Incomplete month frame')
            for table in ('frame','openings','opening_positions','histories','checkpoints'):
                target.execute(f'INSERT INTO main.{table} SELECT * FROM {alias}.{table}')
            source_salt=target.execute(f"SELECT value FROM {alias}.settings WHERE key='salt_sha256'").fetchone()
            existing=target.execute("SELECT value FROM main.settings WHERE key='salt_sha256'").fetchone()
            if existing and source_salt!=existing:raise ValueError('Different campaign salts across source frames')
            if source_salt:target.execute("INSERT OR IGNORE INTO main.settings VALUES('salt_sha256',?)",source_salt)
            target.commit();target.execute('DETACH DATABASE '+alias)
    except BaseException:target.rollback();raise
    finally:target.execute('PRAGMA wal_checkpoint(TRUNCATE)');target.close()


def execute(output, inputs, config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    salt=Path(inputs['salt']['path']).read_bytes()
    if len(salt)<16:raise ValueError('Campaign salt too short')
    if config['phase']=='census':
        if 'resume_frame' in inputs:
            prior=Path(inputs['resume_frame']['path']);destination=output/'PRIVATE_FRAME.sqlite'
            if destination.exists():raise ValueError('Resume is a new attempt only')
            if digest(prior)!=inputs['resume_frame']['sha256']:raise ValueError('Resume checkpoint hash changed')
            prior_con=sqlite3.connect(prior)
            try:
                if prior_con.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid SQLite checkpoint')
            finally:prior_con.close()
            shutil.copyfile(prior,destination)
        spec=inputs['source']; result=census(spec['path'],spec['sha256'],config['month'],salt,output/'PRIVATE_FRAME.sqlite',config.get('max_games'),telemetry=output,expected_games=config.get('expected_games'))
        if '_yield' in result:
            yielded=result.pop('_yield');checkpoint=dict(path=str(output/'PRIVATE_FRAME.sqlite'),sha256=digest(output/'PRIVATE_FRAME.sqlite'),**yielded)
            write_json(output/'CHECKPOINT.json',dict(checkpoint=checkpoint,counts=result))
            return dict(status='yielded',reason=yielded['reason'],checkpoint=checkpoint)
    elif config['phase']=='sample':
        selected,frame=choose_players(inputs['frame']['path'],config.get('players',10000))
        write_json(output/'PRIVATE_SELECTED_PLAYERS.json',selected)
        result=collect_positions(config['sources'],selected,salt,output/'PRIVATE_POSITIONS.jsonl.gz');result['frame']=frame
    elif config['phase']=='merge':
        merge_frames([value['path'] for key,value in sorted(inputs.items()) if key.startswith('frame')],output/'PRIVATE_FRAME.sqlite')
        result=dict(merged=True)
    else:raise ValueError('Unknown CH0 phase')
    write_json(output/'SOURCE.json',result)
    return dict(status='complete',scientific_effect_computed=False)


def verify(output,inputs,config):
    output=Path(output);check=output/'replay';check.mkdir(exist_ok=True)
    execute(check,inputs,config)
    if (output/'SOURCE.json').read_bytes()!=(check/'SOURCE.json').read_bytes():raise ValueError('Source replay counts differ')
    if config['phase'] in ('census','merge'):
        left=sqlite3.connect(output/'PRIVATE_FRAME.sqlite');right=sqlite3.connect(check/'PRIVATE_FRAME.sqlite')
        try:
            for table in ('frame','openings','opening_positions','histories','checkpoints','settings'):
                n=len(left.execute('PRAGMA table_info('+table+')').fetchall());order=','.join(str(i+1) for i in range(n))
                a=left.execute(f'SELECT * FROM {table} ORDER BY {order}');b=right.execute(f'SELECT * FROM {table} ORDER BY {order}')
                while True:
                    x=a.fetchmany(1000);y=b.fetchmany(1000)
                    if x!=y:raise ValueError('Source replay table differs: '+table)
                    if not x:break
        finally:left.close();right.close()
    elif digest(output/'PRIVATE_POSITIONS.jsonl.gz')!=digest(check/'PRIVATE_POSITIONS.jsonl.gz'):raise ValueError('Position sample replay differs')
    return dict(verified=True,complete_recalculation=True)

