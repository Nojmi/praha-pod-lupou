import pandas as pd,numpy as np,json,math,pickle
from shapely.geometry import LineString,Polygon,Point
from shapely.ops import transform
U='/mnt/user-data/uploads/';A='/mnt/user-data/attachments/86c00a9c-a82f-5c8d-afb0-c3da3d7856ef/'
D=json.load(open('data.json'))
ring=Polygon(D['ring']).buffer(300)   # meters
rt=pd.read_csv(A+'f12eac81-routes.txt',dtype=str).set_index('route_id')
t=pd.read_csv(A+'0bf177f5-trips.txt',dtype=str,usecols=['route_id','shape_id','direction_id'])
cnt=t.groupby(['route_id','direction_id','shape_id']).size().reset_index(name='n').sort_values('n',ascending=False)
best=cnt.groupby(['route_id','direction_id']).head(1)
want=set(best.shape_id)
print('shapes wanted',len(want))
parts=[]
for ch in pd.read_csv(U+'shapes.txt',chunksize=800000,usecols=['shape_id','shape_pt_lat','shape_pt_lon','shape_pt_sequence']):
    parts.append(ch[ch.shape_id.isin(want)])
S=pd.concat(parts).sort_values(['shape_id','shape_pt_sequence'])
c=math.cos(math.radians(50.08))
S['x']=(S.shape_pt_lon-14.42)*c*111320;S['y']=(S.shape_pt_lat-50.08)*110574
MODE={'1':4,'0':2,'3':1,'11':1,'2':8,'4':16,'7':32}
lines={}  # route_id -> dict
for (rid,did),g in best.groupby(['route_id','direction_id']):
    sh=S[S.shape_id==g.shape_id.iloc[0]]
    if len(sh)<2: continue
    ls=LineString(zip(sh.x,sh.y))
    cl=ls.intersection(ring)
    if cl.is_empty: continue
    geoms=[cl] if cl.geom_type=='LineString' else [x for x in getattr(cl,'geoms',[]) if x.geom_type=='LineString']
    for gm in geoms:
        gm=gm.simplify(6)
        if gm.length<150: continue
        r=rt.loc[rid]
        L=lines.setdefault(rid,{'name':r.route_short_name,'m':MODE[r.route_type],'col':r.route_color if isinstance(r.route_color,str) else '','night':int(r.is_night),'reg':int(r.is_regional),'seg':[]})
        L['seg'].append([[int(round(x)),int(round(y))] for x,y in gm.coords])
print('routes in Prague',len(lines))
pickle.dump(lines,open('lines.pkl','wb'))
import collections
km=collections.Counter();pts=0
for L in lines.values():
    for s in L['seg']:
        pts+=len(s);km[L['m']]+=sum(math.hypot(a[0]-b[0],a[1]-b[1]) for a,b in zip(s,s[1:]))/1000
print(pts,dict(km))
