import os
import sys
import json

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.multisim import multisim

from hardwares import (
    HWBoard,
    MyOutOfOrderCPU,
    MyClassicPrivateL1SharedL2CacheHierarchyBuild,
    DDR4,
    DDR4_2x,
)

from imp_stage3_configs import make_imp_stage3_prefetcher

multisim.set_num_processes(4)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BENCHMARKS = {
    "simple_triad": {
        "binary": "benchmarks/simple_triad/simple_triad-m5.x",
        "args": ["1000000", "1"],
    },
    "matmult": {
        "binary": "benchmarks/matmult/matmult-m5.x",
        "args": ["1"],
    },
    "spmv": {
        "binary": "benchmarks/spmv/spmv-m5.x",
        "args": [],
    },
    "merge": {
        "binary": "benchmarks/merge/merge-m5.x",
        "args": ["x"],
    },
    "quick": {
        "binary": "benchmarks/quick/quick-m5.x",
        "args": ["x"],
    },
    "bfs": {
        "binary": "benchmarks/bfs/bfs-m5.x",
        "args": [],
    },
}

MEMORIES = {
    "ddr4_1x": DDR4,
    "ddr4_2x": DDR4_2x,
}

with open("imp_stage3_plan.json") as f:
    STAGE3_PLAN = json.load(f)


def make_board(memory_name, pf_level, config_name):
    IMPPF = make_imp_stage3_prefetcher(config_name)

    if pf_level == "l1d":
        l1d_pf = IMPPF
        l2_pf = None
    elif pf_level == "l2":
        l1d_pf = None
        l2_pf = IMPPF
    else:
        raise ValueError(f"Unknown pf_level: {pf_level}")

    processor = MyOutOfOrderCPU(
        width=4,
        rob_size=128,
        num_int_regs=160,
        num_fpvec_regs=160,
        lsq_size=64,
    )

    memory = MEMORIES[memory_name]()

    cache_hierarchy = MyClassicPrivateL1SharedL2CacheHierarchyBuild(
        l1d_size="16KiB",
        l1d_assoc=8,
        l2_size="256KiB",
        l2_assoc=16,
        l1d_prefetcher=l1d_pf,
        l2_prefetcher=l2_pf,
    )

    return HWBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )


def add_simulation(benchmark_name, pf_level, memory_name, config_name):
    benchmark_info = BENCHMARKS[benchmark_name]
    binary_path = os.path.join(PROJECT_ROOT, benchmark_info["binary"])

    if not os.path.exists(binary_path):
        raise FileNotFoundError(binary_path)

    board = make_board(memory_name, pf_level, config_name)

    board.set_se_binary_workload(
        BinaryResource(local_path=binary_path),
        arguments=benchmark_info["args"],
    )

    sim_id = f"{benchmark_name}_imp3_{config_name}_{pf_level}_{memory_name}"

    multisim.add_simulator(
        Simulator(
            board=board,
            id=sim_id,
        )
    )


for case_key, config_names in STAGE3_PLAN.items():
    benchmark_name, pf_level, memory_name = case_key.split("|")

    for config_name in config_names:
        add_simulation(benchmark_name, pf_level, memory_name, config_name)
