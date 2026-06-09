/*
* The reference code is one used in Tony-Nowatzki course:
  - https://github.com/PolyArch/cs251a-microbench/blob/master/spmv.c
*/

#include <stdio.h>
# include <sys/time.h>
# include <time.h>
#ifdef USEM5OPS
  #include <gem5/m5ops.h>
#endif

#include "randArr.h"

#define ASIZE sizeof(randArr)/sizeof(int)

int temp[ASIZE];

void merge(int numbers[], int temp[], int left, int mid, int right) {
  int i, left_end, num_elements, tmp_pos;
 
  left_end = mid - 1;
  tmp_pos = left;
  num_elements = right - left + 1;
 
  while ((left <= left_end) && (mid <= right)) {
    if (numbers[left] <= numbers[mid]) {
      temp[tmp_pos++] = numbers[left++];
    } else {
      temp[tmp_pos++] = numbers[mid++];
    }
  }
 
  while (left <= left_end) {
    temp[tmp_pos++] = numbers[left++];
  }
  
  while (mid <= right) {
    temp[tmp_pos++] = numbers[mid++];
  }
 
  for (i=0; i < num_elements; i++) {
    numbers[right] = temp[right];
    right = right - 1;
  }
}

void m_sort(int numbers[], int temp[], int left, int right) {
  int mid;
  if (right > left) {
    mid = (right + left) / 2;
    m_sort(numbers, temp, left, mid);
    m_sort(numbers, temp, mid+1, right);
    merge(numbers, temp, left, mid+1, right);
  }
}

void mergeSort(int numbers[], int temp[], int array_size) {
  m_sort(numbers, temp, 0, array_size - 1);
}
 
int main(int argc, char* argv[]) {
  struct timespec t0, t1;
  double  t_elapsed;

  printf("\n----merge----\n");
  clock_gettime(CLOCK_MONOTONIC, &t0);

#ifdef USEM5OPS
    m5_reset_stats(0,0); 
#endif
  mergeSort(randArr, temp, ASIZE);
#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif

  clock_gettime(CLOCK_MONOTONIC, &t1);
  t_elapsed = (double) (t1.tv_sec - t0.tv_sec) * 1.0E+09 + 
              (double) (t1.tv_nsec - t0.tv_nsec); //ns

  //summary
  // printf("a[%i]=%.2e. b[%i]=%.2e. c[%i]=%.2e.\n", 0, a[0], 0, b[0], 0, c[0]);
  printf("Execution time: %.6f (ms) \n", t_elapsed/1.0E+06);
 
  if(argc>=2) {
    printf("random_elem:%d, %s\n", randArr[(1+argc) % ASIZE],argv[0]);
  }
}