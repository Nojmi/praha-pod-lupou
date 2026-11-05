import json,math,pickle,base64,collections,numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
from PIL import Image,ImageDraw
from shapely.geometry import Polygon
D=json.load(open('data3.json'));pois,green=pickle.load(open('amen.pkl','rb'));cnt=pickle.load(open('freq.pkl','rb'))
ring=Polygon(D['ring']);xs=[p[0] for p in D['ring']];ys=[p[1] for p in D['ring']]
CELL=100;x0=math.floor(min(xs)/CELL)*CELL;y0=math.floor(min(ys)/CELL)*CELL
W=math.ceil((max(xs)-x0)/CELL);H=math.ceil((max(ys)-y0)/CELL);print('grid',W,H)
cx=x0+(np.arange(W)+.5)*CELL;cy=y0+(np.arange(H)+.5)*CELL
GX,GY=np.meshgrid(cx,cy)  # [H,W]
pts=np.c_[GX.ravel(),GY.ravel()]
from shapely import contains_xy
inside=contains_xy(ring,pts[:,0],pts[:,1]).reshape(H,W);print('cells in Prague',inside.sum(),'area km2',inside.sum()*CELL*CELL/1e6)
# OSM data bbox (lat 49.963..50.145, lon 14.086..14.757)
c=math.cos(math.radians(50.08))
osm_y0=(49.963-50.080)*110574;osm_y1=(50.145-50.080)*110574
osmok=(GY>osm_y0)&(GY<osm_y1)
DET=1.3;SP=80.0
def mins(d):return np.minimum(d*DET/SP,60)
def enc(a,null):
    a=a.copy();a=np.where(inside&null,a,255) if null is not None else np.where(inside,a,255)
    return a.astype(np.uint8)
nodes=D['nodes']
N=np.array([[n[0],n[1]] for n in nodes]);mask=np.array([n[3] for n in nodes])
out={}
d,_=cKDTree(N).query(pts);out['walk']=enc(np.round(mins(d)).reshape(H,W),None)
R=N[(mask&(4|8))>0];d,_=cKDTree(R).query(pts);out['rapid']=enc(np.round(mins(d)).reshape(H,W),None)
# frekvence
nr=collections.defaultdict(dict)
for (n,r),v in cnt.items():nr[n][r]=v/12.0
tree=cKDTree(N);rad=SP*5/DET
res=np.zeros(len(pts))
ball=tree.query_ball_point(pts,rad)
for i,b in enumerate(ball):
    best={}
    for n in b:
        for r,v in nr.get(n,{}).items():
            if v>best.get(r,0):best[r]=v
    res[i]=sum(best.values())
out['freq']=enc(np.round(np.minimum(res,250)).reshape(H,W),None)
# POI
POI={}
for k,v in pois.items():
    seen=set();L=[]
    for x,y,nm in v:
        key=(round(x/30),round(y/30),nm)
        if key in seen:continue
        seen.add(key);L.append([int(round(x)),int(round(y)),nm])
    POI[k]=L
    A=np.array([[p[0],p[1]] for p in L]);d,_=cKDTree(A).query(pts)
    out[k]=enc(np.round(mins(d)).reshape(H,W),osmok)
print({k:len(v) for k,v in POI.items()})
# zeleň: raster 20 m
RS=20;rw=int(W*CELL/RS);rh=int(H*CELL/RS)
im=Image.new('L',(rw,rh),0);dr=ImageDraw.Draw(im)
GP=[]
def tr(pt):return ((pt[0]-x0)/RS,(rh-(pt[1]-y0)/RS))
for rings,kind in green:
    for outer,inner in rings:
        if len(outer)<3:continue
        try:p=Polygon(outer)
        except Exception:continue
        if not p.is_valid:p=p.buffer(0)
        a=p.area
        if a<4000 or p.is_empty:continue
        dr.polygon([tr(q) for q in outer],fill=1)
        for h in inner:
            if len(h)>=3:dr.polygon([tr(q) for q in h],fill=0)
        q=p.intersection(ring.buffer(300))
        if q.is_empty:continue
        for g in ([q] if q.geom_type=='Polygon' else [z for z in q.geoms if z.geom_type=='Polygon']):
            g=g.simplify(5)
            if g.is_empty or g.area<4000:continue
            GP.append([[int(round(v)) for pt in g.exterior.coords for v in pt]]+[[int(round(v)) for pt in hh.coords for v in pt] for hh in g.interiors])
arr=np.array(im)  # row0 = top (max y)
dist=ndimage.distance_transform_edt(arr==0)*RS
ci=((GX-x0)/RS).astype(int).clip(0,rw-1);cj=((rh-(GY-y0)/RS)).astype(int).clip(0,rh-1)
dg=dist[cj,ci]
out['zelen']=enc(np.round(mins(dg)),osmok)
print('green polys',len(GP),sum(len(r) for g in GP for r in g)//2)
# node freq arrays
for i,n in enumerate(nodes):
    L=n[4];n.append([round(nr.get(i,{}).get(ids,0),1) for ids in []])  # placeholder
rid=pickle.load(open('lines.pkl','rb'))
ids=sorted(rid,key=lambda r:(rid[r]['m'],__import__('re').split(r'(\d+)',rid[r]['name'])))
import re
def natkey(n):return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)',n)]
ids=sorted(rid,key=lambda r:(rid[r]['m'],natkey(rid[r]['name'])))
for i,n in enumerate(nodes):
    n[5]=[round(nr.get(i,{}).get(ids[li],0),1) for li in n[4]]
out_json={k:v for k,v in D.items()}
out_json['nodes']=nodes
out_json['grid']={'x0':x0,'y0':y0,'cell':CELL,'w':W,'h':H,'layers':{k:base64.b64encode(v.tobytes()).decode() for k,v in out.items()}}
out_json['poi']=POI;out_json['green']=GP
s=json.dumps(out_json,separators=(',',':'),ensure_ascii=False);open('data4.json','w').write(s);print(len(s)//1024,'KB')
for k,v in out.items():
    vv=v[v!=255];print(k,'median',np.median(vv),'p90',np.percentile(vv,90),'n',vv.size)
