"""Lesion battery: random vs targeted node and edge removal.

Node strategies: random, out_degree, betweenness_approx, mincut_membership.
Edge strategies: random, weight (strongest first), betweenness_approx.
Tracked per lesion step: weakly-connected giant component fraction,
sensory-motor reachability, newly disconnected pairs.
Degree-matched random controls isolate the effect of targeting from the
effect of removing high-degree nodes.
"""
import numpy as np

from reachability import sensory_motor_reachability


def _name_set(g):
    return set(g.vs["name"])


def node_removal_order(g, strategy, weight_attr="synapses",
                       betweenness_cutoff=3, mincut_info=None):
    """Vertex indices, most-targeted first. None means sample per replicate."""
    n = g.vcount()
    if strategy == "random":
        return None
    if strategy == "out_degree":
        deg = g.outdegree()
        return sorted(range(n), key=lambda i: (-deg[i], i))
    if strategy == "betweenness_approx":
        btw = g.betweenness(directed=True, cutoff=betweenness_cutoff)
        return sorted(range(n), key=lambda i: (-btw[i], i))
    if strategy == "mincut_membership":
        if not mincut_info:
            raise ValueError("mincut_membership needs mincut_info")
        names = set()
        for u, v in mincut_info["cut_edges"]:
            names.add(u)
            names.add(v)
        lut = {name: i for i, name in enumerate(g.vs["name"])}
        # sorted for cross-process determinism: set iteration order over
        # strings varies with PYTHONHASHSEED
        members = sorted(lut[x] for x in names if x in lut)
        in_set = set(members)
        rest = [i for i in range(n) if i not in in_set]
        return members + rest
    raise ValueError(f"unknown node strategy: {strategy}")


def edge_removal_order(g, strategy, weight_attr="synapses", betweenness_cutoff=3):
    """Edge indices, most-targeted first. None means sample per replicate."""
    m = g.ecount()
    if strategy == "random":
        return None
    if strategy == "weight":
        w = g.es[weight_attr]
        return sorted(range(m), key=lambda e: (-w[e], e))
    if strategy == "betweenness_approx":
        eb = g.edge_betweenness(directed=True, cutoff=betweenness_cutoff)
        return sorted(range(m), key=lambda e: (-eb[e], e))
    raise ValueError(f"unknown edge strategy: {strategy}")


def _lesioned_metrics(g, sources, targets, baseline_pairs):
    names = _name_set(g)
    s = [x for x in sources if x in names]
    t = [x for x in targets if x in names]
    weak = g.components(mode="weak")
    gwc = max((len(c) for c in weak), default=0) / g.vcount() if g.vcount() else 0.0
    reach = sensory_motor_reachability(g, s, t, hop_limits=())
    cur = reach["reachable_pairs"]
    return {
        "gwc_fraction": gwc,
        "reachable_pairs": cur,
        "reach_fraction": reach["fraction_reachable"],
        "newly_disconnected": baseline_pairs - cur,
    }


def lesion_curve(g, sources, targets, element="nodes", strategy="random",
                 fractions=(0.01, 0.05, 0.10), n_replicates=20, seed=0,
                 weight_attr="synapses", betweenness_cutoff=3, mincut_info=None):
    """Run one lesion strategy across fractions.

    Random strategies draw n_replicates samples per fraction; targeted
    strategies are deterministic (one replicate). Returns per-fraction lists
    of metric dicts.
    """
    rng = np.random.default_rng(seed)
    base = sensory_motor_reachability(g, sources, targets, hop_limits=())
    baseline_pairs = base["reachable_pairs"]
    if element == "nodes":
        order = node_removal_order(g, strategy, weight_attr,
                                   betweenness_cutoff, mincut_info)
        pool = g.vcount()
    elif element == "edges":
        order = edge_removal_order(g, strategy, weight_attr, betweenness_cutoff)
        pool = g.ecount()
    else:
        raise ValueError(f"element must be nodes or edges, got {element}")

    curves = {}
    for frac in fractions:
        k = max(1, int(round(frac * pool)))
        n_reps = n_replicates if strategy == "random" else 1
        reps = []
        for _ in range(n_reps):
            if strategy == "random":
                doomed = rng.choice(pool, size=min(k, pool), replace=False)
            else:
                doomed = order[:min(k, pool)]
            h = g.copy()
            if element == "nodes":
                h.delete_vertices([int(i) for i in doomed])
            else:
                h.delete_edges([int(i) for i in doomed])
            reps.append(_lesioned_metrics(h, sources, targets, baseline_pairs))
        curves[float(frac)] = reps
    return {
        "element": element,
        "strategy": strategy,
        "baseline_reachable_pairs": baseline_pairs,
        "curves": curves,
    }


def lesion_metrics_for_set(g, sources, targets, remove_idx, baseline_pairs):
    """Metrics for one fixed removal set (used for degree-matched controls)."""
    h = g.copy()
    h.delete_vertices([int(i) for i in remove_idx])
    return _lesioned_metrics(h, sources, targets, baseline_pairs)


def degree_matched_controls(g, removed_nodes, n_replicates=20, seed=0, n_bins=10):
    """Random node sets matched to removed_nodes by out-degree bin.

    Quantile bins over out-degree; each control set has the same size and the
    same binned-degree composition as the removed set, drawn from nodes not
    in the removed set. Returns a list of index lists (may be shorter than
    n_replicates if a bin is exhausted).
    """
    rng = np.random.default_rng(seed)
    deg = np.array(g.outdegree(), dtype=float)
    removed = set(int(i) for i in removed_nodes)
    qs = np.quantile(deg, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9
    qs[-1] += 1e-9
    bins = np.digitize(deg, qs) - 1
    by_bin = {}
    for i in range(g.vcount()):
        by_bin.setdefault(int(bins[i]), []).append(i)
    need = {}
    for i in removed:
        need[int(bins[i])] = need.get(int(bins[i]), 0) + 1
    controls = []
    for _ in range(n_replicates):
        chosen = []
        feasible = True
        for b, c in need.items():
            pool = [i for i in by_bin[b] if i not in removed]
            if len(pool) < c:
                feasible = False
                break
            chosen.extend(rng.choice(pool, size=c, replace=False).tolist())
        if feasible:
            controls.append([int(i) for i in chosen])
    return controls
