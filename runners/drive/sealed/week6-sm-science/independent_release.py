"""Table-specific release decisions on authenticated person memberships (amendment BM).

Only the final numeric rows are passed to the standard writer. Memberships,
failed cell sizes and values of withheld rows are process-local.
"""
from collections import Counter
from dataclasses import dataclass
from week6_sealed_support_v1 import MIN_N, SealedFailure, write_tables

KEPT, MISSING, BELOW, COMPLEMENT = range(1,5)


@dataclass(frozen=True)
class Entry:
    fields: dict
    people: frozenset
    linked_groups: tuple = ()


def safe(memberships):
    groups=tuple(set(group) for group in memberships)
    counts=Counter(tuple(p in group for group in groups) for p in set().union(*groups))
    return all(size>=MIN_N for size in counts.values())


def decide(tables,file_people,known_file_groups=()):
    """Select largest safe memberships first across the complete disclosure surface."""
    universe=frozenset(file_people)
    if len(universe)<MIN_N:raise SealedFailure(12,'Source file below people floor')
    if len({name for _,name,_ in tables})!=len(tables):raise SealedFailure(14,'Repeated table name')
    known=tuple(frozenset(g) for g in known_file_groups)
    domain=universe.union(*known)
    # Source totals may already be public. If their joint partition contains
    # a small cell, release numerics only on an already disclosed roster.
    protected=list(dict.fromkeys((universe,*known)))
    original_safe=safe(protected)
    candidates=[];reasons={};kept={}
    for table_id,name,rows in tables:
        kept[name]=[]
        if rows is None:reasons[name]=MISSING;continue
        if not rows or any(len(row.people)<MIN_N or any(len(g)<MIN_N for g in row.linked_groups) for row in rows):
            reasons[name]=BELOW;continue
        reasons[name]=KEPT
        for i,row in enumerate(rows):
            if row.fields.get('n')!=len(row.people) or not set(row.people)<=domain:
                raise SealedFailure(14,'Contributing membership mismatch')
            if any(not set(g)<=domain for g in row.linked_groups):
                raise SealedFailure(14,'Linked disclosure outside source')
            candidates.append((-len(row.people),table_id,i,name,row))
    trimmed=set()
    for _,_,i,name,row in sorted(candidates,key=lambda v:v[:3]):
        additions=[row.people,*row.linked_groups]
        same_roster=all(g in protected for g in additions)
        if same_roster or (original_safe and safe([*protected,*additions])):
            kept[name].append((i,row))
            for g in additions:
                if g not in protected:protected.append(g)
        else:trimmed.add(name)
    result={};status=[];final=[universe]
    for table_id,name,_ in tables:
        rows=sorted(kept[name],key=lambda v:v[0])
        if name in trimmed and len(rows)<2:reasons[name]=COMPLEMENT;rows=[]
        if rows:
            result[name]=[dict(row.fields) for _,row in rows]
            for _,row in rows:final.extend([row.people,*row.linked_groups])
        status.append(dict(table=table_id,kept=int(bool(rows)),reason=reasons[name],n=len(universe)))
    if original_safe and not safe([*final,*known]):raise SealedFailure(14,'Joint release membership check failed')
    if not original_safe and any(g not in (universe,*known) for g in final):raise SealedFailure(14,'New unsafe membership')
    return result,status


def write_job(out,tables,file_people,selected_ids):
    # Each of the three jobs obtains the identical joint selection before
    # subsetting its output. Combining their files must preserve the same floor.
    result,status=decide(tables,file_people)
    names={name for ix,name,_ in tables if ix in selected_ids}
    payload={name:rows for name,rows in result.items() if name in names}
    payload['table_status']=[s for s in status if s['table'] in selected_ids]
    if not payload['table_status']:raise SealedFailure(14,'Unregistered job selection')
    return write_tables(out,payload)

