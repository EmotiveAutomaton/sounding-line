"""Render the reviewable holdings inventory from the frozen ADM2 metadata."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.stage14.common import filehash,read
from runners.drive.cards.week8_adm2 import WORK,SLUGS,public_rows

FILE=WORK/'ADM2_VERIFIED_SOURCE_INVENTORY.json'
DIGEST='74e039d5dabe33d1ae5aa67357089e205951ca52b8968d7bea678cfe490c9a66'
PAGE=ROOT/'results/phase_2_4_stage_15/WEEK8/ADM2_ARCHIVE_INVENTORY.md'
QUALIFIED={'atus-activity-who':'MNG1 four-year activity and company join','atus-wellbeing':'MNG1 and the original ATUS atlas',
    'couples-daily-hassles':'TWO3 and the original couples atlas','candor':'LKG1 and LKG2 within the seal',
    'pandora-tmp2':'TMP2 original-archive admission counts inside the seal',
    'pandora-tmp2-tp58':'Time-gated TMP2 fallback mount, final reader rehearsal pending',
    'midus-m1-joined':'SLD8 original source check and matched source measures',
    'midus-m2-joined':'SLD6 registered wave-two source','midus-m1m2m3-surveys':'SLD5 and SLD7 three-wave surveys',
    'midus-m2-p1':'SLD9 survey composites','repository-rutledge':'ACC1 and ADP1 first plays',
    'ami-close-talk':'LGH6, RML1 and LGH7 within internal-use scope','ami-close-talk-slr16':'LGH6 and RML1 under the supplementary source terms',
    'icsi-close-talk':'LGH6 and RML1','repository-ami-icsi':'Meeting annotations under the applicable row',
    'openesm-0056':'ATL2 and DRV1','openesm-0057':'ATL2, DRV1 and LAG2','openesm-0049':'ATL2 internal comparison only'}

def cell(text):
    return ' '.join(str(text).split()).replace('|','\\|')

def render():
    if filehash(FILE)!=DIGEST:
        raise ValueError('Frozen source inventory version differs')
    receipt=read(FILE)
    rows=public_rows(receipt['cells'])
    audit={'repository-argrewrite':'L59, ArgRewrite purpose signal'}
    for row in rows:
        if row['source'] in audit:row['use']=audit[row['source']]
        if row['source'] in QUALIFIED:row['admission']=QUALIFIED[row['source']]
    unsupported='No prior study use verified'
    unused=[r for r in rows if r['use']==unsupported]
    used=[r for r in rows if r['use']!=unsupported]
    lines=['# ADM2 · Source inventory at Week 8 intake','',
           f"The archive inventory contains {receipt['registered']} registered source entries and {len(rows)-receipt['registered']} additional physical holdings, including aliases, parent folders and fixtures. Earlier study or source-check evidence was located for {len(used)}. The other {len(unused)} are listed first. A missing cross-reference does not prove a source was never used. The intake digest is `{DIGEST}`.",'',
           'This is the completed metadata census. The separate counted admission checks read and replay the three named original releases. An intake or a fixture can establish a source location without establishing a scientific result.','']
    for head,table in [('Sources without verified prior study use',unused),('Sources with located study or source-check evidence',used)]:
        lines.extend(['## '+head,'','| Holding | Contents | Retained terms | Week 8 admission or scope | Prior evidence |','|---|---|---|---|---|'])
        for r in table:
            terms=r['terms'].replace(';',',')
            if r['source'].startswith('midus-') and terms.startswith('See retained'):terms='ICPSR and MIDUS Conditions of Use'
            if r['source']=='openesm-0046':scope='ADM2 original codebook replay pending, internal noncommercial scope'
            elif r['source'] in SLUGS:scope='ADM2 original-source binding replay pending'
            else:scope=r['admission']
            lines.append('| '+' | '.join(cell(v) for v in (r['source'],r['title'],terms,scope,r['use']))+' |')
        lines.append('')
    lines+=['[Admission design](../../../docs/design/stage-15/week8/ADM2.md) · [Reviewed reporting terms](../../../docs/design/stage-15/week8/ARCHIVE_REVIEW.md).','']
    PAGE.write_text('\n'.join(lines),encoding='utf8',newline='\n')
    print(f'{len(rows)} inventory rows, {len(unused)} without located prior study use.')

if __name__=='__main__':
    render()
