from m5.objects import AMPMPrefetcher, AccessMapPatternMatching

ampm_configurations = {
    # Baseline
    "default": {},

    # limit_stride
    "ls2": {"limit_stride": 2},
    "ls4": {"limit_stride": 4},
    "ls8": {"limit_stride": 8},
    "ls16": {"limit_stride": 16},

    # start_degree
    "sd1": {"start_degree": 1},
    "sd2": {"start_degree": 2},
    "sd8": {"start_degree": 8},
    "sd16": {"start_degree": 16},

    # hot_zone_size
    # l2
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
    "hz256": {
        "hot_zone_size": "256B",
        "access_map_table_entries": "64",
    },
    "hz512": {
        "hot_zone_size": "512B",
        "access_map_table_entries": "32",
    },
    "hz1k": {
        "hot_zone_size": "1KiB",
        "access_map_table_entries": "16",
    },
    "hz2k": {
        "hot_zone_size": "2KiB",
        "access_map_table_entries": "8",
    },
    "hz4k": {
        "hot_zone_size": "4KiB",
        "access_map_table_entries": "4",
    },
    "hz8k": {
        "hot_zone_size": "8KiB",
        "access_map_table_entries": "2",
    },

    # access_map_table_entries
    #l2
    # "amt32": {
    #     "access_map_table_entries": "32",
    #     "hot_zone_size": "8KiB",
    # },
    # "amt64": {
    #     "access_map_table_entries": "64",
    #     "hot_zone_size": "4KiB",
    # },
    # "amt128": {
    #     "access_map_table_entries": "128",
    #     "hot_zone_size": "2KiB",
    # },
    # "amt256": {
    #     "access_map_table_entries": "256",
    #     "hot_zone_size": "1KiB",
    # },
    # "amt512": {
    #     "access_map_table_entries": "512",
    #     "hot_zone_size": "512B",
    # },
    # "amt1024": {
    #     "access_map_table_entries": "1024",
    #     "hot_zone_size": "256B",
    # },
    #l1d
    # access_map_table_entries
    "amt2": {
        "access_map_table_entries": "2",
        "hot_zone_size": "8KiB",
    },
    "amt4": {
        "access_map_table_entries": "4",
        "hot_zone_size": "4KiB",
    },
    "amt8": {
        "access_map_table_entries": "8",
        "hot_zone_size": "2KiB",
    },
    "amt16": {
        "access_map_table_entries": "16",
        "hot_zone_size": "1KiB",
    },
    "amt32": {
        "access_map_table_entries": "32",
        "hot_zone_size": "512B",
    },
    "amt64": {
        "access_map_table_entries": "64",
        "hot_zone_size": "256B",
    },

    # access_map_table_assoc
    "assoc1": {"access_map_table_assoc": 1},
    "assoc2": {"access_map_table_assoc": 2},
    "assoc4": {"access_map_table_assoc": 4},
    "assoc16": {"access_map_table_assoc": 16},

    # epoch_cycles
    "epoch64k": {"epoch_cycles": 64000},
    "epoch128k": {"epoch_cycles": 128000},
    "epoch512k": {"epoch_cycles": 512000},
    "epoch1024k": {"epoch_cycles": 1024000},
}


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