"""Render the Week 8 roster with the current admission reason and native sealed codes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import week8_queue as roster
from tools import week8_spark_queue as dispatch
from tools import week8_local_queue as local
from tools import r48_reports
from tools import r48_retro
import subprocess
from runners.stage14.common import read

OPEN_LIMITS = {
    'TMP2': "Posted trait scores come from different tests with mixed original units. The exclusion rule may miss a community.",
    'SLD8': "Only daily feelings with matching first-wave items can enter the cross-wave comparison.",
    'LGH6': "Speech-overlapping laughs are excluded on ICSI. A funnier moment can change both voicing and the chance that another person joins.",
    'RML1': "Room sound level and pace stand in for stress. Laughs are loud and cluster in time.",
    'ACC1': "A happiness rating occurs every two or three trials. Three outcomes can reach back past the previous rating.",
    'ADP1': "The game lasts minutes and the rating scale has fixed endpoints.",
    'SLD9': "Traits and wellbeing scales are answered in the same sitting. The registered reading concerns which trait leads each row.",
    'LAG2': "A continuing event can resemble persistence of feeling. Selectively missed prompts can widen a gap.",
    'LKG2': "A speaker's self-ratings and guesses about the other person's ratings share her use of the scale.",
    'MNG1': "Meaning has one rating. Each respondent reports only three sampled activities and chooses what to do.",
    'SLD7': "Marriage is chosen and those who marry may already differ before the transition.",
    'LGH7': "An assigned meeting role is an imperfect measure of rank, and leaders may speak more often.",
    'ATL2': "Repeated splits reuse the same diaries. Member 0049 is reported separately.",
    'ADM2': "The records establish prior use only when a filed study or source check can be located.",
    'TWO3': "A difficult stretch shared by both partners can produce a lagged association.",
    'BMP1': "Named maps depend on an identified raster and plane order. The regional boundaries are analyst-defined on the blank silhouette.",
    'DRV1': "Successive changes amplify noise in a rating, and only two diaries measure these items.",
    'TMP3': "The engine learned from writing. A machine transcribed these spoken turns.",
}


def render():
    r48_reports.build()
    r48_reports.build(check=True)
    snapshot = roster.snapshot()
    # A row can have a live corpus and a sibling waiting for headroom.
    # Consult the dispatcher's eligible local reviews independently of row status.
    waiting = {}
    reasons = {}
    for path in sorted((roster.STATE/'reviews').glob('*.json')):
        spec = read(path)
        unit = spec['unit']
        if ('operations' not in spec or not spec.get('fixture') or path.stem != unit
                or (roster.gear.ROOT/unit).exists() or (local.BASE/(unit+'.hold.json')).exists()):
            continue
        waiting.setdefault(spec['card'], []).append(unit)
        reasons[unit] = local.permits(spec)
    pending_spark = dispatch.next_job()
    if pending_spark:
        spec = read(roster.STATE/'reviews'/(pending_spark+'.json'))
        waiting.setdefault(spec['card'], []).append(pending_spark)
        reasons[pending_spark] = dispatch.headroom()
    for card, units in waiting.items():
        if snapshot['rows'][card]['status'] == 'running':
            snapshot['rows'][card]['evidence'] += '. Queued: ' + ', '.join(units)
    roster.render(snapshot)
    text = roster.RETURN.read_text(encoding='utf8')
    first = text.splitlines()[0]
    free = max(0, snapshot['free'])
    new = first
    if reasons:
        label = 'unit' if len(reasons) == 1 else 'units'
        new = f"The ready list contains {len(reasons)} qualified {label} with {free} free shared CPU slots."
        for reason in sorted({r for r in reasons.values() if r}):
            units = ', '.join(k for k,v in reasons.items() if v == reason)
            new += f' {units} waits for {reason.lower()}.'
        if any(r is None for r in reasons.values()):
            new += ' A qualified unit can start at the next dispatcher check.'
    pushed=subprocess.check_output(['git','ls-tree','-r','--name-only','origin/main','--','docs/exchange/r48'],
                                   cwd=ROOT,text=True).splitlines()
    published={Path(p).stem for p in pushed if p.endswith('.md')}
    missing=set(r48_reports.inventory_ids())-published
    if missing:
        new += f' {len(missing)} inventoried earlier studies still need a pushed report while their figures and withholding receipts are reconciled.'
    else:
        new += ' 0 inventoried earlier studies lack a pushed report.'
    held=set()
    for ref in dispatch.SHARED.glob('*.hold.json'):
        if read(ref).get('amendment')!='DN':
            continue
        unit=ref.name.removesuffix('.hold.json')
        path=roster.STATE/'reviews'/(unit+'.json')
        if path.exists():
            card=read(path)['card']
            if snapshot['rows'][card]['status'] not in ('landed','running') and not any(
                    read(p).get('r48') for p in (roster.STATE/'reviews').glob(card+'-*.json')):
                held.add(card)
    if held:
        new += ' In-seal counting for all three forms still needs qualification on '+', '.join(sorted(held))+'.'
    for card, label in [('TMP2','written-history reader'),('TMP3','conversation reader')]:
        reviewed=[read(p) for p in (roster.STATE/'reviews').glob(card+'-*.json')]
        if snapshot['rows'][card]['status']!='landed' and not any(
                q.get('r48') and 'counts' not in q['unit'].lower() and 'fixture' not in q['unit'].lower()
                for q in reviewed):
            new += f' {card} {label} awaits its producer-bound in-seal cell-count rehearsal.'
    text = text.replace(first, new, 1)
    text=text.replace('# Week 8 return\n','# Week 8 return\n\n[Public reports and numerical tables](HELD_RESULTS_DIGEST.md) · [Retrospective inventory](HELD_RESULTS_INVENTORY.md).\n',1)
    for key in snapshot['rows']:
        if key in published:
            spec=read(r48_reports.SPECS)[key]
            rows=r48_reports.rows_for(key,spec,read(r48_reports.SEALED))
            headline=next((r for r in rows if r['quantity']==spec.get('headline')),None)
            result=(f"{headline['quantity']}, {r48_reports.effect(headline)} ({headline['size']} {headline['unit']})."
                    if headline else spec['basis'])
            prefix='- '+key+'. '
            text='\n'.join(f"- [{key} report](r48/{key}.md). {spec['verdict'].capitalize()}. {result} {spec['limit']}"
                           if line.startswith(prefix) else line for line in text.split('\n'))
    text=text.replace('The AMI comparison is complete and filed internally.','The AMI comparison is published in the R48 digest.')
    text = text.replace('## Study roster\n', f"## Study roster\n\nRead at {snapshot['at']} (UTC).\n", 1)
    limits = [f"- {card}. {OPEN_LIMITS[card]}" for card, row in snapshot['rows'].items()
              if card in OPEN_LIMITS and row['status'] != 'landed']
    if limits:
        text = text.replace('## Sealed invocations\n', '## Limits for open rows\n\n' +
                            '\n'.join(limits) + '\n\n## Sealed invocations\n', 1)
    if (roster.PUBLIC/'ADM2_ARCHIVE_INVENTORY.md').exists():
        text = text.replace('ADM2 source and terms review is pending.',
                            'The [holdings census](../../results/phase_2_4_stage_15/WEEK8/ADM2_ARCHIVE_INVENTORY.md) lists each source, its retained terms, its admission and the evidence of earlier use. The counted original-source checks are queued.')
    atlas_routes = roster.PUBLIC/'ADM2_ATLAS_ROUTES.json'
    if atlas_routes.is_file():
        count = sum(r['status'] == 'atlas catalogue' for r in read(atlas_routes)['rows'])
        lead = 'The campaign opened November 27'
        text = text.replace(lead, f'The [prospective atlas register](../../results/phase_2_4_stage_15/WEEK8/ADM2_ATLAS_ROUTES.json) adds {count} diaries with verified event and feeling fields. The split-half study retains its frozen roster.\n\n' + lead, 1)
    for card, attempts in snapshot['attempts'].items():
        for unit, terminal, _, sealed in attempts:
            if not sealed or terminal != 'FAILED':
                continue
            native = dispatch.SHARED / (unit + '.native.json')
            code = read(native)['native'] if native.is_file() else None
            if code is None and unit == 'LKG1-liking-gap':
                record = read(roster.PUBLIC/'LKG1_LIKING_GAP_DISPOSITION.json')
                submitted = read(roster.gear.ROOT/unit/'SUBMITTED.json')
                if record['full_write_through'] and record['entry_sha256'] == submitted['entry']:
                    code = record['native_exit']
            if code is not None:
                prefix = f'- {card}, {unit}. Exit '
                lines = text.splitlines(keepends=True)
                for pos, line in enumerate(lines):
                    if line.startswith(prefix):
                        lines[pos] = line.rstrip() + f" Native study exit {code}.\n"
                text = ''.join(lines)
    text += (f"\n## Retrospective sealed invocations\n\n{r48_retro.balance()} of {r48_retro.LIMIT} "
             "used or reserved under R48 section 7. [Disposition by study](../design/stage-15/week8/R48_RETROSPECTIVE.md).\n")
    roster.RETURN.write_text(text, encoding='utf8', newline='\n')
    index = roster.DESIGN / 'README.md'
    index.write_text(index.read_text(encoding='utf8').replace(first,new,1), encoding='utf8', newline='\n')
    print(new)


if __name__ == '__main__':
    render()
