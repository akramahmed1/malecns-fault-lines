"""End-to-end orchestration of the Fault Lines battery on the synthetic test graph.

Steps:
  1. build test graph, write CSVs, compute ground truth, checksums
  2. smoke-test the chunked builder against the in-memory builder
  3. per threshold: graph stats, reachability, disjoint paths, mincut
     (asserted against ground truth), undirected global mincut
  4. lesion battery (nodes and edges)
  5. degree-matched controls for targeted node strategies
  6. null graphs per threshold and model, with degree/region checks
  7. statistics: bootstrap CIs, permutation tests, effect sizes, BH-FDR
  8. manifest.json, results_summary.json, results_summary.md

Usage: python run_all.py [--config config.yaml] [--outdir test_run]
"""
import argparse
import datetime
import os
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graph_build
import lesions as lesions_mod
import make_test_graph
import mincut as mincut_mod
import nulls as nulls_mod
import reachability as reach_mod
import stats as stats_mod
from utils import (config_hash, load_config, package_versions, setup_logger,
                   sha256_file, to_jsonable, write_json)


def region_pair_counter(g):
    regs = g.vs["region"]
    return Counter((regs[e.source], regs[e.target]) for e in g.es)


def main():
    ap = argparse.ArgumentParser(description="Fault Lines pipeline end-to-end run")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--outdir", default="test_run")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = args.config if os.path.isabs(args.config) else os.path.join(here, args.config)
    outdir = args.outdir if os.path.isabs(args.outdir) else os.path.join(here, args.outdir)
    os.makedirs(outdir, exist_ok=True)
    log = setup_logger(outdir)

    cfg = load_config(cfg_path)
    chash = config_hash(cfg)
    log.info(f"config sha256: {chash}")
    t_start = time.time()
    seeds = cfg["seeds"]
    thresholds = [int(t) for t in cfg["thresholds"]]
    fractions = [float(f) for f in cfg["lesion_fractions"]]
    results = {"config_hash": chash, "thresholds": {}}
    utc_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # ---- 1. test graph, ground truth, checksums ----
    log.info("building synthetic test graph")
    edges_df, nodes_df = make_test_graph.build_test_graph(seed=int(seeds["test_graph"]))
    edges_csv = os.path.join(outdir, "test_edges.csv")
    nodes_csv = os.path.join(outdir, "test_nodes.csv")
    edges_df.to_csv(edges_csv, index=False)
    nodes_df.to_csv(nodes_csv, index=False)
    gt = make_test_graph.compute_ground_truth(edges_df, nodes_df, thresholds,
                                              int(seeds["test_graph"]))
    gt_path = os.path.join(outdir, "ground_truth.json")
    write_json(gt_path, gt)
    log.info(f"test graph: {len(nodes_df)} nodes, {len(edges_df)} edges "
             f"(SYNTHETIC, seed {seeds['test_graph']})")

    sensory = nodes_df.loc[nodes_df["is_sensory"], "node"].tolist()
    motor = nodes_df.loc[nodes_df["is_motor"], "node"].tolist()
    log.info(f"sensory set ({len(sensory)}): {sensory}")
    log.info(f"motor set ({len(motor)}): {motor}")

    # ---- 2. chunked builder smoke test ----
    srcs, dsts, weights = graph_build.load_edgelist_csv(edges_csv)
    g_mem = graph_build.build_graph(srcs, dsts, weights, threshold=0)
    g_chunk = graph_build.build_graph_chunked(edges_csv, threshold=0)
    assert g_chunk.vcount() == g_mem.vcount(), "chunked builder node mismatch"
    assert g_chunk.ecount() == g_mem.ecount(), "chunked builder edge mismatch"
    assert sorted(g_chunk.vs["name"]) == sorted(g_mem.vs["name"])
    assert sum(g_chunk.es["synapses"]) == sum(g_mem.es["synapses"])
    log.info("chunked builder smoke test: PASS "
             f"({g_chunk.vcount()} nodes, {g_chunk.ecount()} edges)")

    graphs = {}
    for t in thresholds:
        g = graph_build.build_graph(srcs, dsts, weights, threshold=t)
        graph_build.attach_node_metadata(g, nodes_df)
        graphs[t] = g

    # ---- 3-7. per-threshold battery ----
    p_labels, p_values = [], []
    ctrl_seed = int(seeds["lesions"])
    for t in thresholds:
        g = graphs[t]
        r = results["thresholds"][str(t)] = {}
        log.info(f"--- threshold {t}: {g.vcount()} nodes, {g.ecount()} edges ---")

        r["graph_stats"] = graph_build.graph_stats(g)
        log.info(f"stats: {r['graph_stats']}")

        reach = reach_mod.sensory_motor_reachability(g, sensory, motor,
                                                     hop_limits=cfg["hop_limits"])
        r["reachability"] = reach
        log.info(f"reachability: {reach['reachable_pairs']}/{reach['total_pairs']} "
                 f"pairs ({reach['fraction_reachable']:.3f}); "
                 f"hop fractions: {reach['hop_limited_fraction']}")

        r["disjoint_paths"] = reach_mod.edge_disjoint_path_counts(
            g, sensory, motor, max_pairs=int(cfg["max_disjoint_pairs"]),
            seed=int(seeds["stats"]))
        log.info(f"disjoint paths: mean {r['disjoint_paths']['mean_disjoint_paths']:.2f} "
                 f"over {r['disjoint_paths']['n_pairs_reachable']} reachable pairs")

        mc = mincut_mod.st_mincut_between_sets(g, sensory, motor)
        r["mincut"] = mc
        gt_val = gt["thresholds"][str(t)]["mincut_value"]
        gt_n = gt["thresholds"][str(t)]["n_cut_edges"]
        assert abs(mc["value"] - gt_val) < 1e-9, \
            f"mincut mismatch at t={t}: {mc['value']} vs ground truth {gt_val}"
        assert mc["n_cut_edges"] == gt_n, \
            f"cut edge count mismatch at t={t}"
        log.info(f"mincut: value={mc['value']:.0f} edges={mc['n_cut_edges']} "
                 f"matches ground truth: PASS")

        r["global_mincut_undirected"] = mincut_mod.global_mincut_undirected(g)
        log.info(f"global undirected mincut: {r['global_mincut_undirected']}")

        # ---- 4. lesion battery ----
        r["lesions"] = {"nodes": {}, "edges": {}}
        for strategy in cfg["node_strategies"]:
            r["lesions"]["nodes"][strategy] = lesions_mod.lesion_curve(
                g, sensory, motor, element="nodes", strategy=strategy,
                fractions=fractions, n_replicates=int(cfg["lesion_replicates"]),
                seed=int(seeds["lesions"]), betweenness_cutoff=int(cfg["betweenness_cutoff"]),
                mincut_info=mc)
        for strategy in cfg["edge_strategies"]:
            r["lesions"]["edges"][strategy] = lesions_mod.lesion_curve(
                g, sensory, motor, element="edges", strategy=strategy,
                fractions=fractions, n_replicates=int(cfg["lesion_replicates"]),
                seed=int(seeds["lesions"]) + 7, betweenness_cutoff=int(cfg["betweenness_cutoff"]))
        max_frac = max(fractions)
        rand_loss = np.mean([b["newly_disconnected"]
                             for b in r["lesions"]["nodes"]["random"]["curves"][max_frac]])
        tgt_loss = r["lesions"]["nodes"]["out_degree"]["curves"][max_frac][0]["newly_disconnected"]
        check = "PASS" if tgt_loss >= rand_loss else "WARN"
        log.info(f"lesion sanity t={t}: out_degree loss {tgt_loss} vs random mean "
                 f"{rand_loss:.1f}: {check}")

        # ---- 5. degree-matched controls for targeted node strategies ----
        r["controls"] = {}
        baseline_pairs = r["lesions"]["nodes"]["random"]["baseline_reachable_pairs"]
        for strategy in ["out_degree", "betweenness_approx", "mincut_membership"]:
            order = lesions_mod.node_removal_order(
                g, strategy, betweenness_cutoff=int(cfg["betweenness_cutoff"]),
                mincut_info=mc)
            strat_res = {}
            for frac in fractions:
                k = max(1, int(round(frac * g.vcount())))
                removed = order[:k]
                ctrls = lesions_mod.degree_matched_controls(
                    g, removed, n_replicates=int(cfg["lesion_replicates"]),
                    seed=ctrl_seed, n_bins=int(cfg["degree_match_bins"]))
                ctrl_seed += 1
                ctrl_metrics = [lesions_mod.lesion_metrics_for_set(
                    g, sensory, motor, c, baseline_pairs) for c in ctrls]
                tgt = r["lesions"]["nodes"][strategy]["curves"][frac][0]
                tgt_loss_f = baseline_pairs - tgt["reachable_pairs"]
                ctrl_losses = [baseline_pairs - m["reachable_pairs"] for m in ctrl_metrics]
                if ctrl_losses:
                    pt = stats_mod.permutation_test(tgt_loss_f, ctrl_losses,
                                                    alternative="greater")
                    es = stats_mod.cohens_d([tgt_loss_f], ctrl_losses)
                    label = f"t{t}|lesion|{strategy}|f{frac}|vs-control"
                    p_labels.append(label)
                    p_values.append(pt["p_value"])
                    strat_res[str(frac)] = {
                        "targeted_loss": tgt_loss_f,
                        "control_mean_loss": float(np.mean(ctrl_losses)),
                        "n_controls": len(ctrl_losses),
                        "permutation": pt,
                        "cohens_d": es,
                    }
                else:
                    # Rare high-degree nodes cannot always be matched: the top
                    # out-degree bin is exhausted once its members are removed.
                    strat_res[str(frac)] = {
                        "targeted_loss": tgt_loss_f,
                        "control_mean_loss": None,
                        "n_controls": 0,
                        "permutation": None,
                        "cohens_d": None,
                        "note": "degree-matched controls infeasible: "
                                "out-degree bin exhausted",
                    }
            r["controls"][strategy] = strat_res
        log.info(f"controls done for t={t}")

        # ---- 6. null graphs ----
        r["nulls"] = {}
        for model in cfg["null_models"]:
            null_graphs, infos = nulls_mod.make_null_graphs(
                g, model, int(cfg["null_replicates"]), int(seeds["nulls"]),
                swap_factor=int(cfg["edge_swap_factor"]))
            oi, oo = nulls_mod.degree_sequences(g)
            for h in null_graphs:
                ni, no = nulls_mod.degree_sequences(h)
                assert np.array_equal(oi, ni) and np.array_equal(oo, no), \
                    f"degree sequence changed in {model} null at t={t}"
            if model == "region_constrained":
                assert region_pair_counter(null_graphs[0]) == region_pair_counter(g), \
                    "region-to-region counts changed in constrained null"
            null_reach = []
            null_gwc = []
            for h in null_graphs:
                rr = reach_mod.sensory_motor_reachability(h, sensory, motor, hop_limits=())
                null_reach.append(rr["fraction_reachable"])
                weak = h.components(mode="weak")
                null_gwc.append(max((len(c) for c in weak), default=0) / h.vcount())
            r["nulls"][model] = {
                "n_replicates": len(null_graphs),
                "mean_swaps_done": float(np.mean([i["swaps_done"] for i in infos])),
                "reach_fraction_mean": float(np.mean(null_reach)),
                "reach_fraction_sd": float(np.std(null_reach, ddof=1)) if len(null_reach) > 1 else 0.0,
                "gwc_fraction_mean": float(np.mean(null_gwc)),
            }
            pt = stats_mod.permutation_test(reach["fraction_reachable"], null_reach,
                                            alternative="greater")
            label = f"t{t}|null|{model}|reachability"
            p_labels.append(label)
            p_values.append(pt["p_value"])
            r["nulls"][model]["permutation_vs_observed"] = pt
            log.info(f"null {model} t={t}: {len(null_graphs)} replicates, "
                     f"degree preservation PASS, reach {r['nulls'][model]['reach_fraction_mean']:.3f} "
                     f"vs observed {reach['fraction_reachable']:.3f} (p={pt['p_value']:.4f})")

        # ---- bootstrap CIs for random node-lesion losses ----
        r["bootstrap"] = {}
        for frac in fractions:
            losses = [baseline_pairs - b["reachable_pairs"]
                      for b in r["lesions"]["nodes"]["random"]["curves"][frac]]
            r["bootstrap"][str(frac)] = stats_mod.bootstrap_ci(
                losses, n_boot=int(cfg["bootstrap_replicates"]),
                alpha=float(cfg["fdr_alpha"]), seed=int(seeds["stats"]))

    # ---- 7b. FDR across the full family ----
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

    # ---- 8. outputs ----
    elapsed = time.time() - t_start
    results["elapsed_seconds"] = elapsed
    write_json(os.path.join(outdir, "results_summary.json"), results)

    manifest = {
        "study": cfg["study"],
        "dataset": cfg["dataset"],
        "timestamp_utc": utc_now,
        "config_hash": chash,
        "config": cfg,
        "seeds": seeds,
        "package_versions": package_versions(),
        "inputs": {
            "test_edges.csv": sha256_file(edges_csv),
            "test_nodes.csv": sha256_file(nodes_csv),
            "ground_truth.json": sha256_file(gt_path),
            "ground_truth_verified": True,
            "synthetic": True,
        },
        "outputs": ["run.log", "test_edges.csv", "test_nodes.csv",
                    "ground_truth.json", "results_summary.json",
                    "results_summary.md", "manifest.json"],
        "notes": "Synthetic test-graph run. No MaleCNS data used.",
    }
    write_json(os.path.join(outdir, "manifest.json"), manifest)
    _write_summary_md(outdir, results, manifest, thresholds, fractions)

    log.info(f"END-TO-END RUN: PASS in {elapsed:.1f}s")
    log.info(f"config hash {chash}")
    print("END-TO-END RUN: PASS")
    print(f"config hash: {chash}")
    print(f"FDR: {fdr['n_rejected']}/{fdr['n_tests']} rejected")


def _write_summary_md(outdir, results, manifest, thresholds, fractions):
    lines = []
    a = lines.append
    a("# Fault Lines pipeline: test-graph run summary")
    a("")
    a("SYNTHETIC DATA ONLY. No MaleCNS data was used in this run.")
    a("")
    a(f"Config hash: `{manifest['config_hash']}`")
    a(f"Timestamp (UTC): {manifest['timestamp_utc']}")
    a(f"Elapsed: {results['elapsed_seconds']:.1f} s")
    a("")
    a("## Graph scale per threshold")
    a("")
    a("| threshold | nodes | edges | largest weak comp | reachability |")
    a("|---|---|---|---|---|")
    for t in thresholds:
        r = results["thresholds"][str(t)]
        gs = r["graph_stats"]
        rc = r["reachability"]
        a(f"| {t} | {gs['n_nodes']} | {gs['n_edges']} | {gs['largest_weak']} "
          f"| {rc['reachable_pairs']}/{rc['total_pairs']} ({rc['fraction_reachable']:.3f}) |")
    a("")
    a("## Minimum cuts (verified against planted ground truth)")
    a("")
    for t in thresholds:
        mc = results["thresholds"][str(t)]["mincut"]
        a(f"threshold {t}: value={mc['value']:.0f}, cut edges={mc['n_cut_edges']}, "
          f"match=PASS")
    a("")
    a("## Lesion highlights (nodes, max fraction)")
    a("")
    max_frac = max(fractions)
    for t in thresholds:
        r = results["thresholds"][str(t)]["lesions"]["nodes"]
        rand_m = np.mean([b["newly_disconnected"] for b in r["random"]["curves"][max_frac]])
        tgt = r["out_degree"]["curves"][max_frac][0]["newly_disconnected"]
        a(f"threshold {t}, fraction {max_frac}: out_degree newly disconnected={tgt}, "
          f"random mean={rand_m:.1f}")
    a("")
    a("## Null-model comparison")
    a("")
    for t in thresholds:
        for model in ("degree_preserving", "region_constrained"):
            n = results["thresholds"][str(t)]["nulls"][model]
            pt = n["permutation_vs_observed"]
            a(f"threshold {t}, {model}: null reach {n['reach_fraction_mean']:.3f}, "
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
