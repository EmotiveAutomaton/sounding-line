"""Retain unlocated hypotheses when filtering the private contribution viewer.

The original renderer, reviewed viewer, forecasts and source pins remain intact.
This versioned presentation repair makes no inference calls and changes no scores.
"""
import argparse
from pathlib import Path
from runners.stage11.core import PRIVATE
from runners.stage11_review import build_review


def build(root=PRIVATE):
    build_review(root)
    content = (root/'contribution-map-reviewed.html').read_text(encoding='utf-8')
    changes = [
        ("if(selected&&e.quote&&!selected.includes(e.quote))return;",
         "if(selected&&e.quote&&c.artifact.includes(e.quote)&&!selected.includes(e.quote))return;"),
        ("e.quote?'Text: “'+e.quote+'”':'No located supporting passage.'",
         "e.quote?(c.artifact.includes(e.quote)?'Text: “':'Reference not located in endpoint: “')+e.quote+'”':'No located supporting passage.'"),
    ]
    for old,new in changes:
        if content.count(old)!=1:
            raise ValueError('original viewer no longer matches the bounded repair')
        content=content.replace(old,new)
    path=root/'contribution-map-reviewed-v2.html'
    if path.exists() and path.read_text(encoding='utf-8')!=content:
        raise ValueError('versioned viewer changed')
    path.write_text(content,encoding='utf-8',newline='\n')
    return dict(path=str(path),scientific_changes=False,
                repair='Unlocated reference hypotheses remain visible after passage selection.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=PRIVATE)
    print(build(parser.parse_args().root))
