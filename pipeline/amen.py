import osmium,math,pickle,collections
c=math.cos(math.radians(50.08))
P=lambda lon,lat:((lon-14.42)*c*111320,(lat-50.08)*110574)
F='/mnt/user-data/uploads/planet_14_086_49_963_14_757_50_145_osm.pbf'
def cat(t):
    a=t.get('amenity');s=t.get('shop');h=t.get('healthcare');l=t.get('leisure')
    if a=='kindergarten':return 'ms'
    if a=='school':return 'zs'
    if a=='pharmacy':return 'lekarna'
    if a in('doctors','clinic','hospital') or h in('doctor','clinic','hospital'):return 'lekar'
    if s in('supermarket','convenience','greengrocer','bakery','general','department_store','mall'):return 'obchod'
    return None
def isgreen(t):
    l=t.get('leisure');lu=t.get('landuse');n=t.get('natural')
    return l in('park','garden','nature_reserve','recreation_ground','common','playground') and t.get('access') not in('private','no') or lu in('forest','village_green','recreation_ground','meadow') or n in('wood','grassland','scrub','heath')
pois=collections.defaultdict(list);green=[]
fp=osmium.FileProcessor(F).with_locations().with_areas()
for o in fp:
    t=o.tags
    if o.is_node():
        k=cat(t)
        if k:pois[k].append((*P(o.location.lon,o.location.lat),t.get('name','')))
    elif o.is_area():
        k=cat(t)
        if k:
            try:
                ring=[P(n.lon,n.lat) for n in next(iter(o.outer_rings()))]
                x=sum(p[0] for p in ring)/len(ring);y=sum(p[1] for p in ring)/len(ring)
                pois[k].append((x,y,t.get('name','')))
            except Exception:pass
        if isgreen(t) and not t.get('building'):
            try:
                rings=[([P(n.lon,n.lat) for n in out],[[P(n.lon,n.lat) for n in inn] for inn in o.inner_rings(out)]) for out in o.outer_rings()]
                green.append((rings,t.get('leisure') or t.get('landuse') or t.get('natural')))
            except Exception:pass
print({k:len(v) for k,v in pois.items()},len(green))
pickle.dump((dict(pois),green),open('amen.pkl','wb'))
