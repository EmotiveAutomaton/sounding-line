"""Finite corpus-cost admission. DESIGN CHECK: LESSONS 3-5; source, numerical
or resource failure refuses; complete support-only pilot permits sizing only.
"""
import argparse
from .suggestion_corpus_v3 import prepare,run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run'])
    (prepare if p.parse_args().action=='prepare' else run)('pilot')
