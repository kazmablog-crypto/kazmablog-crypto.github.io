import sys, json, math, glob, collections
import numpy as np
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import shape
D=sys.argv[1]; OUT=sys.argv[2]
K=math.cos(math.radians(49.8))
def projxy(x,y): return ((np.asarray(x)-12)*111.32*K,(51.1-np.asarray(y))*110.57)
def proj_geom(g):
    return shapely.transform(g, lambda c: np.c_[(c[:,0]-12)*111.32*K,(51.1-c[:,1])*110.57])
pop=json.load(open(D+'/pop2026.json')); pop={int(k):v for k,v in pop.items()}
am=json.load(open(D+'/am_stats.json'))['features']; nvo={a['attributes']['vo_kod']:a['attributes']['n'] for a in am if a['attributes']['vo_kod'] is not None}
vo=[]
for f in sorted(glob.glob(D+'/vo_*.json')): vo+=json.load(open(f))['features']
print('okrsky',len(vo),file=sys.stderr)
obec_n=collections.defaultdict(int); obec_vos=collections.defaultdict(list)
for f in vo:
    p=f['properties']; obec_n[p['obec']]+=nvo.get(p['kod'],0); obec_vos[p['obec']].append(f)
# population per okrsek
vpop={}
for ob,fs in obec_vos.items():
    P=pop.get(ob,0)
    if obec_n[ob]>0:
        for f in fs: vpop[f['properties']['kod']]=P*nvo.get(f['properties']['kod'],0)/obec_n[ob]
    else:
        geoms=[proj_geom(shape(f['geometry'])) for f in fs]; A=sum(g.area for g in geoms) or 1
        for f,g in zip(fs,geoms): vpop[f['properties']['kod']]=P*g.area/A
print('people in okrsky %.0f / %d'%(sum(vpop.values()),sum(pop.values())),file=sys.stderr)
# national border from obce
ob=[]
for f in sorted(glob.glob(D+'/obce_*.json')): ob+=json.load(open(f))['features']
step=0.5
geoms=[proj_geom(shape(f['geometry'])) for f in vo]
allb=shapely.union_all([g.buffer(0) for g in [proj_geom(shape(f['geometry'])) for f in ob]]).buffer(0.05)
minx,miny,maxx,maxy=allb.bounds
gx,gy=np.meshgrid(np.arange(minx,maxx,step),np.arange(miny,maxy,step)); pts=shapely.points(gx.ravel(),gy.ravel())
inside=shapely.contains(allb,pts) if False else None
tree=shapely.STRtree(pts)
W=np.zeros(len(pts)); used=np.zeros(len(pts),bool)
for f,g in zip(vo,geoms):
    P=vpop.get(f['properties']['kod'],0)
    idx=tree.query(g,predicate='contains')
    if len(idx): W[idx]+=P/len(idx); used[idx]=True
    else:
        c=g.representative_point(); j=tree.nearest(c); W[j]+=P; used[j]=True
keep=used
S=np.c_[gx.ravel()[keep],gy.ravel()[keep]]; W=W[keep]
print('cells',len(S),'people %.0f'%W.sum(),file=sys.stderr)
np.save(OUT+'/S.npy',S); np.save(OUT+'/W.npy',W)
# border outline (simplified) and top towns from ČSÚ
border=allb.buffer(-0.05).simplify(0.3)
if border.geom_type=='MultiPolygon': border=max(border.geoms,key=lambda g:g.area)
inv=lambda x,y: (x/(111.32*K)+12, 51.1-y/110.57)
json.dump([[round(a,1),round(b,1)] for a,b in border.exterior.coords],open(OUT+'/border.json','w'))
towns=sorted(ob,key=lambda f:-pop.get(f['properties']['kod'],0))[:40]
tw=[]
for f in towns:
    c=proj_geom(shape(f['geometry'])).representative_point(); tw.append([f['properties']['nazev'],pop[f['properties']['kod']],round(c.x,1),round(c.y,1)])
json.dump(tw,open(OUT+'/towns.json','w'),ensure_ascii=False)
print('area km2 %.0f'%border.area,file=sys.stderr)
