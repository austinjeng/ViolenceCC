import importlib.util
import pytest
import pathlib

PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")


# ---------------------------------------------------------------------------
# Environment-conditional test collection.
# test_ctrgcn_smoke.py imports mmcv/pyskl which only exist in the vcc-ctrgcn
# conda env. In vcc-main (the Phase 3 training env), those modules are absent
# and the test module fails at import time. Skip collecting it when mmcv is
# unavailable so `pytest --collect-only` succeeds end-to-end. Tests that
# require vcc-ctrgcn are still runnable in that env.
# ---------------------------------------------------------------------------
collect_ignore_glob: list[str] = []
if importlib.util.find_spec("mmcv") is None:
    collect_ignore_glob.append("test_ctrgcn_smoke.py")


@pytest.fixture
def weight_dir():
    return PROJECT_ROOT / "data" / "weights" / "ctrgcn"


@pytest.fixture
def pyskl_config_dir():
    return pathlib.Path("D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet")


@pytest.fixture
def splits_dir():
    return PROJECT_ROOT / "data" / "splits"


# ---------------------------------------------------------------------------
# Phase 3 additions: synthetic-feature fixtures + integration temp dirs.
# Plans 02-07 import these; the real Phase 2 feature cache is not required
# except for tests explicitly marked `requires_features`.
# ---------------------------------------------------------------------------


@pytest.fixture
def feature_dir_ucf():
    """Real UCF-Crime feature root on E:/ (integration tests)."""
    p = pathlib.Path("E:/features/ucf")
    if not p.exists():
        pytest.skip("E:/features/ucf not mounted")
    return p


@pytest.fixture
def tmp_feature_dir(tmp_path):
    """Writable temp dir shaped like features/{dataset}/{modality}/*.npy."""
    (tmp_path / "skeleton").mkdir()
    (tmp_path / "clip").mkdir()
    return tmp_path


@pytest.fixture
def synth_skel_features():
    """Callable returning [N, 256] float32 skeleton features."""
    from tests.fixtures.synthetic import make_skel
    return make_skel


@pytest.fixture
def synth_clip_features():
    """Callable returning [N, 1024] float32 CLIP features."""
    from tests.fixtures.synthetic import make_clip
    return make_clip


@pytest.fixture
def synth_batch():
    """Callable returning a paired-bag batch dict (D-04 structure)."""
    from tests.fixtures.synthetic import make_batch
    return make_batch


@pytest.fixture
def smoke_cfg(tmp_path):
    """Minimal training config dict used by integration smoke tests."""
    return {
        "seed": 42,
        "dataset": "ucf",
        "paths": {
            "skeleton_features": str(tmp_path / "skeleton"),
            "clip_features": str(tmp_path / "clip"),
            "splits_dir": str(tmp_path / "splits"),
            "results_dir": str(tmp_path / "results"),
        },
        "model": {"variant": "skeleton_only", "skel_dim": 256, "head_hidden": [128, 32], "dropout": 0.3},
        "data": {"T": 32, "batch_size": 16, "num_workers": 0, "pin_memory": False},
        "train": {
            "lr": 1.0e-4, "weight_decay": 1.0e-2, "epochs": 2,
            "warmup_epochs": 1, "patience": 10,
            "k_topk": 3, "margin": 1.0,
            "lam_sparse": 8.0e-3, "lam_smooth": 8.0e-4,
        },
        "wandb": {"project": "violencecc", "mode": "disabled", "tags": []},
    }
