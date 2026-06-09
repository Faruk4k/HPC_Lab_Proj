# include <stdio.h>
#include <stdlib.h>
# include <unistd.h>
# include <math.h>
# include <float.h>
# include <limits.h>
# include <time.h>
# include <sys/time.h>


#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif

#ifdef USEARMIE
  #define __START_TRACE() {asm volatile ("hint 0x40");}
  #define __STOP_TRACE() {asm volatile ("hint 0x41");}
#endif


#define STREAM_TYPE double
#define OFFSET	64

STREAM_TYPE * __restrict x;
STREAM_TYPE * __restrict y;


/***************************************************************************************************
kernel main function
***************************************************************************************************/
int main(int argc, char** argv)
{
    double a = 3.0; // scalar
    int k, n;
    struct timespec t0, t1;
    double  t_elapsed;

    if (argc != 2)
    {
        printf("Invalid number of arguments. \n");
        printf("Usage: \n");
        printf("     ./daxpy.x <ARRAY_SIZE> \n");
        printf(" <ARRAY_SIZE>: double elements of the array\n");
        return 0;
    } else {
        n = atol(argv[1]);
    }

    /**********************************
    Start the main loop of the kernel
    *********************************/
    // Initialize data for the stream
    if((k = posix_memalign((void **) &x, 64, (n * sizeof(STREAM_TYPE)))) != 0)
    {
        fprintf(stderr, "Allocation of array a failed, return code is %ld\n", k);
        return 0;
    }
    if((k = posix_memalign((void **) &y, 64, (n * sizeof(STREAM_TYPE)))) != 0)
    {
        fprintf(stderr, "Allocation of array b failed, return code is %ld\n", k);
        return 0;
    }

    printf("Array SIZE      : %d \n", n);

#pragma omp parallel for
    for (int i = 0; i < n; i++)
    {
        x[i] = 0.0;
        y[i] = 2.0;
    }

    printf("\n----daxpy----\n");
    clock_gettime(CLOCK_MONOTONIC, &t0);

#ifdef USEM5OPS
    m5_reset_stats(0,0); 
#endif
#ifdef USEARMIE
  __START_TRACE();
#endif
    for (int i = 0; i<n; i++)
    {
        y[i] = a*x[i] + y[i];
    }
#ifdef USEARMIE
  __STOP_TRACE();
#endif
#ifdef USEM5OPS
    m5_dump_stats(0,0); 
#endif

    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns

    //summary
    printf("x[%i]=%.2e. y[%i]=%.2e. \n", 0, x[0], 0, y[0]);
    printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
    printf("   Rate [MB/s]: %.1f \n", 
        (double)(1.0E-06 * n * sizeof(STREAM_TYPE) * 2)/(t_elapsed * 1.0E-09));


    free(x);
    free(y);

    return 0;
}
