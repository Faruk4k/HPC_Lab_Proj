#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif

#define ITERS 10000//4096


void loop_nosve()
{
    int i;
#ifdef USEM5OPS
        m5_reset_stats(0,0);
#endif
    for (int i = 0; i < ITERS; i++) {
        asm volatile(
            "fmla v0.2d,  v30.2d, v31.2d\n\t"
            "fmla v1.2d,  v30.2d, v31.2d\n\t"
            "fmla v2.2d,  v30.2d, v31.2d\n\t"
            "fmla v3.2d,  v30.2d, v31.2d\n\t"
            "fmla v4.2d,  v30.2d, v31.2d\n\t"
            "fmla v5.2d,  v30.2d, v31.2d\n\t"
            "fmla v6.2d,  v30.2d, v31.2d\n\t"
            "fmla v7.2d,  v30.2d, v31.2d\n\t"
            "fmla v8.2d,  v30.2d, v31.2d\n\t"
            "fmla v9.2d,  v30.2d, v31.2d\n\t"
            "fmla v10.2d, v30.2d, v31.2d\n\t"
            "fmla v11.2d, v30.2d, v31.2d\n\t"
            "fmla v12.2d, v30.2d, v31.2d\n\t"
            "fmla v13.2d, v30.2d, v31.2d\n\t"
            "fmla v14.2d, v30.2d, v31.2d\n\t"
            "fmla v15.2d, v30.2d, v31.2d\n\t"
            "fmla v16.2d, v30.2d, v31.2d\n\t"
            "fmla v17.2d, v30.2d, v31.2d\n\t"
            "fmla v18.2d, v30.2d, v31.2d\n\t"
            "fmla v19.2d, v30.2d, v31.2d\n\t"
            "fmla v20.2d, v30.2d, v31.2d\n\t"
            "fmla v21.2d, v30.2d, v31.2d\n\t"
            "fmla v22.2d, v30.2d, v31.2d\n\t"
            "fmla v23.2d, v30.2d, v31.2d\n\t"
            "fmla v24.2d, v30.2d, v31.2d\n\t"
            "fmla v25.2d, v30.2d, v31.2d\n\t"
            "fmla v26.2d, v30.2d, v31.2d\n\t"
            "fmla v27.2d, v30.2d, v31.2d\n\t"
            "fmla v28.2d, v30.2d, v31.2d\n\t"
            "fmla v29.2d, v30.2d, v31.2d\n\t"
            :
            :
            : "v0","v1","v2","v3","v4","v5","v6","v7",
            "v8","v9","v10","v11","v12","v13","v14","v15",
            "v16","v17","v18","v19","v20","v21","v22","v23",
            "v24","v25","v26","v27","v28","v29","v30","v31"
        );
    }

#ifdef USEM5OPS
        m5_dump_stats(0,0);
#endif

}

void  loop_sve() 
{
    int i;
#ifdef USEM5OPS
        m5_reset_stats(0,0);
#endif 
    for(i=0; i < ITERS; i+=1) {
        // non-portable ARMv8 NEON/ASIMD assembly code
        asm volatile(
                "ptrue p0.d\n\t"
                "fmla  z0.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z1.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z2.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z3.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z4.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z5.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z6.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z7.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z8.d,p0/m,z30.d,z31.d\n\t" 
                "fmla  z9.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z10.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z11.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z12.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z13.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z14.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z15.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z16.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z17.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z18.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z19.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z20.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z21.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z22.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z23.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z24.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z25.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z26.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z27.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z28.d,p0/m,z30.d,z31.d\n\t" 
                "fmla z29.d,p0/m,z30.d,z31.d\n\t" 
                :
                :
                : "p0","z0","z1","z2",
                    "z3","z4","z5",
                    "z6","z7","z8",
                    "z9","z10","z11",
                    "z12","z13","z14",
                    "z15","z16","z17","z18",
                    "z19","z20","z21",
                    "z22","z23","z24",
                    "z25","z26","z27",
                    "z28","z29","z30",
                    "z31"
                );
    } // i

#ifdef USEM5OPS
        m5_dump_stats(0,0);
#endif
}


int main(int argc, char* argv[]) 
{
    struct timespec t0, t1;
    double  t_elapsed;

    argc&=10000;
    printf("\n----FP BENCHMARK----\n");
    clock_gettime(CLOCK_MONOTONIC, &t0);

    loop_nosve(); 
    //loop_sve();

    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns

    //summary
    printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
    return 0;
}