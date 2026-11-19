import sys;sys.path.insert(0,'work');import load,numpy as np,pandas as pd,warnings;warnings.filterwarnings('ignore')
PRED=sys.argv[1] if len(sys.argv)>1 else 'work/pred.parquet'; QUIET=len(sys.argv)>2
O=pd.read_parquet(PRED)
t=pd.read_csv('ext2/regular_season_totals_2010_2024.csv',usecols=['TEAM_ABBREVIATION','TEAM_NAME']).drop_duplicates()
def key(n):
    n=n.replace('Los Angeles Clippers','LA Clippers')
    for a_,b in [('Charlotte','CHA'),('New Orleans','NOP'),('Nets','BKN')]:
        if a_ in n: return b
    return n
ab2k={r.TEAM_ABBREVIATION:key(r.TEAM_NAME) for r in t.itertuples()}
d,q,bad=load.load_clean('ext/Data/OddsData.sqlite'); d['hk']=d.Home.map(key)
O['hk']=O.h.map(ab2k)
M=O.merge(d[['Date','hk','home_line','OU']],left_on=['date','hk'],right_on=['Date','hk'])
M['close']=-M.home_line   # predicted home margin from market
M=M.dropna(subset=['box','rapm','team','close'])
tr=M[(M.season>=2011)&(M.season<=2018)]; ho=M[M.season>=2021]
def rmse(x,y): return np.sqrt(((x-y)**2).mean())
res={}
for nm,dd in [('TRAIN 2011-19',tr),('HOLDOUT 2021-24',ho)]:
    r={c:rmse(dd[c],dd.margin) for c in ['close','team','box','rapm']}
    res[nm]=r
    if not QUIET: print(nm,len(dd),' RMSE:',{k:round(v,3) for k,v in r.items()})
# info beyond close: fit blend weight on train, apply to holdout
out={}
for c in ['team','box','rapm']:
    x=(tr[c]-tr.close).values; y=(tr.margin-tr.close).values; b=(x@y)/(x@x)
    xh=(ho[c]-ho.close).values; yh=(ho.margin-ho.close).values; bh=(xh@yh)/(xh@xh); se=np.sqrt(((yh-bh*xh)**2).mean()/(xh@xh))
    blend=ho.close+b*(ho[c]-ho.close)
    out[c]=(b,bh,bh/se,rmse(blend,ho.margin)-rmse(ho.close,ho.margin))
    if not QUIET:
        print(f'{c:5s} weight vs close: train {b:+.3f} | holdout {bh:+.3f} (t={bh/se:+.2f}) | holdout RMSE change from blending {out[c][3]:+.4f}')
        for th in [2,3,4]:
            e=ho[c]-ho.close; sel=e.abs()>=th; res_=np.sign(e[sel])*(ho.margin[sel]-ho.close[sel]); w=(res_>0).sum(); l=(res_<0).sum()
            print(f'      holdout ATS when |{c}-close|>={th}: {w}-{l} {w/max(w+l,1):.1%}')
if QUIET: print(' '.join(f"{k}:tr_b={v[0]:+.3f},ho_b={v[1]:+.3f},t={v[2]:+.2f}" for k,v in out.items()), {k:round(v,3) for k,v in res['TRAIN 2011-19'].items()})
M.to_parquet('work/M.parquet')
