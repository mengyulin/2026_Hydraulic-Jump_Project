/** Teaching adapter (2026-09-14): inactive MODEL_GN branches removed.
 * qcc scans include names before the C preprocessor, including disabled ones.
 * The selected MODEL_GN=0 equations, stages and diagnostics are unchanged.
 * Student code tour: ../docs/code-guide.md.
 */
/** GC1991 controlled explicit Saint-Venant/Green-Naghdi experiment.
 * Flat rectangular bed, SI, one horizontal dimension and one depth average.
 * Built with local instrumented copies of the pinned Basilisk headers.
 * See prepare_gc1991_sv_gn.py for the complete, reviewable header patch.
 */
#include "grid/multigrid1D.h"

#ifndef MODEL_GN
# define MODEL_GN 0
#endif
double in_h = .043, in_u = 2.737, out_h = .222;
double roughness = .008, channel_width = .46;
double end_time = 300., mean_start = 150., gn_buffer = .25;
double stage_qin, stage_qout, stage_fin, stage_fout, stage_gn;
double stage_drag, stage_active;
int boundary_kind = 1; // 0: original reconstructed ghosts; 1: imposed face fluxes.

# include "sv_instrumented.h"


scalar h_integral[], h2_integral[], u_integral[], first_integral[], second_integral[];
double volume0, momentum0, mass_in, mass_out, force_in, force_out, drag_impulse;
double gn_impulse, mean_weight, first_weight, second_weight;
double min_stage_h = HUGE, min_stage_in = HUGE, max_stage_in_error;
double max_mass_error, max_momentum_error, max_solver_ratio;
double active_time, all_time;
int max_solver_cycles, solver_failures, rejected;
FILE * history;

h[left] = dirichlet(in_h);
eta[left] = dirichlet(in_h);
u.n[left] = dirichlet(in_u);
h[right] = dirichlet(out_h);
eta[right] = dirichlet(out_h);
u.n[right] = neumann(0.);

double volume (void)
{
  double sum = 0.;
  foreach(reduction(+:sum)) sum += h[]*Delta;
  return sum;
}

double momentum (void)
{
  double sum = 0.;
  foreach(reduction(+:sum)) sum += h[]*u.x[]*Delta;
  return sum;
}

/** Both predictor and corrector evaluate the same Manning source. Only the
 * corrector flux/source is integrated by the final explicit-midpoint update.
 * The GN ledger is separate from the hydrostatic boundary force ledger.
 */
double update_checked (scalar * state, scalar * updates, double limit)
{
  stage_gn = stage_active = 0.;
  double next = update_saint_venant(state, updates, limit);

  scalar hs = state[0];
  vector us = vector(state[1]), du = vector(updates[1]);
  double total_drag = 0., minh = HUGE;
  foreach(reduction(+:total_drag) reduction(min:minh) reduction(min:next)) {
    minh = min(minh, hs[]);
    if (hs[] > dry) {
      double R = channel_width*hs[]/(channel_width + 2.*hs[]);
      double rate = G*sq(roughness)*fabs(us.x[])/pow(R, 4./3.);
      double source = - hs[]*rate*us.x[];
      du.x[] += source;
      total_drag += source*Delta;
      if (rate > 0.) next = min(next, .5/rate);
    }
  }
  stage_drag = total_drag;
  min_stage_h = min(min_stage_h, minh);
  min_stage_in = min(min_stage_in, stage_qin);
  max_stage_in_error = max(max_stage_in_error, fabs(stage_qin/(in_h*in_u) - 1.));
  return next;
}

/** Integrate a linear interpolation between old/new endpoint states over the
 * exact overlap with a statistics window. This uses every solver time step.
 */
double linear_integral (double old, double now, double a, double b, double step)
{
  return step*((b - a)*old + .5*(b*b - a*a)*(now - old));
}

void advance_checked (scalar * output, scalar * input, scalar * changes, double step)
{
  if (output != input) {
    advance_saint_venant(output, input, changes, step);
    return;
  }
  scalar old_h[], old_u[];
  foreach() { old_h[] = h[]; old_u[] = u.x[]; }
  advance_saint_venant(output, input, changes, step);
  mass_in += step*stage_qin; mass_out += step*stage_qout;
  force_in += step*stage_fin; force_out += step*stage_fout;
  drag_impulse += step*stage_drag; gn_impulse += step*stage_gn;
  active_time += step*stage_active; all_time += step;
  double a = clamp((mean_start - t)/step, 0., 1.);
  double b = clamp((end_time - t)/step, 0., 1.);
  double mid = (mean_start + end_time)/2.;
  double split = clamp((mid - t)/step, a, b);
  if (b > a) {
    foreach() {
      h_integral[] += linear_integral(old_h[], h[], a, b, step);
      u_integral[] += linear_integral(old_u[], u.x[], a, b, step);
      double d = h[] - old_h[];
      h2_integral[] += step*((b-a)*sq(old_h[]) + (b*b-a*a)*old_h[]*d +
                             (b*b*b-a*a*a)*sq(d)/3.);
      first_integral[] += linear_integral(old_h[], h[], a, split, step);
      second_integral[] += linear_integral(old_h[], h[], split, b, step);
    }
    mean_weight += step*(b-a);
    first_weight += step*(split-a); second_weight += step*(b-split);
  }
  double mr = volume() - volume0 - mass_in + mass_out;
  double pr = momentum() - momentum0 - force_in + force_out - drag_impulse - gn_impulse;
  max_mass_error = max(max_mass_error, fabs(mr));
  max_momentum_error = max(max_momentum_error, fabs(pr));
}

int main (int argc, char ** argv)
{
  if (argc != 14) {
    fprintf(stderr, "usage: solver hin uin hout n x0 xout N end average_start CFL boundary_kind breaking initial.dat\n");
    return 2;
  }
  in_h=atof(argv[1]); in_u=atof(argv[2]); out_h=atof(argv[3]); roughness=atof(argv[4]);
  double start=atof(argv[5]), finish=atof(argv[6]);
  N=atoi(argv[7]); end_time=atof(argv[8]); mean_start=atof(argv[9]);
  CFL=atof(argv[10]); boundary_kind=atoi(argv[11]);
  if (!(in_h > 0. && in_u > 0. && out_h > 0. && roughness >= 0. &&
        finish > start && N >= 32 && mean_start >= 0. && end_time > mean_start &&
        CFL > 0. && CFL <= .5 && (boundary_kind == 0 || boundary_kind == 1))) return 2;
  origin(start); size(finish-start); G=9.81;

  // Keep the input path in a field independent of user-specific directories.
  FILE * input=fopen(argv[13], "r");
  if (!input) return 2;
  fclose(input);
  history=fopen("history.dat", "w");
  if (!history) return 2;
  // init reads this file after the grid has been constructed.
  extern const char * initial_path;
  initial_path=argv[13];
  run();
  fclose(history);
  return rejected ? 3 : 0;
}

const char * initial_path;

event init (i = 0)
{
  FILE * input=fopen(initial_path, "r");
  if (!input) exit(2);
  foreach(serial) {
    double coordinate, depth, velocity;
    if (fscanf(input, "%lf %lf %lf", &coordinate, &depth, &velocity) != 3 ||
        fabs(coordinate-x) > 1e-8 || depth <= 0.) exit(2);
    zb[]=0.; h[]=depth; u.x[]=velocity; eta[]=depth;
    h_integral[]=h2_integral[]=u_integral[]=first_integral[]=second_integral[]=0.;
  }
  fclose(input);
  volume0=volume(); momentum0=momentum();
  update=update_checked; advance=advance_checked;
  fprintf(history, "# t dt V P mass_in mass_out force_in force_out drag_impulse gn_impulse mass_res momentum_res min_H max_H max_U x50 crossings stage_qin stage_qout max_in_error min_stage_h solver_ratio solver_cycles active_fraction\n");
}

event observe (t = 0.; t += 1.)
{
  double v=volume(), p=momentum(), lo=HUGE, hi=0., umax=0., x50=nan("");
  double prior_h=in_h, prior_x=X0, threshold=(in_h+out_h)/2.;
  int crossings=0;
  foreach(serial) {
    lo=min(lo,h[]); hi=max(hi,h[]); umax=max(umax,fabs(u.x[]));
    if (h[] >= threshold && prior_h < threshold) {
      if (!crossings) x50=prior_x+(x-prior_x)*(threshold-prior_h)/(h[]-prior_h);
      crossings++;
    }
    prior_h=h[]; prior_x=x;
  }
  fprintf(history, "%.12g %.12g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.12g %.12g %.12g %.12g %d %.17g %.17g %.12g %.12g %.12g %d %.12g\n",
          t,dt,v,p,mass_in,mass_out,force_in,force_out,drag_impulse,gn_impulse,
          v-volume0-mass_in+mass_out,p-momentum0-force_in+force_out-drag_impulse-gn_impulse,
          lo,hi,umax,x50,crossings,stage_qin,stage_qout,max_stage_in_error,min_stage_h,
          max_solver_ratio,max_solver_cycles,all_time ? active_time/all_time : 0.);
  fflush(history);
  if (!isfinite(v) || !isfinite(p) || lo <= 1e-6 || min_stage_h <= 0. ||
      hi > 2. || umax > 50. || max_mass_error > 1e-7 || max_momentum_error > 1e-7 ||
      solver_failures > 4 || (t > 5. && boundary_kind && max_stage_in_error > 1e-8)) {
    rejected=1;
    fprintf(stderr, "Rejected at t=%.12g: Hmin=%g stage_Hmin=%g mass=%g momentum=%g pressure_failures=%d\n",
            t,lo,min_stage_h,max_mass_error,max_momentum_error,solver_failures);
    return 1;
  }
}

event finish (t = end_time)
{
  FILE * f=fopen("profile.dat", "w");
  fprintf(f,"# x H_mean H_sd U_mean H_first H_second H_final U_final q_final\n");
  foreach(serial) {
    double hm=h_integral[]/mean_weight;
    fprintf(f,"%.12g %.12g %.12g %.12g %.12g %.12g %.12g %.12g %.12g\n",x,hm,
            sqrt(max(0.,h2_integral[]/mean_weight-sq(hm))),u_integral[]/mean_weight,
            first_integral[]/first_weight,second_integral[]/second_weight,h[],u.x[],h[]*u.x[]);
  }
  fclose(f);
  f=fopen("verification.dat","w");
  fprintf(f,"# max_mass_error max_momentum_error max_inlet_error min_stage_h mean_weight first_weight second_weight max_pressure_ratio pressure_failures active_fraction\n");
  fprintf(f,"%.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %d %.17g\n",
          max_mass_error,max_momentum_error,max_stage_in_error,min_stage_h,
          mean_weight,first_weight,second_weight,max_solver_ratio,solver_failures,
          all_time ? active_time/all_time : 0.);
  fclose(f);
  fprintf(stderr,"Completed t=%.12g steps=%d model_gn=%d\n",t,i,MODEL_GN);
  return 1;
}
