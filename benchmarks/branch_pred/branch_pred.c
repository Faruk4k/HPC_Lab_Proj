/*
* The code is adapted from the reference one here:
*   https://github.com/VerticalResearchGroup/microbench
*/

#include <stdio.h>
#include <time.h>
#include <stdlib.h>

#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif


/* 
* Hard to predict. Generating 'randArr_hard.h' for this experiment as follows:
* - Generate a random array (0, 1, 2)
*   python ./rand_c_arr.py --len=16384 --range=3 --name=randArr --output=randArr_hard.h
* - Generate non-random array second
*   python ./rand_c_arr.py --len=16384 --range=3 --name=randArr --non_random --output=randArr_easy.h
* - Other random file
*   python ./rand_c_arr.py --len=16384 --range=16384 --name=randArr2 --output=randArr_hard2.h
*/

#ifdef BRANCHPD_EASY
#include "randArr_easy.h"
#else
#include "randArr_hard.h"
#include "randArr_hard2.h"
#endif



#define STEP   2048
#define ITERS  64

int arr[STEP];
int arr1[STEP];
int arr2[STEP];

__attribute__ ((noinline))
int loop() {
  int t = 0,i,iter;

#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif  
  for(iter=0; iter < ITERS; ++iter) {
    for(i=0; i < STEP; i+=1) {
      if(randArr[i] == 0)  {
        t+=3+3*t;
        arr[i]=t;
      } else if(randArr[i] == 1) {
        t-=1-5*t;
        arr1[i]=t;
      } else {
        t+=2-3*t;
        arr2[i]=t;
      }
    }
  }
#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif  
  return t;
}


int main(int argc, char* argv[]) {
  struct timespec t0, t1;
  double  t_elapsed;

  argc&=10000;

  printf("\n----BRANCH PREDICTION----\n");
  clock_gettime(CLOCK_MONOTONIC, &t0);
  
  int t=loop();
  volatile int a = t;

  clock_gettime(CLOCK_MONOTONIC, &t1);
    t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
                (double) (t1.tv_nsec - t0.tv_nsec); //ns

  printf("argc = %d, a = %d, arr[0] = %d, arr1[1] = %d, arr2[2] = %d \n", 
    argc, t, arr[0], arr1[1], arr2[2]);
  //summary
  printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
}
