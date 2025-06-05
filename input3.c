struct Pt{
	int x,y;
	};

//struct Pt		points[20/4+5];
struct Pt point;

int sum( int x, int y)
{
	int	 i,s, v[5 + 3];
	int a;
	s=0;
	if (a == 4)
	    a = 10;
    else
        a = 20;
    int c;
	for(i=0;i<5;i=i+1){
		s=s+i;
		}
	return s;
}

int ceva, altceva;

void main()
{
	int		i,s;
	for(i=0;i<1000000;i=i+1)
	s=sum(2, 3);
	put_i(s);
}

