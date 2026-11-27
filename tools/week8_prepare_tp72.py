"""Build the TP72 units and release each only after its preceding receiver check."""
import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_tmp3 as local
from runners.drive.sealed.week8_tmp3_receiver import PINS as CONVERSATION_PINS
from runners.stage14.common import read,freeze,filehash
from tools import week8_prepare_lkg1 as past

UNITS = {
    'fixture': (local.TARGET,'TMP3','tp72-fixture',local.TARGET_CAP),
    'history': ('TMP2-TP72-original-histories','TMP2','pandora-tmp2-tp72',15000),
    'conversation': ('TMP3-TP72-original-conversations','TMP3','candor-tmp3-tp72',18000)}
HISTORY = ['traits','channels','contrast','stability','fixed_profile','posts_needed','matching','growth','curve_check']
SPEECH = ['conversation_affect','conversation_traits']


def prior_conversations():
    previous,pins = past.previous()
    census = past.OLD/'lattice-20261120/spark-sc1-counts-v1/gated-return/survey_columns.csv'
    traits = ('extraversion','agreeable','conscientious','neurotic','open')
    names = {prefix+t for t in traits for prefix in ('my_','your_')}|{'you_think_my_status','i_think_your_status'}
    with census.open(newline='') as f:
        trait_counts={r['column']:int(r['n']) for r in csv.DictReader(f) if r['column'] in names}
    earlier=local.gear.ROOT/'LKG2-speaker-traits-standing-DN'
    terminal=earlier/'COMPLETE.json'
    table=earlier/'gated-return/comparisons.csv'
    complete=read(terminal)
    if not complete['verified'] or complete['aggregates']!={table.name:filehash(table)}:
        raise ValueError('Prior disclosure changed')
    with table.open(newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=1 or rows[0]['measure']!='11':
        raise ValueError('The prior roster reconstruction covers only released measure 11')
    return dict(previous=previous,pin=list(CONVERSATION_PINS['survey']),trait_counts=trait_counts,
                standing_people=int(rows[0]['n'])),[*pins,terminal,table]


def unit_entry(mode):
    unit,card,alias,cap=UNITS[mode]
    config=local.configuration(mode,True)
    inputs=local.inputs()+[Path(local.__file__),Path(__file__),Path(local.gear.__file__),local.gear.AUTHORITY,
                           ROOT/'tools/week8_spark.ps1',ROOT/'tools/week8_sealed.py']
    if mode=='history':
        binding=local.STATE/'TMP2_DJ_BINDING.json'
        mapping=ROOT/'docs/design/stage-15/week8/TMP2_MAPPING.md'
        record=read(binding)
        if record['provider_binding_sha256']!=filehash(mapping):
            raise ValueError('DJ mapping changed')
        config['files']=record['archives']
        inputs.extend([binding,mapping])
    if mode=='conversation':
        config['prior'],additional=prior_conversations()
        inputs.extend(additional)
    program=local.package.package(local.STUDY,local.MODULES,config,cap)
    entry=local.STATE/'sealed'/unit/'run.py'
    entry.parent.mkdir(exist_ok=True,parents=True)
    if not entry.exists():
        with entry.open('xb') as f:
            f.write(program)
    if entry.read_bytes()!=program:
        raise ValueError('A prepared unit already has different bytes')
    return entry,inputs


def prepare(mode,release):
    unit,card,alias,cap=UNITS[mode]
    entry,inputs=unit_entry(mode)
    if not release:
        print('Built',unit,filehash(entry))
        return
    host=local.gear.ROOT/local.UNIT
    host_review=local.STATE/'reviews'/(local.UNIT+'.json')
    proof=host/'REHEARSAL.json'
    done=read(host/'COMPLETE.json')
    if (not done['verified'] or done['review_sha256']!=filehash(host_review)
            or done['results']!={proof.name:filehash(proof)}
            or read(proof)['target_entry_sha256']!=filehash(unit_entry('fixture')[0])
            or not read(proof)['installed_gate_passed']):
        raise ValueError('The counted receiver rehearsal does not cover this package')
    pins=read(host_review)['pins']
    for p in local.inputs():
        if pins.get(str(p))!=filehash(p):
            raise ValueError('The receiver or its registered inputs changed after rehearsal')
    inputs.extend([entry,host_review,proof,host/'COMPLETE.json'])
    if mode!='fixture':
        check=local.gear.ROOT/local.TARGET
        remote=read(check/'COMPLETE.json')
        verified=check/'gated-return/conversation_affect.csv'
        submission=read(check/'SUBMITTED.json')
        if (not remote['verified'] or submission['source']!='tp72-fixture'
                or submission['entry']!=read(proof)['target_entry_sha256']
                or remote['aggregates']!={verified.name:filehash(verified)}):
            raise ValueError('The mounted rehearsal did not return its verified constructed form')
        # Compare the actual support and categorical labels across architectures.
        with verified.open(newline='') as f:
            rows=list(csv.DictReader(f))
        if (len(rows)!=12 or len({(r['reading'],r['outcome']) for r in rows})!=12
                or any(int(r['n'])!=12 or int(r['isoN'])!=200 or int(r['rotN'])!=200 for r in rows)):
            raise ValueError('Target support, matched controls or labels failed')
        inputs.extend([check/'COMPLETE.json',check/'SUBMITTED.json',verified])
    review=dict(unit=unit,card=card,source=alias,cap=cap,fixture_gate_passed=True,
                tables=[n+'.csv' for n in (HISTORY if mode=='history' else SPEECH)],
                pins={str(p):filehash(p) for p in inputs},
                r48=dict(entry_sha256=filehash(entry),rehearsal=str(proof),ruling=local.gear.RULING_SHA256))
    path=local.STATE/'reviews'/(unit+'.json')
    if path.exists():
        if read(path)!=review:
            raise ValueError('A different review exists')
    else:
        freeze(path,review)
    print('Ready',unit,filehash(path))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=UNITS)
    parser.add_argument('--release',action='store_true')
    args=parser.parse_args()
    prepare(args.mode,args.release)
