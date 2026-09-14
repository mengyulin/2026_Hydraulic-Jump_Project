/** Startup/source/strip diagnostics derived from the frozen shared-flux version.
 * Basilisk provides the uniform grid and event clock. Arrays hold nodal states
 * and shared faces explicitly, including the two half-width end volumes.
 * B is the paper's steady-iteration correction, not full unsteady GN.
 */
#include "grid/cartesian1D.h"
#include "run.h"
#define CAP 4098
typedef struct { double h, q; } State;
State y[CAP], p[CAP], z[CAP], f[CAP], dflux[CAP], rhs[CAP];
double vel[CAP], hydro[CAP], bflux[CAP], sensor[CAP];
double meanh[CAP], meanq[CAP], meanh2[CAP], first[CAP], last[CAP];
double meanflux[CAP], meandiff[CAP];
int M, nodes, use_b, periodic_domain, scheme, rejected=0, steps=0;
int source_mode=0, strip_mode=0;
State accepted_start[CAP], adv_face[CAP], b_face[CAP];
FILE *diagnostics;
double hin, uin, hout, mann, xa, xb, cfl, kappa, finish, avg, max_dt;
double dx, now=0., wt=0., wfirst=0., wlast=0.;
double v0, p0, mass_impulse=0., momentum_impulse=0., source_impulse=0.;
double max_mass_error=0., max_momentum_error=0., min_depth=HUGE;
double filter_energy=0., max_filter_rate=0.;
const double g=9.81, width=.46;
FILE *history;
const char *initial_path;

double weight(int j) { return !periodic_domain && (j==0 || j==nodes-1) ? .5 : 1.; }
int idx(int j) { return periodic_domain ? (j%nodes+nodes)%nodes : j; }
double radius(double h) { return width*h/(width+2.*h); }
double source(State a) { return source_mode ? 0. : -g*sq(mann)*a.q*fabs(a.q)/a.h/pow(radius(a.h),4./3.); }

/** Exact q_t=-K(h)q|q| with h fixed; signed impulse for the global ledger. */
double exact_drag(State *a,double tau) {
  double impulse=0.;
  for(int j=0;j<nodes;j++) {
    double old=a[j].q;
    double K=g*sq(mann)/(a[j].h*pow(radius(a[j].h),4./3.));
    a[j].q=old/(1.+tau*K*fabs(old));
    impulse+=dx*weight(j)*(a[j].q-old);
  }
  return impulse;
}

void failure_dump(State *a,const char *stage) {
  FILE *fp=fopen("stage_failure.dat","w");
  fprintf(fp,"# time %.17g dt %.17g stage %s\n",t,dt,stage);
  fprintf(fp,"# j x h q accepted_h accepted_q stage_h stage_q rhs_h rhs_q source_q adv_momentum_gradient b_momentum_gradient artificial_momentum_gradient\n");
  for(int j=0;j<nodes;j++) {
    double vol=dx*weight(j);
    State base=stage[0]=='p' ? y[j] : p[j];
    fprintf(fp,"%d %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n",
     j,xa+j*dx,a[j].h,a[j].q,accepted_start[j].h,accepted_start[j].q,base.h,base.q,
     rhs[j].h,rhs[j].q,source(base),-(adv_face[j+1].q-adv_face[j].q)/vol,
     -(b_face[j+1].q-b_face[j].q)/vol,-(dflux[j+1].q-dflux[j].q)/vol);
  }
  fclose(fp);
}
double energy(State a) { return .5*sq(a.q)/a.h+.5*g*sq(a.h); }
double sum_state(State *a,int component) {
  double s=0.; for(int j=0;j<nodes;j++) s+=dx*weight(j)*(component ? a[j].q : a[j].h); return s;
}
int valid(State *a,const char *stage) {
  for(int j=0;j<nodes;j++) {
    min_depth=min(min_depth,a[j].h);
    if(!(a[j].h>1e-8) || !isfinite(a[j].h) || !isfinite(a[j].q) || a[j].h>10. || fabs(a[j].q)>100.) {
      fprintf(stderr,"rejected t=%.17g stage=%s node=%d h=%.17g q=%.17g\n",t,stage,j,a[j].h,a[j].q);
      failure_dump(a,stage);rejected=1;return 0;
    }
  }
  return 1;
}

/** Face k separates nodes k-1 and k. Exterior faces are 0 and nodes.
 * The same face value is used with opposite signs in both adjacent volumes.
 * Stage +/- is the original forward predictor / backward corrector pairing.
 */
void operator(State *a,int direction,double *mh,double *mq,double *sqint) {
  for(int j=0;j<nodes;j++) {
    vel[j]=a[j].q/a[j].h;
    hydro[j]=sq(a[j].q)/a[j].h+.5*g*sq(a[j].h);
    sensor[j]=bflux[j]=0.;
  }
  for(int j=0;j<nodes;j++) if(periodic_domain || (j>0 && j<nodes-1)) {
    int l=idx(j-1),r=idx(j+1);
    double ux=direction>0 ? (vel[r]-vel[j])/dx : (vel[j]-vel[l])/dx;
    if(use_b) bflux[j]=-cube(a[j].h)*(vel[j]*(vel[r]-2.*vel[j]+vel[l])/sq(dx)-sq(ux))/3.;
    sensor[j]=fabs(a[r].h-2.*a[j].h+a[l].h)/(fabs(a[r].h)+2.*fabs(a[j].h)+fabs(a[l].h));
  }
  int start=periodic_domain ? 0 : 1;
  for(int k=start;k<nodes;k++) {
    int l=idx(k-1),r=idx(k),ll=idx(k-2),rr=idx(k+1);
    int high=scheme && (periodic_domain || (k>=4 && k<=M-2));
    int base=direction>0 ? r : l;
    f[k]=(State){a[base].q,hydro[base]};
    b_face[k]=(State){0.,0.};
    if(high) {
      int far=direction>0 ? rr : ll;
      f[k].h+=(a[base].q-a[far].q)/6.;
      f[k].q+=(hydro[base]-hydro[far])/6.+(7.*bflux[base]-bflux[far])/6.;
      b_face[k].q=(7.*bflux[base]-bflux[far])/6.;
    }
    double speed=max(fabs(vel[l])+sqrt(g*a[l].h),fabs(vel[r])+sqrt(g*a[r].h));
    if(strip_mode==2 || (strip_mode==1 && !high)) {
      // Fixed Rusanov hydrostatic flux; the B correction and kappa are unchanged.
      f[k].h=.5*(a[l].q+a[r].q)-.5*speed*(a[r].h-a[l].h);
      f[k].q=.5*(hydro[l]+hydro[r])-.5*speed*(a[r].q-a[l].q)+b_face[k].q;
    }
    adv_face[k]=(State){f[k].h,f[k].q-b_face[k].q};
    double eps=kappa*speed*max(sensor[l],sensor[r]);
    dflux[k]=(State){-eps*(a[r].h-a[l].h),-eps*(a[r].q-a[l].q)};
    f[k].h+=dflux[k].h;f[k].q+=dflux[k].q;
    max_filter_rate=max(max_filter_rate,eps/dx);
  }
  if(periodic_domain) { f[nodes]=f[0];dflux[nodes]=dflux[0];adv_face[nodes]=adv_face[0];b_face[nodes]=b_face[0]; }
  else {
    // Strong supercritical reservoir inflow is prescribed as physical flux.
    double uout=vel[nodes-1]+2.*sqrt(g*a[nodes-1].h)-2.*sqrt(g*hout);
    double exit_discharge=hout*uout;
    f[0]=(State){hin*uin,hin*sq(uin)+.5*g*sq(hin)};
    f[nodes]=(State){exit_discharge,sq(exit_discharge)/hout+.5*g*sq(hout)};
    dflux[0]=dflux[nodes]=(State){0.,0.};
    adv_face[0]=f[0];adv_face[nodes]=f[nodes];
    b_face[0]=b_face[nodes]=(State){0.,0.};
  }
  *mh=f[0].h-f[nodes].h;*mq=f[0].q-f[nodes].q;*sqint=0.;
  for(int j=0;j<nodes;j++) {
    double vol=dx*weight(j),s=source(a[j]);
    rhs[j]=(State){-(f[j+1].h-f[j].h)/vol,-(f[j+1].q-f[j].q)/vol+s};
    *sqint+=vol*s;
  }
}

void record(void) {
  double emin=sum_state(y,0)-v0-mass_impulse;
  double pm=sum_state(y,1)-p0-momentum_impulse-source_impulse;
  fprintf(history,"%.17g %d %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n",now,steps,
          sum_state(y,0),sum_state(y,1),emin,pm,y[0].h,y[nodes-1].h,y[nodes-1].q);
  fflush(history);
  double lo=HUGE,hi=-HUGE,ql=HUGE,qh=-HUGE,rough=0.;int where=0;
  for(int j=0;j<nodes;j++) {
    if(y[j].h<lo) { lo=y[j].h;where=j; }
    hi=max(hi,y[j].h);ql=min(ql,y[j].q);qh=max(qh,y[j].q);
    if(j>0 && j<nodes-1)rough+=fabs(y[j+1].h-2.*y[j].h+y[j-1].h);
  }
  fprintf(diagnostics,"%.17g %.17g %.17g %.17g %.17g %d %.17g %.17g\n",now,lo,hi,ql,qh,where,xa+where*dx,rough);
  fflush(diagnostics);
}

int main(int argc,char **argv) {
  if(argc!=4)return 2;
  FILE *options=fopen(argv[3],"r");if(!options)return 2;
  int options_count=fscanf(options,"%d %d",&source_mode,&strip_mode);fclose(options);
  if(options_count!=2 || source_mode<0 || source_mode>1 || strip_mode<0 || strip_mode>2)return 2;
  FILE *fp=fopen(argv[1],"r");if(!fp)return 2;
  int n=fscanf(fp,"%d %d %d %d %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf",
   &M,&use_b,&periodic_domain,&scheme,&hin,&uin,&hout,&mann,&xa,&xb,&cfl,&kappa,&finish,&avg,&max_dt);
  fclose(fp);
  if(n!=15 || M<8 || M>4096 || use_b<0 || use_b>1 || periodic_domain<0 || periodic_domain>1 || scheme<0 || scheme>1 ||
     hin<=0 || hout<=0 || mann<0 || xb<=xa || cfl<=0 || cfl>.65 || kappa<0 || finish<=avg || avg<0 || max_dt<=0)return 2;
  nodes=periodic_domain ? M : M+1;dx=(xb-xa)/M;
  N=nodes;origin(xa-dx/2.);size(nodes*dx);initial_path=argv[2];
  history=fopen("history.dat","w");if(!history)return 2;
  fprintf(history,"# time steps volume momentum mass_error momentum_error inlet_node_h outlet_node_h outlet_node_q\n");
  diagnostics=fopen("diagnostics.dat","w");if(!diagnostics)return 2;
  fprintf(diagnostics,"# time min_h max_h min_q max_q min_h_node min_h_x roughness_sum\n");
  run();fclose(history);fclose(diagnostics);return rejected ? 3 : 0;
}

event init(i=0) {
  FILE *fp=fopen(initial_path,"r");if(!fp)exit(2);
  for(int j=0;j<nodes;j++) {
    double xj;if(fscanf(fp,"%lf %lf %lf",&xj,&y[j].h,&y[j].q)!=3 || fabs(xj-(xa+j*dx))>1e-8)exit(2);
  }
  fclose(fp);if(!valid(y,"initial"))return 1;
  v0=sum_state(y,0);p0=sum_state(y,1);record();
}

event advance(i++;t<finish) {
  if(t>=finish-1e-10)return 1;
  if(steps>=2000000) { rejected=1;fprintf(stderr,"step_limit\n");return 1; }
  double speed=0.;
  for(int j=0;j<nodes;j++) {
    double u=fabs(y[j].q/y[j].h),c=sqrt(g*y[j].h);
    // Conservative explicit third-derivative estimate, not a stability proof.
    speed=max(speed,u+c+(use_b ? 2.*sq(y[j].h)*u/(3.*sq(dx)) : 0.));
  }
  dt=dtnext(min(min(cfl*dx*(periodic_domain?1.:.5)/speed,max_dt),finish-t));
  if(!(dt>1e-12)) { rejected=1;fprintf(stderr,"small_timestep\n");return 1; }
  memcpy(accepted_start,y,nodes*sizeof(State));
  double split_impulse=source_mode ? exact_drag(y,.5*dt) : 0.;
  double mh1,mq1,s1,mh2,mq2,s2;
  operator(y,1,&mh1,&mq1,&s1);
  double saved_f[CAP],saved_d[CAP];
  for(int k=0;k<=nodes;k++) { saved_f[k]=f[k].h;saved_d[k]=dflux[k].h; }
  // Diagnostic first-order energy rate from the dissipative part of each stage.
  double de1=0.,de2=0.;
  for(int j=0;j<nodes;j++) {
    double u=y[j].q/y[j].h;
    de1-=(-.5*sq(u)+g*y[j].h)*(dflux[j+1].h-dflux[j].h)+u*(dflux[j+1].q-dflux[j].q);
    p[j]=(State){y[j].h+dt*rhs[j].h,y[j].q+dt*rhs[j].q};
  }
  if(!valid(p,"predictor")) { memcpy(y,accepted_start,nodes*sizeof(State));return 1; }
  operator(p,-1,&mh2,&mq2,&s2);
  for(int j=0;j<nodes;j++) {
    double u=p[j].q/p[j].h;
    de2-=(-.5*sq(u)+g*p[j].h)*(dflux[j+1].h-dflux[j].h)+u*(dflux[j+1].q-dflux[j].q);
    z[j]=(State){.5*(y[j].h+p[j].h+dt*rhs[j].h),.5*(y[j].q+p[j].q+dt*rhs[j].q)};
  }
  if(!valid(z,"corrector")) { memcpy(y,accepted_start,nodes*sizeof(State));return 1; }
  if(source_mode) {
    split_impulse+=exact_drag(z,.5*dt);
    memcpy(y,accepted_start,nodes*sizeof(State));
  }
  double aa=clamp((avg-t)/dt,0.,1.),bb=clamp((finish-t)/dt,0.,1.);
  double split=clamp((.5*(avg+finish)-t)/dt,aa,bb);
  for(int j=0;j<nodes;j++) {
    double dh=z[j].h-y[j].h;
    meanh[j]+=dt*((bb-aa)*y[j].h+.5*(bb*bb-aa*aa)*dh);
    meanq[j]+=dt*((bb-aa)*y[j].q+.5*(bb*bb-aa*aa)*(z[j].q-y[j].q));
    meanh2[j]+=dt*((bb-aa)*sq(y[j].h)+(bb*bb-aa*aa)*y[j].h*dh+(cube(bb)-cube(aa))*sq(dh)/3.);
    first[j]+=dt*((split-aa)*y[j].h+.5*(split*split-aa*aa)*dh);
    last[j]+=dt*((bb-split)*y[j].h+.5*(bb*bb-split*split)*dh);
    y[j]=z[j];
  }
  // A step-mean face flux with exact window overlap, consistent with RK impulse.
  for(int k=0;k<=nodes;k++) {
    meanflux[k]+=.5*dt*(bb-aa)*(saved_f[k]+f[k].h);
    meandiff[k]+=.5*dt*(bb-aa)*(saved_d[k]+dflux[k].h);
  }
  wt+=dt*(bb-aa);wfirst+=dt*(split-aa);wlast+=dt*(bb-split);
  mass_impulse+=.5*dt*(mh1+mh2);momentum_impulse+=.5*dt*(mq1+mq2);source_impulse+=.5*dt*(s1+s2)+split_impulse;
  filter_energy+=.5*dt*(de1+de2);
  max_mass_error=max(max_mass_error,fabs(sum_state(y,0)-v0-mass_impulse));
  max_momentum_error=max(max_momentum_error,fabs(sum_state(y,1)-p0-momentum_impulse-source_impulse));
  steps++;now=t+dt;
  if(steps==1 || (int)now>(int)t || now>=finish-1e-10)record();
}

event outputs(t=end) {
  FILE *fp=fopen("profile.dat","w");
  fprintf(fp,"# x h_final q_final h_mean q_mean h_sd mean_first mean_last\n");
  for(int j=0;j<nodes;j++) {
    double h=wt>0 ? meanh[j]/wt : NAN;
    fprintf(fp,"%.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n",xa+j*dx,y[j].h,y[j].q,h,
     wt>0?meanq[j]/wt:NAN,wt>0?sqrt(max(0.,meanh2[j]/wt-h*h)):NAN,
     wfirst>0?first[j]/wfirst:NAN,wlast>0?last[j]/wlast:NAN);
  }
  fclose(fp);fp=fopen("face_flux.dat","w");fprintf(fp,"# x mass_flux artificial_mass_flux\n");
  for(int k=0;k<=nodes;k++) {
    double xface=periodic_domain ? xa+(k-.5)*dx : (k==0?xa:k==nodes?xb:xa+(k-.5)*dx);
    fprintf(fp,"%.17g %.17g %.17g\n",xface,wt>0?meanflux[k]/wt:NAN,wt>0?meandiff[k]/wt:NAN);
  }
  fclose(fp);fp=fopen("budget.dat","w");
  fprintf(fp,"# actual_time steps rejected dx weight mass_error_max momentum_error_max mass_impulse momentum_impulse source_impulse filter_energy_rate_integral min_stage_h max_filter_rate final_volume final_momentum\n");
  fprintf(fp,"%.17g %d %d %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n",
   now,steps,rejected,dx,wt,max_mass_error,max_momentum_error,mass_impulse,momentum_impulse,source_impulse,
   filter_energy,min_depth,max_filter_rate,sum_state(y,0),sum_state(y,1));fclose(fp);
}
