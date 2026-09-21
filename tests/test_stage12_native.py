"""Actual shared architecture, probability and state-transition controls."""
from pathlib import Path
import tempfile,unittest
import numpy as np
from runners.stage12 import native_math as N,native_shared as S
from runners.stage12.common import filehash


class NativeShared(unittest.TestCase):
    def test_original_alignment_resolves_bound_parent_not_missing_local_copy(self):
        with tempfile.TemporaryDirectory() as td:
            snapshot=Path(td)/'SNAPSHOT.json';root=Path(td)/S.FIXTURE
            (root/'reader').mkdir(parents=True);(root/'COMPLETE.json').write_text('{}')
            np.savez(root/'reader/train.npz',codes=np.zeros((1,32),dtype=int),novel=np.ones((1,32),bool))
            cfg={'fixture_complete_sha256':filehash(root/'COMPLETE.json')}
            resolved=S.bound_fixture(snapshot,cfg)
            self.assertEqual(S.public(resolved/'reader/train.npz')['codes'].shape,(1,32))
            self.assertFalse((Path(td)/S.SITES[0]/'inputs/reader').exists())
            (root/'COMPLETE.json').write_text('{"changed":true}')
            with self.assertRaises(ValueError):S.bound_fixture(snapshot,cfg)
    def test_both_native_architectures_and_copied_observations(self):
        import torch
        torch.set_num_threads(1);torch.manual_seed(120921)
        codes=np.arange(64).reshape(2,32)%32;novel=np.ones_like(codes,dtype=bool);novel[:,::3]=False
        tokens=np.full((2,33),32);positions=novel.cumsum(1)
        for i in range(2):tokens[i,1:1+novel[i].sum()]=codes[i,novel[i]]
        for kind in ('transformer','recurrent'):
            embedding=torch.nn.Embedding(33,32)
            encoder=(torch.nn.GRU(32,38,batch_first=True) if kind=='recurrent' else
                torch.nn.TransformerEncoderLayer(32,4,64,dropout=0,activation='gelu',batch_first=True))
            head=torch.nn.Linear(38 if kind=='recurrent' else 32,32)
            # No training: compare the port against native framework equations.
            a={}
            for name,module in [('embedding',embedding),('encoder',encoder),('head',head)]:
                module.eval();a.update({name+'.'+k:v.detach().numpy() for k,v in module.state_dict().items()})
            with torch.no_grad():
                x=embedding(torch.tensor(tokens))
                if kind=='recurrent':hidden,_=encoder(x)
                else:
                    p=torch.arange(33)[:,None]*torch.exp(torch.arange(0,32,2)*(-np.log(10000)/32))
                    positions_array=torch.zeros((33,32));positions_array[:,0::2]=torch.sin(p);positions_array[:,1::2]=torch.cos(p)
                    a['positions']=positions_array.numpy();hidden=encoder(x+positions_array,src_mask=torch.triu(torch.ones(33,33,dtype=torch.bool),1))
                hidden=hidden[torch.arange(2)[:,None],torch.tensor(positions)]
                probabilities=head(hidden).reshape(2,32,4,8).softmax(-1)
            h,p=N.reconstruct(a,codes,novel,kind)
            S.close(h,hidden.numpy(),2e-5);S.close(p,probabilities.numpy(),2e-6)
            if kind=='transformer':
                before,q=N.reconstruct(a,codes,novel,kind,'pre-final-normalization')
                S.close(N.final_normalize(a,before),h);S.close(q,p)
            altered=codes.copy();altered[~novel]=(altered[~novel]+1)%32
            S.close(N.reconstruct(a,altered,novel,kind)[0],h,0)
            with self.assertRaises(ValueError):N.reconstruct(a,codes.astype(float),novel,kind)
            with self.assertRaises(ValueError):N.reconstruct(a,codes,novel.astype(int),kind)
            with self.assertRaises(ValueError):N.reconstruct(a,codes+99,novel,kind)

    def test_world_reference_and_distinct_composition_types(self):
        laws=np.zeros((16,4,8));world=N.law(-120921)
        for r in N.enumerate_world(world):
            a=r['final'];laws[r['maker_index'],r['context_index'],a[0]+2*a[1]+4*a[2]]+=r['probability']*64
        calculated=np.array([[N.endpoint_law(world,m,c) for c in N.CONTEXTS] for m in N.MAKERS])
        S.close(laws,calculated,1e-12);self.assertTrue(S.composition_controls()['passed'])
        # Null head cannot turn a coordinate swap into forecast selectivity.
        a={'head.weight':np.zeros((32,2)),'head.bias':np.zeros(32)}
        h=np.array([[0.,0.]]);changed=S.swap(h,np.ones((1,2)),np.array([1.,0.]))
        S.close(N.decode(a,h),N.decode(a,changed),0)

    def test_production_ruler_and_saved_policy_damage(self):
        known=np.zeros(S.SHAPE);known[...,S.ARTIFACTS.index((1,1,0))]=1
        pi=np.zeros(S.SHAPE[:-2],dtype=int);success,values,_=S.policy_values(known,pi)
        S.close(success,np.ones(2));S.check_optimal(known,pi,values)
        inert=np.broadcast_to(np.eye(8)[None,None,:,None,None,:],S.SHAPE)
        S.close(S.policy_values(inert,pi)[0],S.SUCCESS[list(S.INITIAL)])
        broken=values.copy();broken[0,0,0,0]+=.1
        with self.assertRaises(ValueError):S.check_optimal(known,pi,broken)
        self.assertTrue(np.isinf(N.loss(np.array([[1.,0.]]),np.array([[0.,1.]])))[0])

    def test_source_escape_corruption_and_evaluator_leak_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'source';p.write_text('original')
            sha=filehash(p);S.checked(p,sha,root);p.write_text('modified')
            with self.assertRaises(ValueError):S.checked(p,sha,root)
            with self.assertRaises(ValueError):S.checked(p,filehash(p),root/'nested')
            np.savez(root/'leak.npz',codes=np.zeros((1,32),dtype=int),novel=np.ones((1,32),bool),maker=np.zeros(1))
            with self.assertRaises(ValueError):S.public(root/'leak.npz')


if __name__=='__main__':unittest.main()
