"""MOD-03/04/05/06 shared head (D-05, D-06)."""
import torch
import torch.nn as nn

from src.models.mil_head import MILHead


def test_mil_head_output_shape_3d():
    head = MILHead(input_dim=256)
    out = head(torch.randn(2, 32, 256))
    assert out.shape == (2, 32, 1)


def test_mil_head_output_shape_2d():
    head = MILHead(input_dim=256)
    out = head(torch.randn(8, 256))
    assert out.shape == (8, 1)


def test_mil_head_output_sigmoid_range():
    head = MILHead(input_dim=256)
    out = head(torch.randn(4, 32, 256))
    assert (out >= 0).all() and (out <= 1).all()


def test_mil_head_layer_widths_d06():
    """D-06: hidden 128 -> 32; exactly 3 Linears."""
    head = MILHead(input_dim=512)
    linears = [m for m in head.mlp if isinstance(m, nn.Linear)]
    assert len(linears) == 3
    assert linears[0].in_features == 512 and linears[0].out_features == 128
    assert linears[1].in_features == 128 and linears[1].out_features == 32
    assert linears[2].in_features == 32 and linears[2].out_features == 1


def test_mil_head_dropout_d05():
    """D-05: Dropout(0.3) after each ReLU."""
    head = MILHead(input_dim=256, dropout=0.3)
    dropouts = [m for m in head.mlp if isinstance(m, nn.Dropout)]
    assert len(dropouts) == 2
    assert all(d.p == 0.3 for d in dropouts)


def test_mil_head_final_activation_sigmoid():
    head = MILHead(input_dim=256)
    assert isinstance(head.mlp[-1], nn.Sigmoid)
