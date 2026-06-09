###############################################################################
# Lab goal: Exploring Out-of-Order micro architecture configurations
#           the impact of small, medium, and big O3 microarchitecture
#           performance comparision of In-order vs Out-of-order architecture
###############################################################################


from hardwares import *

from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource

import m5

def get_board(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size):
    cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild()
    memory = DDR3()
    cpu = MyOutOfOrderCPU(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size)

    board = HWBoard(
        clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
    )

    return board


board = get_board(width=2, rob_size=32, num_int_regs=64, num_fpvec_regs=64, lsq_size=5)
board.set_se_binary_workload(
    BinaryResource("../benchmarks/fp_bench/fp_bench-m5.x"),
    arguments = [""]
)

# Set max Nr. simulated instructions (e.g. 5 mils helpful for bfs)


simulator = Simulator(board=board)
simulator.run()

print("Exited at tick", m5.curTick())

print(f"Simulation finished.")

