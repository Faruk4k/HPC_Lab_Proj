import os

benchmarks = ["simple_triad", "matmult", "spmv", "merge", "quick", "bfs"]

imp_configs = [
    "default",
    "dist4", "dist8", "dist32", "dist64",
    "thr1", "thr3", "thr4",
    "sdist2", "sdist8", "sdist16",
    "sthr2", "sthr8",
    "pt8", "pt32", "pt64",
    "ipd2", "ipd8", "ipd16",
    "addrlen2", "addrlen8", "addrlen16",
]

levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]

root = "results_imp_multisim"

expected = set()
for bench in benchmarks:
    for cfg in imp_configs:
        for level in levels:
            for mem in memories:
                expected.add(f"{bench}_imp_{cfg}_{level}_{mem}")

actual = set()
for name in os.listdir(root):
    path = os.path.join(root, name)
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "stats.txt")):
        actual.add(name)

missing = sorted(expected - actual)
extra = sorted(actual - expected)

print("Expected:", len(expected))
print("Actual valid top-level stats:", len(actual))
print("Missing:", len(missing))
print("Extra:", len(extra))

with open("missing_imp_runs.txt", "w") as f:
    for x in missing:
        f.write(x + "\n")

if missing:
    print("\nMissing examples:")
    for x in missing[:20]:
        print("MISSING", x)

if extra:
    print("\nExtra examples:")
    for x in extra[:20]:
        print("EXTRA", repr(x))
