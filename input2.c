struct Pt{
	int x,y;
	};

struct Pt		points[20/4+5];

int		count()
{
	int		i,n;
	for(i=n=0;i<10;i=i+1){
		if(points[i].x>=0&&points[i].y>=0)n=n+1;
		}
	return n;
}

void main()
{
	put_i(count());
}


int sum()
{
	int	 i,v[5],s;
	s=0;
	for(i=0;i<5;i=i+1){
		v[i]=i;
		s=s+v[i];
		}
	return s;
}

void main()
{
	int		i,s;
	for(i=0;i<1000000;i=i+1)
	s=sum();
	put_i(s);
}

/*** primul *** program ***/
void main()
{
	put_s("salut");
}
//sfarsit

void main()
{
	int		x;
	put_s("x=");
	x=get_i();
	put_i(x);
}

void main()
{
	int		x;
	put_s("x=");
	x=get_i();
	if(x<0)put_s("negativ");
		else put_s("pozitiv");
}

int isdigit(char ch)
{
	return ch>='0'&&ch<='9';
}

void main()
{
	char		c;
	put_s("c=");
	c=get_c();
	put_i(isdigit(c));
}
void main()
{
	int		i,n;
	double	s;
	s=0.0;
	put_s("n=");
	n=get_i();
	for(i=0;i<n;i=i+1){
		s=s+get_i();
		}
	put_s("media=");
	put_d(s/n);
}
void main()
{
	int		i,n,t;
	int		v[100];
	put_s("n=");
	n=get_i();
	for(i=0;i<n;i=i+1){
		v[i]=get_i();
		}
	for(i=0;i<n/2;i=i+1){
		t=v[i];
		v[i]=v[n-i-1];
		v[n-i-1]=t;
		}
	for(i=0;i<n;i=i+1){
		put_c('#');
		put_i(v[i]);
		}
}
void main()
{
	double	r,pi;
	pi=3.14;
	put_s("r=");
	r=get_d();
	put_s("perimetrul=");
	put_d(2e0*pi*r);
	put_s("aria=");
	put_d(pi*r*r);
}
/*
testare analizor lexical
*/
void main()
{
	if(0xc==014)put_s("\"egal\"\t\t(h,o)");
		else put_s("\"inegal\"\t\t(h,o)");
	if(20E-1==2.0&&0.2e+1==0x2)put_c('=');  // 2 scris in diverse feluri
		else put_c('\\');
}