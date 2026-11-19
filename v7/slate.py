"""Project tonight's games: player ratings x projected minutes, adjusted for the injury report,
blended toward the market line. Usage: python -m v7.slate 2026-11-19"""
import sys, os, datetime as dt, json, pandas as pd, numpy as np
from . import espn, ratings
from .config import GTD_SHARE, MARKET_WEIGHT, EDGE_PTS
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def projected_minutes(P, G):
    """EWMA (half-life 5 games) of each player's minutes, for the team he last played for."""
    g = G[["event", "date"]].drop_duplicates()
    p = P.merge(g, on="event").sort_values(["pid", "date"])
    p["ewm"] = p.groupby("pid")["min"].transform(lambda s: s.ewm(halflife=5).mean())
    last = p.groupby("pid").tail(1)
    # drop players who haven't played in 25+ days (long-term absences not on the report, two-way, released)
    last = last[pd.to_datetime(last.date) >= pd.to_datetime(last.date).max() - pd.Timedelta(days=25)]
    return last[["pid", "name", "team", "ewm", "date"]].rename(columns={"ewm": "pmin", "date": "last_game"})

def run(day):
    P = pd.read_parquet(f"{DATA}/players.parquet"); G = pd.read_parquet(f"{DATA}/games.parquet")
    r, hca, prior = ratings.fit(P, G, day)
    mins = projected_minutes(P, G[pd.to_datetime(G.date) < pd.Timestamp(day)])
    inj = pd.DataFrame(espn.injuries())
    tag = inj.dropna(subset=["pid"]).set_index("pid").tag if len(inj) else pd.Series(dtype=str)
    games = espn.scoreboard(day.replace("-", ""))
    rows, detail = [], []
    for g in games:
        side = {}
        for t, sgn in ((g["home"], 1), (g["away"], -1)):
            roster = mins[mins.team == t].copy()
            roster["status"] = roster.pid.map(tag).fillna("")
            roster["avail"] = np.where(roster.status.isin(["OUT", "OFS"]), 0.0, np.where(roster.status == "GTD", GTD_SHARE, 1.0))
            roster["proj"] = roster.pmin * roster.avail
            scale = 240 / roster.proj.sum() if roster.proj.sum() > 0 else 0
            roster["proj"] *= scale
            roster["rating"] = [r.get(pid, prior.get(pid, -2.0)) for pid in roster.pid]
            roster["value"] = roster.proj / 48 * roster.rating
            # full-strength version: everyone at usual minutes, to show what injuries cost
            full = roster.pmin * (240 / roster.pmin.sum()) / 48 * roster.rating
            side[t] = (roster.value.sum(), full.sum())
            for x in roster.itertuples():
                detail.append(dict(date=day, team=t, player=x.name, status=x.status, usual_min=round(x.pmin, 1),
                                   proj_min=round(x.proj, 1), rating=round(x.rating, 2), pts_tonight=round(x.value, 2)))
        model = side[g["home"]][0] - side[g["away"]][0] + hca          # projected home margin
        inj_cost = (side[g["home"]][0] - side[g["home"]][1]) - (side[g["away"]][0] - side[g["away"]][1])
        mkt = -g["spread_home"] if g["spread_home"] is not None else None
        fair = mkt + (1 - MARKET_WEIGHT) * (model - mkt) if mkt is not None else None
        edge = (fair - mkt) if mkt is not None else None
        pick = ""
        if edge is not None and abs(model - mkt) >= EDGE_PTS:
            pick = f'{g["home"]} {g["spread_home"]:+g}' if model > mkt else f'{g["away"]} {-g["spread_home"]:+g}'
        rows.append(dict(date=day, tip_utc=g["tip"], away=g["away"], home=g["home"],
                         dk_spread_home=g["spread_home"], dk_open_home=g["spread_home_open"], dk_total=g["total"],
                         model_margin_home=round(model, 1), model_spread_home=round(-model, 1),
                         gap_vs_market=round(model - mkt, 1) if mkt is not None else None,
                         injury_swing_home=round(inj_cost, 1), lean=pick))
    S = pd.DataFrame(rows); D = pd.DataFrame(detail)
    os.makedirs(f"{DATA}/slates", exist_ok=True)
    S.to_csv(f"{DATA}/slates/{day}.csv", index=False); D.to_csv(f"{DATA}/slates/{day}_players.csv", index=False)
    return S, D

if __name__ == "__main__":
    S, D = run(sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat())
    print(S.to_string(index=False))
