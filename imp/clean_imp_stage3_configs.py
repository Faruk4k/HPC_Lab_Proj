import ast
import json
from pathlib import Path

CONFIG_IN = "imp_stage3_configs.py"
PLAN_IN = "imp_stage3_plan.json"

CONFIG_OUT = "imp_stage3_configs_clean.py"
PLAN_OUT = "imp_stage3_plan_clean.json"


def load_configs(path):
    text = Path(path).read_text()
    tree = ast.parse(text)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, "id", None) == "imp_stage3_configurations":
                    return ast.literal_eval(node.value)

    raise RuntimeError("Could not find imp_stage3_configurations")


def canonical_name(params):
    parts = []

    s = params.get("streaming_distance")
    if s is not None:
        parts.append(f"s{s}")

    sth = params.get("stream_counter_threshold")
    if sth is not None:
        parts.append(f"sth{sth}")

    dist = params.get("max_prefetch_distance")
    if dist is not None:
        parts.append(f"dist{dist}")

    ipd = params.get("ipd_table_entries")
    if ipd is not None:
        parts.append(f"ipd{ipd}")

    addr = params.get("addr_array_len")
    if addr is not None:
        parts.append(f"addr{addr}")

    pt = params.get("pt_table_entries")
    if pt is not None:
        parts.append(f"pt{pt}")

    if not parts:
        return "default"

    return "_".join(parts)


configs = load_configs(CONFIG_IN)
plan = json.loads(Path(PLAN_IN).read_text())

# Map identical parameter dictionaries to one canonical name.
param_to_name = {}
clean_configs = {}
old_to_new = {}

for old_name, params in configs.items():
    key = tuple(sorted(params.items()))
    name = canonical_name(params)

    # If two different param sets somehow produce same name, add suffix.
    final_name = name
    suffix = 2
    while final_name in clean_configs and clean_configs[final_name] != params:
        final_name = f"{name}_v{suffix}"
        suffix += 1

    if key in param_to_name:
        final_name = param_to_name[key]
    else:
        param_to_name[key] = final_name
        clean_configs[final_name] = params

    old_to_new[old_name] = final_name


clean_plan = {}
for case, names in plan.items():
    new_names = []
    for old in names:
        new_names.append(old_to_new[old])

    # Remove duplicate parameter-equivalent configs within each case.
    clean_plan[case] = sorted(set(new_names))


with open(CONFIG_OUT, "w") as f:
    f.write("from m5.objects import IndirectMemoryPrefetcher\n\n")
    f.write("# Auto-cleaned Stage 3 configs with canonical names.\n\n")
    f.write("imp_stage3_configurations = {\n")
    for name, params in sorted(clean_configs.items()):
        f.write(f'    "{name}": {repr(params)},\n')
    f.write("}\n\n")
    f.write(
'''def make_imp_stage3_prefetcher(config_name):
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
'''
    )


Path(PLAN_OUT).write_text(json.dumps(clean_plan, indent=2, sort_keys=True))

print("Original unique config names:", len(configs))
print("Clean unique parameter configs:", len(clean_configs))
print("Original planned runs:", sum(len(v) for v in plan.values()))
print("Clean planned runs:", sum(len(v) for v in clean_plan.values()))
print()
print(f"Wrote {CONFIG_OUT}")
print(f"Wrote {PLAN_OUT}")