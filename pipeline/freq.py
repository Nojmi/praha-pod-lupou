import pandas as pd,numpy as np,json,math,pickle,collections
A='/mnt/user-data/attachments/86c00a9c-a82f-5c8d-afb0-c3da3d7856ef/';U='/mnt/user-data/uploads/'
D=json.load(open('data3.json'))
cal=pd.read_csv(A+'fa17cfe8-calendar.txt',dtype=str)
cd=pd.read_csv(A+'c250d5a8-calendar_dates.txt',dtype=str)
day='20261111'  # středa
act=set(cal[(cal.wednesday=='1')&(cal.start_date<=day)&(cal.end_date>=day)].service_id)
x=cd[cd.date==day];act|=set(x[x.exception_type=='1'].service_id);act-=set(x[x.exception_type=='2'].service_id)
print('active services',len(act))
tr=pd.read_csv(A+'0bf177f5-trips.txt',dtype=str,usecols=['route_id','service_id','trip_id'])
rt=pd.read_csv(A+'f12eac81-routes.txt',dtype=str).set_index('route_id')
tr=tr[tr.service_id.isin(act)];tr['night']=tr.route_id.map(rt.is_night)
tr=tr[tr.night=='0'];print('weekday day trips',len(tr))
route_ids=pickle.load(open('lines.pkl','rb')).keys()
tr=tr[tr.route_id.isin(route_ids)];print('in-Prague routes trips',len(tr))
t2r=dict(zip(tr.trip_id,tr.route_id))
st=pd.read_csv(A+'90401833-stops.txt',dtype=str,usecols=['stop_id','stop_name','stop_lat','stop_lon'])
c=math.cos(math.radians(50.08))
st['x']=(st.stop_lon.astype(float)-14.42)*c*111320;st['y']=(st.stop_lat.astype(float)-50.08)*110574
byname=collections.defaultdict(list)
for i,n in enumerate(D['nodes']):byname[n[2]].append(i)
sinfo={r.stop_id:(r.stop_name,r.x,r.y) for r in st.itertuples()}
cache={}
def node_of(sid):
    if sid in cache:return cache[sid]
    s=sinfo.get(sid);r=None
    if s and s[0] in byname:
        b=min(byname[s[0]],key=lambda i:(D['nodes'][i][0]-s[1])**2+(D['nodes'][i][1]-s[2])**2)
        if math.hypot(D['nodes'][b][0]-s[1],D['nodes'][b][1]-s[2])<500:r=b
    cache[sid]=r;return r
cnt=collections.Counter()
for ch in pd.read_csv(U+'stop_times_1.txt',chunksize=500000,usecols=['trip_id','stop_id','departure_time','pickup_type'],dtype=str):
    ch=ch[ch.trip_id.isin(t2r)&(ch.pickup_type!='1')]
    h=ch.departure_time.str.slice(0,2).astype(int)
    ch=ch[(h>=7)&(h<19)]
    for tid,sid in zip(ch.trip_id,ch.stop_id):
        n=node_of(sid)
        if n is not None:cnt[(n,t2r[tid])]+=1
print('node-route pairs',len(cnt))
pickle.dump(dict(cnt),open('freq.pkl','wb'))
tot=collections.Counter()
for (n,r),v in cnt.items():tot[n]+=v
print('top',[(D['nodes'][n][2],round(v/12,1)) for n,v in tot.most_common(8)])
