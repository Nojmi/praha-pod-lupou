import pandas as pd,numpy as np,json,math,pickle,collections
from shapely.geometry import LineString
from shapely.ops import unary_union
A='/mnt/user-data/attachments/86c00a9c-a82f-5c8d-afb0-c3da3d7856ef/'
D=json.load(open('data.json'));lines=pickle.load(open('lines.pkl','rb'))
def natkey(n):
    import re
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)',n)]
order=sorted(lines.items(),key=lambda kv:(-kv[1]['m'] if False else 0,))
ids=sorted(lines,key=lambda r:(lines[r]['m'],natkey(lines[r]['name'])))
idx={r:i for i,r in enumerate(ids)}
# stops -> node
st=pd.read_csv(A+'90401833-stops.txt',dtype=str,usecols=['stop_id','stop_name','stop_lat','stop_lon'])
c=math.cos(math.radians(50.08))
st['x']=(st.stop_lon.astype(float)-14.42)*c*111320;st['y']=(st.stop_lat.astype(float)-50.08)*110574
byname=collections.defaultdict(list)
for i,n in enumerate(D['nodes']): byname[n[2]].append(i)
sinfo={r.stop_id:(r.stop_name,r.x,r.y) for r in st.itertuples()}
def node_of(sid):
    s=sinfo.get(sid)
    if not s: return None
    cand=byname.get(s[0]);
    if not cand: return None
    b=min(cand,key=lambda i:(D['nodes'][i][0]-s[1])**2+(D['nodes'][i][1]-s[2])**2)
    d=math.hypot(D['nodes'][b][0]-s[1],D['nodes'][b][1]-s[2])
    return b if d<500 else None
rs=pd.read_csv(A+'1aae9c54-route_stops.txt',dtype=str,usecols=['route_id','stop_id']).drop_duplicates()
rs=rs[rs.route_id.isin(idx)]
nl=collections.defaultdict(set);miss=0
cache={}
for r in rs.itertuples():
    if r.stop_id not in cache: cache[r.stop_id]=node_of(r.stop_id)
    n=cache[r.stop_id]
    if n is None: miss+=1;continue
    nl[n].add(idx[r.route_id])
print('route-stop pairs',len(rs),'unmapped',miss,'nodes with lines',len(nl))
nodes=[n+[sorted(nl.get(i,[]),key=lambda k:k)] for i,n in enumerate(D['nodes'])]
# unique length per mode
stat={}
for m in (1,2,4,8,16,32):
    segs=[LineString(s) for r in ids if lines[r]['m']==m for s in lines[r]['seg']]
    if not segs: continue
    u=unary_union([s.buffer(12) for s in segs]);stat[m]=round(u.area/24/1000,1)
print(stat)
L=[{'n':lines[r]['name'],'m':lines[r]['m'],'c':lines[r]['col'],'nt':lines[r]['night'],'rg':lines[r]['reg'],
    's':[[v for p in s for v in p] for s in lines[r]['seg']]} for r in ids]
cn=collections.Counter((l['m'],l['nt']) for l in L);print(cn)
out={'nodes':nodes,'edges':D['edges'],'ring':D['ring'],'lines':L,'km':stat}
s=json.dumps(out,separators=(',',':'),ensure_ascii=False);open('data2.json','w').write(s);print(len(s)//1024,'KB')
