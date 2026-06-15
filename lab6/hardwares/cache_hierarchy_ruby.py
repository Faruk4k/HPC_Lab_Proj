
from gem5.components.cachehierarchies.ruby.\
    mesi_two_level_cache_hierarchy import MESITwoLevelCacheHierarchy

from gem5.components.cachehierarchies.ruby.\
    abstract_ruby_cache_hierarchy import AbstractRubyCacheHierarchy
from gem5.components.cachehierarchies.\
    abstract_two_level_cache_hierarchy import AbstractTwoLevelCacheHierarchy
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.utils.requires import requires

from .network import *
from gem5.components.cachehierarchies.ruby.\
    caches.mesi_two_level.l1_cache import L1Cache
from gem5.components.cachehierarchies.ruby.\
    caches.mesi_two_level.l2_cache import L2Cache
from gem5.components.cachehierarchies.ruby.\
    caches.mesi_two_level.directory import Directory
from gem5.components.cachehierarchies.ruby.\
    caches.mesi_two_level.dma_controller import DMAController

from m5.objects import (
    RubySystem,
    RubySequencer,
    DMASequencer,
    RubyPortProxy
)

class MyMESITwoLevelCacheBuildStd(MESITwoLevelCacheHierarchy):
    def __init__(self):
        super().__init__(
            l1i_size="16KiB",
            l1i_assoc=8,
            l1d_size="16KiB",
            l1d_assoc=8,
            l2_size="256KiB",
            l2_assoc=16,
            num_l2_banks=1,
        )

class MyMESITwoLevelCacheBuildCustom(
    AbstractRubyCacheHierarchy, AbstractTwoLevelCacheHierarchy
):
    """A two level private L1 shared L2 MESI hierarchy.

    In addition to the normal two level parameters, you can also change the
    number of L2 banks in this protocol.

    The on-chip network is a either clustertree or point-to-point all-to-all 
    simple network with a configurable latency.
    """

    def __init__(self, link_latency: int, network_select: str):
        AbstractRubyCacheHierarchy.__init__(self=self)
        AbstractTwoLevelCacheHierarchy.__init__(
            self,
            l1i_size="32KiB",
            l1i_assoc=8,
            l1d_size="32KiB",
            l1d_assoc=8,
            l2_size="512KiB",
            l2_assoc=8,
        )

        self._link_latency = link_latency
        self._network_select = network_select

    def incorporate_cache(self, board: AbstractBoard) -> None:

        requires(coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL)

        cache_line_size = board.get_cache_line_size()

        self.ruby_system = RubySystem()

        # MESI_Two_Level needs 5 virtual networks
        self.ruby_system.number_of_virtual_networks = 5

        if self._network_select == "pt2pt":
            self.ruby_system.network = LabSimplePt2Pt(
                self.ruby_system, self._link_latency
            )
            self._num_l2_banks = board.get_processor().get_num_cores()
        if self._network_select == "garnetpt2pt":
            self.ruby_system.network = LabGarnetPt2Pt (
                self.ruby_system, self._link_latency
            )
            self._num_l2_banks = board.get_processor().get_num_cores()
        elif self._network_select == "clustertree":
            self.ruby_system.network = LabL1L2ClusterTree(
                self.ruby_system, self._link_latency
            )
            #self._num_l2_banks = board.get_processor().get_actual_num_cores()
            self._num_l2_banks = board.get_processor().get_num_cores() - 1
        elif self._network_select == "garnetmesh":
            self.ruby_system.network = LabGarnetMesh (
                self.ruby_system, self._link_latency
                )
            self._num_l2_banks = board.get_processor().get_num_cores()

        else:
            raise ValueError(f"Incorrect ruby network model: {self._network_select}")
        
        self.ruby_system.network.number_of_virtual_networks = 5


        runtime_isa = board.get_processor().get_isa()

        self._l1_controllers = []
        for i, core in enumerate(board.get_processor().get_cores()):
            cache = L1Cache(
                self._l1i_size,
                self._l1i_assoc,
                self._l1d_size,
                self._l1d_assoc,
                self.ruby_system.network,
                core,
                self._num_l2_banks,
                cache_line_size,
                runtime_isa,
                board.get_clock_domain(),
            )

            cache.sequencer = RubySequencer(
                version=i,
                dcache=cache.L1Dcache,
                clk_domain=cache.clk_domain,
                ruby_system=self.ruby_system,
            )

            if board.has_io_bus():
                cache.sequencer.connectIOPorts(board.get_io_bus())

            cache.ruby_system = self.ruby_system

            core.connect_icache(cache.sequencer.in_ports)
            core.connect_dcache(cache.sequencer.in_ports)

            core.connect_walker_ports(
                cache.sequencer.in_ports, cache.sequencer.in_ports
            )

            # Connect the interrupt ports
            if runtime_isa == ISA.X86:
                int_req_port = cache.sequencer.interrupt_out_port
                int_resp_port = cache.sequencer.in_ports
                core.connect_interrupt(int_req_port, int_resp_port)
            else:
                core.connect_interrupt()

            self._l1_controllers.append(cache)

        self._l2_controllers = [
            L2Cache(
                self._l2_size,
                self._l2_assoc,
                self.ruby_system.network,
                self._num_l2_banks,
                cache_line_size,
            )
            for _ in range(self._num_l2_banks)
        ]
        # TODO: Make this prettier: The problem is not being able to proxy
        # the ruby system correctly
        for cache in self._l2_controllers:
            cache.ruby_system = self.ruby_system

        self._directory_controllers = [
            Directory(self.ruby_system.network, cache_line_size, range, port)
            for range, port in board.get_memory().get_mem_ports()
        ]
        # TODO: Make this prettier: The problem is not being able to proxy
        # the ruby system correctly
        for dir in self._directory_controllers:
            dir.ruby_system = self.ruby_system

        self._dma_controllers = []
        if board.has_dma_ports():
            dma_ports = board.get_dma_ports()
            for i, port in enumerate(dma_ports):
                ctrl = DMAController(self.ruby_system.network, cache_line_size)
                ctrl.dma_sequencer = DMASequencer(version=i, in_ports=port)
                self._dma_controllers.append(ctrl)
                ctrl.ruby_system = self.ruby_system

        self.ruby_system.num_of_sequencers = len(self._l1_controllers) + len(
            self._dma_controllers
        )
        self.ruby_system.l1_controllers = self._l1_controllers
        self.ruby_system.l2_controllers = self._l2_controllers
        self.ruby_system.directory_controllers = self._directory_controllers

        if len(self._dma_controllers) != 0:
            self.ruby_system.dma_controllers = self._dma_controllers

        # Create the network and connect the controllers.
        if self._network_select == "pt2pt":
            self.ruby_system.network.connectControllers(
                self._l1_controllers
                + self._l2_controllers
                + self._directory_controllers
                + self._dma_controllers
            )
            self.ruby_system.network.setup_buffers()
        elif self._network_select == "clustertree":                    
            self.ruby_system.network.connectControllers(
                self._l1_controllers,
                self._l2_controllers,
                self._directory_controllers[0],
            )
            self.ruby_system.network.setup_buffers()
        elif self._network_select == "garnetpt2pt":
            self.ruby_system.network.connectControllers(
                self._l1_controllers
                + self._l2_controllers
                + self._directory_controllers
                + self._dma_controllers
            )
        elif self._network_select == "garnetmesh":            
            self.ruby_system.network.connectControllers(
                self._l1_controllers
                + self._l2_controllers
                + self._directory_controllers
                + self._dma_controllers,
                len(self._l1_controllers)
            )


        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.ruby_system.sys_port_proxy = RubyPortProxy(
            ruby_system=self.ruby_system
        )
        board.connect_system_port(self.ruby_system.sys_port_proxy.in_ports)




