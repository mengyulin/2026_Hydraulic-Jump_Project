/* Analytic bed; x increases downstream, S0=-b_x. SI, vertical depth.
 * kind 0 flat; 1 cosine slope transition; 2 straight slope; 3 cosine bump.
 * b, b_x, b_xx must be changed together for the B pressure closure.
 */
int bed_kind=0;
int outflow_kind=0; /* 0 prescribed subcritical tailwater; 1 supercritical outflow */
double bed_s1=0.,bed_s2=0.,bed_a=11.,bed_b=13.,bed_end=30.,bed_zend=0.;
void read_bed(const char *path) {
  FILE *fp=fopen(path,"r"); if(!fp)exit(2);
  int r=fscanf(fp,"%d %lf %lf %lf %lf %lf %lf %d",&bed_kind,&bed_s1,&bed_s2,&bed_a,&bed_b,&bed_end,&bed_zend,&outflow_kind);
  fclose(fp);if(r!=8 || bed_kind<0 || bed_kind>3 || bed_b<=bed_a || outflow_kind<0 || outflow_kind>1)exit(2);
}
double bed_z(double x) {
  if(!bed_kind)return bed_zend;
  if(bed_kind==2)return bed_zend+bed_s1*(bed_end-x);
  if(bed_kind==3)return bed_zend+bed_s1*(1.-cos(2.*pi*(x-bed_a)/(bed_b-bed_a)));
  double L=bed_b-bed_a,za=bed_zend+bed_s2*(bed_end-bed_b)+.5*(bed_s1+bed_s2)*L;
  if(x<=bed_a)return za+bed_s1*(bed_a-x);
  if(x>=bed_b)return bed_zend+bed_s2*(bed_end-x);
  double r=x-bed_a;
  return za-.5*(bed_s1+bed_s2)*r-(bed_s1-bed_s2)*L/(2.*pi)*sin(pi*r/L);
}
double bed_x(double x) {
  if(!bed_kind)return 0.;
  if(bed_kind==2)return -bed_s1;
  if(bed_kind==3)return bed_s1*2.*pi/(bed_b-bed_a)*sin(2.*pi*(x-bed_a)/(bed_b-bed_a));
  if(x<=bed_a)return -bed_s1;
  if(x>=bed_b)return -bed_s2;
  return -.5*(bed_s1+bed_s2)-.5*(bed_s1-bed_s2)*cos(pi*(x-bed_a)/(bed_b-bed_a));
}
double bed_xx(double x) {
  if(bed_kind==3)return bed_s1*sq(2.*pi/(bed_b-bed_a))*cos(2.*pi*(x-bed_a)/(bed_b-bed_a));
  if(bed_kind!=1 || x<=bed_a || x>=bed_b)return 0.;
  return .5*(bed_s1-bed_s2)*pi/(bed_b-bed_a)*sin(pi*(x-bed_a)/(bed_b-bed_a));
}
