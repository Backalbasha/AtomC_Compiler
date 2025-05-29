struct Pt{
	int x,y;
	};

struct Pt		points[20/4+5];

int sum( int x, int y)
{
	int	 i,v[5],s, x;
	int a;
	s=0;
	if (a == 4)
	    a = 10;
    else
        a = 20;
    int c;
	for(i=0;i<5;i=i+1){
		v[i]=i;
		s=s+v[i];
		}
	return s;
}

int ceva, altceva;

void main()
{
	int		i,s;
	for(i=0;i<1000000;i=i+1)
	s=sum();
	put_i(s);
}

