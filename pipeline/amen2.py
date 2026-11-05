"""Další vrstvy z OSM: střední/vysoké/základní školy, dětská hřiště, sportoviště, cyklostezky."""
import osmium,math,pickle,collections,re
c=math.cos(math.radians(50.08))
P=lambda lon,lat:((lon-14.42)*c*111320,(lat-50.08)*110574)
F='/mnt/user-data/uploads/planet_14_086_49_963_14_757_50_145_osm.pbf'
SEC=re.compile(r'gymn[aá]zium|st[rř]edn[ií]|\bS[SO][ŠSÚU]?\b|\bSO[ŠU]\b|u[cč]ili[sš]t[eě]|lyceum|konzervato[rř]|obchodn[ií] akademie|pr[uů]myslov|akademie|vy[sš][sš][ií] odborn',re.I)
UNI=re.compile(r'univerzit|fakulta|vysok[aá] [sš]kola|\bVŠ\b|\bV[SŠ]E\b|[cč]vut|akademie v[eě]d|university',re.I)
def cat(t):
    a=t.get('amenity');l=t.get('leisure');n=t.get('name','')
    if a in('university','college'):return 'vs'
    if a=='school':
        isced=t.get('isced:level','')
        if UNI.search(n) and not re.search(r'z[aá]kladn',n,re.I):return 'vs'
        if SEC.search(n) or re.search(r'[34]',isced) and not re.search(r'[12]',isced):return 'sr'
        return 'zs'
    if l=='playground':return 'hriste'
    if l in('pitch','sports_centre','track','stadium','fitness_station') and t.get('access') not in('private','no'):return 'sport'
    return None
pois=collections.defaultdict(list);cyc=[];lane=[]
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
                pois[k].append((sum(p[0] for p in ring)/len(ring),sum(p[1] for p in ring)/len(ring),t.get('name','')))
            except Exception:pass
    elif o.is_way():
        hw=t.get('highway')
        if not hw:continue
        try:pts=[P(n.lon,n.lat) for n in o.nodes]
        except Exception:continue
        if len(pts)<2:continue
        if hw=='cycleway' or (hw in('path','footway','track','pedestrian') and t.get('bicycle')=='designated' and t.get('segregated')!='no'):cyc.append(pts)
        elif any(t.get(k) in('lane','track','opposite_lane','opposite_track','shared_lane') for k in('cycleway','cycleway:left','cycleway:right','cycleway:both')) and t.get('cycleway') not in('shared_lane',):lane.append(pts)
print({k:len(v) for k,v in pois.items()},len(cyc),len(lane))
pickle.dump((dict(pois),cyc,lane),open('amen2.pkl','wb'))
