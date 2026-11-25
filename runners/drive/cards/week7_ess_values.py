"""Weighted descriptive variance decomposition for the ESS Human Values items (VAL1)."""
import numpy as np
import pandas as pd

ITEMS = "ipcrtiv imprich ipeqopt ipshabt impsafe impdiff ipfrule ipudrst ipmodst ipgdtim impfree iphlppl ipstrgv ipsuces ipadvnt ipbhprp iprspot iplylfr impenv imptrad impfun".split()
CLOCK = ["inwyys", "inwyr", "inwds", "inwyye", "inwde"]
COLUMNS = ["cntry", "essround", "edition", "anweight", "pspwght", "pweight", *CLOCK,
           *ITEMS, *(v + "a" for v in ITEMS)]


def decompose(values, weights, groups, countries, year):
    """Use weighted cell moments; all shares have the same population denominator."""
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        raise ValueError("No weighted item observations")
    g, w, y = groups[valid], weights[valid], values[valid]
    def sum_by(index, amounts, size):
        return np.bincount(index, weights=amounts, minlength=size)

    size = len(countries)
    mass = sum_by(g, w, size)
    occupied = mass > 0
    means = np.divide(sum_by(g, w*y, size), mass, out=np.zeros(size), where=occupied)
    within = np.dot(w, (y-means[g])**2)
    codes = countries[occupied]
    cell_w, cell_y = mass[occupied], means[occupied]
    country_w = np.bincount(codes, weights=cell_w)
    country_y = np.divide(np.bincount(codes, weights=cell_w*cell_y), country_w,
                          out=np.zeros_like(country_w), where=country_w > 0)
    grand = np.average(y, weights=w)
    time_ss = np.dot(cell_w, (cell_y-country_y[codes])**2)
    country_ss = np.dot(country_w, (country_y-grand)**2)
    total = np.dot(w, (y-grand)**2)
    if not np.isclose(within + time_ss + country_ss, total, rtol=1e-9, atol=1e-8):
        raise ValueError("Variance decomposition did not close")
    # Compute both axes from exactly the observations with a usable clock.
    years = year[valid]
    timed = np.isfinite(years)
    time_groups = g[timed]
    tm = sum_by(time_groups, w[timed], size)
    keep = tm > 0
    tc, tw = countries[keep], tm[keep]
    tx = sum_by(time_groups, w[timed]*years[timed], size)[keep]/tw
    ty = sum_by(time_groups, w[timed]*y[timed], size)[keep]/tw
    slopes, masses = [], []
    for c in np.unique(tc):
        take = tc == c
        if take.sum() < 2 or np.ptp(tx[take]) < 1:
            continue
        x, weight, response = tx[take], tw[take], ty[take]
        x = x - np.average(x, weights=weight)
        slopes.append(10*np.dot(weight*x, response)/np.dot(weight, x*x))
        masses.append(weight.sum())
    return dict(n=int(valid.sum()), cells=int(occupied.sum()), countries=int((country_w>0).sum()),
                within_share=float(within/total) if total else None,
                country_share=float(country_ss/total) if total else None,
                round_share=float(time_ss/total) if total else None,
                round_to_within=float(time_ss/within) if within else None,
                timed_n=int(timed.sum()), slope_countries=len(slopes),
                absolute_points_per_decade=float(np.average(np.abs(slopes), weights=masses)) if slopes else None,
                signed_points_per_decade=float(np.average(slopes, weights=masses)) if slopes else None)


def analyse(frame):
    if frame.cntry.isna().any() or frame.essround.isna().any():
        raise ValueError("Missing country or round key")
    group, pairs = pd.factorize(pd.MultiIndex.from_frame(frame[["cntry", "essround"]]), sort=True)
    countries = pd.factorize(pairs.get_level_values(0), sort=True)[0]
    a = frame[ITEMS].to_numpy(dtype=float, copy=True)
    b = frame[[i+"a" for i in ITEMS]].to_numpy(dtype=float, copy=True)
    for values in (a,b):
        values[~np.isin(values, np.arange(1.,7.))] = np.nan
    overlap = np.isfinite(a) & np.isfinite(b)
    if np.any(overlap & (a != b)):
        raise ValueError("Conflicting valid item forms")
    main_n, alternate_n = np.isfinite(a).sum(axis=0), np.isfinite(b).sum(axis=0)
    raw = np.where(np.isfinite(a), a, b)
    centered = raw - raw.mean(axis=1, keepdims=True)
    w = frame.anweight.to_numpy(dtype=float, copy=True)
    need = ~np.isfinite(w) | (w<=0)
    product = (frame.pspwght * frame.pweight).to_numpy(dtype=float)
    available = need & (product>0) & (frame.pspwght.to_numpy()>0) & np.isfinite(product)
    w[available] = product[available]
    year = np.full(len(w), np.nan)
    for key in CLOCK:
        column = frame[key]
        if key in ("inwds", "inwde"):
            column = pd.to_datetime(column, errors="coerce").dt.year
        x = column.to_numpy(dtype=float)
        use = ~np.isfinite(year) & (x>=2002) & (x<=2026)
        year[use] = x[use]
    rows = []
    for j, item in enumerate(ITEMS):
        for form, matrix in (("raw",raw),("person_centred",centered)):
            rows.append(dict(item=item, form=form, **decompose(matrix[:,j],w,group,countries,year)))
    return dict(rows=rows, people=len(frame), complete_21=int(np.isfinite(centered[:,0]).sum()),
                supplied_weight=int((~need).sum()), reconstructed_weight=int(available.sum()),
                missing_weight=int((need & ~available).sum()), valid_year=int(np.isfinite(year).sum()),
                items={item:dict(main=int(main_n[i]),alternate=int(alternate_n[i]),
                       both=int(overlap[:,i].sum())) for i,item in enumerate(ITEMS)})
