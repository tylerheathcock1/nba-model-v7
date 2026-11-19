import sys,numpy as np,pandas as pd,warnings;warnings.filterwarnings('ignore')
HL=float(sys.argv[1]) if len(sys.argv)>1 else 90; LAM=float(sys.argv[2]) if len(sys.argv)>2 else 20; A=float(sys.argv[3]) if len(sys.argv)>3 else 0.35
OUT=sys.argv[4] if len(sys.argv)>4 else 'work/pred.parquet'
P=pd.read_parquet('work/P.parquet'); G=pd.read_parquet('work/G.parquet').sort_values('date').reset_index(drop=True)
P=P.merge(G[['gid']].reset_index().rename(columns={'index':'gi'}),on='gid')
pid_codes,pid_idx=np.unique(P.personId,return_inverse=True); P['pi']=pid_idx; NP=len(pid_codes)
teams=sorted(set(G.h)|set(G.a)); tix={t:i for i,t in enumerate(teams)}
G['hi']=G.h.map(tix); G['ai']=G.a.map(tix)
gdate=G.date.values; P['sgn']=np.where(P.home,1.0,-1.0)
out=[]
for s in sorted(G.season.unique()):
    if s==2010: continue
    gs=G[G.season==s]; d0=gs.date.min(); d1=gs.date.max()
    for start in pd.date_range(d0,d1,freq='7D'):
        end=start+pd.Timedelta(days=7)
        hist=G[(G.date<start)&(G.date>=start-pd.Timedelta(days=500))]
        age=(start-hist.date).dt.days.values; w=0.5**(age/HL)
        gw=pd.Series(w,index=hist.index)
        ph=P[P.gi.isin(hist.index)]
        pw=gw.reindex(ph.gi).values
        # box prior
        agg=pd.DataFrame({'pi':ph.pi.values,'wm':ph['min'].values*pw,'wg':ph.gmsc.values*pw}).groupby('pi').sum()
        g48=agg.wg/agg.wm*48; lg=(agg.wg.sum()/agg.wm.sum())*48
        m=agg.wm; shr=m/(m+300)
        r0=pd.Series(-2.0,index=range(NP)); r0.loc[agg.index]=A*(g48-lg)*shr+(-2.0)*(1-shr)
        # RAPM ridge toward prior, players active in window
        act=agg.index.values; col={p:i for i,p in enumerate(act)}; k=len(act)
        rows=hist.index.values; rpos={g:i for i,g in enumerate(rows)}
        X=np.zeros((len(rows),k+1)); X[:,k]=1.0
        ri=ph.gi.map(rpos).values; ci=ph.pi.map(col).values
        np.add.at(X,(ri,ci),ph.sgn.values*ph['min'].values/48)
        y=hist.margin.values
        prior=np.append(r0.loc[act].values,0.0)
        L=np.full(k+1,LAM); L[k]=1e-6
        XtW=X.T*w
        r=np.linalg.solve(XtW@X+np.diag(L),XtW@y+L*prior)
        rap=r0.copy(); rap.loc[act]=r[:k]; hca=r[k]
        # team ridge baseline
        T=np.zeros((len(rows),len(teams)+1)); T[np.arange(len(rows)),hist.hi.values]=1; T[np.arange(len(rows)),hist.ai.values]=-1; T[:,-1]=1
        Lt=np.full(len(teams)+1,3.0); Lt[-1]=1e-6; TtW=T.T*w
        tr=np.linalg.solve(TtW@T+np.diag(Lt),TtW@y)
        # predict this week's games using players who played + projected minutes
        wk=G[(G.date>=start)&(G.date<end)&(G.season==s)]
        pw_=P[P.gi.isin(wk.index)].copy()
        pw_['pm']=pw_.pmin.fillna(15.0)
        tot=pw_.groupby(['gi','home']).pm.transform('sum'); pw_['pm']=pw_.pm*240/tot
        pw_['rb']=r0.values[pw_.pi.values]; pw_['rr']=rap.values[pw_.pi.values]
        pw_['cb']=pw_.sgn*pw_.pm/48*pw_.rb; pw_['cr']=pw_.sgn*pw_.pm/48*pw_.rr
        sm=pw_.groupby('gi')[['cb','cr']].sum()
        for gi,row in wk.iterrows():
            out.append(dict(gid=row.gid,date=row.date,season=s,h=row.h,a=row.a,margin=row.margin,
                 box=sm.cb.get(gi,np.nan)+hca, rapm=sm.cr.get(gi,np.nan)+hca, team=tr[row.hi]-tr[row.ai]+tr[-1]))
O=pd.DataFrame(out); O.to_parquet(OUT)
print(len(O)); print(O[['box','rapm','team','margin']].describe().round(2))
