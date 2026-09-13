"""Exact sensory-to-motor reachability via SCC condensation + bitsets.

The MaleCNS graphs have a giant strongly-connected component (161k of 173k
nodes at threshold 5), so the condensation DAG has only ~11k nodes. Reachability
between the sensory and motor sets is computed exactly on the DAG with numpy
bitsets: one uint64 word per 64 motor targets, propagated in reverse
topological order. Output schema is identical to
reachability.sensory_motor_reachability (reachable pair counts, per-source
counts, hop-limited fractions, shortest-path summaries), verified by direct
comparison.
"""
import numpy as np


def resolve_ids(g, ids):
    ids = list(ids)
    if len(ids) and isinstance(ids[0], str):
        lut = {n: i for i, n in enumerate(g.vs["name"])}
        return [lut[x] for x in ids]
    return [int(i) for i in ids]


def _condensation(g):
    """Return (comp array, dag igraph object, topo order list)."""
    comp = np.array(g.components(mode="strong").membership, dtype=np.int64)
    el = np.array(g.get_edgelist(), dtype=np.int64)
    cu = comp[el[:, 0]]
    cv = comp[el[:, 1]]
    keep = cu != cv
    if np.any(keep):
        pairs = np.unique(
            np.stack([cu[keep], cv[keep]], axis=1), axis=0)
    else:
        pairs = np.zeros((0, 2), dtype=np.int64)
    import igraph as ig
    d = int(comp.max()) + 1
    dag = ig.Graph(n=d, edges=[(int(u), int(v)) for u, v in pairs],
                   directed=True)
    topo = dag.topological_sorting(mode="out")
    succ = dag.get_adjlist(mode="out")
    return comp, dag, topo, succ


def condensation_reachability(g, sources, targets, hop_limits=(2, 3, 4),
                              seed=0):
    """Exact sensory-to-motor reachability, fast path via condensation DAG."""
    s_idx = resolve_ids(g, sources)
    t_idx = resolve_ids(g, targets)
    names = g.vs["name"]
    total = len(s_idx) * len(t_idx)
    n_t = len(t_idx)
    w = (n_t + 63) // 64

    comp, dag, topo, succ = _condensation(g)
    d = len(topo)
    bits = np.zeros((d, w), dtype=np.uint64)
    t_comp = comp[np.array(t_idx, dtype=np.int64)]
    for j, c in enumerate(t_comp):
        bits[int(c), j // 64] |= np.uint64(1) << np.uint64(j % 64)

    # reverse-topological propagation: full reachability
    for v in reversed(topo):
        bv = bits[v]
        for s_ in succ[v]:
            bv |= bits[s_]

    s_comp = comp[np.array(s_idx, dtype=np.int64)]
    per_source = {}
    reachable_pairs = 0
    for s, c in zip(s_idx, s_comp):
        k = int(np.unpackbits(
            bits[int(c)].view(np.uint8)).sum())
        per_source[names[s]] = k
        reachable_pairs += k

    # Hop-limited fractions: exact, via per-target reverse neighborhoods.
    # (A DAG bitset propagation would overcount: intra-SCC hops are invisible
    # on the condensation.) Baseline-only cost; the lesion loop passes ().
    hop_frac = {}
    s_set = set(s_idx)
    for h in hop_limits:
        h = int(h)
        c = 0
        for t in t_idx:
            c += len(set(g.neighborhood(t, order=h, mode="in")) & s_set)
        hop_frac[h] = c / total if total else 0.0

    # shortest-path summaries on a seeded random sample of sources
    # (exact per pair; full all-pairs distances are infeasible at this scale)
    rng = np.random.default_rng(seed)
    s_sample = [s_idx[i] for i in rng.choice(
        len(s_idx), size=min(200, len(s_idx)), replace=False)]
    dists = g.distances(source=s_sample, target=t_idx, mode="out")
    lens = [v for row in dists for v in row if v != float("inf")]

    return {
        "n_sources": len(s_idx),
        "n_targets": len(t_idx),
        "total_pairs": total,
        "reachable_pairs": int(reachable_pairs),
        "fraction_reachable": reachable_pairs / total if total else 0.0,
        "per_source_reachable": per_source,
        "hop_limited_fraction": hop_frac,
        "mean_shortest_path": float(np.mean(lens)) if lens else None,
        "median_shortest_path": float(np.median(lens)) if lens else None,
        "shortest_path_sources_sampled": len(s_sample),
        "method": "condensation_bitset_exact",
    }


def lesioned_metrics_fast(g, sources, targets, baseline_pairs):
    """Drop-in replacement for lesions._lesioned_metrics (identical schema).

    sources/targets are vertex names; filters to vertices present in g.
    """
    names = set(g.vs["name"])
    s = [x for x in sources if x in names]
    t = [x for x in targets if x in names]
    lut = {n: i for i, n in enumerate(g.vs["name"])}
    s_idx = [lut[x] for x in s]
    t_idx = [lut[x] for x in t]
    pairs, gwc = fast_lesion_reachable_pairs(g, s_idx, t_idx)
    total = len(s_idx) * len(t_idx)
    return {
        "gwc_fraction": gwc,
        "reachable_pairs": int(pairs),
        "reach_fraction": pairs / total if total else 0.0,
        "newly_disconnected": int(baseline_pairs - pairs),
    }


def lesion_metrics_for_removal(g, sources, targets, remove_idx, baseline_pairs,
                               element="nodes"):
    """Metrics for one fixed removal set (degree-matched controls).

    Identical schema to lesions.lesion_metrics_for_set.
    """
    h = g.copy()
    idx = [int(i) for i in remove_idx]
    if element == "nodes":
        h.delete_vertices(idx)
    else:
        h.delete_edges(idx)
    m = lesioned_metrics_fast(h, sources, targets, baseline_pairs)
    del h
    return m


def fast_lesion_reachable_pairs(g, s_idx, t_idx):
    """Minimal exact reachable-pair count for the lesion loop.

    s_idx, t_idx are integer index lists. Returns (reachable_pairs, gwc_fraction).
    Skips per-source dicts, hop fractions, and shortest paths.
    """
    comp, dag, topo, succ = _condensation(g)
    n_t = len(t_idx)
    w = (n_t + 63) // 64
    d = len(topo)
    bits = np.zeros((d, w), dtype=np.uint64)
    s_idx_a = np.array(s_idx, dtype=np.int64)
    t_idx_a = np.array(t_idx, dtype=np.int64)
    t_comp = comp[t_idx_a]
    for j, c in enumerate(t_comp):
        bits[int(c), j // 64] |= np.uint64(1) << np.uint64(j % 64)
    for v in reversed(topo):
        bv = bits[v]
        for s_ in succ[v]:
            bv |= bits[s_]
    s_comp = comp[s_idx_a]
    total = 0
    for c in s_comp:
        total += int(np.unpackbits(bits[int(c)].view(np.uint8)).sum())
    weak = g.components(mode="weak")
    gwc = max((len(c) for c in weak), default=0) / g.vcount()
    return total, gwc
