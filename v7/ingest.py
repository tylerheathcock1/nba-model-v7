"""Backfill / update ESPN player box scores and game results into data/*.parquet.
Usage: python -m v7.ingest 2025-10-21 2026-11-19"""
import sys, datetime as dt, os, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from . import espn
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def run(start, end):
    gpath, ppath = f"{DATA}/games.parquet", f"{DATA}/players.parquet"
    G = pd.read_parquet(gpath) if os.path.exists(gpath) else pd.DataFrame()
    P = pd.read_parquet(ppath) if os.path.exists(ppath) else pd.DataFrame()
    have = set(P.event) if len(P) else set()
    d = dt.date.fromisoformat(start); end = dt.date.fromisoformat(end)
    games = []
    while d <= end:
        for g in espn.scoreboard(d.strftime("%Y%m%d")):
            g["date"] = d.isoformat(); games.append(g)
        d += dt.timedelta(days=1)
    games = [g for g in games if g["season_type"] == 2]  # regular season only
    new = pd.DataFrame(games)
    if len(new):
        G = pd.concat([G[~G.event.isin(new.event)] if len(G) else G, new], ignore_index=True)
    todo = [g["event"] for g in games if g["status"] == "STATUS_FINAL" and g["event"] not in have]
    def safe(ev):
        try:
            return espn.boxscore(ev)
        except Exception as e:
            print(f"box {ev} failed: {e}"); return []
    with ThreadPoolExecutor(6) as ex:
        rows = [r for rs in ex.map(safe, todo) for r in rs]
    if rows:
        P = pd.concat([P, pd.DataFrame(rows)], ignore_index=True)
    os.makedirs(DATA, exist_ok=True)
    G.to_parquet(gpath, index=False); P.to_parquet(ppath, index=False)
    print(f"games {len(G)} | player rows {len(P)} | new boxes {len(todo)}")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
