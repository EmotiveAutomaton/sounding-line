"""Checkpointed P1 suggestions. DESIGN CHECK: LESSONS 3-5; missing/full-source
or resource failure refuses; complete fixed roster permits later card analysis.
"""
import argparse
from .suggestion_corpus_v3 import prepare,run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run'])
    (prepare if p.parse_args().action=='prepare' else run)('main')
