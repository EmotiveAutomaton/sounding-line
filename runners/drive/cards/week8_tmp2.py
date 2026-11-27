"""Count the original-reader rehearsal on invented histories against the TMP2 allowance."""
import csv
from datetime import date, timedelta
import hashlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

from . import week8_gear as gear
from runners.drive.sealed import week8_package as package
from runners.stage14.common import filehash, freeze, read
from tools.week8_sealed import GATE, HOST, STATE

FIXTURE = 'TMP2-TP58-original-archive-fixture'
UNIT = 'TMP2-DJ-TP58-reader'
MANIFEST_DIGEST = 'f2a7a8eb109f9691394305b2409ceede434d0761bc97e328c41d04c677868752'
RECEIPT_DIGEST = '524294e81cfc0076a755c35f53c2578798f86428aa9b0068fe650cb8f17ab243'
ALIAS = 'pandora-tmp2-tp58'
PRODUCER = gear.REPO/'.agent-state/drive-20261115/week7-phase1/TP58-delivery-a'
STUDY = package.LIB/'week8_tmp2_reader.py'
MODULES = [STUDY, package.LIB/'week8_tmp2_source.py', package.LIB/'week7_tmp1_shell.py']
NOTE = gear.REPO/'docs/design/stage-15/week8/TMP2_READER.md'
MAPPING = gear.REPO/'docs/design/stage-15/week8/TMP2_MAPPING.md'
BINDING = STATE/'TMP2_DJ_BINDING.json'
TABLES = ['traits.csv','contrast.csv','channels.csv','stability.csv','posts_needed.csv','fixed_profile.csv','matching.csv','growth.csv','curve_check.csv']


def reviewed():
    archive = Path(read(gear.REPO/'.agent-state/data_collection_root.json')['root'])
    receipt = archive/'_handoffs/repo-requests/DC-20261127-TMP2-TP58/SOURCE_RECEIPT.json'
    manifest = PRODUCER/'manifest.json'
    if filehash(receipt) != RECEIPT_DIGEST or filehash(manifest) != MANIFEST_DIGEST:
        raise ValueError('Unrecognized source or reader manifest')
    source = read(receipt)
    binding = read(BINDING)
    if (source['source_alias'] != ALIAS or source['tp58_producer_manifest_sha256'] != MANIFEST_DIGEST
            or source['pandora_archive_receipt_sha256'] != binding['source_receipt_sha256']
            or binding['provider_binding_sha256'] != filehash(MAPPING)):
        raise ValueError('Combined receipt differs from the reviewed original mappings')
    payload = read(manifest)
    combined = {r['path']:r for r in source['files']}
    expected = {'payload/'+p:s for p,s in payload.items()}
    expected.update({'projection/'+r['name']:r['sha256'] for r in binding['archives'].values()})
    if len(combined) != 22 or len(source['files']) != 22 or set(expected) != set(combined):
        raise ValueError('Combined source roster differs')
    if any(combined[p]['sha256'] != s for p,s in expected.items()):
        raise ValueError('Combined source digest differs')
    pins = [receipt,manifest,BINDING,MAPPING,NOTE,*MODULES,Path(package.__file__),package.SUPPORT,package.RELEASE,
            Path(__file__),GATE,HOST,gear.REPO/'tools/week8_spark.ps1',gear.REPO/'tools/week8_sealed.py']
    return binding, payload, pins


def design(unit):
    if unit != FIXTURE:
        raise ValueError('Unrecognized constructed rehearsal')
    _, payload, pins = reviewed()
    expected = {PRODUCER/'payload'/k:v for k,v in payload.items()}
    return dict(inputs=[*pins,*expected],expected={str(k):v for k,v in expected.items()},peak=1.5,cap=600,
                operations=['execute'],source='invented-histories-with-verified-engine-bundle')


def zip_table(path, name, header, rows):
    text = io.StringIO(newline='')
    writer = csv.writer(text)
    writer.writerow(header)
    writer.writerows(rows)
    content = text.getvalue().encode('utf8')
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr(name,content)
    return dict(name=path.name,bytes=path.stat().st_size,expanded=len(content),sha256=filehash(path))


def invented(projection, fixture_source):
    fixture_source.mkdir()
    with (projection/'traits.csv').open(encoding='utf8',newline='') as stream:
        raw = csv.reader(stream)
        header = next(raw)
        profiles = [[a,*[float(n)*100 for n in v]] for a,*v in raw]
    profiles += [[f'unposted{i}',40,50,60,70,80] for i in range(12)]
    profiles += [[f'incomplete{i}','',50,60,70,80] for i in range(12)]
    with (projection/'comments.csv').open(encoding='utf8',newline='') as stream:
        comments = []
        for r in csv.DictReader(stream):
            if r['id'].startswith('excluded-'):
                body, group = 'Openness 80 and Neuroticism 60', 'collection'
            else:
                body, group = (r['text']+' ')*2, r['community']
            comments.append([r['author'],body,group,r['day'],r['id']])
    # These authored markup tokens count in the source and vanish on the producer's
    # documented text cleaning. They keep the invented outside-writer style fit testable.
    markup = '<'+' '.join(['example']*60)+'>'
    for i in range(32,48):
        for day in range(18,126):
            comments.append([f'person{i}',markup,'fiction',str(date(2000,1,1)+timedelta(days=day)),f'{i}-{day}'])
    return dict(profiles=zip_table(fixture_source/'pandora_profiles.zip','author_profiles.csv',header,profiles),
                comments=zip_table(fixture_source/'pandora_comments.zip','all_comments_since_2015.csv',
                                   ['author','body','subreddit','created_utc','id'],comments))


def fixture():
    binding, payload, _ = reviewed()
    if len(payload) != 20 or filehash(GATE) != read(HOST)['installed_gate_sha256']:
        raise ValueError('Reader or installed gate changed')
    unit = package.package(STUDY,MODULES,dict(files=binding['archives'],payload=payload,real_image=True),15400)
    compile(unit,'run.py','exec')
    return dict(exact_producer_files=20,archive_files=2,combined_verified=True,
                compiled_entry_sha256=hashlib.sha256(unit).hexdigest(),scope='constructed rehearsal only')


def run(unit, directory, mode):
    if unit != FIXTURE or mode != 'execute':
        raise ValueError('Unrecognized local operation')
    _, payload, _ = reviewed()
    with TemporaryDirectory(dir=directory) as tmp:
        work = Path(tmp)
        mount = work/'fixture'
        mount.mkdir()
        shutil.copytree(PRODUCER/'payload',mount/'payload')
        factory = mount/'payload/made.py'
        if filehash(factory) != payload['made.py']:
            raise ValueError('Fixture generator differs')
        spec = importlib.util.spec_from_file_location('tmp2_invented',factory)
        made = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(made)
        original = work/'invented'
        made.make(original)
        files = invented(original,mount/'projection')
        entry = work/'entry.py'
        entry.write_bytes(package.package(STUDY,MODULES,dict(files=files,payload=payload,real_image=False),600,fixture=True))
        out = work/'aggregates'
        out.mkdir()
        subprocess.run([sys.executable,'-B',str(entry),str(mount),str(out)],check=True)
        if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip() != 'gate passed':
            raise ValueError('Fixture failed the installed gate')
        tables = {}
        for path in sorted(out.iterdir()):
            with path.open(encoding='utf8',newline='') as stream:
                rows=list(csv.DictReader(stream))
            if not rows or path.name not in TABLES:
                raise ValueError('Unexpected fixture output')
            if set(int(r['n']) for r in rows) != ({48} if path.name in ('traits.csv','contrast.csv','channels.csv') else {32}):
                raise ValueError('Fixture membership reconstruction failed')
            tables[path.name] = len(rows)
        if 'traits.csv' not in tables or 'stability.csv' not in tables:
            raise ValueError('Two separately sized synthetic cohorts must be recovered')
        freeze(directory/'REHEARSAL.json',dict(constructed_only=True,producer_manifest=MANIFEST_DIGEST,
               archive_merge_receipt=RECEIPT_DIGEST,subject_counts=[48,32],aggregate_rows=tables,
               independent_projection_and_reader_replay=True,installed_gate_passed=True))


def check(unit, directory):
    proof = directory/'REHEARSAL.json'
    if unit != FIXTURE or not read(proof)['installed_gate_passed']:
        raise ValueError('Missing complete rehearsal')
    return {proof.name:filehash(proof)}
