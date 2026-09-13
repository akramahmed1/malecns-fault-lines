"""Build directed weighted graphs from edge lists.

Edge list format: CSV with columns src, dst, synapses.
Weights are synapse counts, matching MaleCNS semantics (Cell Results:
124.2M synaptic connections define 25.6M edges between 166,483 neurons).

Two builders:
  build_graph: in-memory, for test-scale graphs.
  build_graph_chunked: two-pass chunked build for full-scale edge lists.
    Pass 1 collects the vertex name set; pass 2 streams edges in chunks.
    Never materializes a dense matrix. This is the builder the real
    MaleCNS run will use.
"""
import igraph as ig
import numpy as np
import pandas as pd

SRC_COL = "src"
DST_COL = "dst"
W_COL = "synapses"


def load_edgelist_csv(path, usecols=None):
    df = pd.read_csv(path, usecols=usecols)
    return (
        df[SRC_COL].astype(str).to_numpy(),
        df[DST_COL].astype(str).to_numpy(),
        df[W_COL].to_numpy(dtype=np.int64),
    )


def build_graph(srcs, dsts, weights, threshold=0):
    """Build a directed igraph graph, keeping edges with weight >= threshold."""
    mask = weights >= threshold
    srcs, dsts, weights = srcs[mask], dsts[mask], weights[mask]
    names = list(dict.fromkeys(list(srcs) + list(dsts)))  # order-preserving unique
    index = {n: i for i, n in enumerate(names)}
    edges = [(index[s], index[d]) for s, d in zip(srcs, dsts)]
    g = ig.Graph(n=len(names), edges=edges, directed=True)
    g.vs["name"] = names
    g.es["synapses"] = [int(w) for w in weights]
    return g


def build_graph_chunked(path, threshold=0, chunksize=500_000):
    """Two-pass chunked build for full-scale edge lists.

    Pass 1: stream the CSV and collect the vertex name set.
    Pass 2: stream again, adding edges chunk by chunk.
    Memory stays proportional to vertices plus one chunk, never to edges.
    """
    names = []
    seen = set()
    for chunk in pd.read_csv(path, usecols=[SRC_COL, DST_COL],
                             chunksize=chunksize, dtype=str):
        for col in (SRC_COL, DST_COL):
            for v in chunk[col].unique():
                if v not in seen:
                    seen.add(v)
                    names.append(v)
    index = {n: i for i, n in enumerate(names)}
    g = ig.Graph(n=len(names), directed=True)
    g.vs["name"] = names
    for chunk in pd.read_csv(path, chunksize=chunksize,
                             dtype={SRC_COL: str, DST_COL: str}):
        sub = chunk[chunk[W_COL] >= threshold]
        if len(sub) == 0:
            continue
        edges = [(index[s], index[d]) for s, d in zip(sub[SRC_COL], sub[DST_COL])]
        e0 = g.ecount()
        g.add_edges(edges)
        g.es[e0:g.ecount()][W_COL] = [int(w) for w in sub[W_COL].to_numpy()]
    return g


def attach_node_metadata(g, nodes_df):
    """Attach per-node attributes (e.g. region) from a DataFrame with a node column."""
    lut = {}
    for _, row in nodes_df.iterrows():
        lut[str(row["node"])] = row
    for attr in nodes_df.columns:
        if attr == "node":
            continue
        vals = []
        for name in g.vs["name"]:
            row = lut.get(name)
            vals.append(None if row is None else row[attr])
        g.vs[attr] = vals
    return g


def threshold_variants(srcs, dsts, weights, thresholds):
    """Build one graph per synapse threshold (config thresholds: 0, 5, 11)."""
    return {int(t): build_graph(srcs, dsts, weights, threshold=int(t))
            for t in thresholds}


def graph_stats(g):
    weak = g.components(mode="weak")
    strong = g.components(mode="strong")
    n = g.vcount()
    return {
        "n_nodes": n,
        "n_edges": g.ecount(),
        "density": (g.ecount() / (n * (n - 1))) if n > 1 else 0.0,
        "weak_components": len(weak),
        "largest_weak": max((len(c) for c in weak), default=0),
        "strong_components": len(strong),
        "largest_strong": max((len(c) for c in strong), default=0),
    }
