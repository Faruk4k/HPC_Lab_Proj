from hardwares.components_classic import HWBoard, SingleCycleCPU, MESITwoLevelCache, DDR3

from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource


if __name__ == "__m5_main__":
    cpu = SingleCycleCPU()
    cache = MESITwoLevelCache()
    memory = DDR3()
    board = HWBoard(
        clk_freq="2GHz", processor=cpu, cache_hierarchy=cache, memory=memory
    )

    # Here we set the workload. In this case we want to run a simple "Hello World!"
    # program compiled to the ARM ISA. The `Resource` class will automatically
    # download the binary from the gem5 Resources cloud bucket if it's not already
    # present.
    board.set_se_binary_workload(
        # The `Resource` class reads the `resources.json` file from the gem5
        # resources repository:
        # https://github.com/gem5/gem5-resources.
        # Any resource specified in this file will be automatically retrieved.
        # At the time of writing, this file is a WIP and does not contain all
        # resources. Jira ticket: https://gem5.atlassian.net/browse/GEM5-1096
       obtain_resource("arm-hello64-static", resource_version="1.0.0")
    )

    #board.set_se_binary_workload(
    #    BinaryResource("../benchmarks/helloworld/helloworld.x"),
    #    )

    simulator = Simulator(board=board)
    simulator.run()
    print(f"Simulation finished.")