import unittest
from runners.drive.content_features import scalar_features,token_view

class Tokenizer:
    def __call__(self,text,**kw):return {'input_ids':list(range(len(text))),'offset_mapping':[(i,i+1) for i in range(len(text))]}
    def build_inputs_with_special_tokens(self,ids):return [1000]+ids+[1001]

class FeaturesTests(unittest.TestCase):
    def test_order_and_target_independence(self):
        menu=['known fresh','other'];a=scalar_features('known',menu);b=scalar_features('known',menu[::-1])
        self.assertEqual(a[0][:-1],b[1][:-1]);self.assertEqual(a[0][2],.5)
        self.assertEqual([x[-1] for x in a],[0,1])
    def test_scope_tail_context_head_suggestion(self):
        tok=Tokenizer();a,ma=token_view(tok,'a'*300,'context');b,mb=token_view(tok,'a'*300,'suggestion')
        self.assertEqual(len(a),256);self.assertEqual(a[1],46);self.assertEqual(b[1],0)
        self.assertEqual(ma['codepoint_end'],300);self.assertEqual(mb['codepoint_end'],254)
        self.assertTrue(ma['truncated']);self.assertTrue(mb['truncated'])
    def test_empty_and_invalid_role(self):
        ids,scope=token_view(Tokenizer(),'','context');self.assertEqual(ids,[1000,1001]);self.assertFalse(scope['truncated'])
        with self.assertRaises(ValueError):token_view(Tokenizer(),'a','future')

if __name__=='__main__':unittest.main()
