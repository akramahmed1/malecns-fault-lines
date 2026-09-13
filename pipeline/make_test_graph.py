"""Synthetic test graph with a planted sensory-to-motor bottleneck.

SYNTHETIC DATA. Not MaleCNS data. Every downstream module is validated
against the ground truth written here (ground_truth.json), which is
deterministic for the fixed seed.

Structure:
  sensory (6) -> A (30, region brain) -> hubs h0, h1 (region bottleneck)
            -> B (30, region vnc) -> motor (6, region motor)
All sensory-to-motor paths cross the A->hub and hub->B edge sets, so the
minimum s-t cut concentrates at the bottleneck by construction. The builder
asserts this: every cut edge must touch h0 or h1 (vacuously true when a
threshold disconnects the graph and the cut is empty).
"""
import os

import numpy as np
import pandas as pd

from utils import make_rng, write_json

N_SENSORY = 6
N_A = 30
N_B = 30
N_MOTOR = 6
HUBS = ["h0", "h1"]


def build_test_graph(seed=42):
    rng = make_rng(seed)
    sensory = [f"s{i}" for i in range(N_SENSORY)]
    layer_a = [f"a{i}" for i in range(N_A)]
    layer_b = [f"b{i}" for i in range(N_B)]
    motor = [f"m{i}" for i in range(N_MOTOR)]

    edges = []

    def add(u, v, w):
        if u != v:
            edges.append((u, v, int(w)))

    # sensory -> A, strong
    for s in sensory:
        for a in rng.choice(layer_a, size=10, replace=False):
            add(s, a, rng.integers(20, 51))
    # A -> A sparse recurrent
    for _ in range(60):
        u, v = rng.choice(layer_a, size=2, replace=False)
        add(u, v, rng.integers(5, 16))
    # A -> hubs, weak: planted bottleneck, incoming side
    for a in layer_a:
        for h in HUBS:
            if rng.random() < 0.35:
                add(a, h, rng.integers(2, 7))
    # hubs -> B, weak: planted bottleneck, outgoing side
    for h in HUBS:
        for b in layer_b:
            if rng.random() < 0.5:
                add(h, b, rng.integers(2, 7))
    # B -> B sparse recurrent
    for _ in range(60):
        u, v = rng.choice(layer_b, size=2, replace=False)
        add(u, v, rng.integers(5, 16))
    # B -> motor, strong
    for m in motor:
        for b in rng.choice(layer_b, size=10, replace=False):
            add(b, m, rng.integers(20, 51))

    edges_df = pd.DataFrame(edges, columns=["src", "dst", "synapses"])
    region = {}
    region.update({s: "sensory" for s in sensory})
    region.update({a: "brain" for a in layer_a})
    region.update({h: "bottleneck" for h in HUBS})
    region.update({b: "vnc" for b in layer_b})
    region.update({m: "motor" for m in motor})
    nodes = sensory + layer_a + HUBS + layer_b + motor
    nodes_df = pd.DataFrame({
        "node": nodes,
        "region": [region[n] for n in nodes],
        "is_sensory": [n in sensory for n in nodes],
        "is_motor": [n in motor for n in nodes],
    })
    return edges_df, nodes_df


def compute_ground_truth(edges_df, nodes_df, thresholds, seed):
    """Min-cut ground truth per threshold, verified against the planted bottleneck."""
    from graph_build import build_graph
    from mincut import st_mincut_between_sets

    srcs = edges_df["src"].astype(str).to_numpy()
    dsts = edges_df["dst"].astype(str).to_numpy()
    weights = edges_df["synapses"].to_numpy(dtype=np.int64)
    sensory = nodes_df.loc[nodes_df["is_sensory"], "node"].tolist()
    motor = nodes_df.loc[nodes_df["is_motor"], "node"].tolist()

    gt = {"synthetic": True, "seed": int(seed), "thresholds": {}}
    for t in thresholds:
        g = build_graph(srcs, dsts, weights, threshold=int(t))
        res = st_mincut_between_sets(g, sensory, motor)
        hub_names = set(HUBS)
        cut_ok = all((u in hub_names or v in hub_names)
                     for u, v in res["cut_edges"])
        gt["thresholds"][str(int(t))] = {
            "mincut_value": res["value"],
            "n_cut_edges": res["n_cut_edges"],
            "cut_edges": res["cut_edges"],
            "cut_through_bottleneck": bool(cut_ok),
            "n_source_side": len(res["source_side"]),
            "n_target_side": len(res["target_side"]),
        }
        assert cut_ok, (
            f"planted bottleneck violated at threshold {t}: "
            f"cut edges {res['cut_edges']}"
        )
    return gt


def main(outdir=".", thresholds=(0, 5, 11), seed=42):
    os.makedirs(outdir, exist_ok=True)
    edges_df, nodes_df = build_test_graph(seed=seed)
    edges_df.to_csv(os.path.join(outdir, "test_edges.csv"), index=False)
    nodes_df.to_csv(os.path.join(outdir, "test_nodes.csv"), index=False)
    gt = compute_ground_truth(edges_df, nodes_df, thresholds, seed)
    write_json(os.path.join(outdir, "ground_truth.json"), gt)
    print(f"wrote test graph: {len(nodes_df)} nodes, {len(edges_df)} edges")
    for t, info in gt["thresholds"].items():
        print(f"  threshold {t}: mincut={info['mincut_value']} "
              f"cut_edges={info['n_cut_edges']} bottleneck={info['cut_through_bottleneck']}")


if __name__ == "__main__":
    main()
