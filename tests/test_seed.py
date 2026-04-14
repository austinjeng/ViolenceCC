"""TRN-03: deterministic seed utility tests."""
import inspect
import random
import numpy as np
import torch

from src.utils.seed import set_deterministic, seed_worker, make_generator


def test_set_deterministic_sets_torch_rng():
    set_deterministic(42)
    a = torch.rand(5)
    set_deterministic(42)
    b = torch.rand(5)
    assert torch.equal(a, b), f"torch RNG not reproducible: {a} vs {b}"


def test_set_deterministic_sets_numpy_rng():
    set_deterministic(42)
    a = np.random.rand(5)
    set_deterministic(42)
    b = np.random.rand(5)
    assert np.array_equal(a, b)


def test_set_deterministic_sets_python_rng():
    set_deterministic(42)
    a = random.random()
    set_deterministic(42)
    b = random.random()
    assert a == b


def test_set_deterministic_cudnn_flags():
    set_deterministic(42)
    assert torch.backends.cudnn.deterministic is True
    assert torch.backends.cudnn.benchmark is False


def test_seed_worker_is_module_level():
    # Windows spawn can pickle module-level funcs but not lambdas.
    assert inspect.getsourcefile(seed_worker).endswith("seed.py")
    assert seed_worker.__module__ == "src.utils.seed"


def test_make_generator_reproducible():
    g1 = make_generator(42)
    g2 = make_generator(42)
    a = torch.rand(5, generator=g1)
    b = torch.rand(5, generator=g2)
    assert torch.equal(a, b)
