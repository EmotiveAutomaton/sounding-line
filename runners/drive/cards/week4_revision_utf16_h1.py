"""Exact materialization for the separately frozen S2 source implementation.

DESIGN CHECK: LESSONS2-5. Same UTF-16 units, strict decoding and delta checks
as stage9.coauthor. Known invalid surrogate/bounds cases must still refuse.
Full source parity with the retained cost prefix gates corpus admission.
"""
from array import array
import sys
from runners.stage9.coauthor import units,delta_ops


def text_of(values):
    a=array('H',values)
    if a.itemsize!=2:raise RuntimeError('Unsupported unsigned-short width')
    if sys.byteorder!='little':a.byteswap()
    return a.tobytes().decode('utf-16-le')


def apply_delta(document,provenance,value,*,insertion_owner=None,watched_owner=None):
    if len(document)!=len(provenance):raise ValueError('provenance/document disagreement')
    out,owners,position,edited=[],[],0,False
    for op in delta_ops(value):
        if 'insert' in op:
            new=units(op['insert'])
            if watched_owner is not None and 0<position<len(document):
                edited|=provenance[position-1]==provenance[position]==watched_owner and bool(new)
            out.extend(new);owners.extend([insertion_owner]*len(new))
        else:
            action='retain' if 'retain' in op else 'delete';count=op[action]
            if type(count) is not int or count<0 or position+count>len(document):raise ValueError('invalid UTF-16 retain/delete boundary')
            if action=='retain':out.extend(document[position:position+count]);owners.extend(provenance[position:position+count])
            elif watched_owner is not None:edited|=watched_owner in provenance[position:position+count]
            position+=count
    out.extend(document[position:]);owners.extend(provenance[position:]);text_of(out)
    return out,owners,edited
