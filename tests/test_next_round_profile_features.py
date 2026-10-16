import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timedelta,timezone
import numpy as np
from runners.next_round.profile_features import engine,profile_vector,choice_features,predict_all,validate_native,run
from runners.stage14.common import freeze

class ProfileFeaturesTests(unittest.TestCase):
    def test_changed_native_source_and_future_history_refuse(self):
        target=dict(writer='a',prompt='x',open_at=10,document='given text',menu=['a','b'],handling='accept')
        raw=dict(target,resolved_at=11);config=dict(cutoff=9,h2=[dict(resolved_at=8)],h3=[dict(resolved_at=7)])
        validate_native(target,raw,config)
        with self.assertRaises(ValueError):validate_native(target,dict(raw,menu=['changed']),config)
        with self.assertRaises(ValueError):validate_native(target,raw,dict(config,h3=[dict(resolved_at=9)]))
        with self.assertRaises(ValueError):validate_native(target,dict(raw,resolved_at=9),config)

    def test_actual_run_refuses_without_scientific_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);freeze(root/'PLAN.json',dict(implementation_hash='a'*64,ledger_schema_hash='b'*64))
            freeze(root/'admission.json',dict(scope='wrong'))
            with patch('runners.next_round.profile_features.ROOT',root),patch('runners.next_round.profile_features.predict_all') as fit:
                with self.assertRaises(ValueError):run(root/'admission.json')
                fit.assert_not_called();self.assertFalse((root/'ATTEMPT.claim').exists())

    def test_profile_interaction_changes_option_contrast(self):
        a=choice_features([1],profile_vector(['likes quiet endings']),2)
        b=choice_features([1],profile_vector(['likes abrupt endings']),2)
        self.assertFalse(np.array_equal(a[0]-a[1],b[0]-b[1]))
        np.testing.assert_array_equal(profile_vector(['ONE two one']),profile_vector(['two one ONE']))

    def test_canonical_engine_learns_and_donor_reverses_planted_relation(self):
        Backbone,Choice,_,_=engine();t=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=[]
        for i in range(32):
            label=i%2;v=profile_vector(['bright' if label==0 else 'dark'])
            rows.append(Choice(str(i),'training-'+str(i),t+timedelta(seconds=2*i),t+timedelta(seconds=2*i+1),choice_features([1],v,2),label))
        fit=Backbone.fit(rows,until=t+timedelta(seconds=100))
        for label,word,donor in ((0,'bright','dark'),(1,'dark','bright')):
            self.assertGreater(fit.predict('unseen',choice_features([1],profile_vector([word]),2))[label],.8)
            self.assertLess(fit.predict('unseen',choice_features([1],profile_vector([donor]),2))[label],.2)
        base=[Choice(r.id,r.maker,r.opened,r.resolved,choice_features([1],np.zeros(32),2),r.taken) for r in rows]
        b=Backbone.fit(base,until=t+timedelta(seconds=100))
        np.testing.assert_allclose(b.predict('unseen',choice_features([1],np.zeros(32),2)),[.5,.5],atol=1e-10)

    def test_prequential_handler_future_labels_and_cold_start(self):
        records=[];labels=[]
        for i in range(4):
            x=choice_features([1],np.zeros(32)).tolist()
            records.append(dict(key=str(i),writer='w'+str(i),prompt='p',open_at=1600000000000+i*2000,
                resolved_at=1600000001000+i*2000,features={a:x for a in ('baseline','own','donor')}))
            labels.append(dict(key=str(i),action=i%4))
        a=predict_all(records,labels)
        labels[-1]['action']=0;b=predict_all(records,labels)
        self.assertEqual(a,b)
        self.assertTrue(a[0]['arms']['baseline']['cold_start'])
        self.assertEqual(a[-1]['arms']['own']['training_keys'],['0','1','2'])

if __name__=='__main__':unittest.main()
