import unittest
from runners.drive.intake import metadata_page,query,get


class MetadataTests(unittest.TestCase):
    def test_continuation_and_duplicates(self):
        page={'pageid':1,'title':'Test','revisions':[{'revid':2,'timestamp':'2020-01-01T00:00:00Z'}]}
        seen=set();_,rows,cont=metadata_page({'query':{'pages':[page]},'continue':{'rvcontinue':'next'}},seen)
        self.assertEqual(cont,{'rvcontinue':'next'});self.assertEqual(len(rows),1)
        with self.assertRaises(ValueError):metadata_page({'query':{'pages':[page]}},seen)
    def test_missing_and_api_error(self):
        for obj in [{'query':{'pages':[{'missing':True}]}},{'error':{'code':'maxlag'}}]:
            with self.assertRaises(ValueError):metadata_page(obj,set())
    def test_allowlist_and_encoded_titles(self):
        with self.assertRaises(ValueError):get('https://example.com/private')
        self.assertIn('Theory+of+mind',query({'titles':'Theory of mind'}))


if __name__=='__main__':unittest.main()
