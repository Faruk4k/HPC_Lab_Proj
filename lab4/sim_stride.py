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

multisim.set_num_processes(16)

def get_board(l1d_size, l1d_assoc, l2_size, l2_assoc):
    cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild(l1d_size, l1d_assoc, l2_size, l2_assoc)
    memory = DDR3()
    cpu = MyOutOfOrderCPU(width=8, rob_size=192, num_int_regs=256, num_fpvec_regs=256, lsq_size=32)

    board = HWBoard(
        clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
    )

    return board

configurations = {
    "deg1_dist1" : {"degree": 1, "distance": 1},
    "deg1_dist4" : {"degree": 1, "distance": 4},
    "deg1_dist8" : {"degree": 1, "distance": 8},
    "deg1_dist16" : {"degree": 1, "distance": 16},
    "deg1_dist32" : {"degree": 1, "distance": 32},
    "deg4_dist1" : {"degree": 4, "distance": 1},
    "deg4_dist4" : {"degree": 4, "distance": 4},
    "deg4_dist8" : {"degree": 4, "distance": 8},
    "deg4_dist16" : {"degree": 4, "distance": 16},
    "deg4_dist32" : {"degree": 4, "distance": 32},
    "deg8_dist1" : {"degree": 8, "distance": 1},
    "deg8_dist4" : {"degree": 8, "distance": 4},
    "deg8_dist8" : {"degree": 8, "distance": 8},
    "deg8_dist16" : {"degree": 8, "distance": 16},
    "deg8_dist32" : {"degree": 8, "distance": 32},
    "deg16_dist1" : {"degree": 16, "distance": 1},
    "deg16_dist4" : {"degree": 16, "distance": 4},
    "deg16_dist8" : {"degree": 16, "distance": 8},
    "deg16_dist16" : {"degree": 16, "distance": 16},
    "deg16_dist32" : {"degree": 16, "distance": 32},
    "deg32_dist1" : {"degree": 32, "distance": 1},
    "deg32_dist4" : {"degree": 32, "distance": 4},
    "deg32_dist8" : {"degree": 32, "distance": 8},
    "deg32_dist16" : {"degree": 32, "distance": 16},
    "deg32_dist32" : {"degree": 32, "distance": 32}
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



