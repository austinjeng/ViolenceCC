import pytest
import pathlib

PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")


@pytest.fixture
def weight_dir():
    return PROJECT_ROOT / "data" / "weights" / "ctrgcn"


@pytest.fixture
def pyskl_config_dir():
    return pathlib.Path("D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet")


@pytest.fixture
def splits_dir():
    return PROJECT_ROOT / "data" / "splits"
