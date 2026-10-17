import unittest
from runners.drive.readers import pack,contexts,COMMON_WINDOW


class Tokens:
    bos_token_id=0;eos_token_id=1
    def encode(self,text,**kw):return [ord(c) for c in text]
    def decode(self,ids,**kw):return ''.join(chr(i) for i in ids)
    def __call__(self,text,**kw):return dict(input_ids=self.encode(text),offset_mapping=[(i,i+1) for i in range(len(text))])


class PackingTests(unittest.TestCase):
    def test_whole_context_not_truncated(self):
        tok=Tokens();r=pack(tok,'x'*2047,'a');self.assertFalse(r['eligible'])
        r=pack(tok,'x'*2046,'a');self.assertTrue(r['eligible']);self.assertEqual(len(r['prefix'])+len(r['target']),2048)
    def test_byte_denominator_and_offsets(self):
        r=pack(Tokens(),'','😀');self.assertEqual(r['utf8_bytes'],4);self.assertEqual(r['offsets'],[(0,1)])
        self.assertEqual(r['prefix'],[0])
    def test_prompt_not_duplicated_and_recent_context_explicit(self):
        c=contexts(Tokens(),'prompt','prompt'+'x'*120)
        self.assertEqual(c['c3'].count('prompt'),1)
        self.assertEqual(c['c2'].count('x'),101)  # 'context' plus exactly 100 draft units
        self.assertEqual(c['c0'],'')


if __name__=='__main__':unittest.main()
