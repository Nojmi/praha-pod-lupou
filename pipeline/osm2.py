import pickle,json,math
from shapely.geometry import LineString,Polygon,MultiLineString
from shapely.ops import unary_union
D=json.load(open('data2.json'));ring=Polygon(D['ring']).buffer(300)
roads,rivers,waters=pickle.load(open('osm.pkl','rb'))
def enc(g,tol):
    g=g.simplify(tol);out=[]
    gs=[g] if g.geom_type=='LineString' else [x for x in getattr(g,'geoms',[]) if x.geom_type=='LineString']
    for x in gs:
        if x.length<12:continue
        out.append([int(round(v)) for p in x.coords for v in p])
    return out
R={}
tol={'motorway':3,'trunk':3,'primary':3,'secondary':3,'tertiary':3,'minor':3,'service':4}
for k,v in roads.items():
    if k=='path':continue
    segs=[]
    for pts,nm in v:
        if len(pts)<2:continue
        g=LineString(pts)
        if not g.intersects(ring):continue
        segs+=enc(g.intersection(ring),tol[k])
    R[k]=segs;print(k,len(segs),sum(len(s) for s in segs)//2)
riv=[]
for pts,nm,ww,w in rivers:
    if len(pts)<2:continue
    g=LineString(pts)
    if g.intersects(ring): riv+=enc(g.intersection(ring),4)
print('rivers',len(riv))
W=[]
for rings,nm,wt in waters:
    for outer,inner in rings:
        try:p=Polygon(outer,inner)
        except Exception:continue
        if not p.is_valid:p=p.buffer(0)
        if p.is_empty or p.area<3000:continue
        p=p.intersection(ring)
        if p.is_empty:continue
        for q in ([p] if p.geom_type=='Polygon' else [x for x in p.geoms if x.geom_type=='Polygon']):
            q=q.simplify(4)
            if q.is_empty or q.area<3000:continue
            W.append([[int(round(v)) for pt in q.exterior.coords for v in pt]]+[[int(round(v)) for pt in h.coords for v in pt] for h in q.interiors])
print('water polys',len(W),sum(len(r) for w in W for r in w)//2)
D['roads']=R;D['rivers']=riv;D['water']=W
s=json.dumps(D,separators=(',',':'),ensure_ascii=False);open('data3.json','w').write(s);print(len(s)//1024,'KB')
