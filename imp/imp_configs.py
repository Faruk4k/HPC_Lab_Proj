from m5.objects import IndirectMemoryPrefetcher

imp_configurations = {
    "default": {},

    # max_prefetch_distance, default = 16
    "dist4":  {"max_prefetch_distance": 4},
    "dist8":  {"max_prefetch_distance": 8},
    "dist32": {"max_prefetch_distance": 32},
    "dist64": {"max_prefetch_distance": 64},

    # prefetch_threshold, default = 2
    "thr1": {"prefetch_threshold": 1},
    "thr3": {"prefetch_threshold": 3},
    "thr4": {"prefetch_threshold": 4},

    # streaming_distance, default = 4
    "sdist2":  {"streaming_distance": 2},
    "sdist8":  {"streaming_distance": 8},
    "sdist16": {"streaming_distance": 16},

    # stream_counter_threshold, default = 4
    "sthr2": {"stream_counter_threshold": 2},
    "sthr8": {"stream_counter_threshold": 8},

    # Prefetch table capacity, default = 16 entries, assoc = 16
    "pt8":  {"pt_table_entries": "8",  "pt_table_assoc": 8},
    "pt32": {"pt_table_entries": "32", "pt_table_assoc": 16},
    "pt64": {"pt_table_entries": "64", "pt_table_assoc": 16},

    # Indirect pattern detector capacity, default = 4 entries, assoc = 4
    "ipd2":  {"ipd_table_entries": "2",  "ipd_table_assoc": 2},
    "ipd8":  {"ipd_table_entries": "8",  "ipd_table_assoc": 4},
    "ipd16": {"ipd_table_entries": "16", "ipd_table_assoc": 4},

    # Number of misses tracked, default = 4
    "addrlen2":  {"addr_array_len": 2},
    "addrlen8":  {"addr_array_len": 8},
    "addrlen16": {"addr_array_len": 16},
}

def make_imp_prefetcher(config_name):
    params = dict(imp_configurations[config_name])

    # IMP calls PrefetchInfo::get(), so restrict notifications as much as possible.
    params.setdefault("on_read", True)
    params.setdefault("on_write", False)
    params.setdefault("on_data", True)
    params.setdefault("on_inst", False)

    # Only trigger IMP on demand misses, not every access or prefetch hits.
    params.setdefault("on_miss", True)
    params.setdefault("prefetch_on_access", False)
    params.setdefault("prefetch_on_pf_hit", False)

    class ConfiguredIMPPrefetcher(IndirectMemoryPrefetcher):
        def __init__(self):
            super().__init__(**params)

    return ConfiguredIMPPrefetcher