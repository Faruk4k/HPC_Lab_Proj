#!/bin/bash

set -e

GEM5=../../gem5/build/ALL/gem5.opt
CONFIG=run.py

BENCH_NAME=simple_triad
BENCH_BIN=../benchmarks/simple_triad/simple_triad-m5.x
BENCH_ARGS="1000000 1"

STRIDE_CONFIGS=(
  deg1_dist1 deg1_dist4 deg1_dist8 deg1_dist16 deg1_dist32
  deg4_dist1 deg4_dist4 deg4_dist8 deg4_dist16 deg4_dist32
  deg8_dist1 deg8_dist4 deg8_dist8 deg8_dist16 deg8_dist32
  deg16_dist1 deg16_dist4 deg16_dist8 deg16_dist16 deg16_dist32
  deg32_dist1 deg32_dist4 deg32_dist8 deg32_dist16 deg32_dist32
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

      OUTDIR="results/${BENCH_NAME}/stride/${cfg}/${level}/${mem}"

      echo "=================================================="
      echo "Running benchmark : ${BENCH_NAME}"
      echo "Stride config     : ${cfg}"
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
        --prefetcher stride \
        --stride-config "${cfg}" \
        --pf-level "${level}" \
        --memory "${mem}"

    done
  done
done