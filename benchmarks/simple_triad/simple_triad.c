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

#define STREAM_TYPE double
#define OFFSET	64

#ifndef STREAM_ARRAY_SIZE
    STREAM_TYPE * __restrict a;
    STREAM_TYPE * __restrict b;
    STREAM_TYPE * __restrict c;
#endif

/***************************************************************************************************
kernel main function
***************************************************************************************************/
int main(int argc, char** argv)
{
    double scalar = 3.0;
    int k, loops, array_size;
    struct timespec t0, t1;
    double  t_elapsed;

    if (argc != 3)
    {
        printf("Invalid number of arguments. \n");
        printf("Usage: \n");
        printf("     ./stream-triad.bin <ARRAY_SIZE> <LOOP>\n");
        printf(" <ARRAY_SIZE>: double elements of the array\n");
        printf("       <LOOP>: kernel loop\n");
        return 0;
    } else {
        array_size = atol(argv[1]);
        loops      = atoi(argv[2]);
    }

    /**********************************
    Start the main loop of the kernel
    *********************************/
    // Initialize data for the stream
    if((k = posix_memalign((void **) &a, 64, (array_size * sizeof(STREAM_TYPE)))) != 0)
    {
        fprintf(stderr, "Allocation of array a failed, return code is %ld\n", k);
        return 0;
    }
    if((k = posix_memalign((void **) &b, 64, (array_size * sizeof(STREAM_TYPE)))) != 0)
    {
        fprintf(stderr, "Allocation of array b failed, return code is %ld\n", k);
        return 0;
    }
    if((k = posix_memalign((void **) &c, 64, (array_size * sizeof(STREAM_TYPE)))) != 0)
    {
        fprintf(stderr, "Allocation of array b failed, return code is %ld\n", k);
        return 0;
    }

    printf("Array SIZE      : %d \n", array_size);
    printf("Array LOOP      : %d \n", loops);

#pragma omp parallel for
    for (int elemt = 0; elemt < array_size; elemt++)
    {
        a[elemt] = 0.0;
        b[elemt] = 2.0;
        c[elemt] = 1.0;
    }

    printf("\n----triad----\n");
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for(int exp_idx = 0; exp_idx < loops; exp_idx++)
    {
#ifdef USEM5OPS
    m5_reset_stats(0,0); 
#endif
#pragma omp parallel for
        for (int elemt = 0; elemt<array_size; elemt++)
        {
            a[elemt] = scalar*b[elemt] + c[elemt];
        }
#ifdef USEM5OPS
    m5_dump_stats(0,0); 
#endif
    } 

    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns
    t_elapsed /= loops;               

    //summary
    printf("a[%i]=%.2e. b[%i]=%.2e. c[%i]=%.2e.\n", 0, a[0], 0, b[0], 0, c[0]);
    printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
    printf("   Rate [MB/s]: %.1f \n", 
        (double)(1.0E-06 * array_size * sizeof(STREAM_TYPE) * 3)/(t_elapsed * 1.0E-09));

#ifndef STREAM_ARRAY_SIZE
    free(a);
    free(b);
    free(c);
#endif

    return 0;
}
