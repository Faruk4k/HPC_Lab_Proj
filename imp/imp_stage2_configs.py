from m5.objects import IndirectMemoryPrefetcher

imp_stage2_configurations = {
    # ------------------------------------------------------------------
    # Baselines / anchors from Stage 1
    # ------------------------------------------------------------------
    "default": {},

    "s2": {
        "streaming_distance": 2,
    },

    "s8": {
        "streaming_distance": 8,
    },

    "s16": {
        "streaming_distance": 16,
    },

    # ------------------------------------------------------------------
    # Stream-aggressive / stream-conservative combinations
    # Good for simple_triad, merge, parts of matmult
    # ------------------------------------------------------------------
    "s8_sth2": {
        "streaming_distance": 8,
        "stream_counter_threshold": 2,
    },

    "s8_sth8": {
        "streaming_distance": 8,
        "stream_counter_threshold": 8,
    },

    "s16_sth2": {
        "streaming_distance": 16,
        "stream_counter_threshold": 2,
    },

    "s16_sth8": {
        "streaming_distance": 16,
        "stream_counter_threshold": 8,
    },

    "s2_sth2": {
        "streaming_distance": 2,
        "stream_counter_threshold": 2,
    },

    "s2_sth8": {
        "streaming_distance": 2,
        "stream_counter_threshold": 8,
    },

    # ------------------------------------------------------------------
    # Prefetch-table/noise-control combinations
    # Useful for BFS/quick/irregular cases where pollution may matter
    # ------------------------------------------------------------------
    "s8_pt8_sth8": {
        "streaming_distance": 8,
        "stream_counter_threshold": 8,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
    },

    "s16_pt8_sth8": {
        "streaming_distance": 16,
        "stream_counter_threshold": 8,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
    },

    "s8_pt8_sth2": {
        "streaming_distance": 8,
        "stream_counter_threshold": 2,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
    },

    "s16_pt8_sth2": {
        "streaming_distance": 16,
        "stream_counter_threshold": 2,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
    },

    # ------------------------------------------------------------------
    # Indirect-pattern capacity combinations
    # Targeted at SpMV and BFS
    # ------------------------------------------------------------------
    "s8_ipd8_addr8": {
        "streaming_distance": 8,
        "ipd_table_entries": "8",
        "ipd_table_assoc": 4,
        "addr_array_len": 8,
    },

    "s16_ipd8_addr8": {
        "streaming_distance": 16,
        "ipd_table_entries": "8",
        "ipd_table_assoc": 4,
        "addr_array_len": 8,
    },

    "s8_ipd16_addr16": {
        "streaming_distance": 8,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
        "addr_array_len": 16,
    },

    "s16_ipd16_addr16": {
        "streaming_distance": 16,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
        "addr_array_len": 16,
    },

    # ------------------------------------------------------------------
    # Lookahead-distance combinations
    # Tests whether max_prefetch_distance only matters after streaming is high
    # ------------------------------------------------------------------
    "s8_dist32_addr8": {
        "streaming_distance": 8,
        "max_prefetch_distance": 32,
        "addr_array_len": 8,
    },

    "s16_dist32_addr16": {
        "streaming_distance": 16,
        "max_prefetch_distance": 32,
        "addr_array_len": 16,
    },

    "s8_dist8_addr8": {
        "streaming_distance": 8,
        "max_prefetch_distance": 8,
        "addr_array_len": 8,
    },

    "s16_dist8_addr16": {
        "streaming_distance": 16,
        "max_prefetch_distance": 8,
        "addr_array_len": 16,
    },

    # ------------------------------------------------------------------
    # Capacity-heavy combinations
    # Tests whether larger tables help when irregularity is high
    # ------------------------------------------------------------------
    "s8_ipd16_pt32": {
        "streaming_distance": 8,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
        "pt_table_entries": "32",
        "pt_table_assoc": 16,
    },

    "s16_ipd16_pt32": {
        "streaming_distance": 16,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
        "pt_table_entries": "32",
        "pt_table_assoc": 16,
    },

    # ------------------------------------------------------------------
    # Aggressive combined candidates
    # Targeted mainly at SpMV; may be too noisy for BFS/quick
    # ------------------------------------------------------------------
    "aggr_s16_sth2_d32_ipd16": {
        "streaming_distance": 16,
        "stream_counter_threshold": 2,
        "max_prefetch_distance": 32,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
    },

    "aggr_s16_sth2_d32_ipd16_addr16": {
        "streaming_distance": 16,
        "stream_counter_threshold": 2,
        "max_prefetch_distance": 32,
        "ipd_table_entries": "16",
        "ipd_table_assoc": 4,
        "addr_array_len": 16,
    },

    # ------------------------------------------------------------------
    # Conservative combined candidates
    # Targeted mainly at BFS/quick where pollution is a concern
    # ------------------------------------------------------------------
    "cons_s8_sth8_pt8_ipd8": {
        "streaming_distance": 8,
        "stream_counter_threshold": 8,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
        "ipd_table_entries": "8",
        "ipd_table_assoc": 4,
    },

    "cons_s2_sth8_pt8": {
        "streaming_distance": 2,
        "stream_counter_threshold": 8,
        "pt_table_entries": "8",
        "pt_table_assoc": 8,
    },
}


def make_imp_stage2_prefetcher(config_name):
    params = dict(imp_stage2_configurations[config_name])

    # Keep the safety restrictions that eliminated the IMP panics.
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