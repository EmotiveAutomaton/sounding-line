"""EX5 fixed public-question export from already verified Posts.xml members.

DESIGN CHECK: exact400/site, actual3-to8 answers, known non-self accepted answer.
Only public post IDs enter attribution URLs. Private owner equality is salted;
user/profile fields never enter the bundle. No scoring or new extraction occurs.
"""
from collections import Counter
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import math
import os
import sqlite3
import time
import xml.etree.ElementTree as ET
from xml.parsers import expat
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
from . import week5_go3_collection as collection
from . import week5_go_revisions as source
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_ex5_v1'
SITES = tuple(source.ARCHIVES)
PER_SITE = 400
BLOCK_BYTES = 1024*1024
SOURCE_FIELDS = ('Id', 'PostTypeId', 'ParentId', 'AcceptedAnswerId', 'OwnerUserId', 'Score', 'CreationDate', 'Title', 'Body')


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []; self.code = []; self.lengths = []; self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.depth += 1
            if self.depth == 1:
                self.code = []
        elif not self.depth and tag in ('p', 'br', 'div', 'li', 'blockquote', 'h1', 'h2', 'h3', 'table', 'tr'):
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag == 'pre':
            if self.depth < 1:
                raise ValueError('Unbalanced preformatted block')
            self.depth -= 1
            if not self.depth:
                length = len(''.join(self.code)); self.lengths.append(length)
                self.parts.append(' [CODE_BLOCK:length='+str(length)+'] ')
        elif not self.depth and tag not in ('b', 'i', 'em', 'strong', 'a', 'span', 'code'):
            self.parts.append(' ')

    def handle_data(self, data):
        (self.code if self.depth else self.parts).append(data)


def plain(body):
    parser = Text(); parser.feed(body); parser.close()
    if parser.depth:
        raise ValueError('Unclosed preformatted block')
    return ' '.join(''.join(parser.parts).split()), parser.lengths


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    modules = (collection, source, source.core, collection.producer, collection.producer.integrity, seal, io)
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in modules} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    if set(config)-{'max_new_draws', 'max_wall_seconds'}:
        raise ValueError('No configurable export population or eligibility rule')
    if type(config.get('max_new_draws', 1)) is not int or config.get('max_new_draws', 1) < 1:
        raise ValueError('Positive whole-byte-block quantum required')
    wall = config.get('max_wall_seconds', 900)
    if not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall <= 0:
        raise ValueError('Positive finite wall bound required')


def authenticate(inputs, stop):
    if set(inputs) != {'source_roster'}:
        raise ValueError('Exact complete five-site source roster required')
    roster = collection.check_roster(inputs['source_roster']); infos = []
    for site in SITES:
        info = collection.authenticate(site, roster[site], stop)
        root = Path(info['root']); plan = seal.read(root/'PLAN.json'); receipt = seal.read(root/'output/SOURCE.json')
        xml = root/'output/xml/Posts.xml'; salt = Path(plan['inputs']['salt'])
        if xml.is_symlink() or io.sha(xml) != receipt['member_sha256']['Posts.xml']:
            raise ValueError('Verified Posts.xml member differs')
        if io.sha(salt) != info['salt_sha256'] or len(salt.read_bytes()) != 32:
            raise ValueError('Private source equality salt differs')
        infos.append({'site': site, 'xml': str(xml), 'xml_sha256': receipt['member_sha256']['Posts.xml'],
            'bytes': xml.stat().st_size, 'salt': str(salt), 'salt_sha256': info['salt_sha256'],
            'source_complete': info['complete_sha256'], 'archive_sha256': source.ARCHIVES[site]})
    return infos


def parse_row(line, independent=False):
    if independent:
        rows = []; parser = expat.ParserCreate()
        parser.StartElementHandler = lambda tag, attrs: rows.append((tag, dict(attrs)))
        parser.Parse(line, True)
        if len(rows) != 1 or rows[0][0] != 'row':
            raise ValueError('Exactly one source row per record required')
        return rows[0][1]
    element = ET.fromstring(line)
    if element.tag != 'row' or len(element):
        raise ValueError('Exactly one source row per record required')
    return element.attrib


def positive_id(value, optional=False):
    if optional and not value:
        return None
    if not isinstance(value, str) or not value.isdigit() or int(value) <= 0:
        raise ValueError('Malformed public post identifier')
    return value


def project(row, site, ordinal, salt):
    public_id = positive_id(row.get('Id')); kind = int(row['PostTypeId'])
    if kind not in (1, 2):
        return None
    parent = positive_id(row.get('ParentId'), True) if kind == 2 else None
    accepted = positive_id(row.get('AcceptedAnswerId'), True) if kind == 1 else None
    if kind == 2 and parent is None:
        raise ValueError('Answer has no public parent')
    owner = row.get('OwnerUserId', '')
    owner = source.salted(salt, site+'-user', owner) if owner.isdigit() and int(owner) > 0 else None
    stamp = datetime.fromisoformat(row['CreationDate'])
    if stamp.tzinfo is not None:
        raise ValueError('Unexpected timestamp timezone form; preserve source order contract')
    stamp = stamp.isoformat(timespec='microseconds')
    body, lengths = plain(row.get('Body', ''))
    return (site, public_id, kind, parent, accepted, owner, int(row.get('Score', '0')), stamp,
            unescape(row.get('Title', '')), body, json.dumps(lengths), ordinal, len(body.split()))


def open_state(output, binding):
    path = output/'posts.sqlite'
    if path.exists():
        snapshot = seal.read(output/'SNAPSHOT.json')
        if snapshot['binding'] != binding or snapshot['sha256'] != io.sha(path):
            raise ValueError('Source/semantic/database checkpoint differs')
        db = sqlite3.connect(path)
        state = json.loads(db.execute('SELECT value FROM state').fetchone()[0])
        if state != snapshot['state']:
            db.close(); raise ValueError('Database state differs from sealed cursor')
    else:
        db = sqlite3.connect(path)
        db.executescript('CREATE TABLE state(value TEXT); CREATE TABLE posts('
            'site TEXT,id TEXT,kind INTEGER,parent TEXT,accepted TEXT,owner TEXT,score INTEGER,stamp TEXT,'
            'title TEXT,body TEXT,code_lengths TEXT,ordinal INTEGER,words INTEGER,PRIMARY KEY(site,id));'
            'CREATE INDEX by_parent ON posts(site,parent);')
        state = {'site_index': 0, 'offset': 0, 'ordinal': 0, 'opened': False, 'closed': False,
                 'completed_bytes': 0, 'blocks': 0, 'site_counts': {}}
        db.execute('INSERT INTO state VALUES(?)', (json.dumps(state, sort_keys=True),)); db.commit()
    db.execute('PRAGMA journal_mode=DELETE'); db.execute('PRAGMA synchronous=FULL'); db.execute('PRAGMA cache_size=-65536')
    return db, state


def checkpoint(output, db, state, binding):
    db.execute('UPDATE state SET value=?', (json.dumps(state, sort_keys=True),)); db.commit(); db.close()
    io.write_json(output/'SNAPSHOT.json', {'binding': binding, 'state': state, 'sha256': io.sha(output/'posts.sqlite')})


def ingest_block(db, state, info, independent=False):
    begin = state['offset']; site = info['site']; salt = Path(info['salt']).read_bytes()
    counts = Counter(state['site_counts'].get(site, {}))
    with Path(info['xml']).open('rb') as stream:
        stream.seek(begin)
        while stream.tell()-begin < BLOCK_BYTES:
            raw = stream.readline()
            if not raw:
                if not state['closed'] or not state['opened']:
                    raise ValueError('Source XML root not complete')
                state.update(site_index=state['site_index']+1, offset=0, ordinal=0, opened=False, closed=False)
                break
            previous = state['offset']; state['offset'] = stream.tell()
            state['completed_bytes'] += state['offset']-previous
            line = raw.strip().removeprefix(b'\xef\xbb\xbf')
            if not line or (line.startswith(b'<?xml ') and not state['opened']):
                continue
            if line == b'<posts>':
                if state['opened'] or state['closed']:
                    raise ValueError('Duplicate source XML root')
                state['opened'] = True; continue
            if line == b'</posts>':
                if not state['opened'] or state['closed']:
                    raise ValueError('Malformed source XML close')
                state['closed'] = True; continue
            if not state['opened'] or state['closed'] or not line.startswith(b'<row '):
                raise ValueError('Source is not one complete post row per line')
            state['ordinal'] += 1; counts['all_post_rows'] += 1
            record = project(parse_row(line, independent), site, state['ordinal'], salt)
            if record is not None:
                db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', record)
                counts['questions' if record[2] == 1 else 'answers'] += 1
    state['site_counts'][site] = dict(counts); state['blocks'] += 1; db.commit()


def ranking(site, ordinal):
    return hashlib.sha256(f'EX5|20261112|{site}|{ordinal}'.encode()).hexdigest()


def select(db, site, independent=False):
    counts = Counter(); selected = []
    questions = db.execute('SELECT id,accepted,owner,title,body,code_lengths,ordinal,words FROM posts WHERE site=? AND kind=1 ORDER BY ordinal', (site,))
    for qid, accepted, owner, title, body, lengths, ordinal, words in questions:
        counts['questions'] += 1
        if not 80 <= words <= 600:
            counts['outside_body_word_band'] += 1; continue
        answers = list(db.execute('SELECT id,owner,score,stamp,body,code_lengths FROM posts WHERE site=? AND kind=2 AND parent=? ORDER BY stamp,CAST(id AS INTEGER)', (site, qid)))
        if not 3 <= len(answers) <= 8:
            counts['outside_answer_count_band'] += 1; continue
        accepted_rows = [a for a in answers if a[0] == accepted]
        if len(accepted_rows) != 1:
            counts['accepted_answer_absent_or_wrong_parent'] += 1; continue
        if owner is None or accepted_rows[0][1] is None:
            counts['unknown_accepted_or_asker_owner'] += 1; continue
        if owner == accepted_rows[0][1]:
            counts['self_accepted'] += 1; continue
        counts['eligible'] += 1
        rank_ = hashlib.sha256(('EX5|20261112|'+site+'|'+str(ordinal)).encode()).hexdigest() if independent else ranking(site, ordinal)
        selected.append((rank_, ordinal, qid))
    selected.sort()
    return selected[:PER_SITE], dict(counts)


def export_question(db, site, qid):
    domain = 'writing' if site == 'writers' else site
    accepted, title, body, lengths = db.execute('SELECT accepted,title,body,code_lengths FROM posts WHERE site=? AND id=?', (site, qid)).fetchone()
    answers = []
    for order, (aid, score, text, code) in enumerate(db.execute('SELECT id,score,body,code_lengths FROM posts WHERE site=? AND parent=? AND kind=2 ORDER BY stamp,CAST(id AS INTEGER)', (site, qid)), 1):
        answers.append({'answer_id': aid, 'body': text, 'code_block_codepoint_lengths': json.loads(code),
            'final_score': score, 'posting_order': order, 'accepted': aid == accepted,
            'attribution_url': f'https://{domain}.stackexchange.com/a/{aid}'})
    return {'site': site, 'question_id': qid, 'title': title, 'body': body,
        'code_block_codepoint_lengths': json.loads(lengths), 'answers': answers,
        'attribution_url': f'https://{domain}.stackexchange.com/questions/{qid}'}


def run(output, inputs, config, independent=False):
    settings(config); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    request_root = output.parent if output.name == 'independent-replay' else output
    stop = lambda: time.monotonic()-start >= config.get('max_wall_seconds', 900) or any((request_root/n).exists() for n in ('YIELD_REQUEST.json', 'STOP_REQUEST.json'))
    try:
        infos = authenticate(inputs, stop)
    except collection.Paused:
        return {'status': 'yielded', 'verified': False, 'phase': 'EX5_authentication', 'completed': 0, 'total': 1}
    if tuple(i['site'] for i in infos) != SITES:
        raise ValueError('Exact ordered five-site source contract required')
    public_sources = [{k: v for k, v in item.items() if k not in ('xml', 'salt')} for item in infos]
    binding = digest({'sources': infos, 'modules': dependencies(), 'independent_parser': independent,
        'per_site': PER_SITE, 'rank': 'EX5|20261112|site|one-based Posts.xml row ordinal',
        'words': 'whitespace words after plain-text/code-marker projection'})
    db, state = open_state(output, binding); added = 0; closed = False
    try:
        while state['site_index'] < len(infos):
            if added >= config.get('max_new_draws', 1) or stop():
                checkpoint(output, db, state, binding); closed = True
                return {'status': 'yielded', 'verified': False, 'phase': 'EX5_posts_bytes',
                    'completed': state['completed_bytes'], 'total': sum(i['bytes'] for i in infos)}
            cpu = time.process_time(); ingest_block(db, state, infos[state['site_index']], independent); added += 1
            if not (output/'COST_PREFIX.json').exists():
                io.write_json(output/'COST_PREFIX.json', {'first_block_CPU_seconds': time.process_time()-cpu,
                    'completed_bytes': state['completed_bytes'], 'total_bytes': sum(i['bytes'] for i in infos),
                    'upstream_authentication_selection_and_full_replay_not_included': True})
            io.write_json(output/'PROGRESS.json', {'phase': 'EX5_posts_bytes', 'completed': state['completed_bytes'], 'total': sum(i['bytes'] for i in infos)})
        selections = {}; counts = {}; bundle_rows = []
        for site in SITES:
            selections[site], counts[site] = select(db, site, independent)
        supported = all(len(selections[site]) == PER_SITE for site in SITES)
        if supported:
            for site in SITES:
                bundle_rows.extend(export_question(db, site, qid) for _, _, qid in selections[site])
        checkpoint(output, db, state, binding); closed = True
    finally:
        if not closed:
            db.close()
    result = {'card': 'EX5', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False, 'activation': [],
        'complete_export': supported, 'status': 'complete' if supported else 'unsupported',
        'per_site_counts': counts, 'rows': len(bundle_rows), 'source_support_complete': True,
        'selection': 'fixed lowest hash; no score or posting-order preference', 'source_sources': public_sources,
        'no_user_fields_exported': True}
    if supported:
        bundle = output/'bundle'; bundle.mkdir(exist_ok=True)
        io.write_json(bundle/'QUESTIONS.json', bundle_rows)
        io.write_json(bundle/'SELECTION.json', {'source_fields_used': list(SOURCE_FIELDS),
            'original_member_preserved': True, 'owner_values_never_exported': True,
            'questions': [{'site': site, 'question_id': qid, 'source_row': ordinal, 'rank_sha256': rank_}
                          for site in SITES for rank_, ordinal, qid in selections[site]]})
        readme = ('# EX5: public questions and their accepted answers\n\n'
            '2,000 questions, exactly400 per verified site, with3–8 actual answers and a known non-self accepted answer. '
            'Selection uses the lowest SHA-256 of EX5|20261112|site|one-based Posts.xml row ordinal, independently of score. '
            'Unknown asker/accepted-answer owner identity is excluded, never guessed. No user or profile fields are exported.\n\n'
            'Body text is HTML-to-text with whitespace normalized. Each preformatted code block is replaced by '
            '[CODE_BLOCK:length=N], N Unicode code points; inline code remains text. The80–600 word gate is applied '
            'to this exported question body using whitespace splitting. Answers are ordered by source creation timestamp, '
            'then numeric public post ID on a tie; final score and accepted label are preserved.\n\n'
            'Derived from the five already verified Stack Exchange dumps under their supplied CC BY-SA3.0 notice. '
            'Retain that licence and acknowledge the original contributors through each public post attribution URL '
            'in QUESTIONS.json. These URLs contain public post IDs only. Code-block omission, HTML conversion and '
            'the fixed selection are the modifications. SELECTION.json records public post IDs, original source-row ordinals, '
            'hash ranks and source column names for audit. Original pinned XML members remain untouched. '
            'Local engine use only; no provider transfer or public release is implied.\n\n'
            +json.dumps({'per_site_counts': counts}, indent=2)+'\n')
        (bundle/'README.md').write_text(readme, encoding='utf8', newline='\n')
        io.write_json(bundle/'MANIFEST.json', {'card': 'EX5', 'complete_export': True, 'sources': public_sources,
            'module_sha256': io.sha(__file__), 'files': {n: io.sha(bundle/n) for n in ('QUESTIONS.json', 'SELECTION.json', 'README.md')}})
    else:
        result['reason'] = 'fewer than400 eligible questions in a site; no convenience substitution'
    io.write_json(output/'RESULT.json', result); return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = run(output/'independent-replay', inputs, config, True)
    if result.get('status') == 'yielded':
        return {**result, 'verified': False}
    if result != seal.read(output/'RESULT.json'):
        raise ValueError('Complete independently parsed source support/export differs')
    if result['complete_export']:
        seal.replay_bundle(output/'bundle', output/'independent-replay/bundle')
    return {'verified': True, 'complete_independent_source_parse_and_selection': True,
            'all_export_fields_replayed': result['complete_export'], 'no_user_fields_exported': True}
