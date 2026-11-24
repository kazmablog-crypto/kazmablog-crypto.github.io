import sys, json
import numpy as np
from scipy.spatial import cKDTree
O=sys.argv[1]; S=np.load(O+'/S.npy'); W=np.load(O+'/W.npy'); area_pl=json.load(open(sys.argv[2]))
cellA=0.25; tree=cKDTree(S); TOT=W.sum()
def stats(C):
    d,_=cKDTree(C).query(S); o=np.argsort(d); cw=np.cumsum(W[o])/TOT
    q=lambda x: float(d[o][min(len(o)-1,np.searchsorted(cw,x))])
    w=lambda km: float(W[d<=km].sum()/TOT*100)
    return {'worst':float(d.max()),'p95people':q(.95),'p99people':q(.99),'w1':w(1),'w2':w(2),'w3':w(3),'w5':w(5)}
def lloyd(C,wt,it):
    n=len(C)
    for _ in range(it):
        _,idx=cKDTree(C).query(S)
        ws=np.bincount(idx,weights=wt,minlength=n); sx=np.bincount(idx,weights=wt*S[:,0],minlength=n); sy=np.bincount(idx,weights=wt*S[:,1],minlength=n)
        nz=ws>0; C[nz,0]=sx[nz]/ws[nz]; C[nz,1]=sy[nz]/ws[nz]
    _,j=tree.query(C); return S[j].copy()
dens=W/cellA; wt=np.sqrt(dens)+np.sqrt(TOT/78000)*0.6
rng=np.random.default_rng(5); res={'pop':{},'stats':{'area':{},'pop':{}}}
for n in (77,206,300,1200,2000,2500,3000):
    if str(n) in area_pl: res['stats']['area'][n]=stats(np.array(area_pl[str(n)],float))
    C=S[rng.choice(len(S),n,replace=False,p=wt/wt.sum())].copy(); C=lloyd(C,wt,50)
    res['stats']['pop'][n]=stats(C)
    if n in (77,206,300,1200): res['pop'][n]=[[round(x,1),round(y,1)] for x,y in C]
    if n==1200: np.save(O+'/C1200.npy',C)
    print(n,'pop',{k:round(v,1) for k,v in res['stats']['pop'][n].items()},file=sys.stderr)
    if n in res['stats']['area']: print(n,'area',{k:round(v,1) for k,v in res['stats']['area'][n].items()},file=sys.stderr)
json.dump(res,open(O+'/place.json','w'),separators=(',',':'))
