import json
import _tmp_tta_harness as H

bb = "clip-vit-b-16"
st = H.build(bb); model = st["model"]
cond = H.load_condition(bb, "gaussian_noise", 5)
mu_s, C_s = H.source_stats(bb, "clip")
f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)               # identity
W = H._coral_W(cond.mu_t_clip, cond.C_t_clip, mu_s, C_s, 1.0)            # full NORM (beta=1)
tclips = {v: H._apply(cond.clips[v], cond.mu_t_clip, mu_s, W) for v in cond.vids}
f1, v1 = H.score(model, cond.skels, tclips, cond.vids)
# custom-forward identity must equal plain identity
f2, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=H.ref_forward)
print(json.dumps({"src": round(f0, 2), "norm_b1": round(f1, 2), "dAUC": round(f1 - f0, 2),
                  "ref_forward_src": round(f2, 2), "vsrc": round(v0, 2), "n": len(cond.vids)}))
