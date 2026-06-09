
###############################################################################
# Lab goal: Exploring of cache coherence protocol
#                  MESI (Ruby), BUS Snooping (Classic memory model)
#                  Mesh, Bus, Point2Point NoCs
# simple_triad, false sharing, dot product, spmv, matmult
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

multisim.set_num_processes(2)

def get_board(num_cores):
    ### ruby model ###
    cache = MyMESITwoLevelCacheBuildCustom(
                                        link_latency=3, #9, #27 
                                        network_select = "garnetmesh"
                                        )
    
    #cache = MyMESITwoLevelCacheBuildStd()
    
    ### classic model ###
    #cache = MyClassicPrivateL1SharedL2CacheHierarchyBuild(l1d_size="16KiB", l1d_assoc=8, 
    #                                                      l2_size="256KiB", l2_assoc=16)

    memory = DDR3()
    #cpu = MyO3Processor(
    #    width=8, rob_size=192, num_int_regs=256, num_fp_regs=256, num_cores=num_cores
    #    )
    
    cpu = MyOutOfOrderCPU(width=8, rob_size=192, num_int_regs=256, num_fpvec_regs=256, 
                          lsq_size=128, sve_vl=2, num_cores=num_cores)
    
    board = HWBoard(
        clk_freq="1GHz", processor=cpu, cache_hierarchy=cache, memory=memory
        )

    return board

configurations = {
    "config_1": {"num_cores": 8},
#    "config_2": {"num_cores": 4},
}

### False sharing ###
benchmarks = {
#    "runA": {
#        "binary": BinaryResource("../benchmarks/false_sharing/false_sharing_pad-m5.x"),
#        "args": ["7"]
#    },
    "runB": {
        "binary": BinaryResource("../benchmarks/false_sharing/false_sharing_nopad-m5.x"),
        "args": ["7"]
    },
}

### Dot product parallelism ###
#benchmarks = {
#    "runA": {
#        "binary": BinaryResource("../benchmarks/dot_product/dot_product_v1-m5.x"),
#        "args": ["4", "300000"]
#},
#    "runB": {
#        "binary": BinaryResource("../benchmarks/dot_product/dot_product_v2-m5.x"),
#        "args": ["4", "300000"]

#    },
#}

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


