"""Bounded tokenizer-only checks; native corpus feasibility is owner-dispatched."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import timing_p7_tokenize_pilot as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p7_batched import prepare


class Tokenizer:
    eos_token_id = 0
    def __call__(self, text, **kwargs):
        if isinstance(text, list):
            items=[self(x, **kwargs) for x in text]
            return {k:[row[k] for row in items] for k in ("input_ids","offset_mapping")}
        ids, offsets, pos = [], [], 0
        while pos < len(text):
            width=2 if text[pos:pos+2]=="ab" else 1
            ids.append(1+sum(ord(c) for c in text[pos:pos+width]));offsets.append((pos,pos+width));pos+=width
        return dict(input_ids=ids,offset_mapping=offsets)


def test_exact_batch_identity_unicode_boundary_revisions_and_crop():
    rows=[dict(prefix=p,target=t) for p,t in [("a","b"),("abc ","😀"),("edited ","z"),("x"*1100,"a"),("ab "*500,"b")]]
    rows=rows*20  # crosses the bounded batch boundary
    batched,_=card.prepare_many(Tokenizer(),rows)
    assert batched==[prepare(Tokenizer(),r["prefix"],r["target"]) for r in rows]
    assert batched[0]["positions"]==[1]  # target shares a native token with prefix
    assert batched[3]["dropped"]>0
    with pytest.raises(ValueError,match="missing or exceeds"):
        card.prepare_many(Tokenizer(),[dict(prefix="",target="z"*1100)])
    with pytest.raises(ValueError,match="exact tokenizer"):
        card.prepare_many(Tokenizer(),[],dict(card.CONFIG,threads=True))


def test_native_fast_bytelevel_batch_offsets_are_identical():
    os.environ["RAYON_NUM_THREADS"]="2"
    os.environ["TOKENIZERS_PARALLELISM"]="true"
    from tokenizers import Tokenizer as NativeTokenizer, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast
    backend=NativeTokenizer(models.BPE(unk_token="<unk>"))
    backend.pre_tokenizer=pre_tokenizers.ByteLevel(add_prefix_space=False)
    backend.train_from_iterator(["ab abc editing revised 😀\n", "word "*30], trainers.BpeTrainer(vocab_size=280,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),special_tokens=["<unk>","<eos>"]))
    tokenizer=PreTrainedTokenizerFast(tokenizer_object=backend,unk_token="<unk>",eos_token="<eos>")
    rows=[dict(prefix=p,target=t) for p,t in [("a","b"),("abc ","😀"),("edited\n","b"),("xy "*1400,"a")]]
    batched,encoded=card.prepare_many(tokenizer,rows)
    assert batched==[prepare(tokenizer,r["prefix"],r["target"]) for r in rows]
    for r,e in zip(rows,encoded):
        native=tokenizer(r["prefix"]+r["target"],add_special_tokens=False,return_offsets_mapping=True)
        assert e=={k:native[k] for k in e}


def fixture_inputs(root):
    root=Path(root); units=[];saved=[]
    for i in range(12):
        rows=[dict(index=j,is_word=True,prefix="ab "*(i*12+j),target="😀" if j%2 else "b") for j in range(8)]
        unit=dict(domain="typed",identity=str(i),source=rows)
        prepared=[prepare(Tokenizer(),r["prefix"],r["target"]) for r in rows]
        census=dict(domain="typed",identity=str(i),locations_sha256=card.original.old.digest(rows),
            native_sha256=card.original.old.digest(prepared),**card.original.work(prepared))
        units.append(unit);saved.append(dict(census=census,seconds=1.))
    path=root/"source.json";write(path,dict(units=units,saved=saved))
    return dict(fixture=str(path.resolve()),sha256=filehash(path))


def fixture_reference(inputs, config):
    if config!=card.CONFIG or filehash(inputs["fixture"])!=inputs["sha256"]:raise ValueError("fixture source/config changed")
    data=read(inputs["fixture"]);saved=dict(enumerate(data["saved"]))
    binding=dict(source_sha256=inputs["sha256"],selection=card.select_units(list(saved.items())),total_units=100,
                 saved_units=12,charged_prior_seconds=12.,scalar_census_projection_seconds=3800.,config=config)
    return binding,data["units"],saved,inputs,{},None,{}


def fixture_locations(unit,*unused):return unit["source"]


def configure(monkeypatch):
    monkeypatch.setattr(card,"reference",fixture_reference)
    monkeypatch.setattr(card,"tokenizer_only",lambda _:Tokenizer())
    monkeypatch.setattr(card.original.old,"locations",fixture_locations)


def test_serialized_handler_fresh_process_yield_resume_and_forgery(tmp_path,monkeypatch):
    configure(monkeypatch);inputs=fixture_inputs(tmp_path);output=tmp_path/"output"
    write(output/"YIELD_REQUEST.json",{})
    assert card.execute(output,inputs,card.CONFIG)["status"]=="yielded"
    checkpoint=next(p for p in (output/"units").glob("*.json") if not p.name.endswith(".receipt.json"));original_bytes=checkpoint.read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert result["sampled_units"]==8 and result["exact_scalar_native_and_work_parity"]
    assert result["model_forwards_executed"]==0 and not result["main_admitted"]
    assert checkpoint.read_bytes()==original_bytes
    args=tmp_path/"args.json";write(args,dict(output=str(output),inputs=inputs))
    code="import json,sys;from pathlib import Path;from tests.test_drive_cards_timing_p7_tokenize_pilot import fixture_reference,fixture_locations,Tokenizer;from runners.drive.cards import timing_p7_tokenize_pilot as c;c.reference=fixture_reference;c.tokenizer_only=lambda _:Tokenizer();c.original.old.locations=fixture_locations;x=json.load(open(sys.argv[1]));print(json.dumps(c.verify(Path(x['output']),x['inputs'],c.CONFIG)))"
    child=subprocess.run([sys.executable,"-c",code,str(args)],capture_output=True,text=True,timeout=60,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=="nt" else 0)
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)["primary"]==result
    forged=read(output/"RECORDS.json");forged[0]["census"]["forward_tokens"]+=1
    (output/"RECORDS.json").write_text(json.dumps(forged),encoding="utf-8")
    with pytest.raises(ValueError,match="fresh source reconstruction"):
        card.verify(output,inputs,card.CONFIG)


def test_full_offset_corruption_refuses_even_when_prepared_ids_match(tmp_path,monkeypatch):
    configure(monkeypatch);inputs=fixture_inputs(tmp_path)
    _,units,saved,source,roster,p6,model=fixture_reference(inputs,card.CONFIG)
    class Corrupt(Tokenizer):
        def __call__(self,text,**kwargs):
            out=super().__call__(text,**kwargs)
            if isinstance(text,list):
                offsets=out["offset_mapping"][0]
                # Corrupt a non-target prefix offset without changing any IDs.
                if len(offsets)>1:offsets[0]=(0,0)
            return out
    with pytest.raises(ValueError,match="full native IDs/offsets"):
        card.compare_unit(1,units[1],saved[1],source,roster,p6,Corrupt())


def test_forecast_includes_replay_and_prior_cost_and_can_hold():
    binding=dict(total_units=1549,saved_units=156,charged_prior_seconds=208.,scalar_census_projection_seconds=3819.)
    timing=dict(source_seconds=9.,scalar_prepare_seconds=1.,batched_prepare_seconds=.01,
                cache_work_and_digest_seconds=0.,identity_validation_seconds=.1)
    rows=[dict(census=dict(domain="typed"),timings=timing)]*8
    result=card.summarize(rows,binding,20.)
    assert result["worst_observed_whole_unit_batched_over_scalar_ratio"]==pytest.approx(.901)
    assert not result["conditionally_fits_census_cap"]  # 100x tokenizer speed cannot fix replay cost
    assert result["projected_cumulative_census_seconds"]>2700
    timing["source_seconds"]=.1
    assert card.summarize(rows,binding,20.)["conditionally_fits_census_cap"]
    timing["scalar_prepare_seconds"]=float("nan")
    with pytest.raises(ValueError,match="invalid tokenizer comparison timing"):
        card.summarize(rows,binding,20.)
