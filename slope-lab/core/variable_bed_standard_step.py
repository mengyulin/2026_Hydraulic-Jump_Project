"""GC1991-based standard step on a prismatic rectangular, piecewise linear bed.

SI; q is discharge per unit width; x increases downstream; alpha=beta=1.
Reuse the unmodified GC1991 hydraulic functions. Track each boundary-anchored
branch separately, including reverse-control diagnostic marches. No critical
depth fallback, transcritical restart, or HEC-RAS mixed-flow emulation.
Contraction/expansion losses depend on velocity-head change along physical
flow, independently of the numerical marching direction. Arithmetic Sf only.
"""
from bisect import bisect_left
from dataclasses import dataclass
import math

from gc1991_standard_step import (
    G, energy, force, critical, conjugate, friction, bisect,
)


@dataclass(frozen=True)
class Flow:
    q: float
    width: float
    n: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.q, self.width, self.n)):
            raise ValueError("Finite hydraulic inputs required")
        if self.q <= 0 or self.width <= 0 or self.n < 0:
            raise ValueError("Require q>0, width>0 and n>=0")

    @property
    def yc(self):
        return critical(self.q)

    def sf(self, h):
        return friction(h, self.q, self.n, self.width)

    def sf_derivative(self, h):
        # R=Bh/(B+2h): d ln Sf/dh = -10/(3h)+8/[3(B+2h)].
        return self.sf(h) * (-10 / (3 * h) + 8 / (3 * (self.width + 2 * h)))

    def fr(self, h):
        return self.q / math.sqrt(G * h ** 3)

    def normal_depth(self, slope):
        if not math.isfinite(slope) or slope <= 0 or self.n <= 0:
            raise ValueError("Normal depth requires positive n and energy slope")
        hi = 2 * self.yc
        while self.sf(hi) > slope:
            hi *= 2
        return bisect(lambda h: self.sf(h) - slope, self.yc * 1e-6, hi)


@dataclass(frozen=True)
class Losses:
    contraction: float = 0.0
    expansion: float = 0.0

    def __post_init__(self):
        if not all(math.isfinite(v) and 0 <= v < 1
                   for v in (self.contraction, self.expansion)):
            raise ValueError("This solver supports 0 <= Cc, Ce < 1")


class Bed:
    def __init__(self, points):
        self.points = [(float(x), float(z)) for x, z in points]
        if len(self.points) < 2 or not all(math.isfinite(v) for p in self.points for v in p):
            raise ValueError("At least two finite bed points required")
        self.x = [p[0] for p in self.points]
        if any(b <= a for a, b in zip(self.x, self.x[1:])):
            raise ValueError("Bed x must strictly increase")

    def z(self, x):
        if x < self.x[0] - 1e-10 or x > self.x[-1] + 1e-10:
            raise ValueError("Outside bed domain")
        i = max(0, min(len(self.x) - 2, bisect_left(self.x, x) - 1))
        xa, za = self.points[i]
        xb, zb = self.points[i + 1]
        return za + (zb - za) * (x - xa) / (xb - xa)

    def grid(self, dx):
        if not math.isfinite(dx) or dx <= 0:
            raise ValueError("Positive section spacing required")
        # Subdivide each segment independently: every bed break is preserved.
        out = [self.x[0]]
        for a, b in zip(self.x, self.x[1:]):
            count = max(1, math.ceil((b - a) / dx - 1e-10))
            out.extend(a + (b - a) * i / count for i in range(1, count + 1))
        return out


def regime(h, flow):
    if not math.isfinite(h) or h <= 0:
        raise ValueError("Positive finite water depth required")
    if abs(h / flow.yc - 1) <= 1e-10:
        return "critical"
    return "subcritical" if h > flow.yc else "supercritical"


def boundary_depth(spec, flow, z):
    kind = spec["type"]
    if kind == "normal_depth":
        h = flow.normal_depth(spec["slope"])
    elif kind == "depth":
        h = float(spec["depth_m"])
    elif kind == "water_surface":
        h = float(spec["elevation_m"]) - z
    elif kind == "critical_depth":
        h = flow.yc
    else:
        raise ValueError(f"Unsupported boundary type: {kind}")
    regime(h, flow)
    return h


def local_loss(h_up, h_down, flow, losses):
    vh_up = flow.q ** 2 / (2 * G * h_up ** 2)
    vh_down = flow.q ** 2 / (2 * G * h_down ** 2)
    delta = vh_down - vh_up
    c = losses.contraction if delta >= 0 else losses.expansion
    return c * abs(delta)


def residual(h_new, h_known, x_known, z_known, x_new, z_new, flow, losses):
    """Signed energy equation: new-known + sign(dx)*losses = 0."""
    direction = 1 if x_new > x_known else -1
    length = abs(x_new - x_known)
    hu, hd = (h_known, h_new) if direction == 1 else (h_new, h_known)
    hf = length * (flow.sf(hu) + flow.sf(hd)) / 2
    return (z_new - z_known + energy(h_new, flow.q) - energy(h_known, flow.q)
            + direction * (hf + local_loss(hu, hd, flow, losses)))


def effective_coefficient(h_new, h_known, direction, losses):
    """1-a Fr² is the continuous depth-gradient coefficient on this leg."""
    accelerating = direction * (h_new - h_known) < 0
    return 1 + losses.contraction if accelerating else 1 - losses.expansion


def _step_root(h, x, z, xn, zn, flow, losses, branch):
    """Isolate candidate roots with derivative extrema; reject spurious roots.

    Reverse-control marches can have multiple same-Froude-regime roots.
    Retain the effective-energy orientation inherited from the C=0 branch:
    d(E + signed local loss)/dh has the sign of 1-Fr² on that branch.
    A loss-induced fold terminates this branch instead of changing its
    orientation while retaining the same nominal Froude regime.
    If more than one remains, stop as ambiguous rather than switch roots.
    """
    direction = 1 if xn > x else -1
    length = abs(xn - x)
    f = lambda y: residual(y, h, x, z, xn, zn, flow, losses)
    if abs(f(h)) <= 1e-13:
        return dict(status="ok", depth=h, root_count=1)
    yc = flow.yc
    lo, hi = (yc, max(2 * h, 2 * yc)) if branch == "subcritical" else (yc * 1e-6, yc)
    if branch == "subcritical":
        for _ in range(40):
            if f(hi) > 0:
                break
            hi *= 2
        else:
            return dict(status="root_search_bound_exhausted", depth=None, root_count=0)
    def df(y):
        a = effective_coefficient(y, h, direction, losses)
        return 1 - a * flow.fr(y) ** 2 + direction * length * flow.sf_derivative(y) / 2
    # Split at the loss kink and all resolved stationary points. The dense
    # near-yc portion complements logarithmic coverage at very shallow depth.
    nodes = {lo, hi}
    nodes.update(lo * (hi / lo) ** (i / 64) for i in range(1, 64))
    nodes.update(lo + (hi - lo) * i / 64 for i in range(1, 64))
    for v in (h, yc * (1 + losses.contraction) ** (1 / 3),
              yc * (1 - losses.expansion) ** (1 / 3)):
        if lo < v < hi:
            nodes.add(v)
    nodes = sorted(nodes)
    cuts = {lo, hi}
    if lo < h < hi:
        cuts.add(h)
    for a, b in zip(nodes, nodes[1:]):
        # One-sided evaluations avoid interpreting the Cc/Ce kink as df=0.
        aa = math.nextafter(a, b)
        bb = math.nextafter(b, a)
        if df(aa) * df(bb) < 0:
            cuts.add(bisect(df, aa, bb))
    cuts = sorted(cuts)
    roots = []
    for a, b in zip(cuts, cuts[1:]):
        if f(a) * f(b) <= 0:
            y = bisect(f, a, b)
            if all(abs(y - v) > 1e-10 * yc for v in roots):
                roots.append(y)
    accepted = []
    orientation = 1 if branch == "subcritical" else -1
    for y in roots:
        if regime(y, flow) != branch:
            continue
        a = effective_coefficient(y, h, direction, losses)
        d0 = 1 - a * flow.fr(y) ** 2
        d_known = 1 - a * flow.fr(h) ** 2
        # A distant root can regain the right derivative sign after crossing
        # a loss-induced fold. Both ends of this continuous loss leg must
        # retain the inherited orientation; otherwise it is a root switch.
        if orientation * d_known > 0 and orientation * d0 > 0 and orientation * df(y) > 0:
            accepted.append(y)
    if len(accepted) == 1:
        return dict(status="ok", depth=accepted[0], root_count=len(roots))
    return dict(status="no_admissible_root" if not accepted else "ambiguous_roots",
                depth=None, root_count=len(roots))


def critical_event(h, x, target, bed, flow, losses):
    """Solve location and yc simultaneously within this linear-bed step.

    A zero residual at yc is a terminal event, never an ordinary grid reset.
    The trace must approach yc on an admissible same-regime continuation.
    """
    direction = 1 if target > x else -1
    length = abs(target - x)
    slope = -(bed.z(target) - bed.z(x)) / (target - x)
    hu, hd = (h, flow.yc) if direction == 1 else (flow.yc, h)
    numerator = energy(flow.yc, flow.q) - energy(h, flow.q) + direction * local_loss(hu, hd, flow, losses)
    denominator = direction * ((flow.sf(h) + flow.sf(flow.yc)) / 2 - slope)
    if denominator == 0:
        return None
    distance = -numerator / denominator
    if not 1e-10 < distance <= length + 1e-10:
        return None
    xe = x + direction * distance
    # Verify the connected root approaches yc; rules out a remote root
    # across a discrete fold or a C-dependent singularity.
    xp = x + direction * distance * (1 - 1e-5)
    check = _step_root(h, x, bed.z(x), xp, bed.z(xp), flow, losses, regime(h, flow))
    if check["status"] != "ok" or abs(check["depth"] - flow.yc) > .005 * flow.yc:
        return None
    return dict(x_m=xe, depth_m=flow.yc,
                energy_residual_m=residual(flow.yc, h, x, bed.z(x), xe, bed.z(xe), flow, losses),
                Fr=1.0, kind="energy_balanced_critical_endpoint")


def trace(h_start, start, grid, bed, flow, losses, max_halvings=16):
    """Follow the starting regime; off-grid subdivisions/terminal points are logged."""
    branch = regime(h_start, flow)
    direction = 1 if start == "upstream" else -1
    targets = grid if direction == 1 else list(reversed(grid))
    x0 = targets[0]
    rows = [dict(x_m=x0, z_m=bed.z(x0), depth_m=h_start,
                 Fr=flow.fr(h_start), energy_residual_m=0., step_kind="boundary")]
    terminal = None
    if branch == "critical":
        return dict(start=start, regime=branch, role="control_condition_required",
                    rows=rows, termination=dict(kind="critical_boundary_no_continuation", x_m=x0),
                    internal_substeps=0)
    natural = (direction == 1 and branch == "supercritical") or (direction == -1 and branch == "subcritical")
    subdivisions = 0
    for target in targets[1:]:
        while direction * (target - rows[-1]["x_m"]) > 1e-9:
            last = rows[-1]
            x, h = last["x_m"], last["depth_m"]
            xn = target
            for halves in range(max_halvings + 1):
                result = _step_root(h, x, bed.z(x), xn, bed.z(xn), flow, losses, branch)
                if result["status"] == "ok":
                    hn = result["depth"]
                    rows.append(dict(x_m=xn, z_m=bed.z(xn), depth_m=hn,
                                     Fr=flow.fr(hn),
                                     energy_residual_m=residual(hn, h, x, bed.z(x), xn, bed.z(xn), flow, losses),
                                     step_kind="grid" if xn == target else "internal_substep"))
                    if halves:
                        subdivisions += 1
                    break
                event = critical_event(h, x, xn, bed, flow, losses)
                if event:
                    rows.append(dict(x_m=event["x_m"], z_m=bed.z(event["x_m"]),
                                     depth_m=flow.yc, Fr=1., energy_residual_m=event["energy_residual_m"],
                                     step_kind="critical_endpoint"))
                    terminal = event | {"last_regular_x_m": x,
                                       "requested_step_interval_m": sorted([x, xn])}
                    break
                if halves == max_halvings:
                    terminal = dict(kind=result["status"], x_m=x, Fr=flow.fr(h),
                                    last_regular_x_m=x, requested_step_interval_m=sorted([x, xn]))
                    break
                xn = (x + xn) / 2
            if terminal:
                break
        if terminal:
            break
    return dict(start=start, regime=branch,
                role="natural_control_direction" if natural else "boundary_consistency_diagnostic",
                rows=rows, termination=terminal or dict(kind="domain_end", x_m=rows[-1]["x_m"]),
                internal_substeps=subdivisions)


def sample(rows, x, include_terminal=False):
    data = sorted(rows, key=lambda r: r["x_m"])
    if not include_terminal:
        data = [r for r in data if r["step_kind"] != "critical_endpoint"]
    return _sample_sorted(data, [r["x_m"] for r in data], x)


def _sample_sorted(data, xs, x):
    if not data or x < data[0]["x_m"] - 1e-9 or x > data[-1]["x_m"] + 1e-9:
        return None
    i = bisect_left(xs, x)
    if i == 0:
        return data[0]["depth_m"]
    if i == len(xs):
        return data[-1]["depth_m"]
    w = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return data[i - 1]["depth_m"] * (1 - w) + data[i]["depth_m"] * w


def match_jump(up, down, flow):
    """Only natural supercritical-inlet/subcritical-outlet matching is admissible."""
    if up["regime"] != "supercritical" or down["regime"] != "subcritical":
        return []
    ur = sorted((r for r in up["rows"] if r["step_kind"] != "critical_endpoint"), key=lambda r:r["x_m"])
    dr = sorted((r for r in down["rows"] if r["step_kind"] != "critical_endpoint"), key=lambda r:r["x_m"])
    ux, dx = [r["x_m"] for r in ur], [r["x_m"] for r in dr]
    us = lambda x: _sample_sorted(ur, ux, x)
    ds = lambda x: _sample_sorted(dr, dx, x)
    xs = sorted({r["x_m"] for tr in (up, down) for r in tr["rows"]
                 if r["step_kind"] != "critical_endpoint"})
    candidates = []
    def diff(x):
        a, b = us(x), ds(x)
        return None if a is None or b is None else force(a, flow.q) - force(b, flow.q)
    for a, b in zip(xs, xs[1:]):
        ra, rb = diff(a), diff(b)
        if ra is None or rb is None or not (ra >= 0 and rb <= 0):
            continue
        xj = bisect(diff, a, b)
        h1, h2 = us(xj), ds(xj)
        candidates.append(dict(x_m=xj, bracket_m=[a, b], y1_m=h1, y2_m=h2,
                               Fr1=flow.fr(h1), energy_loss_m=energy(h1, flow.q)-energy(h2, flow.q),
                               relative_force_residual=abs(force(h1, flow.q)-force(h2, flow.q))/force(h1, flow.q)))
    return candidates


def solve(case, dx):
    flow = Flow(case["Q_m3s"] / case["width_m"], case["width_m"], case["n"])
    bed = Bed(case["bed"])
    losses = Losses(**case.get("losses", {}))
    grid = bed.grid(dx)
    hin = boundary_depth(case["upstream"], flow, bed.z(grid[0]))
    hout = boundary_depth(case["downstream"], flow, bed.z(grid[-1]))
    up = trace(hin, "upstream", grid, bed, flow, losses)
    down = trace(hout, "downstream", grid, bed, flow, losses)
    jumps = match_jump(up, down, flow)
    # Report the unused/opposite boundary discrepancy, without imposing it
    # by resetting or stitching two same-regime curves.
    out_from_up = sample(up["rows"], grid[-1])
    in_from_down = sample(down["rows"], grid[0])
    status = "unresolved_boundary_compatibility"
    if len(jumps) == 1:
        status = "single_momentum_match"
    elif up["regime"] == down["regime"] == "subcritical" and in_from_down is not None:
        status = "subcritical_downstream_control"
    elif up["regime"] == down["regime"] == "supercritical" and out_from_up is not None:
        status = "supercritical_upstream_control"
    summary = dict(case_id=case["id"], dx_requested_m=dx, Q_m3s=case["Q_m3s"],
                   width_m=flow.width, n=flow.n, losses=case.get("losses", {}),
                   yc_m=flow.yc, hin_m=hin, hout_m=hout,
                   upstream_regime=up["regime"], downstream_regime=down["regime"],
                   Fr_in=flow.fr(hin), Fr_out=flow.fr(hout), status=status,
                   up_termination=up["termination"], down_termination=down["termination"],
                   outlet_depth_from_upstream_m=out_from_up,
                   outlet_depth_mismatch_m=None if out_from_up is None else out_from_up-hout,
                   inlet_depth_from_downstream_m=in_from_down,
                   inlet_depth_mismatch_m=None if in_from_down is None else in_from_down-hin,
                   maximum_energy_residual_m=max(abs(r["energy_residual_m"]) for tr in (up,down) for r in tr["rows"]),
                   internal_substeps=up["internal_substeps"]+down["internal_substeps"],
                   jumps=jumps)
    return dict(summary=summary, upstream_trace=up, downstream_trace=down)
