"""Model v7 settings. Values marked (backtest) were chosen on 2011-19 only; 2021-24 was held out."""
HL = 300            # recency half-life in days (backtest)
LAM = 30            # ridge strength pulling player ratings toward the box-score prior (backtest)
A = 0.35            # scale of the box-score prior (backtest)
PRIOR_MIN = 300     # minutes before a player's own box score outweighs replacement level
REPLACEMENT = -2.0  # rating (pts per 48) for players with little or no NBA history
WINDOW_DAYS = 500   # history used for each fit
GTD_SHARE = 0.5     # share of projected minutes kept for a questionable (GTD) player
MARKET_WEIGHT = 0.9 # final line = market + (1 - weight) x (model - market). Holdout weight on model vs CLOSE was 0.12 and fell each season (0.35, 0.15, -0.09)
EDGE_PTS = 3.0      # flag a lean (0u tracking) when model and market differ by this many points
