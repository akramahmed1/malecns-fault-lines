"""Minimum-cut failure-point identification between node sets.

Primary object: the minimum s-t cut separating a source set (sensory) from a
target set (motor). Cut edges are reported as failure points; the cut value
is the capacity an attacker must remove to disconnect the sets.
"""


def st_mincut_between_sets(g, sources, targets, weight_attr="synapses"):
    """Minimum s-t cut separating all sources from all targets.

    Adds a super source SS (edges SS->s for each source) and a super sink TT
    (edges t->TT for each target). Real edges keep their weight_attr capacity;
    super edges get capacity total_weight + 1 so they never appear in the cut.
    Returns the cut value, the cut edge set as (src_name, dst_name) pairs,
    and both partitions with super vertices removed.
    """
    names = list(g.vs["name"])
    lut = {n: i for i, n in enumerate(names)}
    s_idx = [lut[x] if isinstance(x, str) else int(x) for x in sources]
    t_idx = [lut[x] if isinstance(x, str) else int(x) for x in targets]

    h = g.copy()
    ss = h.vcount()
    tt = h.vcount() + 1
    h.add_vertices(2)
    h.vs[ss]["name"] = "__SUPER_SOURCE__"
    h.vs[tt]["name"] = "__SUPER_SINK__"
    total = float(sum(h.es[weight_attr])) if h.ecount() else 0.0
    inf = total + 1.0
    new_edges = [(ss, s) for s in s_idx] + [(t, tt) for t in t_idx]
    e0 = h.ecount()
    h.add_edges(new_edges)
    h.es[e0:h.ecount()][weight_attr] = [inf] * len(new_edges)

    cut = h.mincut(source=ss, target=tt, capacity=weight_attr)
    part_src = set(cut.partition[0]) - {ss, tt}
    part_tgt = set(cut.partition[1]) - {ss, tt}
    cut_edges = []
    for eid in cut.cut:
        e = h.es[eid]
        u, v = e.source, e.target
        if u in (ss, tt) or v in (ss, tt):
            continue
        cut_edges.append((h.vs[u]["name"], h.vs[v]["name"]))
    return {
        "value": float(cut.value),
        "n_cut_edges": len(cut_edges),
        "cut_edges": cut_edges,
        "source_side": sorted(h.vs[i]["name"] for i in part_src),
        "target_side": sorted(h.vs[i]["name"] for i in part_tgt),
    }


def global_mincut_undirected(g, weight_attr="synapses"):
    """Supplementary undirected global min cut (Stoer-Wagner in C).

    SCALE NOTE: the directed global min cut is far more expensive, so this
    undirected version is a diagnostic only, not a failure-point claim. At
    full MaleCNS scale run it on thresholded graphs (>=5 synapses: 6.24M
    edges per Cell STAR Methods), where igraph's C implementation is the
    only feasible option. networkx cannot hold a 25.6M-edge graph.
    """
    u = g.as_undirected(combine_edges="sum")
    cut = u.mincut(capacity=weight_attr)
    return {
        "value": float(cut.value),
        "partition_sizes": sorted([len(p) for p in cut.partition]),
    }
