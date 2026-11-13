"""Constructed EX4 source projection; original corpus authentication substituted."""
from pathlib import Path
from . import week5_ex4 as study
from . import week5_ex4_words as words


class Session:
    def __init__(self):
        self.events = []; self.doc = []; self.up = 0.
        self.add('Nonproduction', 'NoChange', 0, 0.)

    def add(self, activity, change, cursor, pause=.2, key='x'):
        ordinal = len(self.events); down = self.up + pause * 1000
        event = {'ordinal': ordinal, 'Activity': activity, 'TextChange': change, 'CursorPosition': cursor,
                 'DownTime': down, 'UpTime': down + 50, 'PauseTime': pause * 1000,
                 'DownEvent': key, 'UpEvent': key}
        self.doc, _ = words.original.operation(self.doc, event)
        self.events.append(event); self.up = event['UpTime']

    def type(self, text, pause=1.):
        for i, char in enumerate(text):
            encoded = char.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')
            self.add('Input', encoded, len(self.doc) + len(words.units(char)), pause if i == 0 else .2, key=char)

    def record(self, session='constructed-session'):
        return {'session': session, 'events': self.events, 'final_text': words.text_of(self.doc) + '\n'}


def constructed_chain(root, monkeypatch):
    root = Path(root); source = root / 'source'; source.mkdir(parents=True)
    a = Session(); a.type('alpha ', 2.); a.type('beta ', 3.); a.type('gamma', 1.)
    b = Session(); b.type('bad'); broken = b.record('constructed-failure'); broken['final_text'] = 'not the replay\n'
    records = [a.record(), broken]
    index = [{'ordinal': i, 'session': record['session']} for i, record in enumerate(records)]
    monkeypatch.setattr(study, 'authenticate', lambda inputs: (source / 'COMPLETE.json', source, index,
        {'constructed_records': study.io.sha(Path(__file__)), 'module_sha256': study.io.sha(study.__file__)}))
    monkeypatch.setattr(study.source, 'source_record', lambda complete, folder, entry: records[entry['ordinal']])
    config = {'phase': 'EX4', 'max_new_draws': 1, 'max_wall_seconds': 30}
    terminals = []
    for _ in range(6):
        result = study.execute(root / 'run', {}, config); terminals.append(result)
        if result.get('status') != 'yielded':
            break
    for _ in range(6):
        proof = study.verify(root / 'run', {}, config); terminals.append(proof)
        if proof.get('verified') is True:
            break
    return root / 'run', result, proof, terminals
