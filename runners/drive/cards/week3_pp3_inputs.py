"""PP3 released-change process features; no scientific model or scores.

DESIGN CHECK: LESSONS 1d, 2, 3-5 reread 2026-10-26. NULL and ALTERNATIVE:
every released row remains; features cannot read either intention label, cross
author/project histories, invent pauses across ambiguous/discontinuous records,
or mistake visible editor context for a full manuscript. Changed source hashes,
unknown labels, incomplete cohorts and replay differences fail closed. Known
Unicode edits, timing breaks, future-row isolation and label invariance precede
corpus preparation. Output bands are complete preparation or explicit failure;
missing timing is a flagged field, not row deletion or a scientific null.
"""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

from runners.stage9.scholawrite import validate, LABEL_MAP, SOURCE_COUNTS
from runners.stage14.common import REPO, atomic, filehash
from .timing_p6 import write_equal

FEATURES=('log_pause_ms','pause_missing','log_burst_rows','log_inserted_chars',
          'log_deleted_chars','insertion','deletion','replacement','no_change',
          'at_visible_end','relative_visible_position','log_before_chars',
          'section','subsection','subsubsection','paragraph','figure','table',
          'equation','align','itemize','enumerate','verbatim','dollar_math')
CONFIG={'mode':'source','burst_gap_ms':2000,'rows':61504,'projects':5,'authors':12}
FIXTURE={'mode':'constructed','burst_gap_ms':2000}
COMMAND=re.compile(r'\\(section|subsection|subsubsection|paragraph)\*?\s*\{|\\(begin|end)\s*\{(figure\*?|table\*?|equation\*?|align\*?|itemize|enumerate|verbatim)\}')


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def envelope(before,after):
    """Complete single-envelope edit, not a claim about minimal edit operations."""
    left=0
    while left<min(len(before),len(after)) and before[left]==after[left]:left+=1
    right=0
    while right<min(len(before)-left,len(after)-left) and before[-right-1]==after[-right-1]:right+=1
    return left,len(before)-left-right,len(after)-left-right


def structural_context(prefix):
    values={k:0. for k in FEATURES[12:]};heading=None;stack=[]
    for m in COMMAND.finditer(prefix):
        if m.group(1):heading=m.group(1)
        else:
            name=m.group(3).rstrip('*')
            if m.group(2)=='begin':stack.append(name)
            elif name in stack:del stack[len(stack)-1-stack[::-1].index(name):]
    if heading:values[heading]=1.
    for name in stack:values[name]=1.
    # Literal unescaped dollar parity in the visible prefix; not TeX compilation.
    values['dollar_math']=float(len(re.findall(r'(?<!\\)\$',prefix))%2)
    return [values[k] for k in FEATURES[12:]]


def extract(rows,burst_gap_ms=2000):
    groups=defaultdict(list);counts=Counter();categories=Counter()
    for i,r in enumerate(rows):
        validate(r);counts[r['label']]+=1;categories[r['high-level']]+=1
        groups[(r['project'],r['author'])].append((i,r))
    result=[];missing=Counter()
    for (project,author),stream in sorted(groups.items()):
        stream.sort(key=lambda pair:(pair[1]['timestamp'],pair[0]))
        times=Counter(r['timestamp'] for _,r in stream);previous=None;burst=0
        for ordinal,r in stream:
            reason=None
            if previous is None:reason='first released row'
            elif times[r['timestamp']]!=1 or times[previous['timestamp']]!=1:reason='ambiguous timestamp block'
            elif r['timestamp']<=previous['timestamp']:reason='nonpositive interval'
            elif previous['after text']!=r['before text']:reason='discontinuous visible editor text'
            gap=None if reason else r['timestamp']-previous['timestamp']
            if reason:missing[reason]+=1
            burst=1 if gap is None or gap>burst_gap_ms else burst+1
            left,deleted,inserted=envelope(r['before text'],r['after text'])
            changed=deleted>0 or inserted>0
            x=[math.log1p(gap) if gap is not None else 0.,float(gap is None),math.log1p(burst),
               math.log1p(inserted),math.log1p(deleted),float(inserted>0 and deleted==0),
               float(deleted>0 and inserted==0),float(inserted>0 and deleted>0),float(not changed),
               float(changed and left+deleted==len(r['before text'])),
               left/max(1,len(r['before text'])),math.log1p(len(r['before text']))]
            x+=structural_context(r['before text'][:left])
            assert len(x)==len(FEATURES) and all(math.isfinite(v) for v in x)
            result.append(dict(source_ordinal=ordinal,project=digest({'project':project}),
                author=digest({'project':project,'author':author}),label=r['label'],category=r['high-level'],
                features=x,pause_missing_reason=reason,pause_ms=gap,
                before_sha256=hashlib.sha256(r['before text'].encode()).hexdigest(),
                after_sha256=hashlib.sha256(r['after text'].encode()).hexdigest()))
            previous=r
    result.sort(key=lambda r:r['source_ordinal'])
    assert [r['source_ordinal'] for r in result]==list(range(len(rows)))
    summary=dict(rows=len(rows),projects=len({p for p,a in groups}),project_scoped_author_ids=len(groups),
        source_classes=dict(sorted(counts.items())),source_categories=dict(sorted(categories.items())),
        pause_missing=dict(sorted(missing.items())),pause_observed=len(rows)-sum(missing.values()),
        features=list(FEATURES),row_deletions=0,source_text_exported=False,scientific_admission=False,
        scope='Released labelled edit rows in partial visible editor states; filtered intervals are not raw physical keypress pauses. Project-scoped IDs are not established persons. Labels are annotations, not writer self-report.')
    return result,summary


def load(inputs,config):
    if config==FIXTURE and set(inputs)=={'fixture'}:
        return json.loads(Path(inputs['fixture']).read_text(encoding='utf8'))
    if config!=CONFIG or set(inputs)!={'source_identity'}:raise ValueError('fixed complete source contract required')
    identity=json.loads(Path(inputs['source_identity']).read_text(encoding='utf8'))
    for name,h in identity['source_files']['files'].items():
        p=(REPO/name).resolve();p.relative_to(REPO)
        if filehash(p)!=h:raise ValueError('source file differs')
    from datasets import load_from_disk
    # Read only the authenticated all_sorted release, never the leaked shipped split.
    ds=load_from_disk(str(REPO/'results/scholawrite/dataset/all_sorted'))
    rows=list(ds)
    if len(rows)!=CONFIG['rows']:raise ValueError('incomplete source population')
    return rows


def build(inputs,config):
    result,summary=extract(load(inputs,config),config['burst_gap_ms'])
    if config==CONFIG:
        if (summary['source_classes']!=SOURCE_COUNTS or summary['projects']!=5
                or summary['project_scoped_author_ids']!=12):raise ValueError('canonical source census differs')
    summary['mode']=config['mode']
    summary['input_sha256']={k:filehash(v) for k,v in inputs.items()}
    summary['rows_canonical_sha256']=digest(result)
    return result,summary


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows,summary=build(inputs,config)
    payload=''.join(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows).encode()
    target=output/'ROWS.jsonl.gz';compressed=gzip.compress(payload,mtime=0)
    if target.exists() and target.read_bytes()!=compressed:raise ValueError('source output changed on reentry')
    if not target.exists():target.write_bytes(compressed)
    write_equal(output/'SUMMARY.json',summary)
    return summary


def verify(output,inputs,config):
    rows,summary=build(inputs,config)
    with gzip.open(Path(output)/'ROWS.jsonl.gz','rt',encoding='utf8') as stream:stored=[json.loads(line) for line in stream]
    if stored!=rows or json.loads((Path(output)/'SUMMARY.json').read_text())!=summary:raise ValueError('fresh complete source replay differs')
    return dict(verified=True,complete_source_and_features_replay=True,rows=len(rows),scientific_admission=False)
