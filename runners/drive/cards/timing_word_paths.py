"""Bounded native byte-token path diagnostics, never scientific word scores.

READ: Pimentel/Meister2024 sections4.1-4.3 and5.1-5.4. Counting paths does
not prove compatible word-event probabilities. This preserves all casefold
aliases in the count and reports bounded enumeration incompleteness explicitly.
No canonical path, omitted alias, whitespace convention or <unk> mapping can
silently become a replacement scientific event.
"""
from __future__ import annotations
from functools import lru_cache
import sys

from .timing_text import WORD

EOS=50256


def byte_vocabulary(vocabulary,eos=EOS):
    """Invert GPT-2's reversible byte alphabet, keeping special EOS separate."""
    source=list(range(ord('!'),ord('~')+1))+list(range(0xa1,0xad))+list(range(0xae,0x100))
    represented=source.copy();extra=0
    for byte in range(256):
        if byte not in source:source.append(byte);represented.append(256+extra);extra+=1
    inverse={chr(code):byte for byte,code in zip(source,represented)}
    pieces={}
    for token,index in vocabulary.items():
        if type(index) is not int or index in pieces:raise ValueError('invalid native vocabulary IDs')
        if index==eos:continue
        try:piece=bytes(inverse[char] for char in token)
        except KeyError as exc:raise ValueError('native token outside byte alphabet') from exc
        if not piece:raise ValueError('empty native byte token')
        pieces[index]=piece
    if set(pieces)|{eos}!=set(range(len(vocabulary))):raise ValueError('native vocabulary coverage differs')
    return pieces


def inverse_casefold():
    """Complete current-Python Unicode alphanumeric inverse, plus apostrophes.

    This does not lowercase contexts. Multi-codepoint folds (e.g. sharp-s and
    dotted-I) remain explicit; the folded target need not itself match WORD.
    """
    mapping={}
    for code in range(sys.maxunicode+1):
        char=chr(code)
        if char.isalnum() or char in ("'",'\u2019'):
            mapping.setdefault(char.casefold(),[]).append(char)
    return mapping


def casefold_aliases(folded,inverse,limit=256):
    if not isinstance(folded,str) or not folded or folded.casefold()!=folded or type(limit) is not int or limit<1:
        raise ValueError('invalid folded target or alias bound')
    longest=max(map(len,inverse),default=0)

    def options(position,has_letter,needs_letter):
        for size in range(1,min(longest,len(folded)-position)+1):
            for char in inverse.get(folded[position:position+size],[]):
                quote=char in ("'",'\u2019')
                if quote and (not has_letter or needs_letter):continue
                yield char,position+size,has_letter or not quote,quote

    @lru_cache(None)
    def count(position,has_letter,needs_letter):
        if position==len(folded):return int(has_letter and not needs_letter)
        return sum(count(end,has,needs) for _,end,has,needs in options(position,has_letter,needs_letter))

    result=[]
    def visit(position,text,has_letter,needs_letter):
        if len(result)>=limit:return
        if position==len(folded):
            if has_letter and not needs_letter:
                if not WORD.fullmatch(text) or text.casefold()!=folded:raise ValueError('casefold alias identity failed')
                result.append(text)
            return
        for char,end,has,needs in options(position,has_letter,needs_letter):
            if count(end,has,needs):visit(end,text+char,has,needs)
            if len(result)>=limit:return
    total=count(0,False,False);visit(0,'',False,False)
    return dict(aliases=result,total_aliases=total,enumeration_complete=len(result)==total,
        normalization='Exact Unicode casefold of one original TOKEN word; no context normalization')


class BytePaths:
    def __init__(self,pieces):
        self.pieces=pieces;self.trie={}
        for index,piece in sorted(pieces.items()):
            if not piece:raise ValueError('empty byte token creates unbounded segmentations')
            node=self.trie
            for byte in piece:node=node.setdefault(byte,{})
            node.setdefault(None,[]).append(index)

    def edges(self,data,position):
        node=self.trie
        for end in range(position,len(data)):
            if data[end] not in node:return
            node=node[data[end]]
            for index in node.get(None,[]):yield end+1,index

    def describe(self,data,limit=16):
        if not isinstance(data,bytes) or not data or type(limit) is not int or limit<1:raise ValueError('invalid byte target/bound')
        @lru_cache(None)
        def count(position):
            return 1 if position==len(data) else sum(count(end) for end,_ in self.edges(data,position))
        paths=[]
        def visit(position,path):
            if len(paths)>=limit:return
            if position==len(data):paths.append(path);return
            for end,index in self.edges(data,position):
                if count(end):visit(end,path+[index])
                if len(paths)>=limit:return
        total=count(0);visit(0,[])
        if any(b''.join(self.pieces[i] for i in path)!=data for path in paths):raise ValueError('native byte path identity failed')
        return dict(path_count=total,paths=paths,enumeration_complete=len(paths)==total,byte_length=len(data))


def describe_word(surface,paths,inverse,alias_limit=256):
    if not WORD.fullmatch(surface):raise ValueError('not one original TOKEN word')
    aliases=casefold_aliases(surface.casefold(),inverse,alias_limit)
    rows=[]
    for alias in aliases['aliases']:
        row=paths.describe(alias.encode('utf8'),limit=1)
        rows.append(dict(surface=alias,path_count=row['path_count'],bytes=row['byte_length']))
    return dict(surface=surface,folded=surface.casefold(),casefold_aliases=aliases['total_aliases'],
        enumerated_aliases=len(rows),alias_enumeration_complete=aliases['enumeration_complete'],
        enumerated_native_paths=sum(r['path_count'] for r in rows),
        native_path_count_is_exact=aliases['enumeration_complete'],aliases=rows,
        scientific_event_admitted=False,
        uncovered='Counts exact byte spellings only. Boundary-crossing tokens, skipped separators, context boundary normalization and writer-specific unknown events require separate compatible-event review.')


def native_path_cost(model,torch,prefix_ids,token_paths):
    """Measure exact token-path work only; does not label it a word probability.

    Prefix and position IDs are fixed. Paths that overflow are explicitly
    refused rather than shifting/cropping context to make them fit.
    """
    import time
    values=[];started=time.monotonic()
    for path in token_paths:
        ids=list(prefix_ids)+list(path)
        if not prefix_ids or not path or len(ids)>1024:raise ValueError('native diagnostic context overflow')
        tensor=torch.tensor([ids],dtype=torch.long,device='cpu')
        with torch.inference_mode():
            logits=model(input_ids=tensor,use_cache=False).logits[0]
            losses=torch.nn.functional.cross_entropy(logits[len(prefix_ids)-1:-1].float(),tensor[0,len(prefix_ids):],reduction='none')
        if not torch.isfinite(losses).all() or bool((losses<0).any()):raise ValueError('invalid native path loss')
        values.append(dict(tokens=list(path),native_token_nll=losses.tolist()))
    return dict(paths=values,seconds=time.monotonic()-started,forwards=len(values),
        forward_tokens=sum(len(prefix_ids)+len(p) for p in token_paths),scientific_word_scores=False)
