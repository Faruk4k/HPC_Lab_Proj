import argparse

from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

from prefetchers.stride.hardwares import (
    HWBoard,
    MyOutOfOrderCPU,
    MyClassicPrivateL1SharedL2CacheHierarchyBuild,
    DDR4,
    DDR4_2x,
    MySimpleMemory,
)

from prefetchers.stride.stride_configs import make_stride_prefetcher

def get_memory(memory_name):
    if memory_name == "ddr4_1x":
        return DDR4()

    elif memory_name == "ddr4_2x":
        return DDR4_2x()

    elif memory_name == "simple":
        return MySimpleMemory()

    else:
        raise ValueError(f"Unknown memory type: {memory_name}")

def get_prefetchers(prefetcher_name, pf_level, stride_config):
    l1d_pf = None
    l2_pf = None

    if prefetcher_name == "none":
        return None, None

    if pf_level not in ["l1d", "l2"]:
        raise ValueError("When using a prefetcher, --pf-level must be l1d or l2")

    if prefetcher_name == "stride":
        pf_cls = make_stride_prefetcher(stride_config)
    else:
        raise ValueError(f"Unsupported prefetcher for now: {prefetcher_name}")

    if pf_level == "l1d":
        l1d_pf = pf_cls
        l2_pf = None
    elif pf_level == "l2":
        l1d_pf = None
        l2_pf = pf_cls

    return l1d_pf, l2_pf


parser = argparse.ArgumentParser()

parser.add_argument(
    "--benchmark",
    required=True,
    help="Path to benchmark binary, e.g. benchmarks/simple_triad/stream-triad.bin",
)

parser.add_argument(
    "--benchmark-args",
    default="",
    help='Arguments passed to benchmark, e.g. "1000000 1"',
)

parser.add_argument(
    "--prefetcher",
    choices=["none", "stride"],
    default="none",
)

parser.add_argument(
    "--pf-level",
    choices=["none", "l1d", "l2"],
    default="none",
)

parser.add_argument(
    "--stride-config",
    default="deg4_dist8",
    help="Stride config name from stride_configs.py",
)

parser.add_argument(
    "--memory",
    choices=["ddr4_1x", "ddr4_2x", "simple"],
    default="ddr4_1x",
)

parser.add_argument("--clk-freq", default="3GHz")

parser.add_argument("--cpu-width", type=int, default=4)
parser.add_argument("--rob-size", type=int, default=128)
parser.add_argument("--int-regs", type=int, default=160)
parser.add_argument("--fpvec-regs", type=int, default=160)
parser.add_argument("--lsq-size", type=int, default=64)

parser.add_argument("--l1d-size", default="16KiB")
parser.add_argument("--l1d-assoc", type=int, default=8)
parser.add_argument("--l2-size", default="256KiB")
parser.add_argument("--l2-assoc", type=int, default=16)

args = parser.parse_args()


l1d_pf, l2_pf = get_prefetchers(
    prefetcher_name=args.prefetcher,
    pf_level=args.pf_level,
    stride_config=args.stride_config,
)

processor = MyOutOfOrderCPU(
    width=args.cpu_width,
    rob_size=args.rob_size,
    num_int_regs=args.int_regs,
    num_fpvec_regs=args.fpvec_regs,
    lsq_size=args.lsq_size,
)

memory = get_memory(args.memory)

cache_hierarchy = MyClassicPrivateL1SharedL2CacheHierarchyBuild(
    l1d_size=args.l1d_size,
    l1d_assoc=args.l1d_assoc,
    l2_size=args.l2_size,
    l2_assoc=args.l2_assoc,
    l1d_prefetcher=l1d_pf,
    l2_prefetcher=l2_pf,
)

board = HWBoard(
    clk_freq=args.clk_freq,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

benchmark_arguments = args.benchmark_args.split() if args.benchmark_args else []

board.set_se_binary_workload(
    BinaryResource(local_path=args.benchmark),
    arguments=benchmark_arguments,
)

print("========== RUN CONFIG ==========")
print(f"Benchmark      : {args.benchmark}")
print(f"Benchmark args : {benchmark_arguments}")
print(f"CPU            : Out-of-order Armv8")
print(f"Clock          : {args.clk_freq}")
print(f"CPU width      : {args.cpu_width}")
print(f"ROB size       : {args.rob_size}")
print(f"LSQ size       : {args.lsq_size}")
print(f"L1D            : {args.l1d_size}, assoc {args.l1d_assoc}")
print(f"L2             : {args.l2_size}, assoc {args.l2_assoc}")
print(f"Memory         : {args.memory}")
print(f"Prefetcher     : {args.prefetcher}")
print(f"PF level       : {args.pf_level}")
print(f"Stride config  : {args.stride_config}")
print("================================")

simulator = Simulator(board=board)
simulator.run()
