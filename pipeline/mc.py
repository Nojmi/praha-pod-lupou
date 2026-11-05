"""Městské části: hranice (IPR Praha), sčítání 2021 (ČSÚ) a kriminalita na obyvatele → data/data8.json.
Přidá D['mc'] (seznam 57 městských částí s hranicí v metrech a statistikami) a vrstvu mřížky 'mc' (index městské části, 255 = mimo).
Spouštět z adresáře pipeline/. Vyžaduje: pyshp pyproj shapely numpy pandas.
Vstupy: ../data/mestske_casti/mc.* (Shapefile S-JTSK, IPR Praha, otevřená data), ../data/sldb2021_mestske_casti.csv (výběr z otevřených dat SLDB 2021),
../data/kriminalita_praha_bunky_mesice.csv (Policie ČR)."""
import json,math,base64,csv,numpy as np,pandas as pd,shapefile,shapely
from pyproj import Transformer
from shapely.geometry import Polygon,MultiPolygon
C=math.cos(math.radians(50.08))
def P(lon,lat):return((lon-14.42)*C*111320,(lat-50.08)*110574)
tr=Transformer.from_crs(5514,4326,always_xy=True)
sf=shapefile.Reader('../data/mestske_casti/mc',encoding='utf-8')
geo={}
for sr in sf.shapeRecords():
    rec=sr.record.as_dict();g=sr.shape;pts=g.points;parts=list(g.parts)+[len(pts)];ps=[]
    for i in range(len(parts)-1):
        ring=[P(*tr.transform(x,y)) for x,y in pts[parts[i]:parts[i+1]]];p=Polygon(ring)
        ps.append(p if p.is_valid else p.buffer(0))
    gm=ps[0]
    for p in ps[1:]:gm=gm.symmetric_difference(p)
    geo[str(rec['KOD_MC'])]=gm
st={r['kod_mc']:r for r in csv.DictReader(open('../data/sldb2021_mestske_casti.csv',encoding='utf-8'))}
assert set(st)==set(geo),'kódy městských částí nesedí'
keys=sorted(geo,key=lambda k:st[k]['nazev'])
# kriminalita (stejné váhy a měsíce jako crime.py)
W_CLS={'Násilná':3.0,'Krádeže vloupáním':2.0,'Krádeže':1.0,'Podvody':0.5}
d=pd.read_csv('../data/kriminalita_praha_bunky_mesice.csv');d=d[(d.month>=202511)&(d.month<=202609)&d['class'].isin(W_CLS)].copy()
d['w']=d['count']*d['class'].map(W_CLS);g=d.groupby(['lon','lat'],as_index=False).agg(w=('w','sum'),n=('count','sum'))
gx=(g.lon.values-14.42)*C*111320;gy=(g.lat.values-50.08)*110574
D=json.load(open('../data/data8.json'));G=D['grid'];W,H,x0,y0,CELL=G['w'],G['h'],G['x0'],G['y0'],G['cell']
cx=x0+(np.arange(W)+.5)*CELL;cy=y0+(np.arange(H)+.5)*CELL;GX,GY=np.meshgrid(cx,cy)
idx=np.full((H,W),255,np.uint8);mcs=[];tot_k=0
for i,k in enumerate(keys):
    gm=geo[k];m=shapely.contains_xy(gm,GX.ravel(),GY.ravel()).reshape(H,W);idx[m&(idx==255)]=i
    inside=shapely.contains_xy(gm,gx,gy);kw=float(g.w.values[inside].sum());kn=int(g.n.values[inside].sum());tot_k+=kn
    s=st[k];sg=gm.simplify(6)
    polys=[sg] if isinstance(sg,Polygon) else list(sg.geoms)
    rings=[[int(round(v)) for xy in r.coords for v in xy] for p in polys for r in [p.exterior]+list(p.interiors)]
    pop=int(s['obyvatele'])
    mcs.append(dict(k=k,n=s['nazev'],pop=pop,d14=int(s['vek_0_14']),d65=int(s['vek_65_plus']),st=float(s['prumerne_stari_domu']),rd=int(s['rodinne_domy']),bd=int(s['bytove_domy']),od=int(s['ostatni_budovy']),km2=round(gm.area/1e6,2),kw=round(kw,1),kn=kn,r=rings))
print('MČ',len(mcs),'obyvatel',sum(m['pop'] for m in mcs),'trestných činů v MČ',tot_k,'z',int(g.n.sum()))
print('mřížka mimo MČ (uvnitř walk):',int(((idx==255)&(np.frombuffer(base64.b64decode(G['layers']['walk']),np.uint8).reshape(H,W)!=255)).sum()))
G['layers']['mc']=base64.b64encode(idx.tobytes()).decode();D['mc']=mcs
json.dump(D,open('../data/data8.json','w'),separators=(',',':'),ensure_ascii=False)
for m in sorted(mcs,key=lambda m:-m['kw']/m['pop'])[:5]:print(m['n'],round(m['kw']/m['pop']*1000),'váž. činů/1000 obyv.')
