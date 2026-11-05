import csv,collections,math,json
from shapely import wkt
from shapely.geometry import Point
P='/home/claude/probe/Prague-Tram-Network-Analysis/'
poly=wkt.loads(open('/home/claude/nwuestefeld/prague_gtfs/tariff_zones.wkt',encoding='utf-8').read())
polyb=poly.buffer(0.004)
stops={}
for r in csv.DictReader(open(P+'stops.txt',encoding='utf-8')):
    stops[r['stop_id']]=(float(r['stop_lat']),float(r['stop_lon']),r['stop_name'],r['location_type'],r['parent_station'])
pairs=collections.Counter()
for r in csv.DictReader(open(P+'d.csv',encoding='utf-8')):
    pairs[(r['stop_from'],r['stop_to'],r['route_type'])]+=1
inP={k for k,v in stops.items() if polyb.contains(Point(v[1],v[0]))}
print('stops in/near Prague',len(inP))
E=[(a,b,t,c) for (a,b,t),c in pairs.items() if a in inP and b in inP]
print('edges',len(E),collections.Counter(t for _,_,t,_ in E))
def d(a,b):
    la=math.radians((stops[a][0]+stops[b][0])/2)
    return math.hypot((stops[a][1]-stops[b][1])*math.cos(la)*111320,(stops[a][0]-stops[b][0])*110574)
print('FERRY / FUNI')
for a,b,t,c in E:
    if t in('4','7'): print(t,stops[a][2],'->',stops[b][2],f"{stops[a][0]:.4f},{stops[a][1]:.4f}  {stops[b][0]:.4f},{stops[b][1]:.4f}",round(d(a,b)),'m',c)
import pickle; pickle.dump((stops,E,inP),open('prep.pkl','wb'))
