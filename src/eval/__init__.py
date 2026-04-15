"""src.eval — evaluation-time package (Phase 4).

Intentionally empty: no package-level re-exports. Plan 04-02's
src/eval/test_loader.py carries a sys.argv guard that raises on import
from unknown entry points, so importing this package must NOT transitively
trigger it. Downstream code must import the specific submodule it needs:

    from src.eval.snippet_to_frame import snippet_to_frame
    from src.eval.ucf_annotations import parse_annotations, frame_labels, VideoAnnotation
"""
