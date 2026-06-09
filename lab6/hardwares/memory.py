from gem5.components.memory.dram_interfaces.ddr3 import DDR3_1600_8x8
from gem5.components.memory.dram_interfaces.ddr4 import DDR4_2400_8x8
from gem5.components.memory.memory import ChanneledMemory


class DDR3(ChanneledMemory):
    """
    DDR3_1600_8x8 models a 1 GiB single channel DDR3 DRAM memory with a data
    bus clocked at 1600MHz. This model extends ChanneledMemory from gem5's
    standard library.
    """
    def __init__(self):
        super().__init__(
            dram_interface_class=DDR3_1600_8x8,
            num_channels=2,
            interleaving_size=128,
            size="1GiB",
        )

class DDR4(ChanneledMemory):
    """
    DDR4 models a 1 GiB single channel DDR4 DRAM memory with a data
    bus clocked at 2400MHz.
    """

    def __init__(self):
        super().__init__(
            dram_interface_class=DDR4_2400_8x8,
            num_channels=1,
            interleaving_size=128,
            size="1GiB",
        )
