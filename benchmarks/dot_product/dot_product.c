#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>

#ifdef USEM5OPS
#include "gem5/m5ops.h"
#endif


#define MAX_THREADS 32

typedef struct 
{
    double *X;
    double *Y;
    double *dot;
    unsigned int length;
    unsigned int tid;
    unsigned int threads;
} thread_arg_t;

pthread_t threads[MAX_THREADS];
thread_arg_t args[MAX_THREADS];
pthread_mutex_t lock;

// Interleaved threads
void* parallel_v1(void *arg)
{
    double res;
    thread_arg_t *a = arg;
   
    for (int i=a->tid; i < a->length; i += a->threads) 
    {
        res += a->X[i] * a->Y[i];
    }
    pthread_mutex_lock(&lock);
    *a->dot += res;
    pthread_mutex_unlock(&lock);

    printf("Thread %u is done, res = %.6f \n", a->tid, res);
    return NULL;
}

// Avoid the false sharing issue
void* parallel_v2(void *arg)
{
    double res;
    thread_arg_t *a = arg;
    unsigned int chunk_size = (a->length+a->threads-1)/a->threads;
    

    for (int i=a->tid*chunk_size; i < (a->tid+1)*chunk_size 
            && i < a->length; i++) 
    {
        res += a->X[i] * a->Y[i];
    }
    pthread_mutex_lock(&lock);
    *a->dot += res;
    pthread_mutex_unlock(&lock);
    printf("Thread %u is done, res = %.6f \n", a->tid, res);
}

// Can we do better ? e.g. avoid racing on updating the dot variable
//void parallel_v3(double *X, double *Y, double *dot, 
//    size_t length, size_t tid, size_t threads)
//{
//}

int main(int argc, char *argv[])
{
    double *A;
    double *B;
    double dot = 0.0;
    
    int nthreads, vectorsize;
    struct timespec t0, t1;
    long long  t_elapsed;

    if (argc == 3) {
        nthreads = atoi(argv[1]);
        vectorsize = atoi(argv[2]);
        if (nthreads < 1) 
            nthreads = 1;
        if (nthreads > MAX_THREADS) 
            nthreads = MAX_THREADS;
    } else {
        printf("Usage: ./dot_product.x <nthreads> <vectorsize> \n");
        return 0;
    }

    A = malloc(vectorsize * sizeof(double));
    B = malloc(vectorsize * sizeof(double));

    for (int i = 0; i < vectorsize; i++) {
        A[i] = 1.0;
        B[i] = 1.0;
    }
    pthread_mutex_init(&lock, NULL);

    clock_gettime(CLOCK_MONOTONIC, &t0);
#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif    
    for (unsigned int t = 0; t < nthreads; t++) {
        args[t].X = A;
        args[t].Y = B;
        args[t].dot = &dot;
        args[t].length = vectorsize;
        args[t].tid = t;
        args[t].threads = nthreads;
#ifdef PARA_V1_USED        
        pthread_create(&threads[t], NULL, parallel_v1, &args[t]);
#elif  PARA_V2_USED
        pthread_create(&threads[t], NULL, parallel_v2, &args[t]);
#elif  PARA_V3_USED
        pthread_create(&threads[t], NULL, parallel_v3, &args[t]);
#endif
    }

    for (int t = 0; t < nthreads; t++)
        pthread_join(threads[t], NULL);

    // Reference
    //for (int i = 0; i < vectorsize; i++) {
    //    dot += A[i] * B[i];
    //}

#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif
    
    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (long long) ((t1.tv_sec - t0.tv_sec) * 1e9 + (t1.tv_nsec - t0.tv_nsec));
    printf("All threads finish! Time = %.3f (ms) \n", t_elapsed/1e6);


    printf("dot = %f, expect = %f \n", dot, 1.0 * vectorsize);

    free(A);
    free(B);
    pthread_mutex_destroy(&lock);
    return 0;
}
