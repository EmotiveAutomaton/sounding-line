"""Memory-bounded computation of the unchanged masked causal training objective.

DESIGN CHECK: C05. Preserve every input/context token, supervised target, microbatch
and optimizer step. Compute the frozen vocabulary projection in small blocks of
supervised hidden states. Recompute those projections during backward so their
vocabulary-sized activations are not all retained. This changes numerical grouping,
not the per-microbatch target-mean cross-entropy objective. Requires separate actual
family loss/gradient and memory/timing checks before scientific use.
"""


def projected_loss(hidden, labels, head, chunk_tokens=64):
    import torch
    from torch.utils.checkpoint import checkpoint
    if type(chunk_tokens) is not int or not 1<=chunk_tokens<=256:
        raise ValueError('explicit bounded projection chunk required')
    if hidden.ndim!=3 or labels.shape!=hidden.shape[:2]:
        raise ValueError('full hidden state and target-mask shapes must agree')
    shifted=labels[...,1:].reshape(-1)
    selected=shifted!=-100
    count=int(selected.sum())
    if not count:
        raise ValueError('no supervised causal targets')
    states=hidden[...,:-1,:].reshape(-1,hidden.shape[-1])[selected]
    targets=shifted[selected]

    def block_loss(states,targets):
        logits=head(states).float()
        return torch.nn.functional.cross_entropy(logits,targets,reduction='sum')

    total=None
    for start in range(0,count,chunk_tokens):
        states_part=states[start:start+chunk_tokens]
        targets_part=targets[start:start+chunk_tokens]
        if torch.is_grad_enabled():
            value=checkpoint(block_loss,states_part,targets_part,use_reentrant=False)
        else:
            value=block_loss(states_part,targets_part)
        total=value if total is None else total+value
    return total/count


def causal_loss(model,batch,chunk_tokens=64):
    # Ordinary LoRA adapters are installed in the decoder modules themselves.
    # Prompt tuning, mixed adapters and other model architectures are unsupported.
    core=model.get_base_model() if hasattr(model,'get_base_model') else model
    if core.config.model_type not in ('qwen2','llama'):
        raise ValueError('streamed loss has not been validated for this architecture')
    if hasattr(model,'peft_config'):
        for config in model.peft_config.values():
            if str(config.peft_type) not in ('LORA','PeftType.LORA') or config.is_prompt_learning:
                raise ValueError('streamed loss requires ordinary LoRA')
    if set(batch)!={'input_ids','attention_mask','labels'}:
        raise ValueError('unexpected training input or assistance')
    output=core.model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],use_cache=False)
    return projected_loss(output.last_hidden_state,batch['labels'],core.lm_head,chunk_tokens)
