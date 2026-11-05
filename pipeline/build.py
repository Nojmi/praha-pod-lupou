import pickle,math,json,collections
import networkx as nx
from shapely import wkt
from river import stops,E,inP
lat0=50.08;lon0=14.42;kx=math.cos(math.radians(lat0))*111320;ky=110574
def xy(la,lo): return ((lo-lon0)*kx,(la-lat0)*ky)
# metro lines by components of platform-level graph
G=nx.Graph()
for a,b,t,c in E:
    if t=='1': G.add_edge(a,b)
comps=list(nx.connected_components(G));print('metro comps',len(comps),[len(c) for c in comps])
def letter(c):
    names={stops[s][2] for s in c}
    for k,l in (('Nemocnice Motol','A'),('Zličín','B'),('Letňany','C')):
        if k in names: return l
    return '?'
lines={}
for c in comps:
    for s in c: lines[s]=letter(c)
print(collections.Counter(lines.values()))
# keep edges
keep=[]
for a,b,t,c in E:
    if t not in('0','1','3','2','4','7'): continue
    pa,pb=xy(*stops[a][:2]),xy(*stops[b][:2]);L=math.hypot(pa[0]-pb[0],pa[1]-pb[1])
    if t=='3' and L>2500: continue
    if t=='2' and L>6000: continue
    keep.append((a,b,t,c,L))
used={s for a,b,*_ in keep for s in (a,b)}
# cluster platforms into nodes: same name within 250 m
byname=collections.defaultdict(list)
for s in used: byname[stops[s][2]].append(s)
node_of={};nodes=[]
for name,ids in byname.items():
    cl=[]
    for s in ids:
        p=xy(*stops[s][:2])
        for c_ in cl:
            if math.hypot(p[0]-c_['p'][0],p[1]-c_['p'][1])<250:
                c_['ids'].append(s);n=len(c_['ids']);c_['p']=((c_['p'][0]*(n-1)+p[0])/n,(c_['p'][1]*(n-1)+p[1])/n);break
        else: cl.append({'ids':[s],'p':p})
    for c_ in cl:
        idx=len(nodes);nodes.append({'name':name,'p':c_['p'],'mask':0})
        for s in c_['ids']: node_of[s]=idx
MB={'3':1,'0':2,'1':4,'2':8,'4':16,'7':32}
edges={}
for a,b,t,c,L in keep:
    i,j=node_of[a],node_of[b]
    if i==j: continue
    k=(min(i,j),max(i,j),t)
    e=edges.setdefault(k,{'w':0,'L':L,'line':lines.get(a,'') if t=='1' else ''})
    e['w']+=c
    if t=='1' and not e['line']: e['line']=lines.get(a,'')
for (i,j,t),e in edges.items():
    nodes[i]['mask']|=MB[t];nodes[j]['mask']|=MB[t]
poly=wkt.loads(open('/home/claude/nwuestefeld/prague_gtfs/tariff_zones.wkt',encoding='utf-8').read()).simplify(0.0002)
ring=[xy(la,lo) for lo,la in poly.exterior.coords]
ring=[[round(x),round(y)] for x,y in ring]
out={'nodes':[[round(n['p'][0]),round(n['p'][1]),n['name'],n['mask']] for n in nodes],
 'edges':[[i,j,MB[t],e['w'],e['line']] for (i,j,t),e in edges.items()],'ring':ring}
stat=collections.Counter();km=collections.Counter()
for (i,j,t),e in edges.items(): stat[t]+=1;km[t]+=e['L']/1000
print('nodes',len(nodes),'edges',len(edges),dict(stat),{k:round(v,1) for k,v in km.items()})
print('area km2',round(__import__('shapely').Polygon(ring).area/1e6,1),'ring pts',len(ring))
s=json.dumps(out,ensure_ascii=False,separators=(',',':'));print('json KB',len(s)//1024)
open('data.json','w',encoding='utf-8').write(s)
