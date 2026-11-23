"""Shared captions for Week 7 laughter figures, including the ICSI sampling limit."""
from pathlib import Path
import textwrap

from .week7_icsi_recordings import LIMIT


def save_figure(figure, path, *, card, corpus, caption):
    if card not in ('LGH1','LGH2') or not caption.strip():
        raise ValueError('A laughter card and figure caption are required')
    if corpus=='ICSI':
        caption=caption.rstrip()+' ICSI duration is annotated utterance length. '+LIMIT
    # Reserve space in the figure itself so the scope stays visible when exported.
    width,height=figure.get_size_inches()
    lines=textwrap.wrap(caption,width=max(30,int(width*12)))
    bottom=min(.5,(.38+.17*len(lines))/height)
    figure.tight_layout(rect=(0,bottom,1,1))
    figure.text(.025,.025,'\n'.join(lines),va='bottom',fontsize=9)
    figure.savefig(Path(path),dpi=150,bbox_inches='tight')
