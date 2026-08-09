"""G43 — is the early subspace break affective, or the input adapter's edge?

The one address fact that transfers is the very early two-band break. It gates how every mapping
claim reads — and it has never had its control: **non-affective subspaces measured identically.**
If syntax, topic, and frequency subspaces all break at the same place, the boundary is an
embedding/input phenomenon and says nothing about the affect mappings.

    ADAPTER-EDGE   every control subspace breaks at the same earliest boundary as affect
    AFFECT-SPECIFIC  affect breaks early where controls do not — the boundary carries meaning
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "control_subspaces"

TOPIC_SETS = {
    "cooking": ["The sauce reduced slowly over a low flame.", "She folded the dough twice before resting it.", "Salt early, taste often, adjust at the end.", "The oven door stayed shut for the first hour."],
    "sport": ["The keeper pushed the shot around the post.", "They pressed high for the whole second half.", "Her split at the turn was a personal best.", "The bench emptied when the buzzer sounded."],
    "law": ["The clause survives termination of the agreement.", "Counsel objected on grounds of relevance.", "The statute requires notice within thirty days.", "The court weighed the precedent narrowly."],
    "weather": ["A cold front stalls over the valley tonight.", "Gusts reached fifty knots along the ridge.", "The forecast holds rain through the weekend.", "Fog lifted from the harbour by midmorning."],
    "finance": ["The bond rallied after the rate decision.", "Margins compressed for a third straight quarter.", "The fund rebalanced into short-duration paper.", "Volume spiked into the close on Friday."],
    "medicine": ["The dose was titrated over two weeks.", "Symptoms resolved without further intervention.", "The trial excluded patients with prior events.", "Blood pressure responded to the first agent."],
    "travel": ["The night train reaches the border by six.", "We changed ferries at the smaller island.", "The pass closes after the first heavy snow.", "Her visa allowed a single entry only."],
    "music": ["The theme returns inverted in the coda.", "They tuned down a half step for the encore.", "The chorus lands on a suspended chord.", "Her phrasing dragged just behind the beat."],
}
SYNTAX_SETS = {
    "question": ["Where does the river bend south?", "Why would the committee refuse it?", "When did the last ferry leave?", "How could anyone verify that claim?"],
    "imperative": ["Close the valve before inspecting the seal.", "Send the draft tonight.", "Keep the originals in the safe.", "Check every figure twice."],
    "passive": ["The bridge was closed by the inspectors.", "The letter was signed without being read.", "The fields were flooded during the night.", "The decision was reached after long debate."],
    "conditional": ["If the seal fails, the pump floods.", "If prices rise, the margin vanishes.", "If she calls, take the message.", "If the test passes, ship it."],
    "negation": ["The engine would not turn over.", "Nobody claimed the parcel.", "The results never replicated.", "He did not sign the second page."],
    "coordination": ["She wrote and he edited and they argued.", "The tide rose and the wind turned.", "We packed, drove, and unloaded by noon.", "He cooked and she kept the accounts."],
    "relative": ["The man who fixed the roof left early.", "The rule that nobody follows persists.", "The road, which floods yearly, stayed dry.", "The book that started it all sold out."],
    "comparative": ["The second draft was tighter than the first.", "Nothing moves faster than rumour here.", "The old method proved cheaper than the new.", "Her route was shorter than the map claimed."],
}
FREQ_SETS = {
    "very_common": ["It was there and then it was not.", "They said it would be good and it was.", "We went to see what it was about.", "You do what you can with what you have."],
    "common": ["The market opened late because of the storm.", "Her answer changed the direction of the meeting.", "The children walked home along the river.", "He finished the report before dinner."],
    "mid": ["The auditor flagged an inconsistency in the ledger.", "Gravel crunched under the delivery van.", "The committee deferred the amendment indefinitely.", "A lantern swung from the barn rafter."],
    "uncommon": ["The escarpment glowed ochre at dusk.", "Her monograph catalogued vernacular ironwork.", "The distillate carried a faint juniper note.", "A palimpsest emerged beneath the varnish."],
    "rare": ["The susurrus of the reeds presaged rain.", "His marginalia bristled with obloquy.", "A chatoyant gleam crossed the cabochon.", "The falconer's creance snagged on the gorse."],
    "technical": ["The eigenvalues cluster near the unit circle.", "Backpropagation updates the earlier weights last.", "The titration endpoint drifted with temperature.", "Impedance mismatch reflected half the signal."],
    "archaic": ["Hither came the wanderer, sore bestead.", "He durst not gainsay the elder's word.", "Foreswear thy haste, lest ruin follow.", "The seneschal bade them tarry till morn."],
    "loan": ["The maitre d' seated the entourage anon.", "Her memoir had a certain je ne sais quoi.", "The kibbutz operated a small ulpan.", "He ordered the omakase without a menu."],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415

    from runners.run_b import split                                   # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)

    def best_split(dirs) -> int:
        n = dirs.n_layers
        concepts = list(dirs.concepts)

        def basis(L):
            M = np.array([np.asarray(dirs.vecs[c][L], float) for c in concepts])
            M = M - M.mean(0)
            q, r = np.linalg.qr(M.T)
            return q[:, np.abs(np.diag(r)) > 1e-8]

        B = [basis(L) for L in range(n)]
        k = min(b.shape[1] for b in B)
        A = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                s = np.linalg.svd(B[i][:, :k].T @ B[j][:, :k], compute_uv=False)
                A[i, j] = float(np.clip(s, 0, 1).mean())

        def score(kk):
            w, x = [], []
            for i in range(n):
                for j in range(i + 1, n):
                    (w if (i < kk) == (j < kk) else x).append(A[i, j])
            return float(np.mean(w) - np.mean(x))

        return max(range(1, n - 1), key=score)

    fit, _ = split()
    out = {"model": model_name, "splits": {}}
    for name, sets in (("affect", fit), ("topic", TOPIC_SETS),
                       ("syntax", SYNTAX_SETS), ("frequency", FREQ_SETS)):
        dirs = fit_directions(reader, sets)
        s = best_split(dirs)
        out["splits"][name] = s
        print(f"{name:<10} best two-band split at block {s}")

    aff = out["splits"]["affect"]
    same = sum(1 for k, v in out["splits"].items() if k != "affect" and abs(v - aff) <= 1)
    out["verdict"] = "ADAPTER-EDGE" if same == 3 else \
        f"AFFECT-SPECIFIC ({3 - same} of 3 controls break elsewhere)"
    print(f"\n  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=2),
                                         encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
