"""Model v7 settings. Values marked (backtest) were chosen on 2011-19 only; 2021-24 was held out."""
HL = 150            # recency half-life in days (backtest)
LAM = 30            # ridge strength pulling player ratings toward the box-score prior (backtest)
A = 0.8             # scale of the box-score prior (backtest)
PRIOR_MIN = 300     # minutes before a player's own box score outweighs replacement level
REPLACEMENT = -2.0  # rating (pts per 48) for players with little or no NBA history
WINDOW_DAYS = 500   # history used for each fit
GTD_SHARE = 0.5     # share of projected minutes kept for a questionable (GTD) player
MARKET_WEIGHT = 0.9 # final line = market + (1 - weight) x (model - market) (backtest)
EDGE_PTS = 2.0      # flag a play when the blended edge clears this many points vs the current line
