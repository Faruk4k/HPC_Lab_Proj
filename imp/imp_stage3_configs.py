from m5.objects import IndirectMemoryPrefetcher

# Auto-cleaned Stage 3 configs with canonical names.

imp_stage3_configurations = {
    "s32": {'streaming_distance': 32},
    "s32_dist32_addr16": {'streaming_distance': 32, 'max_prefetch_distance': 32, 'addr_array_len': 16},
    "s32_dist8_addr16": {'streaming_distance': 32, 'max_prefetch_distance': 8, 'addr_array_len': 16},
    "s32_ipd16_addr16": {'streaming_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'addr_array_len': 16},
    "s32_ipd16_pt32": {'streaming_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'pt_table_entries': '32', 'pt_table_assoc': 16},
    "s32_ipd8_addr8": {'streaming_distance': 32, 'ipd_table_entries': '8', 'ipd_table_assoc': 4, 'addr_array_len': 8},
    "s32_sth2": {'streaming_distance': 32, 'stream_counter_threshold': 2},
    "s32_sth2_dist32_ipd16": {'streaming_distance': 32, 'stream_counter_threshold': 2, 'max_prefetch_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4},
    "s32_sth2_dist32_ipd16_addr16": {'streaming_distance': 32, 'stream_counter_threshold': 2, 'max_prefetch_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'addr_array_len': 16},
    "s32_sth2_pt8": {'streaming_distance': 32, 'stream_counter_threshold': 2, 'pt_table_entries': '8', 'pt_table_assoc': 8},
    "s32_sth8": {'streaming_distance': 32, 'stream_counter_threshold': 8},
    "s32_sth8_ipd8_pt8": {'streaming_distance': 32, 'stream_counter_threshold': 8, 'pt_table_entries': '8', 'pt_table_assoc': 8, 'ipd_table_entries': '8', 'ipd_table_assoc': 4},
    "s32_sth8_pt8": {'streaming_distance': 32, 'stream_counter_threshold': 8, 'pt_table_entries': '8', 'pt_table_assoc': 8},
    "s64": {'streaming_distance': 64},
    "s64_dist32_addr16": {'streaming_distance': 64, 'max_prefetch_distance': 32, 'addr_array_len': 16},
    "s64_dist8_addr16": {'streaming_distance': 64, 'max_prefetch_distance': 8, 'addr_array_len': 16},
    "s64_ipd16_addr16": {'streaming_distance': 64, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'addr_array_len': 16},
    "s64_ipd16_pt32": {'streaming_distance': 64, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'pt_table_entries': '32', 'pt_table_assoc': 16},
    "s64_ipd8_addr8": {'streaming_distance': 64, 'ipd_table_entries': '8', 'ipd_table_assoc': 4, 'addr_array_len': 8},
    "s64_sth2": {'streaming_distance': 64, 'stream_counter_threshold': 2},
    "s64_sth2_dist32_ipd16": {'streaming_distance': 64, 'stream_counter_threshold': 2, 'max_prefetch_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4},
    "s64_sth2_dist32_ipd16_addr16": {'streaming_distance': 64, 'stream_counter_threshold': 2, 'max_prefetch_distance': 32, 'ipd_table_entries': '16', 'ipd_table_assoc': 4, 'addr_array_len': 16},
    "s64_sth2_pt8": {'streaming_distance': 64, 'stream_counter_threshold': 2, 'pt_table_entries': '8', 'pt_table_assoc': 8},
    "s64_sth8": {'streaming_distance': 64, 'stream_counter_threshold': 8},
    "s64_sth8_ipd8_pt8": {'streaming_distance': 64, 'stream_counter_threshold': 8, 'pt_table_entries': '8', 'pt_table_assoc': 8, 'ipd_table_entries': '8', 'ipd_table_assoc': 4},
    "s64_sth8_pt8": {'streaming_distance': 64, 'stream_counter_threshold': 8, 'pt_table_entries': '8', 'pt_table_assoc': 8},
}

def make_imp_stage3_prefetcher(config_name):
    params = dict(imp_stage3_configurations[config_name])

    params.setdefault("on_read", True)
    params.setdefault("on_write", False)
    params.setdefault("on_data", True)
    params.setdefault("on_inst", False)

    params.setdefault("on_miss", True)
    params.setdefault("prefetch_on_access", False)
    params.setdefault("prefetch_on_pf_hit", False)

    class ConfiguredIMPPrefetcher(IndirectMemoryPrefetcher):
        def __init__(self):
            super().__init__(**params)

    return ConfiguredIMPPrefetcher
