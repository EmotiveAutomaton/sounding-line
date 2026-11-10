"""Real pinned MiniLM on constructed-only WC2 strings through the successor."""
from pathlib import Path
import numpy as np
from . import week5_bk_outcome_features as card
from .timing_closure_measure import model_identity
from .timing_census import read
from .timing_p6 import write_equal,gzread


def data():
    chosen='The solution preserves the goal while changing the method.'
    other='This alternative changes the purpose and removes the constraint.'
    text=' '.join(['word']*300)
    return dict(data=dict(events=[dict(id='constructed',writer='constructed-a',session='constructed-session',prompt='constructed-prompt',timestamp=0,
        kind='deleted',span=dict(text=chosen,unchosen=[other]),window=dict(text=text),
        context=[dict(text='A neutral continuation addresses the common topic.',writer='constructed-b',prompt='constructed-prompt')],
        sensitivity=None,sensitivity_context=[],kept_reference=None)]))


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'content_complete','model_manifest'} or config:raise ValueError('Pinned local model only; no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source=root/'CONSTRUCTED.json';write_equal(source,data())
    model=model_identity(inputs);encoder=card.Encoder(inputs,2);previous=card.ConstructedEncoder;card.ConstructedEncoder=lambda:encoder
    try:(card.verify if verifying else card.execute)(root/'features',dict(fixture=str(source)),dict(card='WC2',mode='constructed',max_wall_seconds=1200))
    finally:card.ConstructedEncoder=previous
    bank=gzread(root/'features/VECTORS.json.gz');scopes=gzread(root/'features/SCOPES.json.gz')
    # Independent tensor arithmetic on the same documented visible native IDs.
    for text,vector in bank.items():
        scope=scopes[card.text_id(text)];ids=scope['native_ids'];torch=encoder.torch
        with torch.inference_mode():
            hidden=encoder.model(input_ids=torch.tensor([ids]),attention_mask=torch.ones((1,len(ids)),dtype=torch.int64)).last_hidden_state[0]
            v=(hidden.sum(0)/len(ids)).numpy().astype(np.float32);v=v/np.linalg.norm(v)
        if not np.array_equal(v,np.asarray(vector,dtype=np.float32)) or len(v)!=384 or not np.isclose(np.linalg.norm(v),1):raise ValueError('Independent frozen mean-pooling arithmetic differs')
        if encoder.vector(text)[0]!=vector:raise ValueError('Actual native encoder repeat differs')
    if not any(scope['truncated'] and scope['used_tokens']==254 for scope in scopes.values()):raise ValueError('Actual prefix cap not exercised')
    if model_identity(inputs)!=model:raise ValueError('Model source changed')
    receipt=dict(fixture_only=True,actual_frozen_cpu_float32_encoder=True,constructed_texts=len(bank),
                 independent_tensor_pooling_exact=True,real_254_token_truncation=True,all_384_dimension_unit_vectors=True,
                 complete_successor_execute_and_replay=True,model_revision=model.get('revision'))
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Native reader fixture differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    inputs=dict(content_complete='results/phase_2_4_stage_15/raw/drive-content-features-v2/COMPLETE.json',model_manifest='results/phase_2_4_stage_15/raw/drive-content-features-v2/MODEL.json')
    print(json.dumps((verify if a.verify else execute)(a.output,inputs,{})))
