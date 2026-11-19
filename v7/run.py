"""Daily v7 run. Usage: python -m v7.run morning|pretip [YYYY-MM-DD]
1. Pull finished games into data/ (box scores) and grade earlier Pick Log rows (close, result, CLV, line move).
2. Project today's slate and log one Pick Log row per game for this run.
3. Write sheet-ready CSVs to data/out/ and print a short summary (first tip time, leans, scorecard)."""
import sys, os, datetime as dt, numpy as np, pandas as pd
from zoneinfo import ZoneInfo
from . import espn, ingest, slate
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = f"{DATA}/out"; LOG = f"{DATA}/picklog.csv"
PHX = ZoneInfo("America/Phoenix")

def grade(log):
    todo = log[log.result.isna() | (log.result == "")]
    cache = {}
    for i, row in todo.iterrows():
        ev = str(row.event)
        if ev not in cache:
            try: cache[ev] = espn.closing(ev)
            except Exception: cache[ev] = None
        c = cache[ev]
        if not c or not c["final"] or c["close_spread_home"] is None:
            continue
        line, close, model = row.dk_spread_home, c["close_spread_home"], row.model_spread_home
        margin = c["home_score"] - c["away_score"]
        log.at[i, "close_spread_home"] = close; log.at[i, "home_margin"] = margin
        # did the line move toward the model between this run and the close?
        mv = close - line
        log.at[i, "line_move"] = mv
        log.at[i, "moved_toward_model"] = "" if mv == 0 or model == line else ("Y" if np.sign(mv) == np.sign(model - line) else "N")
        if row.lean_side in ("home", "away"):
            home = row.lean_side == "home"
            ats = margin + line if home else -(margin + line)
            log.at[i, "result"] = "W" if ats > 0 else ("L" if ats < 0 else "P")
            log.at[i, "clv_pts"] = (line - close) if home else (close - line)
        else:
            log.at[i, "result"] = "-"
    return log

def scorecard(log):
    g = log[log.close_spread_home.notna()].copy()
    rows = []
    for run in ["morning", "pretip", "all"]:
        x = g if run == "all" else g[g.run == run]
        if not len(x): continue
        gap = x.model_spread_home - x.dk_spread_home; mv = x.close_spread_home - x.dk_spread_home
        beta = float((gap * mv).sum() / (gap * gap).sum()) if (gap * gap).sum() else np.nan
        tw = x[x.moved_toward_model.isin(["Y", "N"])]
        leans = x[x.lean_side.isin(["home", "away"])]
        w = (leans.result == "W").sum(); l = (leans.result == "L").sum()
        rows.append(dict(run=run, games_graded=len(x), line_moved_toward_model=f"{(tw.moved_toward_model == 'Y').mean():.1%}" if len(tw) else "-",
                         moves_counted=len(tw), beta_move_on_gap=round(beta, 3),
                         leans=len(leans), lean_record=f"{w}-{l}", lean_avg_clv=round(leans.clv_pts.astype(float).mean(), 2) if len(leans) else None))
    return pd.DataFrame(rows)

def main(run, day):
    os.makedirs(OUT, exist_ok=True)
    d = dt.date.fromisoformat(day)
    ingest.run((d - dt.timedelta(days=3)).isoformat(), day)
    log = pd.read_csv(LOG, dtype={"event": str}) if os.path.exists(LOG) else pd.DataFrame()
    S, D = slate.run(day)
    games = {g["home"]: g for g in espn.scoreboard(day.replace("-", ""))}
    now = dt.datetime.now(PHX).strftime("%Y-%m-%d %H:%M")
    new = []
    for s in S.itertuples():
        g = games.get(s.home, {})
        if g.get("status") != "STATUS_SCHEDULED" or s.dk_spread_home is None or pd.isna(s.dk_spread_home):
            continue
        side = "" if not s.lean else ("home" if s.lean.startswith(s.home + " ") else "away")
        new.append(dict(date=day, run=run, logged_phx=now, event=str(g["event"]), away=s.away, home=s.home,
                        tip_phx=pd.Timestamp(s.tip_utc).tz_convert(PHX).strftime("%H:%M"),
                        dk_open_home=s.dk_open_home, dk_spread_home=s.dk_spread_home, model_spread_home=s.model_spread_home,
                        gap=round(s.model_spread_home - s.dk_spread_home, 1), injury_swing_home=s.injury_swing_home,
                        lean=s.lean, lean_side=side, close_spread_home=np.nan, line_move=np.nan, moved_toward_model="",
                        home_margin=np.nan, result="", clv_pts=np.nan))
    log = pd.concat([log, pd.DataFrame(new)], ignore_index=True) if new else log
    if len(log): log = grade(log)
    log.to_csv(LOG, index=False)
    sc = scorecard(log) if len(log) else pd.DataFrame()
    # sheet-ready outputs
    S.to_csv(f"{OUT}/slate.csv", index=False)
    D[D.proj_min > 0].sort_values(["team", "proj_min"], ascending=[True, False]).to_csv(f"{OUT}/players.csv", index=False)
    cutoff = (d - dt.timedelta(days=14)).isoformat()
    log[log.date >= cutoff].sort_values(["date", "logged_phx"], ascending=False).to_csv(f"{OUT}/picklog_recent.csv", index=False)
    sc.to_csv(f"{OUT}/scorecard.csv", index=False)
    tips = [pd.Timestamp(g["tip"]) for g in games.values() if g.get("status") == "STATUS_SCHEDULED"]
    first = min(tips).tz_convert(PHX) if tips else None
    print(f"RUN {run} {day} at {now} PHX | games logged {len(new)}")
    print(f"FIRST_TIP_PHX {first.isoformat() if first is not None else 'none'}")
    print(f"PRETIP_RUN_PHX {(first - pd.Timedelta(hours=1)).isoformat() if first is not None else 'none'}")
    print(S[["away", "home", "dk_spread_home", "model_spread_home", "gap_vs_market", "lean"]].to_string(index=False))
    print(sc.to_string(index=False))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else dt.datetime.now(PHX).date().isoformat())
