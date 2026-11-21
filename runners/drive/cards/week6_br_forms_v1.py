"""BR half summaries. Ratings have their documented lowest value subtracted."""
import numpy as np


def gap_masks(dates, first, last):
    """Whole days including both endpoints. Keep round(T/3) at each end."""
    width = np.rint((last - first + 1) / 3).astype(int)
    return dates < first + width, dates > last - width


def graded_stats(r, y):
    """Rectangular person x prompt arrays, padded with NaNs when needed."""
    valid = np.isfinite(r) & np.isfinite(y)
    low = valid & (r == 0)
    above = valid & (r > 0)
    n0, n1 = low.sum(1), above.sum(1)
    count = valid.sum(1).clip(1)
    mean_r = np.where(valid, r, 0).sum(1) / count
    rc = np.where(valid, r - mean_r[:, None], 0)
    ss = (rc * rc).sum(1)
    mean0 = np.where(low, y, 0).sum(1) / n0.clip(1)
    sd0 = np.sqrt((np.where(low, y - mean0[:, None], 0)**2).sum(1) / (n0-1).clip(1))
    distinct = np.where(above, r, -np.inf).max(1) > np.where(above, r, np.inf).min(1)
    slope = (rc * np.where(valid, y, 0)).sum(1) / np.where(ss > 0, ss, 1)
    return dict(b=np.where((n0 >= 2) & (n1 >= 2) & distinct, slope, np.nan),
                L=mean0, S=sd0, n1=n1, n0=n0, sxx=ss)

