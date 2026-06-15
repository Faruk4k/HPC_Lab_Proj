#!/bin/bash
set -e

GEM5=../../gem5/build/ALL/gem5.opt
CONFIG=run.py
ROOT=results_stride_multisim

get_binary() {
  case "$1" in
    simple_triad) echo "../benchmarks/simple_triad/simple_triad-m5.x" ;;
    matmult)      echo "../benchmarks/matmult/matmult-m5.x" ;;
    spmv)         echo "../benchmarks/spmv/spmv-m5.x" ;;
    merge)        echo "../benchmarks/merge/merge-m5.x" ;;
    quick)        echo "../benchmarks/quick/quick-m5.x" ;;
    bfs)          echo "../benchmarks/bfs/bfs-m5.x" ;;
    *) echo "UNKNOWN_BENCHMARK"; exit 1 ;;
  esac
}

get_args() {
  case "$1" in
    simple_triad) echo "1000000 1" ;;
    matmult)      echo "1" ;;
    spmv)         echo "" ;;
    merge)        echo "x" ;;
    quick)        echo "x" ;;
    bfs)          echo "" ;;
    *) echo ""; exit 1 ;;
  esac
}

while read -r bench cfg level mem sim_id; do
  OUTDIR="${ROOT}/${sim_id}"
  STATS="${OUTDIR}/stats.txt"

  if [ -f "${STATS}" ]; then
    echo "Skipping existing: ${sim_id}"
    continue
  fi

  BIN=$(get_binary "${bench}")
  ARGS=$(get_args "${bench}")

  echo "=================================================="
  echo "Rerunning        : ${sim_id}"
  echo "Benchmark        : ${bench}"
  echo "Binary           : ${BIN}"
  echo "Args             : ${ARGS}"
  echo "Stride config    : ${cfg}"
  echo "Level            : ${level}"
  echo "Memory           : ${mem}"
  echo "Output dir       : ${OUTDIR}"
  echo "=================================================="

  rm -rf "${OUTDIR}"
  mkdir -p "${OUTDIR}"

  ${GEM5} \
    --outdir="${OUTDIR}" \
    ${CONFIG} \
    --benchmark "${BIN}" \
    --benchmark-args "${ARGS}" \
    --prefetcher stride \
    --stride-config "${cfg}" \
    --pf-level "${level}" \
    --memory "${mem}"

done < missing_stride_runs.txt