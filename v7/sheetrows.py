"""Print sheet-ready JSON (2-D arrays) for one tab from data/out/. Usage: python -m v7.sheetrows slate|scorecard|picklog|players"""
import sys, os, json, pandas as pd, datetime as dt
from zoneinfo import ZoneInfo
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "out")
SPEC = {
    "slate": ("slate.csv", "Slate: latest run. Spreads are HOME side (negative = home favored). gap = v7 minus DraftKings (pts)."),
    "scorecard": ("scorecard.csv", "Scorecard: moved toward model = share of games where the line moved toward v7 between the run and the close. beta: 1 = moved all the way, 0 = no relation."),
    "picklog": ("picklog_recent.csv", "Pick Log: last 14 days, one row per game per run (full log: data/picklog.csv in the repo). Leans are 0u."),
    "players": ("players.csv", "Players: tonight's projected minutes and ratings. rating = pts per 48 vs average; pts_tonight = rating x proj_min / 48."),
}
tab = sys.argv[1]; f, title = SPEC[tab]
path = os.path.join(OUT, f)
df = pd.read_csv(path) if os.path.exists(path) and os.path.getsize(path) > 1 else pd.DataFrame({"status": ["nothing graded yet"]})
df = df.astype(object).where(df.notna(), "")
stamp = dt.datetime.now(ZoneInfo("America/Phoenix")).strftime("%Y-%m-%d %H:%M Phoenix")
rows = [[f"{title}  (updated {stamp})"], list(df.columns)] + df.values.tolist()
print(json.dumps(rows, default=str))
