"""Sensory-to-motor reachability and redundant-route statistics."""
import numpy as np


def resolve_ids(g, ids):
    """Accept vertex names or indices, return indices."""
    ids = list(ids)
    if len(ids) and isinstance(ids[0], str):
        lut = {n: i for i, n in enumerate(g.vs["name"])}
        return [lut[x] for x in ids]
    return [int(i) for i in ids]


def sensory_motor_reachability(g, sources, targets, hop_limits=(2, 3, 4)):
    """Directed reachability from a source set to a target set.

    Returns reachable-pair counts, per-source counts, hop-limited
    reachability fractions, and shortest-path length summaries.
    """
    s_idx = resolve_ids(g, sources)
    t_idx = resolve_ids(g, targets)
    t_set = set(t_idx)
    total = len(s_idx) * len(t_idx)

    reachable_pairs = 0
    per_source = {}
    for s in s_idx:
        reached = set(g.subcomponent(s, mode="out")) & t_set
        per_source[g.vs[s]["name"]] = len(reached)
        reachable_pairs += len(reached)

    hop_frac = {}
    for h in hop_limits:
        c = 0
        for s in s_idx:
            c += len(set(g.neighborhood(s, order=int(h), mode="out")) & t_set)
        hop_frac[int(h)] = c / total if total else 0.0

    dists = g.distances(source=s_idx, target=t_idx, mode="out")
    lens = [d for row in dists for d in row if d != float("inf")]
    return {
        "n_sources": len(s_idx),
        "n_targets": len(t_idx),
        "total_pairs": total,
        "reachable_pairs": reachable_pairs,
        "fraction_reachable": reachable_pairs / total if total else 0.0,
        "per_source_reachable": per_source,
        "hop_limited_fraction": hop_frac,
        "mean_shortest_path": float(np.mean(lens)) if lens else None,
        "median_shortest_path": float(np.median(lens)) if lens else None,
    }


def edge_disjoint_path_counts(g, sources, targets, max_pairs=200, seed=0):
    """Unweighted edge-disjoint path counts on a sampled set of reachable pairs.

    Uses max flow with unit capacity per pair. Pair sampling uses a fixed seed.

    SCALE NOTE: one max-flow computation per pair is expensive. At full
    MaleCNS scale this must run on a sampled pair set (as here) or be replaced
    by a push-relabel implementation on the thresholded graph. The cap
    max_disjoint_pairs in config.yaml controls the sample size.
    """
    rng = np.random.default_rng(seed)
    s_idx = resolve_ids(g, sources)
    t_idx = resolve_ids(g, targets)
    pairs = [(s, t) for s in s_idx for t in t_idx if s != t]
    if len(pairs) > max_pairs:
        sel = rng.choice(len(pairs), size=max_pairs, replace=False)
        pairs = [pairs[i] for i in sel]
    counts = []
    unit_cap = [1] * g.ecount()
    for s, t in pairs:
        if t in g.subcomponent(s, mode="out"):
            mf = g.maxflow(s, t, capacity=unit_cap)
            counts.append(int(round(mf.value)))
    return {
        "n_pairs_sampled": len(pairs),
        "n_pairs_reachable": len(counts),
        "mean_disjoint_paths": float(np.mean(counts)) if counts else 0.0,
        "min_disjoint_paths": int(min(counts)) if counts else 0,
        "max_disjoint_paths": int(max(counts)) if counts else 0,
    }
