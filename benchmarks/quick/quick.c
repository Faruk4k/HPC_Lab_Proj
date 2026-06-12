/*
* Quick sort benchmark, matching the style of the merge benchmark.
*/

#include <stdio.h>
#include <time.h>
#include <sys/time.h>

#include "randArr.h"

#ifdef USEM5OPS
#include <gem5/m5ops.h>
#endif

#define ASIZE sizeof(randArr)/sizeof(int)

void swap(int numbers[], int i, int j) {
  int temp;
  temp = numbers[i];
  numbers[i] = numbers[j];
  numbers[j] = temp;
}

int partition(int numbers[], int left, int right) {
  int pivot, i, j;

  pivot = numbers[right];
  i = left - 1;

  for (j = left; j < right; j++) {
    if (numbers[j] <= pivot) {
      i++;
      swap(numbers, i, j);
    }
  }

  swap(numbers, i + 1, right);
  return i + 1;
}

void q_sort(int numbers[], int left, int right) {
  int pivot_index;

  if (left < right) {
    pivot_index = partition(numbers, left, right);
    q_sort(numbers, left, pivot_index - 1);
    q_sort(numbers, pivot_index + 1, right);
  }
}

void quickSort(int numbers[], int array_size) {
  q_sort(numbers, 0, array_size - 1);
}

int main(int argc, char* argv[]) {
  struct timespec t0, t1;
  double t_elapsed;

  printf("----quick sort----\n");
  printf("Array SIZE      : %ld \n", ASIZE);

  clock_gettime(CLOCK_MONOTONIC, &t0);

#ifdef USEM5OPS
  m5_reset_stats(0, 0);
#endif

  quickSort(randArr, ASIZE);

#ifdef USEM5OPS
  m5_dump_stats(0, 0);
#endif

  clock_gettime(CLOCK_MONOTONIC, &t1);

  t_elapsed = (double)(t1.tv_sec - t0.tv_sec) * 1.0E+09 +
              (double)(t1.tv_nsec - t0.tv_nsec); // ns

  if(argc >= 2) {
    printf("random_elem:%d, %s\n", randArr[(1 + argc) % ASIZE], argv[0]);
  }

  printf("Execution time: %.6f (ms) \n", t_elapsed / 1.0E+06);

  return 0;
}k