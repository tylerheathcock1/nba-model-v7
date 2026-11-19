# Build tidy player-game and game tables from public box scores (2010-11..2023-24)
import pandas as pd,numpy as np
p=pd.concat([pd.read_csv(f'ext2/regular_season_box_scores_2010_2024_part_{i}.csv',dtype={'gameId':str}) for i in (1,2,3)])
mm=p.minutes.fillna('0:00').astype(str)
p['min']=mm.str.split(':').str[0].astype(float)+mm.str.split(':').str[1].fillna('0').astype(float)/60
p=p[p['min']>0].copy()
p['date']=pd.to_datetime(p.game_date); p['season']=p.season_year.str[:4].astype(int)
p['home']=~p.matchup.str.contains('@')
p['gid']=p.gameId.str.zfill(10)
g=p.groupby(['gid','home']).agg(date=('date','first'),season=('season','first'),team=('teamTricode','first'),teamName=('teamCity','first'),pts=('points','sum')).reset_index()
gh=g[g.home].drop(columns='home').rename(columns={'team':'h','teamName':'hcity','pts':'hpts'})
ga=g[~g.home][['gid','team','teamCity' if False else 'teamName','pts']].rename(columns={'team':'a','teamName':'acity','pts':'apts'})
G=gh.merge(ga,on='gid'); G['margin']=G.hpts-G.apts
# GmSc per player-game
p['gmsc']=p.points+0.4*p.fieldGoalsMade-0.7*p.fieldGoalsAttempted-0.4*(p.freeThrowsAttempted-p.freeThrowsMade)+0.7*p.reboundsOffensive+0.3*p.reboundsDefensive+p.steals+0.7*p.assists+0.7*p.blocks-0.4*p.foulsPersonal-p.turnovers
p=p.sort_values(['personId','date'])
# projected minutes before each game: EWMA of prior appearances (halflife 5 games)
p['pmin']=p.groupby('personId')['min'].transform(lambda s: s.ewm(halflife=5).mean().shift(1))
P=p[['gid','date','season','personId','personName','teamTricode','home','min','pmin','gmsc','plusMinusPoints']].rename(columns={'teamTricode':'team','plusMinusPoints':'pm'})
P.to_parquet('work/P.parquet'); G.to_parquet('work/G.parquet')
print(P.shape,G.shape,G.season.value_counts().sort_index().to_dict())
print('home margin mean',G.margin.mean().round(2))
