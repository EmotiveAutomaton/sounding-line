"""Single prospective literal-confidence interface correction.

DESIGN CHECK: LESSONS 3-5. NULL: malformed/capped answers remain invalid and
failed observed-fact controls block reserved evaluation. ALTERNATIVE: an explicit
JSON-only system instruction admits the same reader without changing its scores,
candidate order, 96-token budget, evidence, or whole-response parser.
"""
import json
import time
from . import readouts as original
from .scoring import probabilities


class Reader(original.Reader):
    def __init__(self):
        super().__init__()
        self.identity['interface']='literal-system-json-v2'

    def elicited(self,prompt,n):
        messages=[dict(role='system',content='You estimate probabilities from the supplied evidence. Respond with only the requested JSON array. Do not write code, instructions, markdown, or an explanation.'),
                  dict(role='user',content=prompt+f'\nReturn only a JSON array of {n} probabilities in the stated order, summing to one.')]
        text=self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        encoded=self.tokenizer(text,return_tensors='pt')
        if encoded['input_ids'].shape[1]>512:raise ValueError('elicited native-token input cap')
        start=time.perf_counter()
        with self.torch.inference_mode():
            out=self.model.generate(**encoded,max_new_tokens=96,do_sample=False,pad_token_id=self.tokenizer.eos_token_id)
        tail=out[0,encoded['input_ids'].shape[1]:];raw=self.tokenizer.decode(tail,skip_special_tokens=True)
        try:value=json.loads(raw);p=probabilities(value,n) if len(tail)<96 else None
        except (ValueError,TypeError):p=None
        return p,dict(raw=raw,generated_tokens=len(tail),input_tokens=int(encoded['input_ids'].shape[1]),elapsed_seconds=time.perf_counter()-start,capped=len(tail)>=96,interface='literal-system-json-v2')


def admission(out):
    original.Reader=Reader
    return original.admission(out)


def run(rows,out,tick):
    original.Reader=Reader
    return original.run(rows,out,tick)


summarize=original.summarize
