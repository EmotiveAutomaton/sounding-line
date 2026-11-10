"""Native human-free AMI/ICSI NXT parser fixture for real worker replay."""
from collections import Counter
from pathlib import Path
import io,zipfile
from .week5_la_source import corpus_data
from .timing_census import read
from .timing_p6 import write_equal


def fixture():
    receipts=[]
    for corpus in ('AMI','ICSI'):
        stream=io.BytesIO();prefix='' if corpus=='AMI' else 'ICSI/'
        folder='words' if corpus=='AMI' else 'Words';da='dialogueActs' if corpus=='AMI' else 'DialogueActs'
        ns='xmlns:n="http://nite.sourceforge.net/"'
        words=f'<r {ns}><w n:id="z" starttime="0" endtime="1">constructed</w><vocalsound n:id="x" starttime="1" endtime="2" type="laugh" description="laugh"/><w n:id="a" starttime="2" endtime="3">words</w></r>'
        acttype='<n:pointer role="da-aspect" href="types.xml#id(inform)"/>' if corpus=='AMI' else ''
        acts=f'<r {ns}><act n:id="d" type="inform" participant="fake-person">{acttype}<n:child href="../{folder}/fixture.A.words.xml#id(z)..id(a)"/></act></r>'
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr(prefix+folder+'/fixture.A.words.xml',words)
            z.writestr(prefix+da+'/fixture.A.dialogue-acts.xml',acts)
            if corpus=='AMI':
                z.writestr('corpusResources/participants.xml',f'<r {ns}><participant n:id="fake-person" native_language="English"/></r>')
                z.writestr('corpusResources/meetings.xml','<r><meeting observation="fixture"><speaker nxt_agent="A" global_name="fake-person"/></meeting></r>')
            else:z.writestr('ICSI/speakers.xml','<r><speaker tag="fake-person"><language name="English"><variety>American</variety><region>Midwest</region></language></speaker></r>')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as z:
            counts=Counter();acts,laughs,metadata=corpus_data(z,corpus,b'0'*32,counts)
        if len(acts)!=1 or len(laughs)!=1 or len(metadata)!=1:raise ValueError('NXT native population differs')
        a=acts[0]
        if [w['text'] for w in a['words']]!=['constructed','words'] or a['start']!=0 or a['end']!=3:
            raise ValueError('NXT native range/mark exclusion failed')
        if any('fake-person' in str(x) for x in (acts,laughs,metadata)):raise ValueError('Unsalted identity escaped')
        info=metadata[a['meeting']]['speakers'][a['speaker']]
        if corpus=='AMI' and info.get('native_language')!='english':raise ValueError('AMI native language mapping failed')
        if corpus=='ICSI' and info.get('english_variety')!='american':raise ValueError('ICSI variety mapping failed')
        receipts.append(dict(corpus=corpus,acts=acts,laughs=laughs,metadata=metadata,counts=dict(counts)))
    return dict(fixture_only=True,scientific_admission=False,sources=receipts)


def execute(output,inputs,config):
    if inputs or config:raise ValueError('Fixture takes no external input')
    write_equal(Path(output)/'FIXTURE.json',fixture())
    return dict(status='complete',fixture_only=True)


def verify(output,inputs,config):
    if read(Path(output)/'FIXTURE.json')!=fixture():raise ValueError('Fresh native source fixture differs')
    return dict(verified=True,complete_parser_replay=True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
