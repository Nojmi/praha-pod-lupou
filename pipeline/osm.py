import osmium,json,math,pickle,collections
c=math.cos(math.radians(50.08))
P=lambda lon,lat:((lon-14.42)*c*111320,(lat-50.08)*110574)
F='/mnt/user-data/uploads/planet_14_086_49_963_14_757_50_145_osm.pbf'
roads=collections.defaultdict(list);rivers=[];waters=[];
fp=osmium.FileProcessor(F).with_locations().with_areas()
for o in fp:
    t=o.tags
    if o.is_way():
        hw=t.get('highway');ww=t.get('waterway')
        try:
            pts=[P(n.lon,n.lat) for n in o.nodes]
        except Exception: continue
        MAP={'residential':'minor','unclassified':'minor','living_street':'minor','pedestrian':'minor','service':'service','footway':'path','cycleway':'path','path':'path','track':'path','steps':'path'}
        if hw:
            k=hw.replace('_link','')
            if k in('motorway','trunk','primary','secondary','tertiary'):roads[k].append((pts,''))
            elif k in MAP:
                if k=='service' and t.get('service') in('driveway','parking_aisle'):continue
                roads[MAP[k]].append((pts,''))
        if False:pass
        elif ww in('river','canal'):
            rivers.append((pts,t.get('name',''),ww,t.get('width','')))
    elif o.is_area():
        if t.get('natural')=='water' or t.get('water') in('river','lake','reservoir','pond') or t.get('landuse')=='reservoir':
            try:
                rings=[]
                for outer in o.outer_rings():
                    rings.append(([P(n.lon,n.lat) for n in outer],[[P(n.lon,n.lat) for n in inn] for inn in o.inner_rings(outer)]))
                waters.append((rings,t.get('name',''),t.get('water','')))
            except Exception as e: pass
print({k:len(v) for k,v in roads.items()},len(rivers),len(waters))
pickle.dump((dict(roads),rivers,waters),open('osm.pkl','wb'))
