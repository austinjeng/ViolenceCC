"""Data pipeline package (MOD-02).

Public API:
    MILFeatureDataset — per-video feature loader with D-09/D-10/D-12 sampling.
    build_dataloaders — paired (normal, abnormal) train loaders + val loader per D-04.
"""
from src.data.dataset import MILFeatureDataset
from src.data.loaders import build_dataloaders

__all__ = ["MILFeatureDataset", "build_dataloaders"]
