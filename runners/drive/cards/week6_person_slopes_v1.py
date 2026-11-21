"""Round 34 person-slope and matching operators, as supplied in pf_slopes.py.

The reference numerical kernels are kept together so the planted-world
qualification and the actual diary tables use identical estimators. Window
membership, missing items and the two-event/two-other support checks belong
to the source panel. The caller bounds bootstrap batches and never serializes
individual matches. Reference SHA-256: 8257bf2bc84a750e123b3f510f1ba572d32c3a73e0e8db8ef48bc942f4455ddb.
"""
import numpy as np

EPS = 1e-6


def half_stats(x, y):
    """slope b, non-event mean L, non-event SD S, whole-half mean m and SD sd; plus n1, n0."""
    n1 = x.sum(1); n0 = x.shape[1] - n1
    m1 = (y * x).sum(1) / np.maximum(n1, 1)
    m0 = (y * (1 - x)).sum(1) / np.maximum(n0, 1)
    sd0 = np.sqrt((((y - m0[:, None]) ** 2) * (1 - x)).sum(1) / np.maximum(n0 - 1, 1))
    return dict(n1=n1, n0=n0, b=m1 - m0, L=m0, S=sd0, m=y.mean(1), sd=y.std(1, ddof=1))


def wmean(W, x):
    return (W * x).sum(-1) / W.sum(-1)


def wcov(W, x, y):
    mx = wmean(W, x)[..., None]; my = wmean(W, y)[..., None]
    return (W * (x - mx) * (y - my)).sum(-1) / W.sum(-1)


def cc(W, x, y):
    """Cross-half covariance 0.5*[cov(x1,y2)+cov(x2,y1)]; x, y are (half1, half2) pairs."""
    return 0.5 * (wcov(W, x[0], y[1]) + wcov(W, x[1], y[0]))


def adjust(W, b, X):
    """b: (b1,b2); X: list of 1 or 2 (half1,half2) covariate pairs (L first). Returns V, Vadj, beta (D,k)."""
    V = wcov(W, b[0], b[1])
    c = np.stack([cc(W, b, Xk) for Xk in X], -1)
    Sig = np.stack([np.stack([cc(W, Xj, Xk) for Xk in X], -1) for Xj in X], -2)
    Sig = 0.5 * (Sig + np.swapaxes(Sig, -1, -2))
    sLL = Sig[:, 0, 0]
    fbL = np.where(sLL > EPS, c[:, 0] / np.where(sLL > EPS, sLL, 1.0), 0.0)
    if len(X) == 1:
        beta = fbL[:, None]
    else:
        full = np.linalg.eigvalsh(Sig).min(-1) > EPS
        safe = np.where(full[:, None, None], Sig, np.eye(2))
        beta = np.linalg.solve(safe, c[..., None])[..., 0]
        beta = np.where(full[:, None], beta, np.stack([fbL, np.zeros(len(V))], -1))
    return V, V - (c * beta).sum(-1), beta


def wpearson(w, x, y):
    W0 = w[None, :]
    return (wcov(W0, x, y) / np.sqrt(wcov(W0, x, x) * wcov(W0, y, y)))[0]


def slope_block(W, h1, h2, useS):
    """useS: dict feeling -> bool, decided once per replicate on the full sample."""
    pr = lambda f, k: (h1[f][k], h2[f][k])
    XA = [pr("A", "L")] + ([pr("A", "S")] if useS["A"] else [])
    XB = [pr("B", "L")] + ([pr("B", "S")] if useS["B"] else [])
    VA, VadjA, bA = adjust(W, pr("A", "b"), XA)
    _, VadjB, bB = adjust(W, pr("B", "b"), XB)
    _, VadjL, _ = adjust(W, pr("A", "b"), [pr("A", "L")])
    C = cc(W, pr("A", "b"), pr("B", "b"))
    kAB = np.stack([cc(W, Xk, pr("B", "b")) for Xk in XA], -1)
    kBA = np.stack([cc(W, Xk, pr("A", "b")) for Xk in XB], -1)
    SAB = np.stack([np.stack([cc(W, Xj, Xk) for Xk in XB], -1) for Xj in XA], -2)
    Cadj = C - (bA * kAB).sum(-1) - (bB * kBA).sum(-1) + np.einsum("di,dij,dj->d", bA, SAB, bB)
    ok = (VadjA > 0) & (VadjB > 0)
    radj = np.where(ok, Cadj / np.sqrt(np.where(ok, VadjA * VadjB, 1.0)), np.nan)
    return VA, VadjL, VadjA, VadjB, radj


def boot_counts(rng, n, D):
    idx = rng.integers(0, n, (D, n)) + n * np.arange(D)[:, None]
    return np.bincount(idx.ravel(), minlength=D * n).reshape(D, n).astype(float)


def zs(F):
    s = F.std(0)
    return (F - F.mean(0)) / np.where(s > 0, s, 1.0)


def hit10(F1, F2, r):
    """Matching score sum_k (2 r x y - r^2 (x^2+y^2)) / (2 (1-r^2)); hit = < 10 others strictly higher."""
    r = np.clip(r, 0.0, 0.95)
    a, q = r / (1 - r ** 2), r ** 2 / (2 * (1 - r ** 2))
    Sc = (F1 * a) @ F2.T - (F1 ** 2 @ q)[:, None] - (F2 ** 2 @ q)[None, :]
    return ((Sc > np.diag(Sc)[:, None]).sum(1) < 10).astype(float)


def fold_hits(rng, F1, F2, arms):
    """Two folds; each fold ranked with weights from the other fold's split-half correlations."""
    n = len(F1)
    fold = np.zeros(n, int); fold[rng.permutation(n)[: n // 2]] = 1
    hits = {a: np.zeros(n) for a in arms}
    chance = np.zeros(n)
    for f in (0, 1):
        te, tr = fold == f, fold != f
        r = np.array([np.corrcoef(F1[tr, k], F2[tr, k])[0, 1] for k in range(F1.shape[1])])
        wt = np.nan_to_num(r)
        chance[te] = 10.0 / te.sum()
        for a, cols in arms.items():
            hits[a][te] = hit10(F1[te][:, cols], F2[te][:, cols], wt[cols])
    return hits, chance.mean()


