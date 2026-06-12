/*
*
* The reference code used in this lab is the one used in Tony-Nowatzki course:
  - https://github.com/PolyArch/cs251a-microbench/blob/master/spmv.c
  *
*/

#include <stdio.h>
#include <time.h>
#include "spmvArr.h"

#ifdef USEM5OPS
#include <gem5/m5ops.h>
#endif

void spmv(float val[NNZ], int cols[NNZ], int rowDelim[N_ROWS+1], float vec[N_COLS], float (*out)[N_ROWS]){
  int i, j;
  float sum, Si;

  for(i = 0; i < N_ROWS; i++){
    sum = 0; Si = 0;
    int tmp_begin = rowDelim[i];
    int tmp_end = rowDelim[i+1];
    for (j = tmp_begin; j < tmp_end; j++){
        Si = val[j] * vec[cols[j]];
        sum = sum + Si;
    }
    (*out)[i] += sum;
  }
}

 
int main(int argc, char* argv[]) {
  float out[N_ROWS];
  struct timespec t0, t1;
  double t_elapsed;

  printf("----spmv----\n");
  printf("N_ROWS          : %d \n", N_ROWS);
  printf("N_COLS          : %d \n", N_COLS);
  printf("NNZ             : %d \n", NNZ);
  
  clock_gettime(CLOCK_MONOTONIC, &t0);

#ifdef USEM5OPS
  m5_reset_stats(0, 0);
#endif

  for(int i = 0; i < 3; ++i) {
    spmv(val,cols,row_delim,vec,&out);
  }

#ifdef USEM5OPS
  m5_dump_stats(0, 0);
#endif

  clock_gettime(CLOCK_MONOTONIC, &t1);

  t_elapsed = (double)(t1.tv_sec - t0.tv_sec) * 1.0E+09 +
              (double)(t1.tv_nsec - t0.tv_nsec); // ns
    
  if(argc>=2) {
    printf("random_elem:%f, %s\n", out[1+argc],argv[0]);
  }

  printf("Execution time: %.6f (ms) \n", t_elapsed / 1.0E+06);

  return 0;
}
