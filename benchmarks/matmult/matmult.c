#include <stdio.h>
#include <time.h>
#include <stdlib.h>

#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif

// Max of 128 is to keep the simulation time reasonable
#define N          128
#define BLKSIZE    64


double A[N][N];
double B[N][N];
double C[N][N];

int loops = 1;

/*
* Your cache blocking implementation
*/
void multiply_blocking()
{

}

/*
* Your interchanged implementation
*/
void multiply_interchanged()
{

}

void multiply()
{

    for (int l = 0; l < loops; l++) {
        printf("Loop %d ... \n", l);
#ifdef USEM5OPS
        m5_reset_stats(0,0);
 #endif    
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                for (int k = 0; k < N; k++) {
                    C[i][j] += A[i][k] * B[k][j];
                }
            }
        }
#ifdef USEM5OPS
        m5_dump_stats(0,0);
#endif    
    }
}

int main(int argc, char* argv[])
{
    struct timespec t0, t1;
    double  t_elapsed;

    if (argc != 2) {
        printf("Invalid number of arguments. \n");
        printf("Usage: \n");
        printf("     ./matmult.x <LOOP>\n");
        return 0;
    } else {
        loops   = atoi(argv[1]);
    }

    printf("\n----MATRIX MULTIPLICATION----\n");
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = 0.5;
            B[i][j] = 0.5;
            C[i][j] = 1.0;
        }
    }

    printf("\n----Computation starts----\n");
    clock_gettime(CLOCK_MONOTONIC, &t0);
    multiply();


    clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns    

    printf("argc = %d, A[argc][argc] = %f, B[argc][argc] = %f, C[argc][argc] = %f \n", 
        argc, A[argc][argc], B[argc][argc], B[argc][argc]);

    //summary
    printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);

    return 0;
}