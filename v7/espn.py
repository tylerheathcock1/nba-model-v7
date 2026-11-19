"""ESPN public NBA feed: schedule/odds, box scores, injuries."""
import json, re, time, urllib.request
BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

def _get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)

def scoreboard(yyyymmdd):
    """Games on a date: id, tip (UTC), home/away abbreviations, status, DraftKings line (current and open)."""
    d = _get(f"{BASE}/scoreboard?dates={yyyymmdd}")
    out = []
    for e in d.get("events", []):
        c = e["competitions"][0]
        if c.get("type", {}).get("abbreviation") not in (None, "STD", "RS"):  # skip all-star etc.
            pass
        teams = {x["homeAway"]: x for x in c["competitors"]}
        o = (c.get("odds") or [{}])[0]
        ps = o.get("pointSpread", {}) or {}
        tot = o.get("total", {}) or {}
        def _num(x):
            try: return float(str(x).replace("o", "").replace("u", ""))
            except Exception: return None
        out.append(dict(
            event=e["id"], tip=e["date"], status=e["status"]["type"]["name"],
            season_type=e.get("season", {}).get("type"),
            home=teams["home"]["team"]["abbreviation"], away=teams["away"]["team"]["abbreviation"],
            home_score=_num(teams["home"].get("score")), away_score=_num(teams["away"].get("score")),
            book=(o.get("provider") or {}).get("name"),
            spread_home=o.get("spread"), total=o.get("overUnder"),
            spread_home_open=_num((ps.get("home") or {}).get("open", {}).get("line")),
            total_open=_num((tot.get("over") or {}).get("open", {}).get("line")),
        ))
    return out

def _mins(s):
    if not s or s in ("--", "0"): return 0.0
    if ":" in s:
        m, sec = s.split(":"); return float(m) + float(sec) / 60
    return float(s)

def boxscore(event):
    """Player rows for a finished game."""
    d = _get(f"{BASE}/summary?event={event}")
    rows = []
    hdr = d.get("header", {}).get("competitions", [{}])[0]
    ha = {c["team"]["abbreviation"]: c["homeAway"] for c in hdr.get("competitors", [])}
    for tb in d.get("boxscore", {}).get("players", []):
        team = tb["team"]["abbreviation"]
        st = tb["statistics"][0]; lab = st["labels"]
        for a in st["athletes"]:
            if a.get("didNotPlay") or not a.get("stats") or "id" not in a.get("athlete", {}):
                continue
            s = dict(zip(lab, a["stats"]))
            def mk(x):
                m, at = (s.get(x) or "0-0").split("-"); return int(m), int(at)
            fgm, fga = mk("FG"); tpm, tpa = mk("3PT"); ftm, fta = mk("FT")
            n = lambda k: int(str(s.get(k, "0")).replace("+", "") or 0)
            rows.append(dict(event=event, team=team, home=ha.get(team) == "home",
                             pid=int(a["athlete"]["id"]), name=a["athlete"]["displayName"],
                             starter=bool(a.get("starter")), min=_mins(s.get("MIN")),
                             pts=n("PTS"), fgm=fgm, fga=fga, tpm=tpm, tpa=tpa, ftm=ftm, fta=fta,
                             oreb=n("OREB"), dreb=n("DREB"), ast=n("AST"), stl=n("STL"), blk=n("BLK"),
                             tov=n("TO"), pf=n("PF"), pm=n("+/-")))
    return rows

def injuries():
    """Current league injury list: team, player id, name, status (Out / Day-To-Day ...), fantasy tag (OUT/GTD), note."""
    d = _get(f"{BASE}/injuries")
    out = []
    for t in d.get("injuries", []):
        for i in t.get("injuries", []):
            a = i.get("athlete", {})
            m = re.search(r"/id/(\d+)", ((a.get("links") or [{}])[0]).get("href", ""))
            out.append(dict(team_name=t.get("displayName"), pid=int(m.group(1)) if m else None, updated=i.get("date"),
                            name=a.get("displayName"), status=i.get("status"),
                            tag=(i.get("details", {}).get("fantasyStatus") or {}).get("abbreviation"),
                            note=i.get("shortComment")))
    return out
