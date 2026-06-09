
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
from m5.objects import ArmMinorCPU, MinorFUPool
from m5.objects import MinorDefaultIntFU, MinorDefaultIntMulFU
from m5.objects import MinorDefaultIntDivFU, MinorDefaultFloatSimdFU
from m5.objects import MinorDefaultMemFU, MinorDefaultFloatSimdFU
from m5.objects import MinorDefaultMiscFU, MinorDefaultPredFU

from m5.objects import *

class MySingleCycleCPU(SimpleProcessor):
    """
    SingleCycleCPU models a single core CPU with support for the Arm
    instruction set architecture (ISA).
    CPUTypes.TIMING refers to TimingSimpleCPU which is an internal CPU model in
    gem5. This is a "single cycle" CPU model. Each instruction takes 0 cycles
    to execute (after fetch) except for memory instructions which are a
    variable number of cycles.
    """
    def __init__(self):
        super().__init__(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.ARM)


class FloatSIMDFU(MinorDefaultFloatSimdFU):
    def __init__(self, operation_latency: int, issue_latency: int):
        """
        FloatSIMDFU extend MinorDefaultFloatSimdFU.MinorDefaultFloatSimdFU
        is an internal gem5 model. Please refer to
        gem5/src/cpu/minor/BaseMinorCPU.py
        for more information and documentation. FloatSIMDFU implements a
        floating point and SIMD functional units for gem5's MinorCPU.
        MinorCPU is an internal gem5 model that models an in-order pipelined
        processor. Please refer to
        https://www.gem5.org/documentation/general_docs/cpu_models/MinorCPU
        to learn more about MinorCPU.

        :param operation_latency: number of cycles it takes to execute
        a floating point/SIMD instruction
        :param issue_latency: number of cycles it takes to decode and issue
        a floating point/SIMD instruction
        """
        super().__init__()
        self.opLat = operation_latency
        self.issueLat = issue_latency
        print(f"fp_op: {operation_latency}, fp_issue: {issue_latency}")


class IntFU(MinorDefaultIntFU):
    def __init__(self, operation_latency: int, issue_latency: int):
        """
        IntFU extend MinorDefaultIntFU.MinorDefaultIntFU is an internal gem5
        model. Please refer to
        gem5/src/cpu/minor/BaseMinorCPU.py
        for more information and documentation. IntFU implements an integer
        functional unit for gem5's MinorCPU. MinorCPU is an internal gem5 model that
        models an in-order pipelined processor. Please refer to
        https://www.gem5.org/documentation/general_docs/cpu_models/MinorCPU
        to learn more about MinorCPU.

        :param operation_latency: number of cycles it takes to execute
        an integer instruction
        :param issue_latency: number of cycles it takes to decode and issue
        an integer instruction
        """
        super().__init__()
        self.opLat = operation_latency
        self.issueLat = issue_latency
        print(f"int_op: {operation_latency}, int_issue: {issue_latency}")


class MyMinorFUPool(MinorFUPool):
    def __init__(
        self,
        int_operation_latency: int,
        int_issue_latency: int,
        fp_operation_latency: int,
        fp_issue_latency: int,
    ):
        """
        MyMinorFUPool extend MinorFUPool. MinorFUPool is an internal gem5
        model. Please refer to
          gem5/src/cpu/minor/BaseMinorCPU.py
        for more information and documentation. MinorFUPool implements a
        pool of functional units for gem5's MinorCPU. This pool includes two
        integer and one floating point and SIMD functional units.  MinorCPU is
        an internal gem5 model that models an in-order pipelined processor.
        Please refer to
          https://www.gem5.org/documentation/general_docs/cpu_models/MinorCPU
        to learn more about MinorCPU.

        :param int_operation_latency: number of cycles it takes to execute
        an integer instruction
        :param int_issue_latency: number of cycles it takes to decode and issue
        an integer instruction
        :param fp_operation_latency: number of cycles it takes to execute
        a floating point/SIMD instruction
        :param fp_issue_latency: number of cycles it takes to decode and issue
        a floating point/SIMD instruction
        """
        super().__init__()
        self.funcUnits = [
            IntFU(int_operation_latency, int_issue_latency),
            IntFU(int_operation_latency, int_issue_latency),
            MinorDefaultIntMulFU(),
            MinorDefaultIntDivFU(),
            MinorDefaultPredFU(),
            MinorDefaultMemFU(),
            MinorDefaultMiscFU(),
            FloatSIMDFU(fp_operation_latency, fp_issue_latency),
            #ex5_LITTLE_FP(),
        ]

class MinorCPUCore(ArmMinorCPU):
    def __init__(
        self,
        int_operation_latency: int,
        int_issue_latency: int,
        fp_operation_latency: int,
        fp_issue_latency: int,
    ):
        """
        MinorCPUCore extends ArmMinorCPU. It allows the user to modify
        pipeline latencies in certain functional units.
        ArmMinorCPU is one of gem5's internal models for the MinorCPU.
        It implements MinorCPU for the Arm ISA.

        :param int_operation_latency: number of cycles it takes to execute
        an integer instruction
        :param int_issue_latency: number of cycles it takes to decode and issue
        an integer instruction
        :param fp_operation_latency: number of cycles it takes to execute
        a floating point/SIMD instruction
        :param fp_issue_latency: number of cycles it takes to decode and issue
        a floating point/SIMD instruction
        """
        super().__init__()
        self.executeFuncUnits = MyMinorFUPool(
            int_operation_latency,
            int_issue_latency,
            fp_operation_latency,
            fp_issue_latency,
        )
        self.fetch1FetchLimit = 1
        self.fetch1LineWidth = 64
        self.fetch1LineSnapWidth = 64
        self.fetch2InputBufferSize = 4

        self.decodeInputWidth = 2
        self.decodeInputBufferSize = 4

        self.executeInputWidth = 2
        self.executeIssueLimit = 2
        self.executeCommitLimit = 2
        self.executeInputBufferSize = 4

        self.executeMemoryCommitLimit = 1
        self.executeMemoryIssueLimit = 1
        self.executeMaxAccessesInMemory =2
        
        self.executeLSQMaxStoreBufferStoresPerCycle = 2
        self.executeLSQRequestsQueueSize = 1
        self.executeLSQTransfersQueueSize = 2
        self.executeLSQStoreBufferSize = 5
        self.executeSetTraceTimeOnIssue = True

        
class MinorCPUStdCore(BaseCPUCore):
    def __init__(
        self,
        int_operation_latency: int,
        int_issue_latency: int,
        fp_operation_latency: int,
        fp_issue_latency: int,
    ):
        """
        MinorCPUStdCore extend BaseCPUCore. It wraps MinorCPUCore into a gem5
        standard library core.

        :param int_operation_latency: number of cycles it takes to execute
        an integer instruction
        :param int_issue_latency: number of cycles it takes to decode and issue
        an integer instruction
        :param fp_operation_latency: number of cycles it takes to execute
        a floating point/SIMD instruction
        :param fp_issue_latency: number of cycles it takes to decode and issue
        a floating point/SIMD instruction
        """
        core = MinorCPUCore(
            int_operation_latency,
            int_issue_latency,
            fp_operation_latency,
            fp_issue_latency,
        )
        super().__init__(core, ISA.ARM)

class MyPipelinedCPU(BaseCPUProcessor):
    def __init__(
        self,
        issue_latency: int = 1,
        int_operation_latency: int = 3,
        fp_operation_latency: int = 6,
    ):
        """
        With the help of MinorCPUStdCore, PipelinedCPU wraps MinorCore into a
        BaseCPUProcessor. BaseCPUProcessor is one of gem5's internal models
        from the standard library. It allows the users to instantiate a
        MinorCPU for the Arm ISA with certain modifiable pipeline latencies.
        All the latencies are keyword (optional) arguments with default values.

        :param issue_latency: number of cycles it takes to decode and issue
        an instruction
        :param int_operation_latency: number of cycles it takes to execute
        an integer instruction
        :param fp_operation_latency: number of cycles it takes to execute
        a floating point/SIMD instruction
        """
        cores = [
            MinorCPUStdCore(
                int_operation_latency,
                issue_latency,
                fp_operation_latency,
                issue_latency,
            )
        ]
        super().__init__(cores)

