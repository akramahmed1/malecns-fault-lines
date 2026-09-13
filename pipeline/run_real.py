"""Real MaleCNS v1.0 battery (thresholds 5 and 11).

REAL DATA RUN. Uses data/edges_w5.csv and data/neurons.csv pulled live from
neuprint.janelia.org (male-cns:v1.0). Not synthetic.

Scale adaptations vs the synthetic pipeline (all recorded in the manifest):
  - Reachability uses reachability_fast (SCC condensation + bitset DP),
    verified exactly equivalent to reachability.sensory_motor_reachability.
  - Lesion metrics use the same fast path (5.2 s vs 303 s per evaluation).
  - betweenness_cutoff 3 -> 2 (cutoff 3 did not finish on 173k nodes).
  - edge_swap_factor 10 -> 1 for null rewiring.
  - Undirected global min cut skipped: Stoer-Wagner is infeasible at 173k
    nodes (diagnostic only, not a failure-point claim).
  - 40 self-loops dropped from the graph (recorded in manifest).
  - Threshold 0 (unfiltered 25.6M edges) out of scope for this run.

Usage: python3 run_real.py [--config config_real.yaml] [--outdir real_run_w5_w11]
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import pickle
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graph_build
import lesions as lesions_mod
import mincut as mincut_mod
import nulls as nulls_mod
import reachability as reach_mod
import reachability_fast as rf
import stats as stats_mod
from utils import (config_hash, load_config, package_versions, setup_logger,
                   sha256_file, to_jsonable, write_json)

MAPPING_DOC = (
    "Sensory/motor sets defined from the neurons.csv superclass column "
    "(MaleCNS v1.0 annotations, pulled live from neuprint.janelia.org).\n"
    "Sensory superclasses: cb_sensory, ol_sensory, vnc_sensory, "
    "sensory_ascending, sensory_descending, visual_projection, "
    "visual_centrifugal.\n"
    "Motor superclasses: descending_neuron, cb_motor, vnc_motor, "
    "vnc_efferent, cb_efferent, efferent_ascending, efferent_descending.\n"
    "Excluded by design: intrinsic superclasses (cb_intrinsic, ol_intrinsic, "
    "vnc_intrinsic: neither sensory input nor motor output), neurons with "
    "empty superclass (9,722: unannotated), ascending_neuron (1,846: VNC to "
    "brain relay, not primary sensory transduction; kept out of the primary "
    "sensory set), endocrine/ENS classes (modulatory, not sensorimotor "
    "pathways), and *_tbc superclasses (unconfirmed annotations). "
    "Only neurons present in the thresholded graph are analyzed; counts of "
    "in-graph vs annotated neurons are reported below."
)


def unit_seed(master_seed, *parts):
    """Deterministic per-checkpoint-unit seed.

    SHA-256 of "master|part1|part2|..." truncated to 32 bits. Stable across
    processes and platforms (unlike the builtin hash()). Every checkpoint
    unit draws from its own stream, so skipping completed units on resume
    cannot shift the draws of later units: a resumed run is bit-identical
    to an uninterrupted run.
    """
    h = hashlib.sha256()
    h.update(str(int(master_seed)).encode("utf-8"))
    for p in parts:
        h.update(b"|")
        h.update(str(p).encode("utf-8"))
    return int(h.hexdigest(), 16) % (2 ** 32)


class Checkpoints:
    """Atomic, fsync'd per-unit checkpoints enabling kill-and-resume.

    Each finished unit is written to outdir/checkpoints/ immediately on
    completion via write-to-temp + fsync + atomic rename, so a VM reboot
    can never leave a half-written checkpoint. On startup, finished units
    are loaded and skipped.
    """

    def __init__(self, outdir, log):
        self.dir = os.path.join(outdir, "checkpoints")
        os.makedirs(self.dir, exist_ok=True)
        self.log = log

    def count(self):
        return len([f for f in os.listdir(self.dir) if f.startswith("ckpt_")])

    def _path(self, name, ext):
        safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in name)
        return os.path.join(self.dir, "ckpt_" + safe + ext)

    def _atomic_write(self, path, data):
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def save_json(self, name, obj):
        self._atomic_write(self._path(name, ".json"),
                           json.dumps(to_jsonable(obj), indent=2).encode("utf-8"))

    def load_json(self, name):
        p = self._path(name, ".json")
        if not os.path.exists(p):
            return None
        with open(p, "r") as f:
            return json.load(f)

    def save_pickle(self, name, obj):
        self._atomic_write(self._path(name, ".pkl"),
                           pickle.dumps(obj, protocol=4))

    def load_pickle(self, name):
        p = self._path(name, ".pkl")
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return pickle.load(f)


def load_sets(neurons_csv, sensory_sc, motor_sc):
    """Return (sensory_names, motor_names, nodes_df, superclass_of)."""
    sensory, motor = [], []
    rows = []
    with open(neurons_csv) as f:
        for r in csv.DictReader(f):
            sc = r["superclass"]
            rows.append((r["bodyId"], sc,
                         sc in sensory_sc, sc in motor_sc))
            if sc in sensory_sc:
                sensory.append(r["bodyId"])
            elif sc in motor_sc:
                motor.append(r["bodyId"])
    import pandas as pd
    nodes_df = pd.DataFrame(rows, columns=["node", "superclass",
                                           "is_sensory", "is_motor"])
    return sensory, motor, nodes_df


def run_lesion_unit(g, sensory, motor, cfg, orders, element, strategy, rng,
                    baseline_pairs):
    """One checkpoint unit: lesion curves for a single (element, strategy).

    The RNG stream is per-unit (see unit_seed), so this unit's draws do not
    depend on any other unit: skipping completed units on resume is safe.
    Returns the result dict with the same schema as run_all.py.
    """
    fractions = [float(x) for x in cfg["lesion_fractions"]]
    n_reps = int(cfg["lesion_replicates"])
    order = orders[(element, strategy)]
    pool = g.vcount() if element == "nodes" else g.ecount()
    curves = {}
    for frac in fractions:
        k = max(1, int(round(frac * pool)))
        reps = n_reps if strategy == "random" else 1
        rep_metrics = []
        for _ in range(reps):
            if strategy == "random":
                doomed = rng.choice(pool, size=min(k, pool), replace=False)
            else:
                doomed = order[:min(k, pool)]
            h = g.copy()
            if element == "nodes":
                h.delete_vertices([int(i) for i in doomed])
            else:
                h.delete_edges([int(i) for i in doomed])
            rep_metrics.append(
                rf.lesioned_metrics_fast(h, sensory, motor, baseline_pairs))
            del h
        curves[float(frac)] = rep_metrics
    return {
        "element": element,
        "strategy": strategy,
        "baseline_reachable_pairs": baseline_pairs,
        "curves": curves,
    }


def main():
    ap = argparse.ArgumentParser(description="Fault Lines: real MaleCNS battery")
    ap.add_argument("--config", default="config_real.yaml")
    ap.add_argument("--outdir", default="real_run_w5_w11")
    ap.add_argument("--data-manifest", default=None,
                    help="pull manifest JSON with input checksums "
                         "(default: data/manifest.json)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = args.config if os.path.isabs(args.config) else os.path.join(here, args.config)
    outdir = args.outdir if os.path.isabs(args.outdir) else os.path.join(here, args.outdir)
    os.makedirs(outdir, exist_ok=True)
    log = setup_logger(outdir)

    cfg = load_config(cfg_path)
    chash = config_hash(cfg)
    log.info(f"REAL MaleCNS v1.0 run. config sha256: {chash}")
    t_start = time.time()
    seeds = cfg["seeds"]
    thresholds = [int(t) for t in cfg["thresholds"]]
    fractions = [float(f) for f in cfg["lesion_fractions"]]

    # ---- checkpoints: kill-and-resume across VM reboots ----
    ckpt = Checkpoints(outdir, log)
    state = ckpt.load_json("run_state")
    if state is None:
        state = {
            "timestamp_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "config_hash": chash,
        }
        ckpt.save_json("run_state", state)
        log.info("checkpointing enabled: fresh run_state written")
    else:
        log.info(f"resuming run started at {state['timestamp_utc']}; "
                 f"{ckpt.count()} checkpoints present")
    utc_now = state["timestamp_utc"]

    results = {"config_hash": chash, "thresholds": {},
               "data": "REAL MaleCNS v1.0 (neuprint.janelia.org), not synthetic"}

    # ---- input checksums (from the pull manifest, re-verified) ----
    manifest_arg = args.data_manifest
    manifest_path = (manifest_arg if manifest_arg and os.path.isabs(manifest_arg)
                     else os.path.join(here, manifest_arg or "data/manifest.json"))
    data_manifest = json.load(open(manifest_path))
    edges_csv = os.path.join(here, cfg["edges_csv"])
    neurons_csv = os.path.join(here, cfg["neurons_csv"])
    edges_sha = sha256_file(edges_csv)
    neurons_sha = sha256_file(neurons_csv)
    assert edges_sha == data_manifest["files"]["edges"], "edges_w5.csv checksum mismatch"
    assert neurons_sha == data_manifest["files"]["neurons.csv"], "neurons.csv checksum mismatch"
    log.info(f"input checksums verified: edges {edges_sha[:16]}..., "
             f"neurons {neurons_sha[:16]}...")

    # ---- sensory/motor sets ----
    sensory_all, motor_all, nodes_df = load_sets(
        neurons_csv, set(cfg["sensory_superclasses"]), set(cfg["motor_superclasses"]))
    with open(os.path.join(outdir, "sensory_motor_mapping.txt"), "w") as f:
        f.write("REAL MaleCNS v1.0 sensory/motor mapping\n")
        f.write("=" * 50 + "\n\n")
        f.write(MAPPING_DOC + "\n\n")
        f.write(f"sensory neurons annotated: {len(sensory_all)}\n")
        f.write(f"motor neurons annotated: {len(motor_all)}\n")
    log.info(f"sensory annotated: {len(sensory_all)}, motor annotated: {len(motor_all)}")

    p_labels, p_values = [], []
    self_loops_dropped = {}
    node_strategies = list(cfg["node_strategies"])
    edge_strategies = list(cfg["edge_strategies"])
    control_strategies = ["out_degree", "betweenness_approx", "mincut_membership"]
    null_models = list(cfg["null_models"])
    n_null_reps = int(cfg["null_replicates"])

    for t in thresholds:
        r = results["thresholds"][str(t)] = {}

        # ---- threshold phase (graph + baseline analyses): one checkpoint ----
        phase = ckpt.load_pickle(f"t{t}_phase")
        if phase is None:
            log.info(f"--- building threshold {t} graph ---")
            g = graph_build.build_graph_chunked(edges_csv, threshold=t)
            loops = [e.index for e in g.es if e.source == e.target]
            g.delete_edges(loops)
            n_loops = len(loops)
            log.info(f"threshold {t}: {g.vcount()} nodes, {g.ecount()} edges, "
                     f"dropped {n_loops} self-loops")
            graph_build.attach_node_metadata(g, nodes_df)

            vnames = set(g.vs["name"])
            sensory = [s for s in sensory_all if s in vnames]
            motor = [m for m in motor_all if m in vnames]
            log.info(f"threshold {t}: sensory in-graph {len(sensory)}/{len(sensory_all)}, "
                     f"motor in-graph {len(motor)}/{len(motor_all)}")

            graph_stats = graph_build.graph_stats(g)
            log.info(f"stats: {graph_stats}")

            # ---- baseline reachability (fast exact) ----
            reach = rf.condensation_reachability(
                g, sensory, motor, hop_limits=cfg["hop_limits"],
                seed=int(seeds["stats"]))
            log.info(f"reachability: {reach['reachable_pairs']}/{reach['total_pairs']} "
                     f"({reach['fraction_reachable']:.4f}); "
                     f"hop fractions: {reach['hop_limited_fraction']}; "
                     f"mean shortest path (200-pair sample): {reach['mean_shortest_path']}")

            # ---- sampled edge-disjoint paths ----
            disjoint = reach_mod.edge_disjoint_path_counts(
                g, sensory, motor, max_pairs=int(cfg["max_disjoint_pairs"]),
                seed=int(seeds["stats"]))
            log.info(f"disjoint paths: mean {disjoint['mean_disjoint_paths']:.2f} "
                     f"over {disjoint['n_pairs_reachable']} reachable pairs")

            # ---- min cut (failure points) ----
            mc = mincut_mod.st_mincut_between_sets(g, sensory, motor)
            mincut_res = {"value": mc["value"], "n_cut_edges": mc["n_cut_edges"],
                          "cut_edges": mc["cut_edges"]}
            log.info(f"mincut: value={mc['value']:.0f} cut_edges={mc['n_cut_edges']}")

            # ---- removal orders (computed once per threshold) ----
            bcut = int(cfg["betweenness_cutoff"])
            orders = {
                ("nodes", "random"): None,
                ("nodes", "out_degree"): lesions_mod.node_removal_order(g, "out_degree"),
                ("nodes", "betweenness_approx"): lesions_mod.node_removal_order(
                    g, "betweenness_approx", betweenness_cutoff=bcut),
                ("nodes", "mincut_membership"): lesions_mod.node_removal_order(
                    g, "mincut_membership", mincut_info=mc),
                ("edges", "random"): None,
                ("edges", "weight"): lesions_mod.edge_removal_order(g, "weight"),
            }
            log.info(f"threshold {t}: removal orders computed")

            base = rf.lesioned_metrics_fast(g, sensory, motor, 0)
            baseline_pairs = base["reachable_pairs"]
            log.info(f"t={t}: baseline reachable pairs = {baseline_pairs}")

            phase = {
                "g": g,
                "sensory": sensory,
                "motor": motor,
                "loops_dropped": n_loops,
                "sensory_in_graph": len(sensory),
                "motor_in_graph": len(motor),
                "graph_stats": graph_stats,
                "reachability": reach,
                "disjoint_paths": disjoint,
                "mincut": mincut_res,
                "orders": orders,
                "baseline_pairs": baseline_pairs,
            }
            ckpt.save_pickle(f"t{t}_phase", phase)
            log.info(f"threshold {t}: phase checkpoint written")
        else:
            log.info(f"threshold {t}: phase checkpoint loaded, skipping rebuild")
        g = phase["g"]
        sensory = phase["sensory"]
        motor = phase["motor"]
        orders = phase["orders"]
        baseline_pairs = phase["baseline_pairs"]
        self_loops_dropped[str(t)] = phase["loops_dropped"]

        # original insertion order, for byte-identical final JSON
        r["sensory_in_graph"] = phase["sensory_in_graph"]
        r["motor_in_graph"] = phase["motor_in_graph"]
        r["sensory_annotated"] = len(sensory_all)
        r["motor_annotated"] = len(motor_all)
        r["graph_stats"] = phase["graph_stats"]
        r["reachability"] = phase["reachability"]
        r["disjoint_paths"] = phase["disjoint_paths"]
        r["mincut"] = phase["mincut"]

        # ---- lesion battery: one checkpoint per (element, strategy) ----
        r["lesions"] = {"nodes": {}, "edges": {}}
        for element, strategies in (("nodes", node_strategies),
                                    ("edges", edge_strategies)):
            for strategy in strategies:
                uname = f"t{t}_lesion_{element}_{strategy}"
                unit = ckpt.load_json(uname)
                if unit is None:
                    useed = unit_seed(seeds["lesions"], "lesion", t,
                                      element, strategy)
                    rng = np.random.default_rng(useed)
                    unit = run_lesion_unit(g, sensory, motor, cfg, orders,
                                           element, strategy, rng,
                                           baseline_pairs)
                    ckpt.save_json(uname, unit)
                    log.info(f"t={t}: lesion {element}/{strategy} done, "
                             f"checkpointed")
                else:
                    # JSON round-trip stringifies float dict keys
                    unit["curves"] = {float(k): v
                                      for k, v in unit["curves"].items()}
                    log.info(f"t={t}: lesion {element}/{strategy} loaded "
                             f"from checkpoint")
                r["lesions"][element][strategy] = unit

        # ---- degree-matched controls: one checkpoint per (strategy, frac) ----
        r["controls"] = {}
        for strategy in control_strategies:
            order = orders[("nodes", strategy)]
            strat_res = {}
            for frac in fractions:
                uname = f"t{t}_control_{strategy}_{frac}"
                unit = ckpt.load_json(uname)
                if unit is None:
                    k = max(1, int(round(frac * g.vcount())))
                    removed = order[:k]
                    cseed = unit_seed(seeds["lesions"], "control", t,
                                      strategy, frac)
                    ctrls = lesions_mod.degree_matched_controls(
                        g, removed,
                        n_replicates=int(cfg["lesion_replicates"]),
                        seed=cseed, n_bins=int(cfg["degree_match_bins"]))
                    tgt = r["lesions"]["nodes"][strategy]["curves"][frac][0]
                    tgt_loss = baseline_pairs - tgt["reachable_pairs"]
                    ctrl_losses = []
                    for c in ctrls:
                        m = rf.lesion_metrics_for_removal(
                            g, sensory, motor, c, baseline_pairs,
                            element="nodes")
                        ctrl_losses.append(baseline_pairs - m["reachable_pairs"])
                    if ctrl_losses:
                        pt = stats_mod.permutation_test(
                            tgt_loss, ctrl_losses, alternative="greater")
                        es = stats_mod.cohens_d([tgt_loss], ctrl_losses)
                        unit = {
                            "targeted_loss": int(tgt_loss),
                            "control_mean_loss": float(np.mean(ctrl_losses)),
                            "n_controls": len(ctrl_losses),
                            "permutation": pt,
                            "cohens_d": es,
                            "test_feasible": True,
                        }
                    else:
                        unit = {
                            "targeted_loss": int(tgt_loss),
                            "control_mean_loss": None,
                            "n_controls": 0,
                            "permutation": None,
                            "cohens_d": None,
                            "test_feasible": False,
                            "note": "degree-matched controls infeasible: "
                                    "out-degree bin exhausted",
                        }
                    ckpt.save_json(uname, unit)
                    log.info(f"t={t}: control {strategy} f={frac} done, "
                             f"checkpointed")
                else:
                    log.info(f"t={t}: control {strategy} f={frac} loaded "
                             f"from checkpoint")
                res = {kk: vv for kk, vv in unit.items()
                       if kk != "test_feasible"}
                strat_res[str(frac)] = res
                if unit.get("test_feasible"):
                    label = f"t{t}|lesion|{strategy}|f{frac}|vs-control"
                    p_labels.append(label)
                    p_values.append(unit["permutation"]["p_value"])
            r["controls"][strategy] = strat_res
        log.info(f"threshold {t}: controls done")

        # ---- null graphs: one checkpoint per replicate ----
        r["nulls"] = {}
        reach_frac_obs = phase["reachability"]["fraction_reachable"]
        for model in null_models:
            reps = []
            for r_idx in range(n_null_reps):
                uname = f"t{t}_null_{model}_{r_idx:02d}"
                rep = ckpt.load_json(uname)
                if rep is None:
                    null_graphs, infos = nulls_mod.make_null_graphs(
                        g, model, 1, int(seeds["nulls"]) + r_idx,
                        swap_factor=int(cfg["edge_swap_factor"]),
                        region_attr=cfg["region_attr"])
                    h = null_graphs[0]
                    oi, oo = nulls_mod.degree_sequences(g)
                    ni, no = nulls_mod.degree_sequences(h)
                    assert np.array_equal(oi, ni) and np.array_equal(oo, no), \
                        (f"degree sequence changed in {model} null "
                         f"replicate {r_idx} at t={t}")
                    if model == "region_constrained":
                        regs = g.vs[cfg["region_attr"]]
                        rc_g = Counter((regs[e.source], regs[e.target])
                                       for e in g.es)
                        rh = h.vs[cfg["region_attr"]]
                        rc_h = Counter((rh[e.source], rh[e.target])
                                       for e in h.es)
                        assert rc_g == rc_h, \
                            "region-to-region counts changed in constrained null"
                    rr = rf.condensation_reachability(h, sensory, motor,
                                                      hop_limits=())
                    weak = h.components(mode="weak")
                    rep = {
                        "swaps_done": int(infos[0]["swaps_done"]),
                        "reach_fraction": float(rr["fraction_reachable"]),
                        "gwc_fraction": float(
                            max((len(c) for c in weak), default=0) / h.vcount()),
                    }
                    del h, null_graphs
                    ckpt.save_json(uname, rep)
                    log.info(f"t={t}: null {model} replicate {r_idx} done, "
                             f"checkpointed")
                else:
                    log.info(f"t={t}: null {model} replicate {r_idx} loaded "
                             f"from checkpoint")
                reps.append(rep)
            null_reach = [x["reach_fraction"] for x in reps]
            null_gwc = [x["gwc_fraction"] for x in reps]
            r["nulls"][model] = {
                "n_replicates": len(reps),
                "mean_swaps_done": float(np.mean([x["swaps_done"]
                                                 for x in reps])),
                "reach_fraction_mean": float(np.mean(null_reach)),
                "reach_fraction_sd": (float(np.std(null_reach, ddof=1))
                                      if len(null_reach) > 1 else 0.0),
                "gwc_fraction_mean": float(np.mean(null_gwc)),
            }
            pt = stats_mod.permutation_test(reach_frac_obs, null_reach,
                                            alternative="greater")
            label = f"t{t}|null|{model}|reachability"
            p_labels.append(label)
            p_values.append(pt["p_value"])
            r["nulls"][model]["permutation_vs_observed"] = pt
            log.info(f"null {model} t={t}: reach "
                     f"{r['nulls'][model]['reach_fraction_mean']:.4f} "
                     f"vs observed {reach_frac_obs:.4f} (p={pt['p_value']:.4f})")

        # ---- bootstrap CIs for random node-lesion losses ----
        r["bootstrap"] = {}
        for frac in fractions:
            losses = [baseline_pairs - b["reachable_pairs"]
                      for b in r["lesions"]["nodes"]["random"]["curves"][frac]]
            r["bootstrap"][str(frac)] = stats_mod.bootstrap_ci(
                losses, n_boot=int(cfg["bootstrap_replicates"]),
                alpha=float(cfg["fdr_alpha"]), seed=int(seeds["stats"]))
        del g, phase
        log.info(f"threshold {t}: complete")

    # ---- FDR ----
    if p_values:
        fdr = stats_mod.benjamini_hochberg(p_values, alpha=float(cfg["fdr_alpha"]))
    else:
        fdr = {"reject": [], "p_adjusted": [], "alpha": float(cfg["fdr_alpha"]),
               "n_tests": 0, "n_rejected": 0}
    results["fdr"] = {
        "labels": p_labels,
        "p_values": [float(p) for p in p_values],
        "rejected": fdr["reject"],
        "p_adjusted": fdr["p_adjusted"],
        "n_rejected": fdr["n_rejected"],
        "n_tests": fdr["n_tests"],
    }
    log.info(f"FDR: {fdr['n_rejected']}/{fdr['n_tests']} rejected at alpha {cfg['fdr_alpha']}")

    # ---- outputs ----
    elapsed = time.time() - t_start
    results["elapsed_seconds"] = elapsed
    write_json(os.path.join(outdir, "results_summary.json"), results)

    manifest = {
        "study": cfg["study"],
        "dataset": cfg["dataset"],
        "data": "REAL MaleCNS v1.0 data from neuprint.janelia.org (male-cns:v1.0). "
                "Not synthetic.",
        "timestamp_utc": utc_now,
        "config_hash": chash,
        "config": cfg,
        "seeds": seeds,
        "package_versions": package_versions(),
        "inputs": {
            "edges_w5.csv": {"sha256": edges_sha,
                             "source": "data/manifest.json (pull 2026-09-12)",
                             "verified": True},
            "neurons.csv": {"sha256": neurons_sha,
                            "source": "data/manifest.json (pull 2026-09-12)",
                            "verified": True},
            "self_loops_dropped_per_threshold": self_loops_dropped,
            "sensory_motor_mapping": "real_run_w5_w11/sensory_motor_mapping.txt",
        },
        "scale_adaptations": [
            "reachability via SCC condensation + bitset DP (reachability_fast), "
            "verified exactly equivalent to reachability.sensory_motor_reachability "
            "on random graphs and on the real graph baseline",
            "lesion metrics via the same fast path (5.2 s vs 303 s per evaluation)",
            "betweenness_cutoff 3 -> 2 (cutoff 3 did not finish on 173k nodes)",
            "edge_swap_factor 10 -> 1 for null rewiring",
            "region-constrained rewiring uses group-restricted proposals "
            "(_rewire_constrained_grouped): the rejection sampler wasted ~75% "
            "of proposals on region-incompatible pairs; the grouped chain is "
            "symmetric and targets the same uniform null distribution, "
            "validated for degree and region-pair-count preservation",
            "undirected global min cut skipped: Stoer-Wagner infeasible at 173k nodes; "
            "diagnostic only, not a failure-point claim",
            "threshold 0 (unfiltered 25.6M edges) out of scope for this run",
            "shortest-path summaries on a seeded 200-source sample (exact per pair)",
        ],
        "outputs": ["run.log", "sensory_motor_mapping.txt",
                    "results_summary.json", "results_summary.md", "manifest.json",
                    "checkpoints/"],
        "reproducibility": {
            "checkpointing": "per-unit checkpoints in outdir/checkpoints/ "
                             "(atomic write + fsync). Units: one threshold "
                             "phase per threshold (graph, orders, baseline "
                             "analyses), one lesion unit per (element, "
                             "strategy), one control unit per (strategy, "
                             "fraction), one null unit per (model, "
                             "replicate). Finished units are skipped on "
                             "resume.",
            "seeding_scheme": "each stochastic checkpoint unit draws from "
                              "its own numpy default_rng stream seeded by "
                              "unit_seed(master_seed, unit_parts), where "
                              "unit_seed is SHA-256('master|part1|...') "
                              "truncated to 32 bits (stable across processes "
                              "and platforms). Lesion units use "
                              "seeds.lesions with parts "
                              "('lesion', threshold, element, strategy); "
                              "control units use seeds.lesions with parts "
                              "('control', threshold, strategy, fraction); "
                              "null replicates keep the original "
                              "seeds.nulls + replicate-index scheme. "
                              "Reachability, disjoint-path sampling, and "
                              "bootstrap calls keep their fixed per-call "
                              "seeds['stats'] seed. Because no unit "
                              "consumes another unit's stream, a resumed run "
                              "is bit-identical to an uninterrupted run.",
            "determinism_fixes": "lesions.node_removal_order "
                                 "mincut_membership now sorts member indices "
                                 "(previously iterated a set of strings, "
                                 "whose order varies with PYTHONHASHSEED). "
                                 "run timestamp is fixed at first launch in "
                                 "checkpoints/run_state.json so resumed runs "
                                 "keep it. results elapsed_seconds is the "
                                 "only wall-clock field and naturally "
                                 "differs between runs.",
        },
        "notes": "Real-data run. No synthetic test graph used.",
    }
    write_json(os.path.join(outdir, "manifest.json"), manifest)
    _write_summary_md(outdir, results, manifest, thresholds, fractions)

    log.info(f"REAL RUN: DONE in {elapsed:.1f}s")
    print("REAL RUN: DONE")
    print(f"FDR: {fdr['n_rejected']}/{fdr['n_tests']} rejected")


def _write_summary_md(outdir, results, manifest, thresholds, fractions):
    lines = []
    a = lines.append
    a("# Fault Lines pipeline: REAL MaleCNS v1.0 run summary")
    a("")
    a("REAL DATA: male-cns:v1.0 from neuprint.janelia.org. Not synthetic.")
    a("")
    a(f"Config hash: `{manifest['config_hash']}`")
    a(f"Timestamp (UTC): {manifest['timestamp_utc']}")
    a(f"Elapsed: {results['elapsed_seconds']:.1f} s")
    a("")
    a("## Graph scale per threshold")
    a("")
    a("| threshold | nodes | edges | largest weak comp | sensory in-graph | motor in-graph | reachability |")
    a("|---|---|---|---|---|---|---|")
    for t in thresholds:
        r = results["thresholds"][str(t)]
        gs = r["graph_stats"]
        rc = r["reachability"]
        a(f"| {t} | {gs['n_nodes']} | {gs['n_edges']} | {gs['largest_weak']} "
          f"| {r['sensory_in_graph']} | {r['motor_in_graph']} "
          f"| {rc['reachable_pairs']}/{rc['total_pairs']} ({rc['fraction_reachable']:.4f}) |")
    a("")
    a("## Minimum s-t cuts (sensory to motor)")
    a("")
    for t in thresholds:
        mc = results["thresholds"][str(t)]["mincut"]
        a(f"threshold {t}: value={mc['value']:.0f}, cut edges={mc['n_cut_edges']}")
    a("")
    a("## Lesion highlights (nodes, max fraction)")
    a("")
    max_frac = max(fractions)
    for t in thresholds:
        r = results["thresholds"][str(t)]["lesions"]["nodes"]
        rand_m = float(np.mean([b["newly_disconnected"] for b in r["random"]["curves"][max_frac]]))
        for strat in ("out_degree", "betweenness_approx", "mincut_membership"):
            tgt = r[strat]["curves"][max_frac][0]["newly_disconnected"]
            a(f"threshold {t}, fraction {max_frac}, {strat}: newly disconnected={tgt}, "
              f"random mean={rand_m:.1f}")
    a("")
    a("## Null-model comparison")
    a("")
    for t in thresholds:
        for model in ("degree_preserving", "region_constrained"):
            n = results["thresholds"][str(t)]["nulls"][model]
            pt = n["permutation_vs_observed"]
            a(f"threshold {t}, {model}: null reach {n['reach_fraction_mean']:.4f}, "
              f"p={pt['p_value']:.4f}")
    a("")
    a("## FDR summary")
    a("")
    fdr = results["fdr"]
    a(f"{fdr['n_rejected']} of {fdr['n_tests']} tests rejected "
      f"at alpha {manifest['config']['fdr_alpha']}.")
    a("")
    a("## Package versions")
    a("")
    for k, v in manifest["package_versions"].items():
        a(f"- {k}: {v}")
    with open(os.path.join(outdir, "results_summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
