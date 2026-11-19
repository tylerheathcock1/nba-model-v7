# NBA Model v7

Player-based NBA spread model: player impact ratings × projected minutes, adjusted for the injury report, blended toward the market line. Judged on closing-line value, not win-loss.

## Pieces
- `v7/espn.py`: ESPN public feed (schedule, DraftKings open/current lines, box scores, injuries)
- `v7/ingest.py`: backfill/update player box scores into `data/`
- `v7/ratings.py`: ridge-regression player ratings shrunk toward a box-score prior
- `v7/slate.py`: tonight's projections and leans
- `v7/config.py`: settings (chosen on 2011-19 backtest; 2021-24 held out)

Work in progress: settings and the market blend are still being tuned.

## Daily operation
A scheduled Claude session runs at 7:30 AM Phoenix and again one hour before the first tip, following `RUNBOOK.md`.
Results go to the NBA_Model_v7 Google Sheet; the full pick log is `data/picklog.csv`.
