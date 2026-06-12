#!/bin/bash

set -e

GEM5=../../gem5/build/ALL/gem5.opt
CONFIG=run.py

BENCH_NAME=spmv
BENCH_BIN=../benchmarks/spmv/spmv-m5.x
BENCH_ARGS="2"

STRIDE_CONFIGS=(
    deg1 deg4 deg8 deg16 deg32
)

PF_LEVELS=(
  l1d
  l2
)

MEMORIES=(
  ddr4_1x
  ddr4_2x
)

for mem in "${MEMORIES[@]}"; do
  for level in "${PF_LEVELS[@]}"; do
    for cfg in "${STRIDE_CONFIGS[@]}"; do

      OUTDIR="results/${BENCH_NAME}/nextline/${cfg}/${level}/${mem}"

      echo "=================================================="
      echo "Running benchmark : ${BENCH_NAME}"
      echo "Nextline config  : ${cfg}"
      echo "Prefetch level    : ${level}"
      echo "Memory            : ${mem}"
      echo "Output dir        : ${OUTDIR}"
      echo "=================================================="

      mkdir -p "${OUTDIR}"

      ${GEM5} \
        --outdir="${OUTDIR}" \
        ${CONFIG} \
        --benchmark "${BENCH_BIN}" \
        --benchmark-args "${BENCH_ARGS}" \
        --prefetcher nextline \
        --nextline-config "${cfg}" \
        --pf-level "${level}" \
        --memory "${mem}"

    done
  done
done
