"""Six prospective four-class TR4 predictors; no corpus execution here.

DESIGN CHECK: LESSONS 3-5 and CONTROLS reread 2026-10-27. NULL equal shares
stay equal; the current outcome never enters its forecast. ALTERNATIVE a known
persistent change must be tracked. Invalid observations refuse; missing ones
advance Gaussian time without an invented choice. All grid states are retained.
"""
import math
import numpy as np
from scipy.special import gammaln, logsumexp, softmax

RATES = (.01, .05, .1, .25, .5, .75, 1.)
HAZARDS = (.01, .025, .05, .1, .2)
Q_GRID = (0., .0001, .001, .01, .1, 1.)
NAMES = ('whole', 'last', 'exponential', 'kalman', 'trend', 'changepoint')


def counts(value):
    x = np.asarray(value)
    if x.shape != (4,) or x.dtype.kind not in 'iu' or x.dtype.kind == 'b' or np.any(x < 0):
        raise ValueError('four nonnegative integer canonical counts required')
    return x.astype(float)


def shares(value):
    x = counts(value)
    return (x + .5)/(x.sum() + 2.)


def observation(value):
    x = counts(value) + .5
    z = np.log(x[1:]/x[0])
    covariance = np.diag(1/x[1:]) + np.full((3, 3), 1/x[0])
    return z, covariance


def log_loss(value, probabilities):
    x = counts(value); p = np.asarray(probabilities, float)
    if p.shape != (4,) or not np.isfinite(p).all() or np.any(p <= 0) or not np.isclose(p.sum(), 1, rtol=0, atol=1e-12):
        raise ValueError('four finite positive normalized probabilities required')
    return float(-x @ np.log(p)/x.sum()) if x.sum() else None


class GaussianBank:
    """Prefix likelihood selects one of all retained constant-q filters."""
    def __init__(self, trend=False, grid=Q_GRID):
        if not grid or any(not math.isfinite(q) or q < 0 for q in grid) or list(grid) != sorted(set(grid)):
            raise ValueError('ordered unique nonnegative q grid required')
        self.grid = np.asarray(grid); self.trend = trend; self.steps = 0
        d = 6 if trend else 3; identity = np.eye(3)
        self.F = np.eye(d)
        if trend: self.F[:3, 3:] = identity
        base = np.block([[identity/3, identity/2], [identity/2, identity]]) if trend else identity
        self.Q = self.grid[:, None, None] * base
        self.mean = np.zeros((len(grid), d))
        self.cov = np.tile(np.diag([10.]*3 + ([1.]*3 if trend else [])), (len(grid), 1, 1))
        self.likelihood = np.zeros(len(grid))

    def prior(self):
        if not self.steps: return self.mean.copy(), self.cov.copy()
        return self.mean @ self.F.T, self.F @ self.cov @ self.F.T + self.Q

    def predict(self):
        mean, _ = self.prior(); index = int(np.argmax(self.likelihood))
        return softmax(np.r_[0., mean[index, :3]]), float(self.grid[index])

    def update(self, value):
        x = counts(value); mean, covariance = self.prior()
        if x.sum():
            z, noise = observation(value); innovation = z - mean[:, :3]
            S = covariance[:, :3, :3] + noise
            sign, logdet = np.linalg.slogdet(S)
            if np.any(sign <= 0): raise ValueError('nonpositive predictive covariance')
            solve = np.linalg.solve(S, innovation[..., None])[..., 0]
            self.likelihood += -.5*(3*math.log(2*math.pi) + logdet + np.sum(innovation*solve, axis=1))
            gain = np.linalg.solve(S, covariance[:, :3, :]).transpose(0, 2, 1)
            self.mean = mean + np.einsum('qij,qj->qi', gain, innovation)
            # Joseph form avoids cancellation in the updated covariance.
            A = np.tile(np.eye(mean.shape[1]), (len(self.grid), 1, 1)); A[:, :, :3] -= gain
            self.cov = A @ covariance @ A.transpose(0, 2, 1) + gain @ noise @ gain.transpose(0, 2, 1)
            self.cov = (self.cov + self.cov.transpose(0, 2, 1))*.5
        else:
            self.mean, self.cov = mean, covariance
        self.steps += 1
        if not all(np.isfinite(v).all() for v in (self.mean, self.cov, self.likelihood)):
            raise ValueError('nonfinite Gaussian state')


class ChangePoint:
    def __init__(self, hazard):
        if not math.isfinite(hazard) or not 0 <= hazard <= 1: raise ValueError('hazard outside unit interval')
        self.hazard = hazard; self.log_weights = np.zeros(1); self.alpha = np.full((1, 4), .5)

    def predict(self):
        return np.exp(self.log_weights) @ (self.alpha/self.alpha.sum(axis=1)[:, None])

    def update(self, value):
        x = counts(value)
        if not x.sum(): return
        total = self.alpha.sum(axis=1)
        ll = gammaln(total)-gammaln(total+x.sum()) + (gammaln(self.alpha+x)-gammaln(self.alpha)).sum(axis=1)
        joint = self.log_weights + ll; evidence = logsumexp(joint)
        grow = joint-evidence+math.log1p(-self.hazard) if self.hazard < 1 else np.full(len(joint), -np.inf)
        reset = math.log(self.hazard) if self.hazard else -np.inf
        self.log_weights = np.r_[reset, grow]
        self.alpha = np.vstack((np.full(4, .5), self.alpha+x))


class SixForecasts:
    def __init__(self, rate, hazard):
        if rate not in RATES or hazard not in HAZARDS: raise ValueError('frozen rate and hazard required')
        self.rate = rate; self.n = 0; self.total = np.zeros(4)
        self.last = self.exponential = np.full(4, .25)
        self.kalman = GaussianBank(); self.trend = GaussianBank(trend=True)
        self.changepoint = ChangePoint(hazard)

    def predict(self):
        kalman, q = self.kalman.predict(); trend, slope_q = self.trend.predict()
        return dict(whole=self.total/self.n if self.n else np.full(4, .25), last=self.last.copy(),
                    exponential=self.exponential.copy(), kalman=kalman, trend=trend,
                    changepoint=self.changepoint.predict()), dict(q=q, trend_q=slope_q, observed_sessions=self.n)

    def update(self, value):
        x = counts(value)
        self.kalman.update(value); self.trend.update(value); self.changepoint.update(value)
        if x.sum():
            p = shares(value); self.total += p; self.last = p
            self.exponential = p if not self.n else (1-self.rate)*self.exponential+self.rate*p
            self.n += 1


def forecast(sequence, rate=.1, hazard=.05):
    model = SixForecasts(rate, hazard); predictions = []
    for value in sequence:
        p, metadata = model.predict()
        predictions.append(dict(probabilities={k:v.tolist() for k,v in p.items()}, **metadata))
        model.update(value)
    return predictions
