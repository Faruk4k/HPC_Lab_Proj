
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.cachehierarchies.abstract_cache_hierarchy import AbstractCacheHierarchy
from gem5.components.cachehierarchies.abstract_two_level_cache_hierarchy import AbstractTwoLevelCacheHierarchy
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from gem5.utils.override import *
from gem5.isas import ISA

from m5.objects import (
    BadAddr,
    BaseXBar,
    Cache,
    L2XBar,
    Port,
    SystemXBar,
    Clusivity,
    BasePrefetcher,
)

from typing import Type, Optional



class MyL1DCache(Cache):
    """
    A simple L1 data cache with default values.

    If the cache has a mostly exclusive downstream cache, ``writeback_clean``
    should be set to ``True``.
    """

    def __init__(
        self,
        size: str,
        assoc: int = 8,
        tag_latency: int = 1,
        data_latency: int = 1,
        response_latency: int = 1,
        mshrs: int = 16,
        tgts_per_mshr: int = 20,
        writeback_clean: bool = False,
        PrefetcherCls = None,
    ):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = tag_latency
        self.data_latency = data_latency
        self.response_latency = response_latency
        self.mshrs = mshrs
        self.tgts_per_mshr = tgts_per_mshr
        self.writeback_clean = writeback_clean
        if PrefetcherCls is not None:
            self.prefetcher = PrefetcherCls()
        
        self.tags.block_size = 64
        

class MyL1ICache(Cache):
    """
    A simple L1 instruction cache with default values.

    If the cache does not have a downstream cache or the downstream cache
    is mostly inclusive as usual, ``writeback_clean`` should be set to ``False``.
    """

    def __init__(
        self,
        size: str,
        assoc: int = 8,
        tag_latency: int = 1,
        data_latency: int = 1,
        response_latency: int = 1,
        mshrs: int = 16,
        tgts_per_mshr: int = 20,
        writeback_clean: bool = True,
        PrefetcherCls = None,
    ):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = tag_latency
        self.data_latency = data_latency
        self.response_latency = response_latency
        self.mshrs = mshrs
        self.tgts_per_mshr = tgts_per_mshr
        self.writeback_clean = writeback_clean
        if PrefetcherCls is not None:
            self.prefetcher = PrefetcherCls()
        self.tags.block_size = 64

class MyL2Cache(Cache):
    """
    A simple L2 Cache with default values.
    """

    def __init__(
        self,
        size: str,
        assoc: int = 16,
        tag_latency: int = 10,
        data_latency: int = 10,
        response_latency: int = 1,
        mshrs: int = 20,
        tgts_per_mshr: int = 12,
        writeback_clean: bool = False,
        clusivity: Clusivity = "mostly_incl",
        PrefetcherCls = None,
    ):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = tag_latency
        self.data_latency = data_latency
        self.response_latency = response_latency
        self.mshrs = mshrs
        self.tgts_per_mshr = tgts_per_mshr
        self.writeback_clean = writeback_clean
        self.clusivity = clusivity
        if PrefetcherCls is not None:
            self.prefetcher = PrefetcherCls()
        self.tags.block_size = 64
        

class MyMMUCache(Cache):
    """
    A simple Memory Management Unit (MMU) cache with default values.

    If the cache does not have a downstream cache or the downstream cache
    is mostly inclusive as usual, ``writeback_clean`` should be set to ``False``.
    """

    def __init__(
        self,
        size: str,
        assoc: int = 4,
        tag_latency: int = 1,
        data_latency: int = 1,
        response_latency: int = 1,
        mshrs: int = 20,
        tgts_per_mshr: int = 12,
        writeback_clean: bool = True,
    ):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = tag_latency
        self.data_latency = data_latency
        self.response_latency = response_latency
        self.mshrs = mshrs
        self.tgts_per_mshr = tgts_per_mshr
        self.writeback_clean = writeback_clean

class MyClassicPrivateL1SharedL2CacheHierarchy(
    AbstractClassicCacheHierarchy, AbstractTwoLevelCacheHierarchy
):
    """
    A cache setup where each core has a private L1 Data and Instruction Cache,
    and a L2 cache is shared with all cores. The shared L2 cache is mostly
    inclusive with respect to the split I/D L1 and MMU caches.
    """

    def _get_default_membus(self) -> SystemXBar:
        """
        A method used to obtain the default memory bus of 64 bit in width for
        the PrivateL1SharedL2 CacheHierarchy.

        :returns: The default memory bus for the PrivateL1SharedL2
                  CacheHierarchy.

        :rtype: SystemXBar
        """
        membus = SystemXBar(width=64)
        membus.badaddr_responder = BadAddr()
        membus.default = membus.badaddr_responder.pio
        return membus

    def __init__(
        self,
        l1d_size: str,
        l1i_size: str,
        l2_size: str,
        l1d_assoc: int = 8,
        l1i_assoc: int = 8,
        l2_assoc: int = 16,
        membus: Optional[BaseXBar] = None,
        l1d_prefetcher: Optional[BasePrefetcher] = None,

    ) -> None:
        """
        :param l1d_size: The size of the L1 Data Cache (e.g., "32KiB").
        :param  l1i_size: The size of the L1 Instruction Cache (e.g., "32KiB").
        :param l2_size: The size of the L2 Cache (e.g., "256KiB").
        :param l1d_assoc: The associativity of the L1 Data Cache.
        :param l1i_assoc: The associativity of the L1 Instruction Cache.
        :param l2_assoc: The associativity of the L2 Cache.
        :param membus: The memory bus. This parameter is optional parameter and
                       will default to a 64 bit width SystemXBar is not
                       specified.
        """

        AbstractClassicCacheHierarchy.__init__(self=self)
        AbstractTwoLevelCacheHierarchy.__init__(
            self,
            l1i_size=l1i_size,
            l1i_assoc=l1i_assoc,
            l1d_size=l1d_size,
            l1d_assoc=l1d_assoc,
            l2_size=l2_size,
            l2_assoc=l2_assoc,
        )

        self.membus = membus if membus else self._get_default_membus()
        self._l1d_prefetcher = l1d_prefetcher


    @overrides(AbstractClassicCacheHierarchy)
    def get_mem_side_port(self) -> Port:
        return self.membus.mem_side_ports

    @overrides(AbstractClassicCacheHierarchy)
    def get_cpu_side_port(self) -> Port:
        return self.membus.cpu_side_ports

    @overrides(AbstractCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard) -> None:
        # Set up the system port for functional access from the simulator.
        board.connect_system_port(self.membus.cpu_side_ports)

        for _, port in board.get_mem_ports():
            self.membus.mem_side_ports = port

        self.l1icaches = [
            MyL1ICache(
                size=self._l1i_size,
                assoc=self._l1i_assoc,
                writeback_clean=False,
            )
            for i in range(board.get_processor().get_num_cores())
        ]
        self.l1dcaches = [
            MyL1DCache(
                size=self._l1d_size, 
                assoc=self._l1d_assoc,
                # set a prefetcher
                PrefetcherCls=self._l1d_prefetcher #StridePrefetcher
                )
            for i in range(board.get_processor().get_num_cores())
        ]
        self.l2bus = L2XBar()
        self.l2cache = MyL2Cache(size=self._l2_size, assoc=self._l2_assoc)
        # ITLB Page walk caches
        self.iptw_caches = [
            MyMMUCache(size="8KiB", writeback_clean=False)
            for _ in range(board.get_processor().get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MyMMUCache(size="8KiB", writeback_clean=False)
            for _ in range(board.get_processor().get_num_cores())
        ]

        if board.has_coherent_io():
            self._setup_io_cache(board)

        for i, cpu in enumerate(board.get_processor().get_cores()):
            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = self.l2bus.cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2bus.cpu_side_ports
            self.iptw_caches[i].mem_side = self.l2bus.cpu_side_ports
            self.dptw_caches[i].mem_side = self.l2bus.cpu_side_ports

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            # ignore X86 here
            if board.get_processor().get_isa() == ISA.X86:
                int_req_port = self.membus.mem_side_ports
                int_resp_port = self.membus.cpu_side_ports
                cpu.connect_interrupt(int_req_port, int_resp_port)
            else:
                cpu.connect_interrupt()

        self.l2bus.mem_side_ports = self.l2cache.cpu_side
        self.membus.cpu_side_ports = self.l2cache.mem_side

    def _setup_io_cache(self, board: AbstractBoard) -> None:
        """Create a cache for coherent I/O connections"""
        self.iocache = Cache(
            assoc=8,
            tag_latency=50,
            data_latency=50,
            response_latency=50,
            mshrs=20,
            size="1KiB",
            tgts_per_mshr=12,
            addr_ranges=board.mem_ranges,
        )
        self.iocache.mem_side = self.membus.cpu_side_ports
        self.iocache.cpu_side = board.get_mem_side_coherent_io_port()



class MyClassicPrivateL1SharedL2CacheHierarchyBuild(MyClassicPrivateL1SharedL2CacheHierarchy):
    def __init__(self, l1d_size: str, l1d_assoc: int, l2_size: str, l2_assoc: str, 
                 l1d_prefetcher=None):
        super().__init__(
            l1i_size="16KiB",
            l1i_assoc=8,
            l1d_size=l1d_size,
            l1d_assoc=l1d_assoc,
            l2_size=l2_size,
            l2_assoc=l2_assoc,
            l1d_prefetcher = l1d_prefetcher,
        )

