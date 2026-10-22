"""Portable banded Newton solve of the unchanged native two-stage residual.

One configured C library per process. Use separate processes, not threads,
for simultaneous runs. Time marching and its budgets are checked separately.
"""
import ctypes as ct
import numpy as np
from scipy.linalg import solve_banded


class Operator:
    def __init__(self,library,c,n,bon,lam,kap,cfl,bedfile):
        self.size=2*(n+1);self.lib=ct.CDLL(str(library))
        ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        self.lib.configure.argtypes=[ct.c_int]*3+[ct.c_double]*9+[ct.c_char_p]
        self.lib.configure(n,bon,0,0.,c['length_m'],c['hin_m'],c['q_m2s'],c['hout_m'],
                           c['n'],lam,kap,cfl,str(bedfile).encode())
        self.lib.native_dt.argtypes=[ptr];self.lib.native_dt.restype=ct.c_double
        self.lib.residual.argtypes=[ptr,ct.c_double,ptr];self.lib.stage.argtypes=[ptr,ct.c_int,ptr]

    def dt(self,u):return self.lib.native_dt(np.ascontiguousarray(u))

    def residual(self,u,step):
        r=np.empty_like(u);self.lib.residual(np.ascontiguousarray(u),step,r);return r

    def stage(self,u,direction):
        r=np.empty_like(u);self.lib.stage(np.ascontiguousarray(u),direction,r);return r

    def newton(self,u,tol=1e-8,maxiter=90):
        u=u.copy();log=[];band=13;n=len(u);colors=2*band+1
        for it in range(maxiter):
            step=self.dt(u);r=self.residual(u,step);norm=float(np.max(abs(r)))
            log.append(dict(iteration=it,residual_Linf=norm,dt=step))
            if norm<tol:return u,log,True
            ab=np.zeros((2*band+1,n));eps=2e-7*np.maximum(abs(u),.1)
            for color in range(colors):
                cols=np.arange(color,n,colors);v=u.copy();v[cols]+=eps[cols]
                dr=self.residual(v,step)-r
                for j in cols:
                    ii=np.arange(max(0,j-band),min(n,j+band+1))
                    ab[band+ii-j,j]=dr[ii]/eps[j]
            try:delta=solve_banded((band,band),ab,-r,check_finite=False)
            except np.linalg.LinAlgError:
                log[-1]['linear_failure']=True;return u,log,False
            scale=1.
            for attempt in range(22):
                trial=u+scale*delta
                if np.all(trial[::2]>1e-6) and np.all(np.isfinite(trial)):
                    nr=float(np.max(abs(self.residual(trial,self.dt(trial)))))
                    if nr<norm*(1-1e-4*scale):break
                scale*=.5
            else:
                log[-1]['line_search_failure']=True;return u,log,False
            log[-1]['step_scale']=scale;u=trial
        return u,log,False
