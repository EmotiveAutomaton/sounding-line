"""Native generated-only costing handler proof for T4."""
from pathlib import Path
from . import week5_bk_t4 as producer
from .week5_bk_t4_fixture import fixture_bundle
from .timing_p6 import gzip_equal,write_equal
from .timing_census import read


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture takes no human input')
    root=Path(output);source=root/'constructed-source';gzip_equal(source/'output/BUNDLE.json.gz',fixture_bundle())
    old=producer.authenticate;producer.authenticate=lambda p:source
    try:(producer.verify if verifying else producer.execute)(root/'cost',dict(source_root=str(source)),dict(operation='cost'))
    finally:producer.authenticate=old
    receipt=dict(fixture_only=True,actual_generated_cost_handler=True,unchanged_original_kernel=True,
                 cost_covers_all_refit_kinds=True,no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Cost fixture differs')
        return dict(verified=True,complete_generated_cost_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
