"""Render the Week 8 roster with the current admission reason and native sealed codes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import week8_queue as roster
from tools import week8_spark_queue as dispatch
from runners.stage14.common import read


def render():
    snapshot = roster.snapshot()
    roster.render(snapshot)
    text = roster.RETURN.read_text(encoding='utf8')
    first = text.splitlines()[0]
    free = max(0, snapshot['free'])
    ready = snapshot['ready']
    new = first
    if ready:
        names = ', '.join(ready)
        reason = dispatch.headroom()
        new = f"The ready list contains {names} with {free} free shared CPU slots."
        if reason:
            new += ' ' + reason + ' currently limits starts.'
        elif all(snapshot['rows'][card]['host'] == 'Spark' for card in ready):
            new += ' The sealed dispatcher starts the next qualified job when its lane is free.'
    text = text.replace(first, new, 1)
    text = text.replace('## Study roster\n', f"## Study roster\n\nRead at {snapshot['at']} (UTC).\n", 1)
    for card, attempts in snapshot['attempts'].items():
        for unit, terminal, _, sealed in attempts:
            if not sealed or terminal != 'FAILED':
                continue
            native = dispatch.SHARED / (unit + '.native.json')
            if native.is_file():
                prefix = f'- {card}, {unit}. Exit '
                lines = text.splitlines(keepends=True)
                for pos, line in enumerate(lines):
                    if line.startswith(prefix):
                        lines[pos] = line.rstrip() + f" Native study exit {read(native)['native']}.\n"
                text = ''.join(lines)
    roster.RETURN.write_text(text, encoding='utf8', newline='\n')
    index = roster.DESIGN / 'README.md'
    index.write_text(index.read_text(encoding='utf8').replace(first,new,1), encoding='utf8', newline='\n')
    print(new)


if __name__ == '__main__':
    render()
