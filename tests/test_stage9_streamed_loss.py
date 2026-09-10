import copy

import pytest
import torch

from runners.stage9.streamed_loss import projected_loss,causal_loss


def test_masked_projection_matches_full_loss_and_gradients():
    torch.manual_seed(92341)
    hidden=torch.randn(4,39,23,requires_grad=True)
    reference_hidden=hidden.detach().clone().requires_grad_()
    head=torch.nn.Linear(23,131,bias=False)
    reference_head=copy.deepcopy(head)
    labels=torch.randint(0,131,(4,39));labels[:,9:23]=-100;labels[3,29:]=-100
    labels[:,0]=-100
    expected=torch.nn.functional.cross_entropy(reference_head(reference_hidden[:,:-1]).float().reshape(-1,131),
                                                labels[:,1:].reshape(-1),ignore_index=-100)
    actual=projected_loss(hidden,labels,head,7)
    expected.backward();actual.backward()
    torch.testing.assert_close(actual,expected,atol=1e-6,rtol=1e-6)
    torch.testing.assert_close(hidden.grad,reference_hidden.grad,atol=1e-7,rtol=1e-5)
    torch.testing.assert_close(head.weight.grad,reference_head.weight.grad,atol=1e-7,rtol=1e-5)
    assert torch.count_nonzero(hidden.grad[:,9:22])==0


@pytest.mark.parametrize('family',['qwen2','llama'])
def test_actual_decoder_lora_matches_full_forward(family):
    from transformers import Qwen2Config,Qwen2ForCausalLM,LlamaConfig,LlamaForCausalLM
    from peft import LoraConfig,get_peft_model
    torch.manual_seed(93401)
    config_class,model_class=(Qwen2Config,Qwen2ForCausalLM) if family=='qwen2' else (LlamaConfig,LlamaForCausalLM)
    config=config_class(vocab_size=79,hidden_size=32,intermediate_size=48,num_hidden_layers=2,
                        num_attention_heads=4,num_key_value_heads=2,max_position_embeddings=128)
    model=get_peft_model(model_class(config),LoraConfig(r=2,lora_alpha=4,lora_dropout=.05,
                                                      target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
    reference=copy.deepcopy(model)
    model.train();reference.train()
    ids=torch.randint(0,79,(2,17));labels=ids.clone();labels[:,:5]=-100
    batch={'input_ids':ids,'attention_mask':torch.ones_like(ids),'labels':labels}
    rng=torch.get_rng_state()
    expected=reference(**batch).loss;expected.backward()
    torch.set_rng_state(rng)
    actual=causal_loss(model,batch,chunk_tokens=5);actual.backward()
    torch.testing.assert_close(actual,expected,atol=1e-6,rtol=1e-6)
    for (name,p),(other,q) in zip(model.named_parameters(),reference.named_parameters()):
        assert name==other
        if p.requires_grad:torch.testing.assert_close(p.grad,q.grad,atol=2e-6,rtol=1e-4)


def test_empty_targets_are_not_zero_loss():
    with pytest.raises(ValueError,match='no supervised'):
        projected_loss(torch.randn(1,3,2),torch.full((1,3),-100),torch.nn.Linear(2,5))
