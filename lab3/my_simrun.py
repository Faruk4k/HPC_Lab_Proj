###############################################################################
# Lab goal: Exploring Out-of-Order micro architecture configurations
#           the impact of small, medium, and big O3 microarchitecture
#           performance comparision of In-order vs Out-of-order architecture
#           branch prediction
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

multisim.set_num_processes(4)

def get_board(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size):
    cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild()
    memory = DDR3()
    cpu = MyOutOfOrderCPU(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size)

    board = HWBoard(
        clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
    )

    return board

configurations = {
    # small one
    "configROB-0": {"width": 2, "rob_size": 32, "num_int_regs": 64, "num_fpvec_regs": 64, "lsq_size": 5},
    # small one + a larger LSQ
    "configROB-1": {"width": 2, "rob_size": 32, "num_int_regs": 64, "num_fpvec_regs": 64, "lsq_size": 16},
    # Medium size
    "configROB-2": {"width": 4, "rob_size": 64, "num_int_regs": 64, "num_fpvec_regs": 64, "lsq_size": 64},
    # Big one
    "configROB-3": {"width": 8, "rob_size": 384, "num_int_regs": 512, "num_fpvec_regs": 512, "lsq_size": 128},
}

benchmarks = {
    "runA": {
        "binary": BinaryResource("../benchmarks/fp_bench/fp_bench-m5.x"),
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
        ### Run simulations in parallel ###
        multisim.add_simulator(simulation)


