"""TTA module: TENT-style and SAR-style entropy minimisation for LN-based fusion heads.

Ported from SAR repo (https://github.com/mr-eggplant/SAR, ICLR 2023 Oral, MIT License).
Adapted: BN -> LN targeting, softmax -> binary entropy, episodic per-video reset.
"""
from src.tta.tent import binary_entropy, configure_model, collect_params, TentAdaptor
from src.tta.sar import SarAdaptor
from src.tta.sam import SAM

__all__ = [
    "binary_entropy",
    "configure_model",
    "collect_params",
    "TentAdaptor",
    "SarAdaptor",
    "SAM",
]
