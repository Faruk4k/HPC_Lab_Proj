###############################################################################
# Lab goal: Exploring cache blocking vs non-blocking, 
#                     interchanged loops
#                     cache size, associativity
#                     memory prefetching
###############################################################################


###############################################################################
# import this to fix multisim invocation issues that it can not find hardwares 
# package 
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
###############################################################################


from hardwares import *

from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource
from gem5.utils.multisim import multisim
from gem5.objects import TaggedPrefecher

multisim.set_num_processes(6)

def get_board(degree):
    l1d_prefetcher = TaggedPrefetcher(**pref_params)
    cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild(
        l1d_size = "32KiB" , l1d_assoc = 4,
        l1d_prefetcher = l1d_prefetcher,
        l2_size = "256KiB" , l2_assoc = 16
    )
    memory = DDR4()
    cpu = MyOutOfOrderCPU(width=8, rob_size=192, num_int_regs=256, num_fpvec_regs=256, lsq_size=32)
    board = HWBoard(
        clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
    )

    return board

configurations = {
    "deg1" : {"degree": 1},
    "deg4" : {"degree": 4},
    "deg8" : {"degree": 8},
    "deg16" : {"degree": 16},
    "deg32" : {"degree": 32}
}

benchmarks = {
    "mm": {
        "binary": BinaryResource("../benchmarks/matmult/matmult-m5.x"),
        "args": ["2"], # <LOOP>
    },
    "spmv": {
        "binary": BinaryResource("../benchmarks/spmv/spmv-m5.x"),
        "args": [],
    },
    "simple_triad": {
        "binary": BinaryResource("../benchmarks/simple_triad/simple_triad-m5.x"),
        "args": ["100000", "2"], # <ARRAY_SIZE>, <LOOP>
    },
    "merge": {
        "binary": BinaryResource("../benchmarks/merge/merge-m5.x"),
        "args": [],
    },
    "quick": {
        "binary": BinaryResource("../benchmarks/quick/quick-m5.x"),
        "args": [],
    },
    "bfs": {
        "binary": BinaryResource("../benchmarks/bfs/bfs-m5.x"),
        "args": [],
    },
}

for benchname, benchcfg in benchmarks.items():
    for archname, archcfg in configurations.items():
        board = get_board(**archcfg)

        board.set_se_binary_workload(
            binary=benchcfg["binary"],
            arguments=benchcfg["args"],
        )

        simulation = Simulator(
            board=board,
            id=f"{archname}-{benchname}",
        )

        multisim.add_simulator(simulation)



