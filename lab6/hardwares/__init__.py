
###############################################################################
# Configurations of gem5 are adapted from gem5bootcamp (2024), gem5 tutorial 
# and Jason Lowe-Power's CA course at UC Davis
# - https://github.com/gem5bootcamp/2024
# - https://www.gem5.org/
# - https://jlpteaching.github.io/comparch/modules/introduction/index
###############################################################################

from gem5.components.boards.simple_board import SimpleBoard
from gem5.isas import ISA

from .cpu import *
from .memory import *
from .cache_hierarchy_ruby import *
from .cache_hierarchy_classic import *
from .network import *

HWBoard = SimpleBoard

__all__ = [
    "HWBoard",
    "MyMESITwoLevelCacheBuildStd",
    "MyMESITwoLevelCacheBuildCustom",
    "MyClassicTwoLevelCacheBuild",
    "MyClassicPrivateL1SharedL2CacheHierarchyBuild",
    "DDR3",
    "MyO3Processor",
    "MyOutOfOrderCPU"
]
