import osmium,math,collections,numpy as np,pickle,time
c=math.cos(math.radians(50.08))
F='/mnt/user-data/uploads/planet_14_086_49_963_14_757_50_145_osm.pbf'
OK={'primary','secondary','tertiary','unclassified','residential','living_street','service','pedestrian','footway','path','track','cycleway','steps','primary_link','secondary_link','tertiary_link','bridleway'}
t0=time.time()
ways=[]  # list of (ids, xs, ys)
cnt=collections.Counter()
fp=osmium.FileProcessor(F,osmium.osm.NODE|osmium.osm.WAY).with_locations()
for w in fp:
    if not w.is_way():continue
    t=w.tags;hw=t.get('highway')
    if hw not in OK:continue
    if t.get('foot')=='no':continue
    if t.get('access') in('private','no') and t.get('foot') not in('yes','designated','permissive'):continue
    if hw=='service' and t.get('service') in('driveway','parking_aisle'):continue
    if hw=='footway' and t.get('footway') in('sidewalk','crossing'):continue
    if hw=='cycleway' and t.get('foot') in('no',):continue
    try:
        ids=[];xy=[]
        for n in w.nodes:
            ids.append(n.ref);xy.append(((n.lon-14.42)*c*111320,(n.lat-50.08)*110574))
    except Exception:continue
    if len(ids)<2:continue
    ways.append((ids,xy));cnt.update(set(ids))
print('ways',len(ways),'nodes',len(cnt),time.time()-t0)
nid={};X=[];Y=[]
def get(i,xy):
    k=nid.get(i)
    if k is None:
        k=len(X);nid[i]=k;X.append(xy[0]);Y.append(xy[1])
    return k
EA=[];EB=[];EL=[]
for ids,xy in ways:
    last=0;acc=0.0
    for k in range(1,len(ids)):
        acc+=math.hypot(xy[k][0]-xy[k-1][0],xy[k][1]-xy[k-1][1])
        if cnt[ids[k]]>1 or k==len(ids)-1:
            a=get(ids[last],xy[last]);b=get(ids[k],xy[k])
            if a!=b and acc<65000:EA.append(a);EB.append(b);EL.append(int(round(acc)))
            last=k;acc=0.0
    # první uzel je vždy konec/křižovatka
print('graph nodes',len(X),'edges',len(EA),time.time()-t0)
pickle.dump((np.array(X),np.array(Y),np.array(EA),np.array(EB),np.array(EL)),open('graph.pkl','wb'))
