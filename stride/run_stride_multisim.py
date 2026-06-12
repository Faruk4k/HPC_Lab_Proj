import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

import os

from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.multisim import multisim

from hardwares import (
    HWBoard,
    MyOutOfOrderCPU,
    MyClassicPrivateL1SharedL2CacheHierarchyBuild,
    DDR4,
    DDR4_2x,
    MySimpleMemory,
)

from stride_configs import make_stride_prefetcher, stride_configurations


# Do not set this too high on the cluster.
# Start with 4 or 8. Increase only if the node has enough cores/RAM.
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

PF_LEVELS = ["l1d", "l2"]


def make_board(memory_name, pf_level, stride_config_name):
    StridePF = make_stride_prefetcher(stride_config_name)

    if pf_level == "l1d":
        l1d_pf = StridePF
        l2_pf = None
    elif pf_level == "l2":
        l1d_pf = None
        l2_pf = StridePF
    else:
        raise ValueError(f"Invalid pf_level: {pf_level}")

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

    board = HWBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )

    return board


def add_stride_simulation(benchmark_name, benchmark_info, memory_name, pf_level, stride_config_name):
    binary_path = os.path.join(PROJECT_ROOT, benchmark_info["binary"])

    if not os.path.exists(binary_path):
        raise FileNotFoundError(f"Benchmark binary does not exist: {binary_path}")

    board = make_board(
        memory_name=memory_name,
        pf_level=pf_level,
        stride_config_name=stride_config_name,
    )

    board.set_se_binary_workload(
        BinaryResource(local_path=binary_path),
        arguments=benchmark_info["args"],
    )

    sim_id = f"{benchmark_name}_stride_{stride_config_name}_{pf_level}_{memory_name}"

    simulator = Simulator(
        board=board,
        id=sim_id,
    )

    multisim.add_simulator(simulator)


for benchmark_name, benchmark_info in BENCHMARKS.items():
    for memory_name in MEMORIES:
        for pf_level in PF_LEVELS:
            for stride_config_name in stride_configurations:
                add_stride_simulation(
                    benchmark_name=benchmark_name,
                    benchmark_info=benchmark_info,
                    memory_name=memory_name,
                    pf_level=pf_level,
                    stride_config_name=stride_config_name,
                )