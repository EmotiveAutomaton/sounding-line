"""Confirm the actual remote publication before closing a locally filed Week 8 row."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.stage14.common import atomic, filehash, read
from tools import r48_reports
from tools.week8_queue import PUBLIC, STATE, gear


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8').strip()


def meeting_terminals(card, receipt, raw_root):
    if card not in ('LGH6','RML1'):
        return {}
    suffix = 'prejoin' if card == 'LGH6' else 'room'
    corpora = receipt.get('corpora', {})
    if set(corpora) != {'ICSI','AMI'}:
        raise ValueError('Both meeting-corpus receipts are required')
    verified = {}
    for corpus, record in corpora.items():
        unit = f'{card}-{corpus}-{suffix}-DN'
        path = raw_root/unit/'COMPLETE.json'
        terminal = read(path)
        digest = filehash(path)
        if (record['unit'] != unit or terminal['unit'] != unit or terminal['card'] != card
                or not terminal['verified'] or record['terminal_sha256'] != digest
                or record['review_sha256'] != terminal['review_sha256'] or record['results'] != terminal['results']):
            raise ValueError('Meeting-corpus receipt differs: '+corpus)
        verified[unit] = digest
    return verified


def confirm():
    r48_reports.build(check=True)
    head=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]
    if head!=git('rev-parse','origin/main'):
        raise RuntimeError('Fetch the latest published revision before confirming landings')
    dispositions=STATE/'dispositions.json'
    states_hash=filehash(dispositions)
    states=read(dispositions)
    if not any(s.get('pending_r48_receipt') for s in states.values()):
        return
    coverage=ROOT/'.agent-state/work-coverage.json'
    coverage_hash=filehash(coverage)
    work=read(coverage)
    specs=read(r48_reports.SPECS)
    for card,s in states.items():
        stem=s.get('pending_r48_receipt')
        if not stem or card not in specs:
            continue
        raw=PUBLIC/(stem+'.json')
        spec=specs[card]
        if ROOT/spec['record']!=raw.with_suffix('.md'):
            raise ValueError('Report must identify the current landing receipt')
        files=[raw,ROOT/spec['record'],r48_reports.OUT/(card+'.md'),r48_reports.OUT/(card+'.csv'),
               r48_reports.DIGEST,r48_reports.SPECS,r48_reports.SEALED,ROOT/'tools/r48_reports.py']
        for path in files:
            rel=path.relative_to(ROOT).as_posix()
            if git('rev-parse',head+':'+rel)!=git('hash-object','--path='+rel,rel):
                raise ValueError('Publication differs: '+rel)
        published_receipt=read(raw)
        corpus_hashes=meeting_terminals(card,published_receipt,gear.ROOT)
        s.update(status='landed',r48_commit=head)
        s.pop('pending_r48_receipt')
        entry,=[v for v in work['work'] if v['card']==card]
        entry['state']='closed'
        atomic(STATE/'r48-landings'/(stem+'.json'),dict(card=card,commit=head,full_write_through=True,
            terminal_sha256=published_receipt['terminal_sha256'],**({'corpus_terminal_sha256':corpus_hashes} if corpus_hashes else {})))
    if filehash(coverage)!=coverage_hash or filehash(dispositions)!=states_hash:
        raise RuntimeError('Operational records advanced during publication verification. Reread before closing.')
    atomic(coverage,work)
    atomic(dispositions,states)


if __name__=='__main__':
    confirm()
