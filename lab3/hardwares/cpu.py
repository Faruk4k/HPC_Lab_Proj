
###############################################################################
# The configuration is adapted from gem5bootcamp (2024), gem5 tutorial 
# and Jason Lowe-Power's CA course at UC Davis
# - https://github.com/gem5bootcamp/2024
# - https://www.gem5.org/
# - https://jlpteaching.github.io/comparch/modules/introduction/index
###############################################################################
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA


from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from m5.objects import ArmO3CPU, TournamentBP, BiModeBP, LocalBP, FUPool
from m5.objects.FuncUnitConfig import *



class MyOutofOrderFUPool(FUPool):
    FUList = [
        # Integer FU
        IntALU(count=2),
        IntMultDiv(count=1),

        # FP and SIMD FU
        FP_ALU(count=1),
        FP_MultDiv(count=1),
        SIMD_Unit(count=1),
        Matrix_Unit(count=1),
        
        # Others
        PredALU(count=1),
        ReadPort(count=1),
        WritePort(count=1),
        #RdWrPort(count=1),
        IprPort(count=1),
    ]

class OutOfOrderCPUCore(ArmO3CPU):
    def __init__(self, width, rob_size, num_int_regs, num_fpvec_regs, lsq_size):
        """
        OutOfOrderCPUCore extends ArmO3CPU. ArmO3CPU is one of gem5's
        internal models the implements an out of order pipeline of Arm ISA.

        This class sets the width of the fetch, decode, rename, issue,
        writeback, and commit stages of the pipeline. It also sets the number
        of entries in the reorder buffer, the number of physical integer
        registers, and the number of physical floating point registers.

        There are many other parameters for the O3 CPU model, but we are only
        interested in the ones mentioned above.

        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param num_int_regs: determines the size of the integer register file.
        :param num_int_regs: determines the size of the vector/floating point
        register file.
        """
        super().__init__()
        self.fetchWidth = width
        self.decodeWidth = width
        self.renameWidth = width
        self.dispatchWidth = width        
        self.issueWidth = width
        self.wbWidth = width
        self.commitWidth = width
        self.squashWidth = width

        self.fetchQueueSize = 64

        self.numROBEntries = rob_size

        self.numPhysIntRegs = num_int_regs
        self.numPhysFloatRegs = num_fpvec_regs
        self.numPhysVecRegs = num_fpvec_regs

        self.fuPool = MyOutofOrderFUPool()
        self.branchPred = TournamentBP()

        self.LQEntries = lsq_size
        self.SQEntries = lsq_size


class OutOfOrderCPUStdCore(BaseCPUCore):
    def __init__(self, width, rob_size, num_int_regs, num_fpvec_regs, lsq_size):
        """
        OutOfOrderCPUStdCore wraps OutOfOrderCPUCore into a gem5 standard
        library core.

        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param num_int_regs: determines the size of the integer register file.
        :param num_int_regs: determines the size of the vector/floating point
        register file.
        """
        core = OutOfOrderCPUCore(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size)
        super().__init__(core, ISA.ARM)


class MyOutOfOrderCPU(BaseCPUProcessor):
    def __init__(self, width, rob_size, num_int_regs, num_fpvec_regs, lsq_size):
        """
        OutOfOrderCPU models a single core CPU. This model uses the O3 CPU model
        which is an out of order pipelined CPU.

        Some parameters of the O3 CPU model are set in this class. Please refer
        to the OutOfOrderCPUCore class for more information.

        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param num_int_regs: determines the size of the integer register file.
        :param num_int_regs: determines the size of the vector/floating point
        register file.
        """
        cores = [
            OutOfOrderCPUStdCore(width, rob_size, num_int_regs, num_fpvec_regs, lsq_size)
        ]
        super().__init__(cores)
        self._width = width
        self._rob_size = rob_size
        self._num_int_regs = num_int_regs
        self._num_fpvec_regs = num_fpvec_regs
        self._lsq_size = lsq_size
    def get_area_score(self):
        """
        get_area_score calculates the area score of a pipeline using its
        parameters width, rob_size, num_int_regs, and num_fp_regs.

        **IMPORTANT**: This is not a real area model.

        :return: the area score of a pipeline using its parameters width,
        rob_size, num_int_regs, and num_fp_regs.
        """
        score = (
            self._width * (2 * self._rob_size + self._num_int_regs + self._num_fpvec_regs)
            + 4 * self._width
            + 2 * self._rob_size
            + self._num_int_regs
            + self._num_fpvec_regs
        )   + self._lsq_size
        return score

