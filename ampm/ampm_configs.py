from m5.objects import AMPMPrefetcher, AccessMapPatternMatching

ampm_configurations_stage1 = {
    # Baseline
    # "default": {},

    # # limit_stride
    # "ls2": {"limit_stride": 2},
    # "ls4": {"limit_stride": 4},
    # "ls8": {"limit_stride": 8},
    # "ls16": {"limit_stride": 16},
    "ls32": {"limit_stride": 32},

    # # start_degree
    # "sd1": {"start_degree": 1},
    # "sd2": {"start_degree": 2},
    # "sd8": {"start_degree": 8},
    # "sd16": {"start_degree": 16},
    "sd32": {"start_degree": 32},
    "sd64": {"start_degree": 64},

    # hot_zone_size
    # l2
    # "hz64": {
    #     "hot_zone_size": "64B",
    #     "access_map_table_entries": "4096",
    # },
    # "hz128": {
    #     "hot_zone_size": "128B",
    #     "access_map_table_entries": "2048",
    # },
    # "hz256": {
    #     "hot_zone_size": "256B",
    #     "access_map_table_entries": "1024",
    # },
    # "hz512": {
    #     "hot_zone_size": "512B",
    #     "access_map_table_entries": "512",
    # },
    # "hz1k": {
    #     "hot_zone_size": "1KiB",
    #     "access_map_table_entries": "256",
    # },
    # "hz2k": {
    #     "hot_zone_size": "2KiB",
    #     "access_map_table_entries": "128",
    # },
    # "hz4k": {
    #     "hot_zone_size": "4KiB",
    #     "access_map_table_entries": "64",
    # },
    # "hz8k": {
    #     "hot_zone_size": "8KiB",
    #     "access_map_table_entries": "32",
    # },
    # l1d
    # "hz64": {
    #     "hot_zone_size": "64B",
    #     "access_map_table_entries": "256",
    # },
    # "hz128": {
    #     "hot_zone_size": "128B",
    #     "access_map_table_entries": "128",
    # },
    # "hz256": {
    #     "hot_zone_size": "256B",
    #     "access_map_table_entries": "64",
    # },
    # "hz512": {
    #     "hot_zone_size": "512B",
    #     "access_map_table_entries": "32",
    # },
    # "hz1k": {
    #     "hot_zone_size": "1KiB",
    #     "access_map_table_entries": "16",
    # },
    # "hz2k": {
    #     "hot_zone_size": "2KiB",
    #     "access_map_table_entries": "8",
    # },
    # "hz4k": {
    #     "hot_zone_size": "4KiB",
    #     "access_map_table_entries": "4",
    # },
    # "hz8k": {
    #     "hot_zone_size": "8KiB",
    #     "access_map_table_entries": "2",
    # },

    # # access_map_table_assoc
    # "assoc1": {"access_map_table_assoc": 1},
    # "assoc2": {"access_map_table_assoc": 2},
    # "assoc4": {"access_map_table_assoc": 4},
    # "assoc16": {"access_map_table_assoc": 16},
    # "assoc32": {"access_map_table_assoc": 32},
    # "assoc64": {"access_map_table_assoc": 64},

    # # epoch_cycles
    # "epoch64k": {"epoch_cycles": 64000},
    # "epoch128k": {"epoch_cycles": 128000},
    # "epoch512k": {"epoch_cycles": 512000},
    # "epoch1024k": {"epoch_cycles": 1024000},
}

'''
Why these values?
1. limit_stride = {8, 16}

Your Stage 1 experiments showed that larger stride limits consistently outperformed the smaller values.

ls2 almost never won.
ls4 occasionally performed well.
ls8 and especially ls16 were repeatedly the best across BFS, SpMV, Quicksort, and Merge Sort.

Therefore, only the two strongest candidates are carried forward.

2. start_degree = {8, 16}

Similarly, higher starting degrees consistently produced the best performance.

Small degrees (1 and 2) rarely appeared among the best-performing configurations.
Degrees 8 and 16 dominated the results for both L1D and L2.

These two values are therefore retained to investigate whether their effectiveness depends on the other AMPM parameters.

3. access_map_table_assoc = {4, 16}

Associativity showed a measurable influence, particularly for BFS and SpMV.

Low associativity (1 or 2) frequently caused more evictions.
Associativities of 4 and 16 repeatedly produced the highest speedups.

Testing both allows evaluation of whether higher associativity is only beneficial when paired with larger access maps or more aggressive prefetching.

4. epoch_cycles = {128k, 1024k}

Epoch length had the smallest influence overall.

Nevertheless,

128k was the most frequent winner across benchmarks.
1024k occasionally produced the best performance for Merge Sort and Quicksort.

Including both values allows the study to determine whether epoch length interacts with the more influential parameters while keeping the search space manageable.

5. access_map_table_entries / hot_zone_size

These parameters cannot be varied independently because

hot_zone_size × access_map_table_entries = cache capacity.

Only the two best-performing cache organizations from Stage 1 are retained.

For L1D these correspond to

64 entries × 256 B
32 entries × 512 B

For L2 they correspond to

512 entries × 512 B
256 entries × 1 KiB

These combinations consistently outperformed the larger hot-zone organizations while respecting the cache-size constraint.
'''

ampm_configurations_stage2_l2 = {
    "default": {},

    "cfg01": {"limit_stride":8,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":128000},
    "cfg02": {"limit_stride":8,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":1024000},
    "cfg03": {"limit_stride":8,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":128000},
    "cfg04": {"limit_stride":8,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":1024000},

    "cfg05": {"limit_stride":8,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":128000},
    "cfg06": {"limit_stride":8,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":1024000},
    "cfg07": {"limit_stride":8,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":128000},
    "cfg08": {"limit_stride":8,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":1024000},

    # "cfg09": {"limit_stride":16,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":128000},
    # "cfg10": {"limit_stride":16,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":1024000},
    # "cfg11": {"limit_stride":16,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":128000},
    # "cfg12": {"limit_stride":16,"start_degree":8,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":1024000},

    # "cfg13": {"limit_stride":16,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":128000},
    # "cfg14": {"limit_stride":16,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":4,"epoch_cycles":1024000},
    # "cfg15": {"limit_stride":16,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":128000},
    # "cfg16": {"limit_stride":16,"start_degree":16,"hot_zone_size":"512B","access_map_table_entries":"512","access_map_table_assoc":16,"epoch_cycles":1024000},

    "cfg17": {"limit_stride":8,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":128000},
    "cfg18": {"limit_stride":8,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":1024000},
    "cfg19": {"limit_stride":8,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":128000},
    "cfg20": {"limit_stride":8,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":1024000},

    "cfg21": {"limit_stride":8,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":128000},
    "cfg22": {"limit_stride":8,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":1024000},
    "cfg23": {"limit_stride":8,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":128000},
    "cfg24": {"limit_stride":8,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":1024000},

    # "cfg25": {"limit_stride":16,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":128000},
    # "cfg26": {"limit_stride":16,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":1024000},
    # "cfg27": {"limit_stride":16,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":128000},
    # "cfg28": {"limit_stride":16,"start_degree":8,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":1024000},

    # "cfg29": {"limit_stride":16,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":128000},
    # "cfg30": {"limit_stride":16,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":4,"epoch_cycles":1024000},
    # "cfg31": {"limit_stride":16,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":128000},
    # "cfg32": {"limit_stride":16,"start_degree":16,"hot_zone_size":"1KiB","access_map_table_entries":"256","access_map_table_assoc":16,"epoch_cycles":1024000},
}

ampm_configurations_stage2_l1d = {
    "default": {},

    # cfg01-08: hot_zone_size = 1KiB, access_map_table_entries = 16
    "cfg01": {"limit_stride": 8,  "start_degree": 8,  "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    "cfg02": {"limit_stride": 8,  "start_degree": 8,  "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    "cfg03": {"limit_stride": 8,  "start_degree": 16, "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    "cfg04": {"limit_stride": 8,  "start_degree": 16, "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    "cfg05": {"limit_stride": 16, "start_degree": 8,  "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    "cfg06": {"limit_stride": 16, "start_degree": 8,  "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    "cfg07": {"limit_stride": 16, "start_degree": 16, "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    "cfg08": {"limit_stride": 16, "start_degree": 16, "hot_zone_size": "1KiB", "access_map_table_entries": "16", "access_map_table_assoc": 4, "epoch_cycles": 1024000},

    # cfg09-16: hot_zone_size = 2KiB, access_map_table_entries = 8
    # "cfg09": {"limit_stride": 8,  "start_degree": 8,  "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    # "cfg10": {"limit_stride": 8,  "start_degree": 8,  "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    # "cfg11": {"limit_stride": 8,  "start_degree": 16, "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    # "cfg12": {"limit_stride": 8,  "start_degree": 16, "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    # "cfg13": {"limit_stride": 16, "start_degree": 8,  "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    # "cfg14": {"limit_stride": 16, "start_degree": 8,  "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
    # "cfg15": {"limit_stride": 16, "start_degree": 16, "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 128000},
    # "cfg16": {"limit_stride": 16, "start_degree": 16, "hot_zone_size": "2KiB", "access_map_table_entries": "8", "access_map_table_assoc": 4, "epoch_cycles": 1024000},
}

ampm_configurations = ampm_configurations_stage2_l1d

def make_ampm_prefetcher(config_name):
    if config_name not in ampm_configurations:
        raise ValueError(
            f"Unknown ampm config '{config_name}'. "
            f"Available configs: {list(ampm_configurations.keys())}"
        )

    params = ampm_configurations[config_name]

    class ConfiguredAMPMPrefetcher(AMPMPrefetcher):
        def __init__(self):
            super().__init__(
                ampm=AccessMapPatternMatching(**params)
            )

    return ConfiguredAMPMPrefetcher