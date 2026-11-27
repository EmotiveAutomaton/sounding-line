"""Render the Week 8 roster with the current admission reason and native sealed codes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import week8_queue as roster
from tools import week8_spark_queue as dispatch
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
    'ATL2': "Repeated splits reuse the same diaries. Member 0049 remains internal.",
    'ADM2': "The records establish prior use only when a filed study or source check can be located.",
    'TWO3': "A difficult stretch shared by both partners can produce a lagged association.",
    'BMP1': "Named maps depend on an identified raster and plane order. The regional boundaries are analyst-defined on the blank silhouette.",
    'DRV1': "Successive changes amplify noise in a rating, and only two diaries measure these items.",
    'TMP3': "The engine learned from writing. A machine transcribed these spoken turns.",
}


def render():
    snapshot = roster.snapshot()
    roster.render(snapshot)
    text = roster.RETURN.read_text(encoding='utf8')
    first = text.splitlines()[0]
    free = max(0, snapshot['free'])
    ready = snapshot['ready']
    new = first
    if ready:
        reason = dispatch.headroom()
        new = f"The ready list contains {len(ready)} studies with {free} free shared CPU slots."
        if reason:
            if reason == 'Shared memory floor including companion headroom':
                mem = roster.gear.resource_snapshot()
                leases = roster.gear.resources.lease_paths()
                minimum = roster.gear.resources.memory_reserve(leases) + 14 + dispatch.SLOT_COST
                new += (f" Windows has {mem['commit_headroom_GiB']:.1f} GiB of memory commitment available. "
                        f"A Spark launcher needs {minimum:.1f} GiB under the shared reserve.")
            else:
                new += ' ' + reason + ' currently limits starts.'
        elif all(snapshot['rows'][card]['host'] == 'Spark' for card in ready):
            new += ' The sealed dispatcher starts the next qualified job when its lane is free.'
    text = text.replace(first, new, 1)
    text = text.replace('## Study roster\n', f"## Study roster\n\nRead at {snapshot['at']} (UTC).\n", 1)
    limits = [f"- {card}. {OPEN_LIMITS[card]}" for card, row in snapshot['rows'].items()
              if card in OPEN_LIMITS and row['status'] != 'landed']
    if limits:
        text = text.replace('## Sealed invocations\n', '## Limits for open rows\n\n' +
                            '\n'.join(limits) + '\n\n## Sealed invocations\n', 1)
    if (roster.PUBLIC/'ADM2_ARCHIVE_INVENTORY.md').exists():
        text = text.replace('ADM2 source and terms review is pending.',
                            'The [holdings census](../../results/phase_2_4_stage_15/WEEK8/ADM2_ARCHIVE_INVENTORY.md) lists each source, its retained terms, its admission and the evidence of earlier use. The counted original-source checks are queued.')
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
    roster.RETURN.write_text(text, encoding='utf8', newline='\n')
    index = roster.DESIGN / 'README.md'
    index.write_text(index.read_text(encoding='utf8').replace(first,new,1), encoding='utf8', newline='\n')
    print(new)


if __name__ == '__main__':
    render()
