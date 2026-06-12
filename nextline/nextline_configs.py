from m5.objects import TaggedPrefetcher

nextline_configurations = {
    "deg1" : {"degree": 1},
    "deg4" : {"degree": 4},
    "deg8" : {"degree": 8},
    "deg16" : {"degree": 16},
    "deg32" : {"degree": 32}
}


def make_nextline_prefetcher(config_name):
    if config_name not in nextline_configurations:
        raise ValueError(
            f"Unknown nextline config '{config_name}'. "
            f"Available configs: {list(nextline_configurations.keys())}"
        )

    params = nextline_configurations[config_name]

    class ConfiguredNextlinePrefetcher(TaggedPrefetcher):
        def __init__(self):
            super().__init__(**params)

    return ConfiguredNextlinePrefetcher
