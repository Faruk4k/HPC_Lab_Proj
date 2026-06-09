#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>

#ifdef USEM5OPS
#include "gem5/m5ops.h"
#endif

#define ITER        300000
#define MAX_THREADS 32
#define CL_SIZE     64 // cache line size = 64 bytes


typedef struct 
{
    volatile unsigned int value;
} data_t;


// cache line padding implementation
//typedef struct 
//{
    //
//} padded_data_t;

typedef struct 
{
    unsigned int tid;
    volatile unsigned int *pdata;
} thread_arg_t;


pthread_t threads[MAX_THREADS];
thread_arg_t args[MAX_THREADS];

void* thread_func(void *arg)
{
    thread_arg_t *a = arg;

    for (int i = 0; i < ITER; i++){
        *a->pdata += 1;
    }

    printf("Thread %u is done, data = %u \n", a->tid, *a->pdata);
    return NULL;
}

int main(int argc, char *argv[])
{
    int nthreads;
    struct timespec t0, t1;
    long long  t_elapsed;

    if (argc > 1) {
        nthreads = atoi(argv[1]);
        if (nthreads < 1) 
            nthreads = 1;
        if (nthreads > MAX_THREADS) 
            nthreads = MAX_THREADS;
    } else {
        printf("Usage: ./false_sharing.x <nthreads> \n");
        return 0;
    }

    printf("Using %d thread(s)\n", nthreads);

#ifdef PADDING_USED
    padded_data_t data[MAX_THREADS];
#else
    data_t data[MAX_THREADS];
#endif

    for (int t = 0; t < nthreads; t++) {
        data[t].value = 0;
    }

    clock_gettime(CLOCK_MONOTONIC, &t0);

#ifdef USEM5OPS
    m5_reset_stats(0,0); 
#endif

    for (unsigned int t = 0; t < nthreads; t++) {
        args[t].pdata = &data[t].value;
        args[t].tid = t;
        pthread_create(&threads[t], NULL, thread_func, &args[t]);
    }

    for (int t = 0; t < nthreads; t++)
        pthread_join(threads[t], NULL);

#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif

    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (long long) ((t1.tv_sec - t0.tv_sec) * 1e9 + (t1.tv_nsec - t0.tv_nsec));
    printf("All threads finish! Time = %.3f (ms) \n", t_elapsed/1e6);

    for (int t = 0; t < nthreads; t++) {
        printf("Data [%u] = %u \n", t, data[t].value);
    }
    return 0;
}
