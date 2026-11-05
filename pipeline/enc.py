import pickle,json,numpy as np,gzip,base64,math
from shapely import contains_xy
from shapely.geometry import Polygon
B=pickle.load(open('bld.pkl','rb'));D=json.load(open('data5.json'))
ring=Polygon(D['ring']).buffer(200)
xs=np.array([b[0] for b in B]);ys=np.array([b[1] for b in B])
keep=contains_xy(ring,xs,ys);B=[b for b,k in zip(B,keep) if k];print('in Prague',len(B))
rx=[p[0] for p in D['ring']];ry=[p[1] for p in D['ring']]
TS=1000;TX0=math.floor((min(rx)-300)/TS)*TS;TY0=math.floor((min(ry)-300)/TS)*TS
NX=math.ceil((max(rx)+300-TX0)/TS);NY=math.ceil((max(ry)+300-TY0)/TS);print('tiles',NX,NY,TX0,TY0)
def tid(b):return int((b[1]-TY0)//TS)*NX+int((b[0]-TX0)//TS)
B.sort(key=tid)
counts=np.zeros(NX*NY,dtype=np.uint16)
H=bytearray();FL=bytearray();NR=bytearray();NP=[];CO=[]
for b in B:
    t=tid(b);counts[t]+=1
    ox=TX0+(t%NX)*TS;oy=TY0+(t//NX)*TS
    H.append(min(255,int(round(b[2]*2))));FL.append(b[3]);NR.append(len(b[4]))
    for r in b[4]:
        NP.append(len(r))
        pts=[(int(round((x-ox)*10)),int(round((y-oy)*10))) for x,y in r]
        CO.append(pts[0][0]);CO.append(pts[0][1])
        for i in range(1,len(pts)):CO.append(pts[i][0]-pts[i-1][0]);CO.append(pts[i][1]-pts[i-1][1])
co=np.array(CO);print('coord range',co.min(),co.max(),'rings',len(NP),'pts',len(CO)//2)
assert co.min()>-32768 and co.max()<32768
raw=counts.astype('<u2').tobytes()+bytes(H)+bytes(FL)+bytes(NR)+np.array(NP,dtype='<u2').tobytes()+co.astype('<i2').tobytes()
z=gzip.compress(raw,9);print('raw',len(raw)//1024,'gz',len(z)//1024,'KB')
# výšková histogram
hs=np.array([b[2] for b in B]);fl=np.array([b[3] for b in B])
bins=[0,6,12,25,40,1000];hist=[int(((hs>=bins[i])&(hs<bins[i+1])).sum()) for i in range(5)]
out={'ring':D['ring'],'nodes':[n[:5] for n in D['nodes']],'lines':D['lines'],'roads':D['roads'],'rivers':D['rivers'],'water':D['water'],'green':D['green'],
 'bld':{'n':len(B),'tn':NX*NY,'nx':NX,'ny':NY,'tx0':TX0,'ty0':TY0,'ts':TS,'np':len(NP),'nc':len(CO),'hist':hist,'known':int((fl>0).sum()),'b':base64.b64encode(z).decode()}}
s=json.dumps(out,separators=(',',':'),ensure_ascii=False);open('data6.json','w').write(s);print(len(s)//1024,'KB total',hist)
