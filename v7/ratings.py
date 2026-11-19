"""Player impact ratings: ridge regression of game margins on player minutes,
shrunk toward a box-score prior (Game Score per 48). Same method as the backtest."""
import numpy as np, pandas as pd
from .config import HL, LAM, A, PRIOR_MIN, REPLACEMENT, WINDOW_DAYS

def gmsc(P):
    return (P.pts + 0.4 * P.fgm - 0.7 * P.fga - 0.4 * (P.fta - P.ftm) + 0.7 * P.oreb + 0.3 * P.dreb
            + P.stl + 0.7 * P.ast + 0.7 * P.blk - 0.4 * P.pf - P.tov)

def fit(P, G, asof):
    """P: player rows (event, team, home, pid, min, box stats). G: games (event, date, home, away, home_score, away_score, status).
    Returns (ratings: Series pid -> points per 48 vs average, hca)."""
    asof = pd.Timestamp(asof)
    g = G[(G.status == "STATUS_FINAL")].copy(); g["date"] = pd.to_datetime(g.date)
    g = g[(g.date < asof) & (g.date >= asof - pd.Timedelta(days=WINDOW_DAYS))].reset_index(drop=True)
    g["margin"] = g.home_score - g.away_score
    w = 0.5 ** ((asof - g.date).dt.days.values / HL)
    gi = pd.Series(range(len(g)), index=g.event)
    p = P[P.event.isin(g.event) & (P["min"] > 0)].copy()
    p["gi"] = gi.reindex(p.event).values; p["w"] = w[p.gi.values]; p["gs"] = gmsc(p)
    agg = p.assign(wm=p["min"] * p.w, wg=p.gs * p.w).groupby("pid")[["wm", "wg"]].sum()
    lg = agg.wg.sum() / agg.wm.sum() * 48
    shr = agg.wm / (agg.wm + PRIOR_MIN)
    prior = A * (agg.wg / agg.wm * 48 - lg) * shr + REPLACEMENT * (1 - shr)
    pids = agg.index.values; col = pd.Series(range(len(pids)), index=pids); k = len(pids)
    X = np.zeros((len(g), k + 1)); X[:, k] = 1.0
    np.add.at(X, (p.gi.values, col.reindex(p.pid).values), np.where(p.home, 1.0, -1.0) * p["min"].values / 48)
    L = np.full(k + 1, LAM); L[k] = 1e-6
    XtW = X.T * w
    r = np.linalg.solve(XtW @ X + np.diag(L), XtW @ g.margin.values + L * np.append(prior.values, 0.0))
    return pd.Series(r[:k], index=pids), float(r[k]), prior
