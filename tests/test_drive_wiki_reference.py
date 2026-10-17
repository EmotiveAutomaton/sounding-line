import unittest
from runners.drive.wiki_reference import article_counts

class ReferenceTests(unittest.TestCase):
    def test_revert_noop_hidden_and_summary(self):
        rows=[dict(revid=i+1,timestamp=str(i),sha1=h*40,userid=1,comment=c,tags=tags)
              for i,(h,c,tags) in enumerate([('a','/* Section */',[]),('b','Reason',[]),('b','Undid revision 4',[]),('a','restored fact',['mw-reverted'])])]
        rows.append(dict(revid=5,timestamp='4'))
        c,e=article_counts(rows)
        self.assertEqual(c['identity_revert'],1);self.assertEqual(c['immediate_noop'],1)
        self.assertEqual(c['nonautomatic_summary_heuristic'],2);self.assertEqual(c['tagged_reverted_revision'],1)
        self.assertEqual(c['hidden_editor'],1);self.assertEqual(c['hidden_sha1'],1);self.assertEqual(e['id:1'],4)
        with self.assertRaises(ValueError):article_counts(rows+rows[:1])

if __name__=='__main__':unittest.main()
