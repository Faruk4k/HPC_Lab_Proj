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
    "small":  {"l1d_size": "16KiB", "l1d_assoc": 8, "l2_size": "256KiB", "l2_assoc": 16},
}


benchmarks = {
    "runA": {
         "binary": BinaryResource("../benchmarks/matmult/matmult-m5.x"),
         "args": ["2", "0"],
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



