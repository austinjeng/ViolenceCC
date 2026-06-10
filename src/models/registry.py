"""Model variant registry (D-16).

YAML `model.variant: <key>` maps via `build_model(**cfg["model"])` to the
wrapper class under src/models/. Registry uses lazy imports so that partial
plan execution does not break collection — each variant becomes available
as Plans 04/05 land.
"""
from __future__ import annotations
import inspect
import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)

# D-15: keys that legitimately ride along in a model config block (e.g. from a
# config_snapshot replay) but are NOT constructor args. These are allow-listed so
# the unexpected-kwarg warning stays silent during normal replay.
_KNOWN_EXTRA_KWARGS = frozenset({"variant", "strategy", "cache_variant", "backbone"})

# Lazy factories: import the class on first call. This avoids ImportError
# when Plans 04/05 have not yet populated the implementation files.
def _get_skeleton_only():
    from src.models.skeleton_only import SkeletonProj
    return SkeletonProj

def _get_clip_only():
    from src.models.clip_only import CLIPProj
    return CLIPProj

def _get_late_fusion():
    from src.models.late_fusion import LateFusion
    return LateFusion

def _get_gated_fusion():
    from src.models.gated_fusion import GatedFusion
    return GatedFusion

def _get_rtfm_i3d():
    # Phase 4 D-18: RTFM variant on XD I3D RGB features (harness gate).
    from src.models.rtfm_i3d import RTFMI3D
    return RTFMI3D


MODEL_REGISTRY: Dict[str, Callable] = {
    "skeleton_only": _get_skeleton_only,
    "clip_only":     _get_clip_only,
    "late_fusion":   _get_late_fusion,
    "gated_fusion":  _get_gated_fusion,
    "rtfm_i3d":      _get_rtfm_i3d,   # D-18
}


def build_model(variant: str, **kwargs):
    """Instantiate a model variant from resolved YAML kwargs.

    Usage:
        cfg = yaml.safe_load(open("configs/gated_fusion.yaml"))
        model = build_model(**cfg["model"])
    """
    if variant not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown variant '{variant}'. Valid: {list(MODEL_REGISTRY)}"
        )
    cls = MODEL_REGISTRY[variant]()

    # D-15: warn (never raise) about kwargs the constructor does not declare, so a
    # typo'd hyperparameter does not silently fall back to a default via **unused.
    # Known replay-only keys (variant/strategy/cache_variant/backbone) are skipped
    # to keep config_snapshot replay quiet; this is non-fatal so replay still works.
    try:
        sig = inspect.signature(cls.__init__)
        has_var_kw = any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        if has_var_kw:
            declared = set(sig.parameters) - {"self"}
            unexpected = [
                k for k in kwargs
                if k not in declared and k not in _KNOWN_EXTRA_KWARGS
            ]
            if unexpected:
                logger.warning(
                    "build_model(%r): unexpected kwargs %s not declared by %s; "
                    "they will be swallowed by **kwargs and IGNORED (possible typo?)",
                    variant, sorted(unexpected), cls.__name__,
                )
    except (ValueError, TypeError):
        # Signature introspection failed (exotic __init__); skip the check rather
        # than break model construction.
        pass

    return cls(**kwargs)
