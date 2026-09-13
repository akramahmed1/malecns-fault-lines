# Fault Lines pipeline

End-to-end analysis scaffold for "Fault Lines in a Fly Brain: Mapping Structural
Resilience in the Complete Male Drosophila Connectome."

**Status: synthetic test graph only.** No MaleCNS data has been used. The test
graph has a planted sensory-to-motor bottleneck so every module has verifiable
expected outputs (see `ground_truth.json` after a run). Nothing here has been
validated against real MaleCNS data yet.

## Graph library choice: igraph, not networkx

The full MaleCNS graph has 166,700 neurons and 25.6M edges (Cell Results;
STAR Methods gives 25.58M). networkx stores every node and edge as Python
objects with per-object dict overhead, which puts a 25.6M-edge graph at tens
of gigabytes of RAM and makes basic traversals impractically slow. igraph is
C-backed with compact array storage: the same graph fits in roughly 1 to 2 GB
and core algorithms (components, BFS, min cut, max flow) run in compiled code.
That is the only feasible option at full scale, so the pipeline is built on
igraph from the start and the test-scale code uses the same calls the full
run will use.

Sparse structures only. There are no dense adjacency matrices anywhere
(a 166,700 by 166,700 dense matrix is impossible). Edge loading for the real
run uses `build_graph_chunked` (two passes over the CSV, memory proportional
to vertices plus one chunk).

## Modules

- `config.yaml`: every parameter in one place. Synapse thresholds [0, 5, 11]
  come from the data dictionary: 11 is the MaleCNS noise threshold, 5 is the
  common weak-connection cutoff (6.24M edges at >=5 in MaleCNS v1.0).
- `utils.py`: config loading and SHA256 hashing, seeded RNG streams, logging,
  JSON helpers, file checksums, package version capture.
- `graph_build.py`: edge list (src, dst, synapses) to directed weighted
  graph; threshold variants; graph stats; the chunked builder for full scale.
- `make_test_graph.py`: synthetic directed weighted graph (74 nodes) with a
  planted bottleneck (hubs h0, h1), region labels (sensory, brain,
  bottleneck, vnc, motor), and sensory/motor sets. Writes `test_edges.csv`,
  `test_nodes.csv`, and `ground_truth.json` (min-cut value and cut edges per
  threshold, asserted to fall on the planted bottleneck).
- `reachability.py`: sensory-to-motor reachability (pair counts, per-source
  counts, hop-limited fractions, shortest-path summaries) and sampled
  edge-disjoint path counts via unit-capacity max flow.
- `mincut.py`: minimum s-t cut between node sets via super source/sink
  (the failure-point identification); supplementary undirected global min cut.
- `lesions.py`: random vs targeted node and edge removal (out-degree,
  cutoff-limited approximate betweenness, min-cut membership, edge weight);
  tracks giant weak component fraction, reachability, newly disconnected
  pairs; degree-matched random controls via out-degree quantile bins.
- `nulls.py`: degree-preserving directed rewiring and region-constrained
  rewiring (preserves region-to-region counts too) by double-edge swaps;
  N replicates with fixed seeds; weight multiset preserved.
- `stats.py`: percentile bootstrap CIs, one-sided permutation tests with the
  +1 correction, Cohen's d, Benjamini-Hochberg FDR.
- `run_all.py`: orchestrates the full battery and writes `manifest.json`
  (config hash, seeds, package versions, timestamps, input checksums),
  `results_summary.json`, `results_summary.md`, and `run.log`.

## How to run

```bash
cd ~/workspace/your_files/fly-connectome-paper-outline/pipeline
python3 run_all.py
```

Options: `--config config.yaml --outdir test_run`. Outputs land in the outdir.

## How the real MaleCNS edge list plugs in later

1. Query neuPrint (`male-cns:v1.0`) with `fetch_adjacencies`, or page the
   bulk edge export, and write `src,dst,synapses` rows to CSV. One row per
   directed neuron pair, weight = synapse count.
2. Write `nodes.csv` with columns `node,region,is_sensory,is_motor` from
   neuprint `fetch_neurons` annotations (region can be superclass,
   hemilineage, or neuropil; the region-constrained null works with any
   categorical label).
3. In `run_all.py`, replace the `make_test_graph` step with loading these
   CSVs and switch graph construction to `build_graph_chunked`.
4. Thresholds [0, 5, 11] and all downstream modules stay the same. The
   ground-truth assertions are test-graph only and must be disabled for the
   real run (there is no planted cut in real data).

## Scale notes: what changes at 25.6M edges

| Test-scale implementation | Full-scale replacement |
|---|---|
| Exact min s-t cut on full graph | Same igraph call, but only on thresholded graphs (>=5 synapses: 6.24M edges); s-t cut with super source/sink stays feasible in C |
| Cutoff-limited approximate betweenness | Keep the cutoff, or move to a GPU implementation (e.g. cuGraph) |
| Edge-disjoint path counts per pair | Sampled pair sets only (already capped by `max_disjoint_pairs`) |
| Full lesion battery on every null replicate | Reduce null replicates or lesion fractions; the config makes this one edit |
| In-memory edge list build | `build_graph_chunked` (already implemented and smoke-tested) |
| Undirected global min cut | Thresholded graphs only; diagnostic, not a failure-point claim |

Expected full-scale behavior is untested. The 25.6M-edge unfiltered graph
will need a high-memory machine; the >=5 and >=11 threshold variants
(6.24M edges and fewer) are the practical working graphs, consistent with
the paper's own noise-threshold practice.

## What is not yet validated

- Real neuPrint property names for edge weights in bulk exports (the exact
  field behind "synapses" still needs a live schema query).
- neuPrint pagination behavior for 25.6M edges.
- Actual runtime and peak memory at full scale.
- Whether `fetch_adjacencies` returns unfiltered edges or pre-thresholded ones.
- Choice of region label for the region-constrained null on real annotations.

## Reproducibility

Every run logs the SHA256 of `config.yaml` to `run.log` and `manifest.json`,
along with seeds per stage, package versions, UTC timestamps, and SHA256
checksums of all inputs. Re-running with the same config and code reproduces
the test-graph results exactly.
