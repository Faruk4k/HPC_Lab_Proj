/*
*
* Floating-point Execution -- 8 Independent instructions per Iteration
*
* The code is adapted from the reference here:
*  https://github.com/VerticalResearchGroup/microbench/blob/master/EF/bench.c
*
*/


#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif

#define ITERS 50000//4096

float loop() {
    float  t1 = 1.1f;
    float  t2 = 89.0f;
    float  t3 = 3.2f;
    float  t4 = 21.0f;
    float  t5 = 2.0f;
    float  t6 = 7.0f;
    float  t7 = 2.5f;
    float  t8 = 3.0f;

    int i;
#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif    
    for(i=0; i < ITERS; i+=1) {
        t1*=0.2f;
        t2*=0.4f;
        t3*=1.2f;
        t4*= 0.12f;
        
        t5*= 0.13f;
        t6*= 0.14f;
        t7*= 0.15f;
        t8*= 0.16f;
    }
#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif
    return t1+t2+t3+t4+t5+t6+t7+t8;
}

float loop_1() {
    register float  t1 = 1.1f;
    register float  t2 = 89.0f;
    register float  t3 = 3.2f;
    register float  t4 = 21.0f;
    register float  t5 = 2.0f;
    register float  t6 = 7.0f;
    register float  t7 = 2.5f;
    register float  t8 = 3.0f;

    int i;
#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif    
    for(i=0; i < ITERS; i+=1) {
        t1*=0.2f;
        t2*=0.4f;
        t3*=1.2f;
        t4*= 0.12f;
        
        t5*= 0.13f;
        t6*= 0.14f;
        t7*= 0.15f;
        t8*= 0.16f;
    }
#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif
    return t1+t2+t3+t4+t5+t6+t7+t8;
}

float loop_2() {
    register float t0 asm("s0") = 1.1f;
    register float t1 asm("s1") = 89.0f;
    register float t2 asm("s2") = 3.2f;
    register float t3 asm("s3") = 21.0f;
    register float t4 asm("s4") = 2.0f;
    register float t5 asm("s5") = 7.0f;
    register float t6 asm("s6") = 2.5f;
    register float t7 asm("s7") = 3.0f;

    register float c0 asm("s15") = 0.2f;
    register float c1 asm("s16") = 0.4f;
    register float c2 asm("s17") = 1.2f;
    register float c3 asm("s18") = 0.12f;
    register float c4 asm("s19") = 0.13f;
    register float c5 asm("s20") = 0.14f;
    register float c6 asm("s21") = 0.15f;
    register float c7 asm("s22") = 0.16f;

    register int i;

/* 
* Enable this to know the Tick starting ROI. helpful for Konata tool usage to 
* visualize the O3 execution
*/
/*
#ifdef USEM5OPS
    m5_exit(0);
#endif
*/

#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif        
    for (i = 0; i < ITERS; i++) {
        asm volatile(
            "fmul %s[t0], %s[t0], %s[c0] \n"
            "fmul %s[t1], %s[t1], %s[c1] \n"
            "fmul %s[t2], %s[t2], %s[c2] \n"
            "fmul %s[t3], %s[t3], %s[c3] \n"
            "fmul %s[t4], %s[t4], %s[c4] \n"
            "fmul %s[t5], %s[t5], %s[c5] \n"
            "fmul %s[t6], %s[t6], %s[c6] \n"
            "fmul %s[t7], %s[t7], %s[c7] \n"
            :
            [t0] "+w"(t0), [t1] "+w"(t1), [t2] "+w"(t2), [t3] "+w"(t3),
            [t4] "+w"(t4), [t5] "+w"(t5), [t6] "+w"(t6), [t7] "+w"(t7)
            :
            [c0] "w"(c0), [c1] "w"(c1), [c2] "w"(c2), [c3] "w"(c3),
            [c4] "w"(c4), [c5] "w"(c5), [c6] "w"(c6), [c7] "w"(c7)
        );
    }
#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif
    return t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7;
}


double  A[ITERS];
float loop_3_chain() {
    register float t0 asm("s0") = 1.1f;
    register float t1 asm("s1") = 89.0f;
    register float t2 asm("s2") = 3.2f;
    register float t3 asm("s3") = 21.0f;
    register float t4 asm("s4") = 2.0f;
    register float t5 asm("s5") = 7.0f;
    register float t6 asm("s6") = 2.5f;
    register float t7 asm("s7") = 3.0f;

    register float c0 asm("s15") = 0.2f;
    register float c1 asm("s16") = 0.4f;
    register float c2 asm("s17") = 1.2f;
    register float c3 asm("s18") = 0.12f;
    register float c4 asm("s19") = 0.13f;
    register float c5 asm("s20") = 0.14f;
    register float c6 asm("s21") = 0.15f;
    register float c7 asm("s22") = 0.16f;

    register int i;
    register double sum = 0;

/*
    for (i = 0; i < ITERS; i++) {
        A[i] = i;
    }
*/

/* 
* Enable this to know the Tick starting ROI. helpful for Konata tool usage to 
* visualize the O3 execution
*/
/*    
#ifdef USEM5OPS
    m5_exit(0);
#endif
*/

#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif        
    for (i = 0; i < ITERS; i++) {
        sum += A[i];

        asm volatile(
            "fmul %s[t0], %s[t0], %s[c0] \n"
            "fmul %s[t1], %s[t1], %s[c1] \n"
            "fmul %s[t2], %s[t2], %s[c2] \n"
            "fmul %s[t3], %s[t3], %s[c3] \n"
            "fmul %s[t4], %s[t4], %s[c4] \n"
            "fmul %s[t5], %s[t5], %s[c5] \n"
            "fmul %s[t6], %s[t6], %s[c6] \n"
            "fmul %s[t7], %s[t7], %s[c7] \n"
            :
            [t0] "+w"(t0), [t1] "+w"(t1), [t2] "+w"(t2), [t3] "+w"(t3),
            [t4] "+w"(t4), [t5] "+w"(t5), [t6] "+w"(t6), [t7] "+w"(t7)
            :
            [c0] "w"(c0), [c1] "w"(c1), [c2] "w"(c2), [c3] "w"(c3),
            [c4] "w"(c4), [c5] "w"(c5), [c6] "w"(c6), [c7] "w"(c7)
        );

    }

#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif
    printf("loop_3_chain(): Sum = %f\n", sum);

    return t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7;
}

int main(int argc, char* argv[]) 
{
    volatile float a1, a2, a3, a4;
    struct timespec t0, t1;
    double  t_elapsed;

    argc&=10000;
    printf("\n----FP BENCHMARK----\n");
    clock_gettime(CLOCK_MONOTONIC, &t0);


//    float r1 = loop();
//    float r2 = loop_1(); 
    float r3 = loop_2(); 
//  float r4 = loop_3_chain(); 

//    a1 = r1;
//    a2 = r2;
    a3 = r3;
//    a4 = r4;


    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns

    //summary
    printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
    return 0;
}