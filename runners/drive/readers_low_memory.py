"""Float32 Pythia scoring with no retained KV cache and bounded vocabulary logits.

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: nonfinite, misaligned,
changed-precision or changed-residency outputs refuse. ALTERNATIVE: complete
token losses agree with ordinary direct scoring and retained cached scoring.
No context truncation, quantization, CPU offload or tolerance relaxation.
"""
import math
from .readers import pack


def token_losses(model, packed, torch, *, block_tokens=32):
    if not packed['eligible'] or block_tokens < 1:
        raise ValueError('eligible complete item and positive block required')
    if model.config.model_type != 'gpt_neox' or model.training:
        raise ValueError('evaluation-mode GPTNeoX required')
    params = list(model.parameters())
    device = params[0].device
    if any(p.dtype != torch.float32 or p.device != device for p in params):
        raise ValueError('uniform float32 model residency required')
    ids = packed['prefix'] + packed['target']
    start = len(packed['prefix']) - 1
    values = []
    with torch.inference_mode():
        # This is the installed GPTNeoXForCausalLM forward, with its vocabulary
        # projection split over target positions. No hidden state is shortened.
        out = model.gpt_neox(input_ids=torch.tensor([ids[:-1]], device=device),
                             use_cache=False, return_dict=True)
        if out.past_key_values is not None:
            raise ValueError('unexpected retained KV cache')
        hidden = out.last_hidden_state[0]
        head = model.get_output_embeddings()
        for offset in range(0, len(packed['target']), block_tokens):
            target = packed['target'][offset:offset + block_tokens]
            logits = head(hidden[start + offset:start + offset + len(target)])
            labels = torch.tensor(target, device=device)
            loss = torch.nn.functional.cross_entropy(logits, labels, reduction='none')
            if not torch.isfinite(loss).all():
                raise ValueError('nonfinite teacher-forced loss')
            values.extend(loss.cpu().tolist())
            del logits, labels, loss
    if len(values) != len(packed['target']):
        raise ValueError('incomplete target loss vector')
    return values


def score_menu(model, tok, context, targets, torch, *, block_tokens=32, check=None):
    if any(p.device.type != 'cuda' for p in model.parameters()):
        raise ValueError('reader not fully resident on GPU')
    result = []
    for target in targets:
        if check:
            check()
        x = pack(tok, context, target)
        if not x['eligible']:
            result.append(x)
            continue
        values = token_losses(model, x, torch, block_tokens=block_tokens)
        if check:
            check()
        total = float(sum(values))
        if not math.isfinite(total):
            raise ValueError('nonfinite total loss')
        result.append(dict(eligible=True, native_token_ids=x['target'], native_token_nll=values,
                           codepoint_offsets=x['offsets'], prefix_tokens=len(x['prefix']),
                           target_tokens=len(x['target']), total_nll=total,
                           mean_token_nll=total / len(values), nll_per_utf8_byte=total / x['utf8_bytes'],
                           utf8_bytes=x['utf8_bytes']))
    return result
