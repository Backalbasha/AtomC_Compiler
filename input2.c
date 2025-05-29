struct Pt{
	int x,y;
	};

struct Pt		points[20/4+5];
int i;
int		count(int iamil, int plm)
{
	int		i,n;
	for(i=n=0;i<10;i=i+1){
	    int adancime;
		if(points[i].x>=0&&points[i].y>=0)n=n+1;
		}
	return n;
}

void main()
{
	put_i(count());
	//struct Pt		points[20/4+5];
}