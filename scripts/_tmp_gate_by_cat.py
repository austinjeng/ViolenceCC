"""One-off: per-category mean gate value (CLIP UCF gated_fusion s42).

Replicates generate_phase6_charts.collect_gate_and_features (gate hook + sigmoid)
to report exact per-category gate means for the H3 figure decision.
"""
from __future__ import annotations
import json, statistics as st
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

from src.models.registry import build_model
from src.utils.checkpoint import load_checkpoint
from src.data.dataset import MILFeatureDataset
from src.eval.ucf_annotations import parse_annotations

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "results" / "ucf_gated_fusion_s42"

snap = json.load(open(RUN / "config_snapshot.json"))["config"]
model = build_model(**snap["model"])
model.load_state_dict(load_checkpoint(RUN / "best_model.pth", device="cpu"), strict=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
model.to(dev).eval()

ds = MILFeatureDataset(
    skel_dir=snap["paths"]["skeleton_features"],
    clip_dir=snap["paths"]["clip_features"],
    split_file=str(ROOT / "data" / "splits" / "ucf_test.txt"),
    dataset="ucf", mode="test",
)

def hook(m, i, o): hook._last = torch.sigmoid(o).detach().cpu()
h = model.gate.register_forward_hook(hook)

gate = {}
with torch.no_grad():
    for b in DataLoader(ds, batch_size=1, shuffle=False, num_workers=0):
        vid = b["video_id"]; vid = vid[0] if isinstance(vid, (list, tuple)) else vid
        kw = {}
        for k in ("skel", "clip"):
            if k in b:
                t = b[k]
                kw[k] = (t if t.dim() == 3 else t.unsqueeze(0)).to(dev)
        model(**kw)
        gate[vid] = float(hook._last.squeeze(0).numpy().mean())
h.remove()

annos = parse_annotations(ROOT / "data" / "annotations" / "ucf_temporal.txt")
motion = {"Fighting","Assault","Arrest","Robbery","Shooting","Stealing","Shoplifting","Abuse"}
scene = {"Explosion","Arson","RoadAccidents","Burglary","Vandalism"}

by_cat = {}
norm = []
for vid, g in gate.items():
    if vid in annos:
        by_cat.setdefault(annos[vid].category, []).append(g)
    else:
        norm.append(g)

print(f"all-gate mean={st.mean(gate.values() if False else list(gate.values())):.4f} "
      f"min={min(gate.values()):.4f} max={max(gate.values()):.4f}  (g>0.5 => more skeleton)")
print(f"{'category':14} {'mean_gate':>9} {'n':>4}  kind")
for c in sorted(by_cat, key=lambda c: -st.mean(by_cat[c])):
    kind = "motion" if c in motion else ("scene" if c in scene else "?")
    print(f"  {c:12} {st.mean(by_cat[c]):9.4f} {len(by_cat[c]):4d}  [{kind}]")
if norm:
    print(f"  {'Normal':12} {st.mean(norm):9.4f} {len(norm):4d}  [normal]")
m = [st.mean(by_cat[c]) for c in by_cat if c in motion]
s = [st.mean(by_cat[c]) for c in by_cat if c in scene]
print(f"--> motion-cat gate mean {st.mean(m):.4f} | scene-cat gate mean {st.mean(s):.4f} "
      f"| spread(max-min cat) {max(st.mean(by_cat[c]) for c in by_cat)-min(st.mean(by_cat[c]) for c in by_cat):.4f}")
