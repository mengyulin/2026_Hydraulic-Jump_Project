#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#define sq(x) ((x)*(x))
#define cube(x) ((x)*(x)*(x))
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define pi 3.14159265358979323846
#define HUGE 1e30
double t=0.,dt=0.;
#include "bed.h"
#define CAP 8194
typedef struct { double h, q; } State;
State y[CAP], p[CAP], z[CAP], f[CAP], dflux[CAP], rhs[CAP];
double vel[CAP], hydro[CAP], bflux[CAP], sensor[CAP];
double meanh[CAP], meanq[CAP], meanh2[CAP], first[CAP], last[CAP];
double meanflux[CAP], meandiff[CAP];
double hlstar[CAP],hrstar[CAP],pbnh[CAP],hydrobed[CAP],nhbed[CAP];
double bed_impulse=0.,nhbed_impulse=0.,stage_bed=0.,stage_nhbed=0.;
int M, nodes, use_b, periodic_domain, scheme, rejected=0, steps=0;
int source_mode=0, strip_mode=0;
State accepted_start[CAP], adv_face[CAP], b_face[CAP];
FILE *diagnostics;
double hin, uin, hout, mann, xa, xb, cfl, kappa, finish, avg, max_dt;
double dx, now=0., wt=0., wfirst=0., wlast=0.;
double v0, p0, mass_impulse=0., momentum_impulse=0., source_impulse=0.;
double max_mass_error=0., max_momentum_error=0., min_depth=HUGE;
double filter_energy=0., max_filter_rate=0.;
double rusanov=1.;
double bz[CAP],bx[CAP],bxx[CAP],rus_h[CAP],rus_q[CAP],eps_face[CAP],speed_face[CAP];
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
    sensor[j]=bflux[j]=pbnh[j]=0.;
  }
  for(int j=0;j<nodes;j++) if(periodic_domain || (j>0 && j<nodes-1)) {
    int l=idx(j-1),r=idx(j+1);
    double ux=direction>0 ? (vel[r]-vel[j])/dx : (vel[j]-vel[l])/dx;
    if(use_b) {
      double uxx=(vel[r]-2.*vel[j]+vel[l])/sq(dx);
      double A=vel[j]*ux*bx[j]+sq(vel[j])*bxx[j];
      double C=sq(ux)-vel[j]*uxx;
      // Keep the original flat evaluation order for the regression.
      bflux[j]=-cube(a[j].h)*(vel[j]*uxx-sq(ux))/3.+.5*sq(a[j].h)*A;
      pbnh[j]=a[j].h*A+.5*sq(a[j].h)*C;
    }
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
      f[k].h=.5*(a[l].q+a[r].q)-.5*rusanov*speed*(a[r].h-a[l].h);
      f[k].q=.5*(hydro[l]+hydro[r])-.5*rusanov*speed*(a[r].q-a[l].q)+b_face[k].q;
    }
    hlstar[k]=a[l].h; hrstar[k]=a[r].h;
    if(bed_kind) {
      double zl=bz[l],zr=bz[r],zface=max(zl,zr);
      double hl=max(0.,a[l].h+zl-zface),hr=max(0.,a[r].h+zr-zface);
      hlstar[k]=hl;hrstar[k]=hr;
      double ql=hl*vel[l],qr=hr*vel[r];
      f[k].h=.5*(ql+qr)-.5*rusanov*speed*(hr-hl);
      f[k].q=.5*(ql*vel[l]+qr*vel[r]+.5*g*(sq(hl)+sq(hr)))-.5*rusanov*speed*(qr-ql)+b_face[k].q;
    }
    // Diagnostic decomposition of the actual reconstructed penalty.
    rus_h[k]=-.5*rusanov*speed*(hrstar[k]-hlstar[k]);
    rus_q[k]=-.5*rusanov*speed*(hrstar[k]*vel[r]-hlstar[k]*vel[l]);
    speed_face[k]=speed;
    adv_face[k]=(State){f[k].h,f[k].q-b_face[k].q};
    double eps=kappa*speed*max(sensor[l],sensor[r]);eps_face[k]=eps;
    double dh=bed_kind ? (a[r].h+bz[r])-(a[l].h+bz[l]) : a[r].h-a[l].h;
    dflux[k]=(State){-eps*dh,-eps*(a[r].q-a[l].q)};
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
    if(outflow_kind)f[nodes]=(State){a[nodes-1].q,hydro[nodes-1]};
    dflux[0]=dflux[nodes]=(State){0.,0.};
    adv_face[0]=f[0];adv_face[nodes]=f[nodes];
    b_face[0]=b_face[nodes]=(State){0.,0.};
  }
  hrstar[0]=a[0].h;hlstar[nodes]=a[nodes-1].h;
  stage_bed=stage_nhbed=0.;
  *mh=f[0].h-f[nodes].h;*mq=f[0].q-f[nodes].q;*sqint=0.;
  for(int j=0;j<nodes;j++) {
    double vol=dx*weight(j);
    hydrobed[j]=bed_kind ? .5*g*(sq(hlstar[j+1])-sq(hrstar[j]))/vol : 0.;
    nhbed[j]=-pbnh[j]*bx[j];
    double s=source(a[j])+hydrobed[j]+nhbed[j];
    stage_bed+=vol*hydrobed[j];stage_nhbed+=vol*nhbed[j];
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


static State rplus[CAP];
void configure(int count,int bon,int periodic,double left,double right,double h_in,double q_in,double h_out,double rough,double lam,double kap,double cf,const char *bedfile) {
 M=count;periodic_domain=periodic;nodes=periodic?M:M+1;use_b=bon;scheme=1;source_mode=0;strip_mode=2;
 xa=left;xb=right;dx=(xb-xa)/M;hin=h_in;uin=q_in/h_in;hout=h_out;mann=rough;rusanov=lam;kappa=kap;cfl=cf;
 read_bed(bedfile);
 for(int j=0;j<nodes;j++){bz[j]=bed_z(xa+j*dx);bx[j]=bed_x(xa+j*dx);bxx[j]=bed_xx(xa+j*dx);}
}
double native_dt(const double *a) {
 const State *s=(const State*)a;double speed=0.;
 for(int j=0;j<nodes;j++){double u=fabs(s[j].q/s[j].h),c=sqrt(g*s[j].h);speed=max(speed,u+c+(use_b?2.*sq(s[j].h)*u/(3.*sq(dx)):0.));}
 return cfl*dx*(periodic_domain?1.:.5)/speed;
}
void residual(const double *a,double step,double *result) {
 memcpy(y,a,nodes*sizeof(State));double mh,mq,si;
 operator(y,1,&mh,&mq,&si);memcpy(rplus,rhs,nodes*sizeof(State));
 for(int j=0;j<nodes;j++)p[j]=(State){y[j].h+step*rhs[j].h,y[j].q+step*rhs[j].q};
 operator(p,-1,&mh,&mq,&si);
 State *r=(State*)result;
 for(int j=0;j<nodes;j++)r[j]=(State){.5*(rplus[j].h+rhs[j].h),.5*(rplus[j].q+rhs[j].q)};
}
void stage(const double *a,int direction,double *result) {
 memcpy(y,a,nodes*sizeof(State));double mh,mq,si;operator(y,direction,&mh,&mq,&si);memcpy(result,rhs,nodes*sizeof(State));
}
void snapshot(const double *a,double *result) {
 memcpy(y,a,nodes*sizeof(State));double mh,mq,si;operator(y,1,&mh,&mq,&si);
 for(int k=1;k<nodes;k++){int j=(k-1)*10;result[j]=xa+(k-.5)*dx;result[j+1]=rus_h[k];result[j+2]=rus_q[k];result[j+3]=dflux[k].h;result[j+4]=dflux[k].q;result[j+5]=b_face[k].q;result[j+6]=speed_face[k];result[j+7]=eps_face[k];result[j+8]=.5*rusanov*speed_face[k]*dx;result[j+9]=eps_face[k]*dx;}
}
