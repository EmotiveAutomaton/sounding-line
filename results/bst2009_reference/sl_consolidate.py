import json, csv, os
D = os.path.dirname(os.path.abspath(__file__))

# ---- Experiment 1 (Fig 5, page 11): panels in x-order = M1, M2, M3, H ----
f5 = json.load(open(os.path.join(D, "sl_fig5.json")))
pan = [f5[f"panel{i}"]["points"] for i in (1, 2, 3, 4)]
rows = []
for i in range(0, 300, 3):
    for j, goal in enumerate("ABC"):
        k = i + j
        blk = pan[0][k][2] and pan[0][k][2][0] < 0.2
        rows.append({
            "stimulus_index": i // 3 + 1, "goal": goal,
            "human_mean": pan[0][k][1],
            "M1_b0.5": pan[0][k][0], "M2_b2.0_g0.25": pan[1][k][0],
            "M3_b2.5_k0.5": pan[2][k][0], "H_b2.5": pan[3][k][0],
            "targeted_black": int(bool(blk)),
        })
with open(os.path.join(D, "SL_BST2009_exp1_from_fig5.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("Exp1 rows:", len(rows))

# ---- Experiment 2 (Fig 8, page 13) ----
f8 = json.load(open(os.path.join(D, "sl_fig8.json")))
pan8 = [f8[f"panel{i}"]["points"] for i in (1, 2, 3, 4)]
rows8 = []
for k in range(len(pan8[0])):
    rows8.append({
        "point_index": k + 1,
        "human_mean": pan8[0][k][1],
        "M1_b0.5": pan8[0][k][0], "M2_b0.5_g0.65": pan8[1][k][0],
        "M3_b1.0_k0.95": pan8[2][k][0], "H_b2.5": pan8[3][k][0],
    })
with open(os.path.join(D, "SL_BST2009_exp2_from_fig8.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows8[0])); w.writeheader(); w.writerows(rows8)
print("Exp2 rows:", len(rows8))

# ---- Experiment 3 (Fig 10, page 17) ----
f10 = json.load(open(os.path.join(D, "sl_fig10.json")))
rows10 = []
for pk, v in f10.items():
    ppl = next((s for s in v["series"] if not s["dashed"]), None)
    mdl = next((s for s in v["series"] if s["dashed"]), None)
    for t in range(4):
        rows10.append({
            "panel": pk, "panel_rect": str(v["rect"]), "trial": t + 1,
            "human_P_path2": ppl["values"][t] if ppl else "",
            "M3_b5_k0.6_P_path2": mdl["values"][t] if mdl else "",
        })
with open(os.path.join(D, "SL_BST2009_exp3_from_fig10.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows10[0])); w.writeheader(); w.writerows(rows10)
print("Exp3 rows:", len(rows10), "(human complete; model missing in 3 flat panels)")
