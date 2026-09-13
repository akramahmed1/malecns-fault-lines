"""Null graphs: degree-preserving and region-constrained directed rewiring.

Both models use double-edge swaps (u,v),(x,y) -> (u,y),(x,v), which preserve
in-degree and out-degree exactly. The region-constrained model additionally
requires region[u]==region[x] and region[v]==region[y], preserving
region-to-region edge counts as well as degrees. Edge weights (synapse
counts) stay with the edge slot, so the weight multiset is preserved while
weight-topology coupling is broken. Replicates use fixed seeds.
"""
import igraph as ig
import numpy as np


def _rewire(edge_arr, n_swaps, rng, region_of=None, constrained=False):
    edges = edge_arr.copy()
    m = len(edges)
    present = set(map(tuple, edges.tolist()))
    done = 0
    attempts = 0
    max_attempts = max(n_swaps * 20, 100)
    while done < n_swaps and attempts < max_attempts:
        attempts += 1
        i, j = rng.integers(0, m, size=2)
        if i == j:
            continue
        u, v = (int(x) for x in edges[i])
        x, y = (int(z) for z in edges[j])
        if len({u, v, x, y}) < 4:
            continue
        if constrained and region_of is not None:
            if not (region_of[u] == region_of[x] and region_of[v] == region_of[y]):
                continue
        if (u, y) in present or (x, v) in present:
            continue
        present.discard((u, v))
        present.discard((x, y))
        present.add((u, y))
        present.add((x, v))
        edges[i] = (u, y)
        edges[j] = (x, v)
        done += 1
    return edges, done


def _rewire_constrained_grouped(edge_arr, n_swaps, rng, region_of):
    """Region-constrained double-edge swaps via group-restricted proposals.

    Scale optimization: the rejection sampler in _rewire wastes most proposals
    on region-incompatible pairs (success rate ~25% on MaleCNS superclasses).
    Here edges are grouped by (region[src], region[dst]); each proposal picks
    a uniform edge i then a uniform edge j from i's group. Constrained swaps
    preserve group membership ((reg[u],reg[y]) == (reg[x],reg[y]) etc.), so
    groups are precomputed once. The proposal is symmetric in (i, j), so the
    chain targets the same uniform distribution over graphs with given
    in/out-degrees and region-to-region counts as the rejection sampler,
    minus the rejection overhead.
    """
    edges = edge_arr.copy()
    m = len(edges)
    regs = np.asarray(region_of)
    _, code = np.unique(regs, return_inverse=True)
    src_code = code[edges[:, 0]]
    dst_code = code[edges[:, 1]]
    n_reg = int(code.max()) + 1
    group = src_code * n_reg + dst_code
    order = np.argsort(group, kind="stable")
    sgroup = group[order]
    bounds = np.searchsorted(sgroup, np.arange(n_reg * n_reg + 1))
    present = set(map(tuple, edges.tolist()))
    done = 0
    attempts = 0
    max_attempts = max(n_swaps * 20, 100)
    while done < n_swaps and attempts < max_attempts:
        attempts += 1
        i = int(rng.integers(0, m))
        gi = int(group[i])
        lo = int(bounds[gi])
        hi = int(bounds[gi + 1])
        if hi - lo < 2:
            continue
        j = int(order[int(rng.integers(lo, hi))])
        if i == j:
            continue
        u, v = int(edges[i, 0]), int(edges[i, 1])
        x, y = int(edges[j, 0]), int(edges[j, 1])
        if len({u, v, x, y}) < 4:
            continue
        if (u, y) in present or (x, v) in present:
            continue
        present.discard((u, v))
        present.discard((x, y))
        present.add((u, y))
        present.add((x, v))
        edges[i] = (u, y)
        edges[j] = (x, v)
        done += 1
    return edges, done


def rewire_graph(g, seed, swap_factor=10, region_attr=None):
    """One rewired null graph. Returns (graph, info dict)."""
    rng = np.random.default_rng(seed)
    n = g.vcount()
    edge_arr = np.array([(e.source, e.target) for e in g.es], dtype=np.int64)
    weights = np.array(g.es["synapses"], dtype=np.int64)
    region_of = None
    constrained = False
    if region_attr is not None and region_attr in g.vs.attributes():
        region_of = np.array(g.vs[region_attr])
        constrained = True
    n_requested = swap_factor * len(edge_arr)
    if constrained:
        new_edges, done = _rewire_constrained_grouped(
            edge_arr, n_requested, rng, region_of)
    else:
        new_edges, done = _rewire(edge_arr, n_requested, rng,
                                  region_of=region_of, constrained=False)
    h = ig.Graph(n=n, edges=[(int(u), int(v)) for u, v in new_edges],
                 directed=True)
    for attr in g.vs.attributes():
        h.vs[attr] = g.vs[attr]
    h.es["synapses"] = [int(w) for w in weights]
    return h, {"swaps_requested": int(n_requested),
               "swaps_done": int(done),
               "region_constrained": constrained}


def make_null_graphs(g, model, n_replicates, base_seed, swap_factor=10,
                     region_attr="region"):
    """N rewired null graphs with fixed seeds (base_seed + replicate index)."""
    graphs = []
    infos = []
    for r in range(n_replicates):
        if model == "degree_preserving":
            h, meta = rewire_graph(g, base_seed + r, swap_factor)
        elif model == "region_constrained":
            h, meta = rewire_graph(g, base_seed + r, swap_factor,
                                   region_attr=region_attr)
        else:
            raise ValueError(f"unknown null model: {model}")
        graphs.append(h)
        infos.append(meta)
    return graphs, infos


def degree_sequences(g):
    """In/out degree sequences, for verifying the nulls preserve degrees."""
    return (np.array(g.indegree(), dtype=np.int64),
            np.array(g.outdegree(), dtype=np.int64))
