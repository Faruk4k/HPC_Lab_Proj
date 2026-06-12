from m5.objects import StridePrefetcher


stride_configurations = {
    "deg1_dist1": {"degree": 1, "distance": 1},
    "deg1_dist4": {"degree": 1, "distance": 4},
    "deg1_dist8": {"degree": 1, "distance": 8},
    "deg1_dist16": {"degree": 1, "distance": 16},
    "deg1_dist32": {"degree": 1, "distance": 32},

    "deg4_dist1": {"degree": 4, "distance": 1},
    "deg4_dist4": {"degree": 4, "distance": 4},
    "deg4_dist8": {"degree": 4, "distance": 8},
    "deg4_dist16": {"degree": 4, "distance": 16},
    "deg4_dist32": {"degree": 4, "distance": 32},

    "deg8_dist1": {"degree": 8, "distance": 1},
    "deg8_dist4": {"degree": 8, "distance": 4},
    "deg8_dist8": {"degree": 8, "distance": 8},
    "deg8_dist16": {"degree": 8, "distance": 16},
    "deg8_dist32": {"degree": 8, "distance": 32},

    "deg16_dist1": {"degree": 16, "distance": 1},
    "deg16_dist4": {"degree": 16, "distance": 4},
    "deg16_dist8": {"degree": 16, "distance": 8},
    "deg16_dist16": {"degree": 16, "distance": 16},
    "deg16_dist32": {"degree": 16, "distance": 32},

    "deg32_dist1": {"degree": 32, "distance": 1},
    "deg32_dist4": {"degree": 32, "distance": 4},
    "deg32_dist8": {"degree": 32, "distance": 8},
    "deg32_dist16": {"degree": 32, "distance": 16},
    "deg32_dist32": {"degree": 32, "distance": 32},
}


def make_stride_prefetcher(config_name):
    if config_name not in stride_configurations:
        raise ValueError(
            f"Unknown stride config '{config_name}'. "
            f"Available configs: {list(stride_configurations.keys())}"
        )

    params = stride_configurations[config_name]

    class ConfiguredStridePrefetcher(StridePrefetcher):
        def __init__(self):
            super().__init__(**params)

    return ConfiguredStridePrefetcher