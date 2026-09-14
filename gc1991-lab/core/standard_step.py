"""Horizontal rectangular-channel standard step and zero-length jump matching.

SI; x positive downstream; alpha=beta=1; full rectangular hydraulic radius.
Scope: GC1991 feasibility, not a general cross-section or transcritical solver.
"""
from bisect import bisect_left
from math import sqrt

G = 9.81


def energy(h, q):
    return h + q*q/(2*G*h*h)


def force(h, q):
    """Specific force per unit width (m2)."""
    return h*h/2 + q*q/(G*h)


def critical(q):
    return (q*q/G)**(1/3)


def conjugate(h, q):
    return h*(sqrt(1 + 8*q*q/(G*h**3)) - 1)/2


def friction(h, q, n, width, wide=False):
    radius = h if wide else width*h/(width + 2*h)
    return n*n*(q/h)**2/radius**(4/3)


def bisect(f, a, b, tolerance=1e-13):
    fa, fb = f(a), f(b)
    if fa == 0:
        return a
    if fb == 0:
        return b
    if fa*fb > 0:
        raise ValueError("No bracketed root")
    for _ in range(80):
        m = (a+b)/2
        fm = f(m)
        if b-a < tolerance:
            return m
        if fa*fm > 0:
            a, fa = m, fm
        else:
            b = m
    return (a+b)/2


def step(h, q, n, width, dx, branch, wide=False):
    """Step supercritical downstream or subcritical upstream by positive dx.

    E_up-E_down=dx*(Sf_up+Sf_down)/2; no step crosses the critical depth.
    Returns None when a forward supercritical step has no admissible root.
    """
    yc = critical(q)
    if not (dx > 0 and h > 0 and q > 0 and width > 0 and n >= 0):
        raise ValueError("Nonphysical input")
    sf = lambda y: friction(y, q, n, width, wide)
    if branch == "super":
        if h >= yc:
            raise ValueError("Supercritical starting state required")
        f = lambda y: energy(h,q)-energy(y,q)-dx*(sf(h)+sf(y))/2
        if f(yc) < 0:
            return None
        return bisect(f,h,yc)
    if branch != "sub" or h <= yc:
        raise ValueError("Subcritical starting state required")
    f = lambda y: energy(y,q)-energy(h,q)-dx*(sf(h)+sf(y))/2
    top = 2*h
    while f(top) < 0:
        top *= 2
    return bisect(f,h,top)


def interpolate(x, xs, ys):
    j = bisect_left(xs,x)
    if j == 0:
        return ys[0]
    if j == len(xs):
        return ys[-1]
    w = (x-xs[j-1])/(xs[j]-xs[j-1])
    return ys[j-1]*(1-w)+ys[j]*w


def solve(q, hin, hout, n, width=.46, x0=.305, xout=14., dx=.02, wide=False):
    count = round((xout-x0)/dx)
    dx = (xout-x0)/count
    xs = [x0+i*dx for i in range(count+1)]
    hs = [hin]
    for _ in range(count):
        h = step(hs[-1],q,n,width,dx,"super",wide)
        if h is None:
            break
        hs.append(h)
    hb = [hout]
    for _ in range(count):
        hb.append(step(hb[-1],q,n,width,dx,"sub",wide))
    hb.reverse()
    residual = [force(h,q)-force(hb[i],q) for i,h in enumerate(hs)]
    jump = None
    for i in range(len(residual)-1):
        if residual[i]*residual[i+1] <= 0:
            weight = residual[i]/(residual[i]-residual[i+1])
            xj = xs[i]+weight*dx
            h1 = interpolate(xj,xs[:len(hs)],hs)
            h2 = interpolate(xj,xs,hb)
            jump = dict(x_m=xj,h1_m=h1,h2_m=h2,
                        Fr1=q/sqrt(G*h1**3),
                        energy_loss_m=energy(h1,q)-energy(h2,q),
                        relative_force_residual=abs(force(h1,q)-force(h2,q))/force(h1,q))
            break
    return dict(q=q,n=n,x0=x0,xout=xout,dx=dx,jump=jump,
                supercritical_branch_last_x=xs[len(hs)-1],
                x=xs,h_super=hs,h_sub=hb)


def critical_distance(q, hin, n, width=.46, intervals=4000):
    """Independent depth-coordinate quadrature of dx/dh=(Fr²-1)/Sf."""
    yc=critical(q)
    dh=(yc-hin)/intervals
    def f(h):
        return (q*q/(G*h**3)-1)/friction(h,q,n,width)
    total=f(hin)+f(yc)
    for j in range(1,intervals):
        total+=(4 if j%2 else 2)*f(hin+j*dh)
    return total*dh/3
