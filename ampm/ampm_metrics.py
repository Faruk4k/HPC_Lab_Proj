import math
import re

STAT_PATTERN = r"^{name}\s+([+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)"
SIMSECONDS_RE = re.compile(STAT_PATTERN.format(name="simSeconds"), re.MULTILINE)


def get_stat(text, regex):
    """Extract a single numeric stat from the stats file text."""
    match = regex.search(text)
    if not match:
        return math.nan
    return float(match.group(1))


def prefetcher_regex(cache_name, stat_name):
    """Build a regex for a prefetcher stat in the given cache unit."""
    name = f"board.cache_hierarchy.{cache_name}.prefetcher.{stat_name}"
    return re.compile(STAT_PATTERN.format(name=name), re.MULTILINE)


def extract_prefetcher_metrics(text, cache_name="l2cache" or "l1dcaches"):
    """Extract prefetcher-related metrics from stats text.

    The returned keys are always the same, regardless of cache unit.
    For L1D stats, pass cache_name="l1dchaches".
    """
    pf_issued = get_stat(text, prefetcher_regex(cache_name, "pfIssued"))
    pf_late = get_stat(text, prefetcher_regex(cache_name, "pfLate"))

    return {
        "simSeconds": get_stat(text, SIMSECONDS_RE),
        "pfIssued": pf_issued,
        "pfUseful": get_stat(text, prefetcher_regex(cache_name, "pfUseful")),
        "pfUnused": get_stat(text, prefetcher_regex(cache_name, "pfUnused")),
        "accuracy": get_stat(text, prefetcher_regex(cache_name, "accuracy")),
        "coverage": get_stat(text, prefetcher_regex(cache_name, "coverage")),
        "pfLate": pf_late,
        "pfTimely": pf_issued - pf_late if not math.isnan(pf_issued) and not math.isnan(pf_late) else math.nan,
    }


def compute_speedup(sim_seconds, baseline_sim_seconds):
    """Compute speedup relative to a baseline run."""
    if sim_seconds and baseline_sim_seconds and not math.isnan(baseline_sim_seconds):
        return baseline_sim_seconds / sim_seconds
    return math.nan
