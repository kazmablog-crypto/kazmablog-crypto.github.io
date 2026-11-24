import json, math, sys
import numpy as np
from scipy.spatial import cKDTree
CZ=json.load(open(sys.argv[1])); K=math.cos(math.radians(49.8))
P=np.array([((x-12)*111.32*K,(51.1-y)*110.57) for x,y in CZ])
def inside(xs,ys):
    c=np.zeros(xs.shape,bool); n=len(P)
    for i in range(n):
        xi,yi=P[i]; xj,yj=P[i-1]
        m=((yi>ys)!=(yj>ys)) & (xs < (xj-xi)*(ys-yi)/((yj-yi) if yj!=yi else 1e-12)+xi)
        c^=m
    return c
minX,minY=P.min(0); maxX,maxY=P.max(0)
step=0.7
gx,gy=np.meshgrid(np.arange(minX,maxX,step),np.arange(minY,maxY,step))
gx,gy=gx.ravel(),gy.ravel(); m=inside(gx,gy); S=np.c_[gx[m],gy[m]]
print('samples',len(S),file=sys.stderr)
def hexgrid(n):
    lo,hi=3,80
    best=None
    for _ in range(40):
        d=(lo+hi)/2; h=d*math.sqrt(3)/2
        ys=np.arange(minY+h/2,maxY,h); pts=[]
        for r,y in enumerate(ys):
            xs=np.arange(minX+(d/2 if r%2 else 0),maxX,d); ins=inside(xs,np.full(xs.shape,y)); pts+= [[x,y] for x in xs[ins]]
        if best is None or abs(len(pts)-n)<abs(len(best)-n): best=pts
        if len(pts)>n: lo=d
        else: hi=d
        if len(pts)==n: break
    return np.array(best,float)
out={}
for n in (77,206,300,1200):
    C=hexgrid(n)
    # top up / trim to exactly n
    rng=np.random.default_rng(1)
    while len(C)<n: C=np.vstack([C,S[rng.integers(len(S))]])
    C=C[:n]
    for it in range(60):                       # Lloyd: even spread
        d,idx=cKDTree(C).query(S)
        sums=np.zeros_like(C); cnt=np.bincount(idx,minlength=n)
        np.add.at(sums,idx,S); nz=cnt>0; C[nz]=sums[nz]/cnt[nz,None]
    for it in range(80):                       # minimax: pull each cache toward its farthest assigned point
        d,idx=cKDTree(C).query(S)
        far=np.zeros(n); fp=C.copy()
        order=np.argsort(d)
        far[idx[order]]=d[order]; fp[idx[order]]=S[order]
        C=C+0.12*(fp-C)
        # keep inside: snap to nearest sample
        _,j=cKDTree(S).query(C); C=S[j]
    d,_=cKDTree(C).query(S)
    print(n,'worst %.1f km'%d.max(),'p95 %.1f'%np.percentile(d,95),file=sys.stderr)
    out[n]=[[round(x,1),round(y,1)] for x,y in C]
print(json.dumps(out,separators=(',',':')))
