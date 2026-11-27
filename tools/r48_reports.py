"""Build public reports from reviewed aggregate tables and verify publication bytes."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCHANGE = ROOT / 'docs/exchange'
OUT = EXCHANGE / 'r48'
INVENTORY = EXCHANGE / 'HELD_RESULTS_INVENTORY.md'
DIGEST = EXCHANGE / 'HELD_RESULTS_DIGEST.md'
SPECS = OUT / 'studies.json'
FIELDS = ['quantity', 'estimate', 'lower', 'upper', 'size', 'unit', 'observations', 'reading']
READINGS = {'positive', 'negative', 'descriptive', 'control', 'support'}
SEALED = OUT / 'sealed_tables.json'


def rows_for(key, spec, locks):
    path = OUT / (key + '.csv')
    data = path.read_bytes()
    reader = csv.DictReader(io.StringIO(data.decode('utf-8')))
    if reader.fieldnames != FIELDS:
        raise ValueError(f'{key}: unexpected aggregate schema')
    rows = list(reader)
    if spec['class'] == 'S':
        # Each digest identifies the checked projection of an original gate release.
        # Empty status-only tables contain no inferred estimates or participant counts.
        if hashlib.sha256(data).hexdigest() != locks[key]:
            raise ValueError(f'{key}: class S table differs from reviewed gate projection')
    for r in rows:
        if None in r or any(v is None for v in r.values()):
            raise ValueError(f'{key}: malformed row')
        if r['reading'] not in READINGS or not r['quantity'] or '|' in r['quantity']:
            raise ValueError(f'{key}: invalid row label')
        if spec['class'] == 'S':
            if (r['unit'] != 'people' or not r['size'].isdigit() or int(r['size']) < 11
                    or re.search(r'\b(minimum|maximum|min|max|id|pid|speaker key|participant key)\b', r['quantity'], re.I)):
                raise ValueError(f'{key}: invalid class S cell')
        for name in ['estimate','lower','upper','size','observations']:
            if r[name] and not math.isfinite(float(r[name])):
                raise ValueError(f'{key}: nonfinite value')
        if bool(r['lower']) != bool(r['upper']) or (r['lower'] and float(r['lower']) > float(r['upper'])):
            raise ValueError(f'{key}: invalid interval')
    return rows


def number(value):
    return format(float(value), '.6g') if value else '—'


def effect(r):
    result = number(r['estimate']) if r['estimate'] else '—'
    if r['lower']:
        result += f" [{number(r['lower'])}, {number(r['upper'])}]"
    return result


def relation(r):
    if r['reading'] in {'descriptive','control','support'}:
        return r['reading'].capitalize()
    if not r['lower']:
        return 'Interval unavailable'
    lo, hi = map(float, (r['lower'], r['upper']))
    if lo <= 0 <= hi:
        return 'Interval includes zero'
    return 'Predicted direction' if (lo > 0) == (r['reading'] == 'positive') else 'Opposite direction'


def render(key, s, rows):
    source_link = os.path.relpath(ROOT / s['record'], OUT).replace(os.sep, '/')
    lines = [f"# {key} · {s['question']}", '', f"**Registered prediction.** {s['prediction']}", '',
             f"**Source and sample.** Class {s['class']}. {s['source']} {s['sample']}", '',
             '**Registered quantities.** ' + s['method'], '']
    if rows:
        folded = len(rows) > 30
        if folded:
            first = next((r for r in rows if r['quantity'] == s.get('headline')), rows[0])
            lines += [f"{first['quantity']}: {effect(first)} ({first['size']} {first['unit']}).",
                      '', f'<details><summary>All {len(rows)} released quantities</summary>', '']
        lines += ['| Quantity | Estimate [interval] | Size and unit | Observations | Reading |',
                  '|---|---:|---|---:|---|']
        for r in rows:
            lines.append(f"| {r['quantity']} | {effect(r)} | {r['size']} {r['unit']} | {r['observations'] or '—'} | {relation(r)} |")
        if folded:
            lines += ['', '</details>']
    else:
        lines.append('The job returned no numerical rows. Estimate, interval and analytical sample size are unavailable.')
    lines += ['', f"**Verdict — {s['verdict']}.** {s['basis']}", '', '**Limit.** ' + s['limit'], '',
              '**Withholding and release condition.** ' + s['withheld'], '',
              f"[Released table]({key}.csv) · [Report generator](../../../tools/r48_reports.py) · [Original record]({source_link})"]
    if s['class'] == 'S':
        lines[-1] += ' · [Retained reporting terms and source credits](../../design/stage-15/R48_SOURCE_TERMS.md)'
    return '\n'.join(lines) + '\n'


def inventory_ids():
    return [line.split('|')[1].strip() for line in INVENTORY.read_text(encoding='utf8').splitlines()
            if re.match(r'^\| [^|]+ \| [0-9]+ \| [PS] \|', line)]


def build(check=False):
    specs = json.loads(SPECS.read_text(encoding='utf8'))
    extra=json.loads((OUT/'earlier.json').read_text(encoding='utf8'))
    if specs.keys() & extra.keys():
        raise ValueError('Duplicate study registration')
    specs.update(extra)
    locks = json.loads(SEALED.read_text(encoding='utf8'))
    if set(locks) != {k for k,s in specs.items() if s['class'] == 'S'}:
        raise ValueError('Missing or unregistered sealed publication')
    digest = ['# Held results digest', '', 'Each interval and size comes from the linked aggregate table. A withheld entry reports its native disposition. The inventory tracks earlier studies awaiting reports.', '',
              '| Study | Week | Question | Verdict | Headline estimate [interval] and size | Limit | Release | Report |',
              '|---|---:|---|---|---|---|---|---|']
    expected = {}
    for key,s in sorted(specs.items(),key=lambda item: (-item[1]['week'],item[0])):
        if len(s['short'].split()) > 15 or not (ROOT / s['record']).is_file():
            raise ValueError(key + ': invalid question or record')
        rows = rows_for(key,s,locks)
        expected[OUT / (key + '.md')] = render(key,s,rows)
        ref = s.get('headline')
        if ref is None:
            headline = s.get('no_headline', 'Withheld; analytical size unavailable')
        else:
            r = next(row for row in rows if row['quantity'] == ref)
            headline = f"{r['quantity']}: {effect(r)}, {r['size']} {r['unit']}"
        digest.append(f"| {key} | {s['week']} | {s['short']} | {s['verdict']} | {headline} | {s['limit']} | {s['status']} | [Report](r48/{key}.md) |")
    missing = [key for key in inventory_ids() if key not in specs]
    status = (f'{len(missing)} earlier entries await reconciliation of the aggregate sheets or withholding receipts.'
              if missing else 'Every inventoried earlier entry has a report.')
    digest += ['', status + ' [Earlier inventory](HELD_RESULTS_INVENTORY.md).']
    expected[DIGEST] = '\n'.join(digest) + '\n'
    for path, content in expected.items():
        data = content.encode('utf8')
        if check:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError(f'Generated report differs: {path.name}')
        elif not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
    print(f'{len(specs)} reports, {len(locks)} class S checks, {len(missing)} earlier entries awaiting reports')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    build(ap.parse_args().check)
