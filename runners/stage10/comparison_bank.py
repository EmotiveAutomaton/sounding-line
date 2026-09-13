"""Read-only complete-cell scoring from an explicit source-bound manifest.

DESIGN CHECK: existing Stage10 comparison freeze and LESSONS3-5. NULL gives
zero paired benefit for identical forecasts; ALTERNATIVE improves known-answer
scores. Incomplete or changed rosters refuse, invalid rows retain worst loss,
and every source group remains distinct. This creates private analysis, not
automatic scientific claims or a replacement for the final write-through.
"""
import argparse
from collections import defaultdict
from pathlib import Path
from . import comparison
from .contracts import digest
from .reader import from_record
from .queue import read
from .ollama import write_new,now
from .revision_bank import sha,finish,checked


def analyze(bundle):
    if set(bundle)!={'schema','sources','cells','scope'} or bundle['schema']!='stage10.comparison-bank.1':raise ValueError('undeclared comparison manifest')
    results=[]
    for spec in bundle['cells']:
        tasks=[from_record(t) for t in spec['tasks']]
        arms=spec['predictions'];cells={}
        if 'R0' not in arms:raise ValueError('direct comparator absent')
        for arm,predictions in arms.items():cells[arm]=comparison.cell(tasks,spec['answers'],predictions,spec['population'])
        pairs={}
        for treated,control in spec['contrasts']:
            if treated not in cells or control not in cells:raise ValueError('declared contrast incomplete')
            pairs[treated+' vs '+control]=comparison.paired(cells[treated],cells[control])
        for arm,cost in spec['costs'].items():
            if arm not in arms or any(type(v) not in {int,float} or v<0 for v in cost.values()):raise ValueError('invalid cost or arm')
        if set(spec['costs'])!=set(arms):raise ValueError('every arm needs costs')
        results.append({'population':spec['population'],'cells':cells,'paired':pairs,'costs':spec['costs'],
                        'scope':spec['scope'],'exclusions':spec.get('exclusions',[])})
    return {'schema':'stage10.comparison-results.1','manifest_sha256':digest(bundle),'results':results,'scope':bundle['scope']}


def run(manifest,output):
    bundle=read(manifest)
    for name,expected in bundle['sources'].items():
        if sha(Path(name))!=expected:raise ValueError('comparison source differs: '+name)
    result=analyze(bundle);binding=digest([bundle,sha(Path(__file__)),sha(Path(comparison.__file__))])
    if (output/'COMPLETE.json').exists():
        checked(output)
        if read(output/'RESULT.json')!=result:raise ValueError('complete analysis changed')
    else:
        output.mkdir(parents=True,exist_ok=False);write_new(output/'RESULT.json',result)
        # Numeric draft stays private with source text. An agent must inspect
        # all cells/controls and complete the stage's single scientific packet.
        lines=['# Stage 10 complete-cell analysis draft','','Private numeric analysis; scientific interpretation and final write-through pending.','']
        for item in result['results']:
            lines += ['## '+item['population'],'',item['scope'],'',
              'Rows are reader strategies. Attempts include invalid forecasts; groups count independent source units. Lower Brier system loss is better and retains invalid forecasts at loss one.','',
              '| Reader | Attempts | Source groups | Invalid | Brier system loss | Generated-choice accuracy |',
              '|---|---:|---:|---:|---:|---:|']
            for arm,cell in item['cells'].items():
                s=cell['summary'];lines.append(f"| {arm} | {s['attempted']} | {s['groups']} | {s['invalid']} | {s['brier_system']:.6f} | {s['generated_accuracy_system']:.6f} |")
            lines+=['','Exact paired log-score denominators, zero-support counts, calibration and costs are in RESULT.json.','']
        (output/'DRAFT.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    return finish(output,binding,{'scientific_verdict':False,'final_stage_packet':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:run(a.manifest,a.output)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():write_new(a.output/'FAILED.json',{'at':now(),'error':repr(exc)})
        raise
