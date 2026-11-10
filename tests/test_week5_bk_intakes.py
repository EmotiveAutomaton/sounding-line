import io,zipfile
import copy,pytest
from runners.drive.cards import week5_bk_intake_fixture as fixture,week5_bk_klicke_intake as source


def test_known_answer_source():assert all(fixture.checks().values())


def test_ambiguous_pairs_fail():
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:
        z.writestr('a/private.csv',fixture.csv_fixture());z.writestr('b/private.csv',fixture.csv_fixture());z.writestr('private.txt','text')
    with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as z:
        try:source.inventory(z)
        except ValueError:return
    raise AssertionError('Ambiguous identity pair accepted')


def test_duration_order_fail():
    raw=fixture.csv_fixture().replace(b'0,10,10,a,a',b'100,10,10,a,a')
    assert raw!=fixture.csv_fixture()
    try:source.project(raw,b'text','hash')
    except ValueError:return
    raise AssertionError('Invalid clock accepted')


def test_one_percent_collection_boundary():
    assert source.collection_status(100,0)=='passes'
    assert source.collection_status(100,1)=='passes'
    assert source.collection_status(100,2)=='invalid_over_one_percent'
    assert source.collection_status(99,1)=='invalid_over_one_percent'


def test_wiki_privacy_and_hash_oracle():
    from runners.drive.cards.week5_bk_wiki_fixture import checks
    assert all(checks().values())


@pytest.mark.parametrize('mutation',['missing_flag','wrong_hash','missing_flag_row','parent_gap'])
def test_wiki_exact_source_bindings(tmp_path,mutation):
    from runners.drive.cards import week5_bk_wiki_intake as w,week5_bk_wiki_fixture as f
    tape=copy.deepcopy(f.tape()[7:12])
    if mutation=='missing_flag':tape[2]['response']['query']['recentchanges'][0].pop('bot')
    if mutation=='wrong_hash':tape[0]['response']['query']['pages'][0]['revisions'][0]['slots']['main']['content']='changed text'
    if mutation=='missing_flag_row':tape[3]['response']['query']['recentchanges']=[]
    if mutation=='parent_gap':tape[0]['response']['query']['pages'][0]['revisions'][0]['parentid']=999
    with pytest.raises(ValueError):w.article(w.Wire(tmp_path,script=tape),dict(pageid=10,title='Constructed article 10'),f.START,f.END)
