import sys, json, math
import numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.vq import kmeans2
C=np.load(sys.argv[1]); n=len(C)
ROAD=1.35; STOP=12/60          # hours on site: find spot, hide, scan-test, photo
nn,_=cKDTree(C).query(C,k=2); local=nn[:,1]
def speed(a,b): return 25 if min(local[a],local[b])<3.5 else 45   # km/h town vs countryside
def tour(idx,start):
    idx=list(idx); pos=start; t=0; km=0
    rem=set(idx)
    while rem:
        cand=np.array(list(rem)); d=np.hypot(C[cand,0]-pos[0],C[cand,1]-pos[1]); j=cand[d.argmin()]
        dist=d.min()*ROAD; v=25 if local[j]<3.5 else 45
        t+=dist/v+STOP; km+=dist; pos=C[j]; rem.remove(j)
    back=np.hypot(pos[0]-start[0],pos[1]-start[1])*ROAD; t+=back/45; km+=back
    return t,km
res=[]
rng=np.random.default_rng(0)
for k in (1,5,10,25,50,100,300,600):
    if k==1: lab=np.zeros(n,int); cent=C.mean(0,keepdims=True)
    else: cent,lab=kmeans2(C,k,seed=1,minit='++',iter=40)
    times=[];kms=[]
    for c in range(k):
        idx=np.where(lab==c)[0]
        if len(idx)==0: continue
        start=C[idx].mean(0)     # helper lives inside their area
        t,km=tour(idx,start); times.append(t); kms.append(km)
    times=np.array(times)
    res.append({'k':k,'max_h':float(times.max()),'avg_h':float(times.mean()),'total_h':float(times.sum()),'km':float(sum(kms)),'per_person':n/k})
    print(k,'people | makespan %.1f h | avg %.1f h | total %.0f person-h | %.0f km'%(times.max(),times.mean(),times.sum(),sum(kms)),file=sys.stderr)
json.dump(res,open(sys.argv[2],'w'))
