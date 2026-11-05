import osmium,math,re,pickle,collections,numpy as np
from shapely.geometry import Polygon
c=math.cos(math.radians(50.08))
P=lambda lon,lat:((lon-14.42)*c*111320,(lat-50.08)*110574)
F='/mnt/user-data/uploads/planet_14_086_49_963_14_757_50_145_osm.pbf'
TYPE={'house':7,'detached':7,'semidetached_house':7,'terrace':8,'bungalow':5,'cabin':4,'residential':12,'apartments':18,'dormitory':15,'garage':3,'garages':3,'carport':3,'shed':3,'roof':4,'hut':3,'kiosk':3,'service':4,'greenhouse':4,'industrial':9,'warehouse':9,'factory':10,'commercial':12,'retail':9,'office':15,'supermarket':8,'church':16,'cathedral':25,'chapel':8,'school':12,'university':14,'hospital':14,'hotel':16,'train_station':9,'public':12,'civic':12,'yes':8}
def num(s):
    m=re.match(r'\s*([0-9]+(?:[.,][0-9]+)?)',s or '')
    return float(m.group(1).replace(',','.')) if m else None
B=[]  # (cx,cy,h,flag,[rings])
for o in osmium.FileProcessor(F,osmium.osm.NODE|osmium.osm.WAY|osmium.osm.RELATION).with_locations().with_areas():
    if not o.is_area():continue
    t=o.tags;bt=t.get('building')
    if not bt or bt=='no':continue
    h=num(t.get('height'));flag=0
    if h:flag=2
    else:
        lv=num(t.get('building:levels'))
        if lv:h=lv*3.0+(1.5 if bt in('house','detached','semidetached_house','residential','yes') and lv<4 else 0);flag=1
        else:h=TYPE.get(bt,8);flag=0
    h=max(2.5,min(h,250))
    try:
        for outer in o.outer_rings():
            pts=[P(n.lon,n.lat) for n in outer]
            holes=[[P(n.lon,n.lat) for n in inn] for inn in o.inner_rings(outer)]
            if len(pts)<4:continue
            p=Polygon(pts,holes)
            if not p.is_valid:p=p.buffer(0)
            if p.is_empty:continue
            if p.area<12:continue
            q=p.simplify(0.5)
            for g in ([q] if q.geom_type=='Polygon' else [z for z in q.geoms if z.geom_type=='Polygon']):
                if g.area<12:continue
                rings=[list(g.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in g.interiors if len(r.coords)>=4]
                if len(rings[0])<3:continue
                cen=g.centroid;B.append((cen.x,cen.y,h,flag,rings))
    except Exception as e:pass
print('buildings',len(B))
pickle.dump(B,open('bld.pkl','wb'))
hs=np.array([b[2] for b in B]);fl=np.array([b[3] for b in B])
print('median h',np.median(hs),'p95',np.percentile(hs,95),'flag counts',collections.Counter(fl.tolist()))
