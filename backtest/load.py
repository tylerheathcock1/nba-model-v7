import sqlite3, pandas as pd, numpy as np, sys
DB=sys.argv[1] if len(sys.argv)>1 else None
def load(db):
    c=sqlite3.connect(db)
    tabs=[f'odds_{y}-{str(y+1)[2:]}_new' for y in range(2007,2023)]+['2023-24','2024-25','odds_2025-26']
    rs_end={2007:'2008-04-16',2008:'2009-04-16',2009:'2010-04-14',2010:'2011-04-13',2011:'2012-04-26',2012:'2013-04-17',
            2013:'2014-04-16',2014:'2015-04-15',2015:'2016-04-13',2016:'2017-04-12',2017:'2018-04-11',2018:'2019-04-10',
            2019:'2020-03-11',2020:'2021-05-16',2021:'2022-04-10',2022:'2023-04-09',2023:'2024-04-14',2024:'2025-04-13',2025:'2026-04-12'}
    out=[]
    for t in tabs:
        y=int(t.replace('odds_','')[:4]); d=pd.read_sql(f'select Date,Home,Away,Spread,ML_Home,ML_Away,Win_Margin,Days_Rest_Home,Days_Rest_Away from "{t}"',c)
        d['Date']=pd.to_datetime(d.Date); d=d[d.Date<=rs_end[y]].copy(); d['season']=y
        # home line (negative = home favored), sign from ML when spread stored unsigned
        for col in ['Spread','ML_Home','ML_Away','Win_Margin','Days_Rest_Home','Days_Rest_Away']: d[col]=pd.to_numeric(d[col],errors='coerce')
        d=d.dropna(subset=['Spread','Win_Margin','Days_Rest_Home','Days_Rest_Away'])
        homefav=d.ML_Home<d.ML_Away
        s=d.Spread.abs()
        d['home_line']=np.where(homefav,-s,s)
        out.append(d)
    d=pd.concat(out,ignore_index=True)
    d['ats']=d.Win_Margin+d.home_line   # >0 home covers
    return d

def load_clean(db):
    c=sqlite3.connect(db)
    d=load(db)
    # attach OU/Points for second check
    tabs=[f'odds_{y}-{str(y+1)[2:]}_new' for y in range(2007,2023)]+['2023-24','2024-25','odds_2025-26']
    ou=pd.concat([pd.read_sql(f'select Date,Home,OU,Points from "{t}"',c) for t in tabs]); ou['Date']=pd.to_datetime(ou.Date)
    for col in ['OU','Points']: ou[col]=pd.to_numeric(ou[col],errors='coerce')
    d=d.merge(ou.drop_duplicates(['Date','Home']),on=['Date','Home'],how='left')
    d['ym']=d.Date.dt.to_period('M')
    q=d.groupby('ym').apply(lambda g: pd.Series({'n':len(g),'sc':np.corrcoef(g.Win_Margin,-g.home_line)[0,1],'tc':np.corrcoef(g.OU.fillna(g.OU.mean()),g.Points)[0,1]}))
    bad=q[(q.sc<0.2)|(q.tc<0.15)].index
    return d[~d.ym.isin(bad)].copy(), q, list(bad)
