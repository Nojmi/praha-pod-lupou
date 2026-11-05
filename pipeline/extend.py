"""Doplní data7.json o vrstvy z amen2.pkl (sr, vs, hriste, sport, cyklo, nové zs) -> data8.json."""
import json,math,base64,pickle,numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString,Polygon
D=json.load(open('../data/data7.json'));pois,cyc,lane=pickle.load(open('amen2.pkl','rb'))
G=D['grid'];W,H,x0,y0,CELL=G['w'],G['h'],G['x0'],G['y0'],G['cell']
L={k:np.frombuffer(base64.b64decode(v),dtype=np.uint8).reshape(H,W) for k,v in G['layers'].items()}
inside=L['walk']!=255
cx=x0+(np.arange(W)+.5)*CELL;cy=y0+(np.arange(H)+.5)*CELL;GX,GY=np.meshgrid(cx,cy);pts=np.c_[GX.ravel(),GY.ravel()]
osm_y0=(49.963-50.080)*110574;osm_y1=(50.145-50.080)*110574;osmok=(GY>osm_y0)&(GY<osm_y1)
def mins(d):return np.minimum(d*1.3/80,60)
def enc(a):return np.where(inside&osmok,np.round(a),255).astype(np.uint8)
POI=D['poi']
for k in('zs','sr','vs','hriste','sport'):
    seen=set();Lp=[]
    for x,y,nm in pois.get(k,[]):
        key=(round(x/30),round(y/30),nm)
        if key in seen:continue
        seen.add(key);Lp.append([int(round(x)),int(round(y)),nm])
    POI[k]=Lp;A=np.array([[p[0],p[1]] for p in Lp]);d,_=cKDTree(A).query(pts)
    L[k]=enc(mins(d).reshape(H,W))
ring=Polygon(D['ring']).buffer(300)
S=[];
def sample(lines):
    for pl in lines:
        ls=LineString(pl)
        n=max(1,int(ls.length//25))
        for i in range(n+1):
            p=ls.interpolate(min(ls.length,i*25));S.append((p.x,p.y))
sample(cyc);sample(lane)
d,_=cKDTree(np.array(S)).query(pts);L['cyklo']=enc(mins(d).reshape(H,W))
def clip(lines):
    out=[]
    for pl in lines:
        ls=LineString(pl).simplify(3)
        g=ls.intersection(ring)
        if g.is_empty:continue
        for s in ([g] if g.geom_type=='LineString' else [z for z in getattr(g,'geoms',[]) if z.geom_type=='LineString']):
            if s.length<15:continue
            out.append([int(round(v)) for p in s.coords for v in p])
    return out
D['cyc']={'stezka':clip(cyc),'pruh':clip(lane)}
G['layers']={k:base64.b64encode(v.tobytes()).decode() for k,v in L.items()}
s=json.dumps(D,separators=(',',':'),ensure_ascii=False);open('../data/data8.json','w').write(s);print(len(s)//1024,'KB',{k:len(v) for k,v in D['cyc'].items()})
for k in('zs','sr','vs','hriste','sport','cyklo'):
    v=L[k][L[k]!=255];print(k,'median',np.median(v),'p90',np.percentile(v,90))
