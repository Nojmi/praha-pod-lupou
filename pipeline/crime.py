"""Kriminalita jako vrstva 'krim' (percentil 0-100, vyšší = horší) do data/data8.json.
Zdroj: Policie ČR, kriminalita.policie.gov.cz (měsíční GeoJSON, souřadnice záměrně zkreslené, Voroného buňky).
Vstup: data/kriminalita_praha_bunky_mesice.csv (lon,lat,month,class,count), měsíce 202511-202609 (poslední měsíc je neúplný)."""
import json,math,base64,numpy as np,pandas as pd
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter
W_CLS={'Násilná':3.0,'Krádeže vloupáním':2.0,'Krádeže':1.0,'Podvody':0.5}
M0,M1=202511,202609
d=pd.read_csv('../data/kriminalita_praha_bunky_mesice.csv')
d=d[(d.month>=M0)&(d.month<=M1)&d['class'].isin(W_CLS)].copy();d['w']=d['count']*d['class'].map(W_CLS)
c=math.cos(math.radians(50.08));P=lambda lon,lat:np.c_[(lon-14.42)*c*111320,(lat-50.08)*110574]
g=d.groupby(['lon','lat'],as_index=False).agg(w=('w','sum'),n=('count','sum'))
pts=P(g.lon.values,g.lat.values);tree=cKDTree(pts)
print('bodů',len(g),'záznamů',int(g.n.sum()))
# plocha Voroného buněk: mřížka 200 m přes celé okolí
xs=np.arange(pts[:,0].min()-1500,pts[:,0].max()+1500,200);ys=np.arange(pts[:,1].min()-1500,pts[:,1].max()+1500,200)
GX,GY=np.meshgrid(xs,ys);_,idx=tree.query(np.c_[GX.ravel(),GY.ravel()])
area=np.bincount(idx,minlength=len(g))*0.04  # km2
dens=g.w.values/np.maximum(area,0.02)
D=json.load(open('../data/data8.json'));G=D['grid'];W,H,x0,y0,CELL=G['w'],G['h'],G['x0'],G['y0'],G['cell']
L={k:np.frombuffer(base64.b64decode(v),dtype=np.uint8).reshape(H,W) for k,v in G['layers'].items()}
inside=L['walk']!=255
cx=x0+(np.arange(W)+.5)*CELL;cy=y0+(np.arange(H)+.5)*CELL;GXg,GYg=np.meshgrid(cx,cy)
_,ig=tree.query(np.c_[GXg.ravel(),GYg.ravel()]);val=dens[ig].reshape(H,W)
m=inside.astype(float);num=gaussian_filter(val*m,4);den=gaussian_filter(m,4)
sm=np.where(den>0.05,num/np.maximum(den,1e-9),0)
vals=sm[inside];order=vals.argsort().argsort();pct=np.zeros(H*W);pct_in=np.round(100*order/(len(vals)-1))
out=np.full((H,W),255,np.uint8);out[inside]=pct_in.astype(np.uint8)
L['krim']=out
G['layers']={k:base64.b64encode(v.tobytes()).decode() for k,v in L.items()}
json.dump(D,open('../data/data8.json','w'),separators=(',',':'),ensure_ascii=False)
print('hustota (vážené incidenty/km2) medián',np.median(sm[inside]),'p90',np.percentile(sm[inside],90),'max',sm[inside].max())
