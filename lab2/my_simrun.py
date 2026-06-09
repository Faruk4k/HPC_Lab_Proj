###############################################################################
# Lab goal: Exploring In-order microarchitecture
#           1 - ILP  
#           2 - Memory subsystem
###############################################################################

from hardwares import *

from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource
from argparse import ArgumentParser

from gem5.components.cachehierarchies.classic.no_cache import NoCache

parser = ArgumentParser(description="A SE mode setup to simulate a cpu type")

parser.add_argument(
    "-c",
    "--cpu",
    type=str,
    help="Type of in-order processor: A simple model (Simple) \
          or A pipelined model (Pipeline) ",
    required=True,
)

arguments = parser.parse_args()

if arguments.cpu.lower() == "simple":
    cpu = MySingleCycleCPU()
elif arguments.cpu.lower() == "pipeline":
    cpu = MyPipelinedCPU()
else:
    print("Error: Unknown CPU type")

#cache = MyClassicTwoLevelCacheBuild()
cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild()
#cache = NoCache()
memory = DDR3()
#memory = MySimpleMemory()
board = HWBoard(
    clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
)

board.set_se_binary_workload(
    ### fb_bench
    #BinaryResource("../benchmarks/fp_bench/fp_bench-m5.x"),
    #arguments = [""]
    ### stream-triad
    BinaryResource("../benchmarks/simple_triad/simple_triad-m5.x"),
    arguments = ["50000", "3"],
)


simulator = Simulator(board=board)
simulator.run()
print(f"Simulation finished.")