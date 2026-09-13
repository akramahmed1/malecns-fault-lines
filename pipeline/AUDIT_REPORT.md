# MaleCNS Battery Reproducibility Audit

**Date:** 2026-09-13
**Scope:** `pipeline/` — raw data (`data/edges_w0.csv`, `data/edges_w5.csv`, `data/neurons.csv`),
results (`real_run_w5_w11/results_summary.json`), and all pipeline scripts.
**Method:** fresh independent checks (pandas, chunked; no pipeline imports), full code read.
Raw CSVs were never modified.
**Reference values (paper):** Berg et al., Cell 189(18), 2026 — 166,700 neurons;
166,483 connected + 217 without synapses; 25.6M graph edges.

---

## Q1. The node discrepancy — RESOLVED (exact arithmetic)

All three counts are reconciled. The download pulled **every** `:Neuron`-labeled node
in neuPrint `male-cns:v1.0` (`MATCH (n:Neuron)` in `pull_malecns.py`); the paper counts
only classification-annotated neurons. The arithmetic closes exactly on all four
paper figures:

| Step | Computation | Result | Paper |
|---|---|---|---|
| DB `:Neuron` nodes | `neurons.csv` rows (0 duplicate bodyIds, verified) | 176,422 | — |
| minus unannotated records (NaN `superclass`; 8,277 fully blank, 1,445 fragment-named) | 176,422 − 9,722 | **166,700** | 166,700 ✓ exact |
| annotated neurons with ≥1 edge to another *annotated* neuron (w0) | measured | **166,483** | 166,483 ✓ exact |
| annotated, no w0 edge (213) + edges only to unannotated partners (4) | 213 + 4 | **217** | 217 ✓ exact |
| w0 edges with both endpoints annotated | measured | 25,582,938 → **25.6M** | 25.6M ✓ |
| distinct endpoints of weight≥5 edges | measured | **173,023** | — |

Bridge 176,422 → 173,023: **3,399** neuron records have no weight≥5 edge
(`len(bodies − w5_nodes)`, measured). Of the 173,023 graph nodes, 165,879 are
annotated and 7,144 are unannotated objects that do have ≥5-synapse edges.
Every edge endpoint in both CSVs exists in `neurons.csv` (0 phantom IDs).

The "connected" convention (edge to another *annotated* neuron) is **inferred from
exact arithmetic**, not confirmed against the paper's Methods text — all four
paper numbers reproduce exactly under it, which is very strong evidence, but the
paper text itself was not re-checked in this audit.

**Verdict: RESOLVED.** No remapping artifact, no duplicate IDs, no wrong-version
pull. The 173,023 vs 166,700 gap is fully explained: the battery graphs include
unannotated DB objects and weak-edge isolates that the paper's headline counts exclude.

---

## Q2. Independent re-derivation — all headline numbers CONFIRMED

Fresh chunked pandas checks (no pipeline code), string IDs matching pipeline behavior:

| Quantity | Reported | Recomputed | Verdict |
|---|---|---|---|
| `edges_w5.csv` rows | 6,287,789 (implied) | 6,287,789 | CONFIRMED |
| w5 self-loops | 40 | 40 | CONFIRMED |
| w5 directed edges after self-loop removal | 6,287,749 | 6,287,789 − 40 = 6,287,749 | CONFIRMED |
| w5 weight range (pre-filtered at pull) | ≥5 | min 5, max 2,591 | CONFIRMED |
| `edges_w0.csv` rows | 25,862,574 | 25,862,574 | CONFIRMED |
| w0 self-loops | — | 122 | (new measurement) |
| w11 rows in w5 file | 2,446,826 (implied) | 2,446,826 | CONFIRMED |
| w11 self-loops (weight≥11) | — | 11 | (new measurement) |
| w11 directed edges after self-loop removal | 2,446,815 | 2,446,826 − 11 = 2,446,815 | CONFIRMED |
| distinct nodes, w5 graph | 173,023 | 173,023 | CONFIRMED |
| distinct nodes, w11 graph | 173,023 | 173,023 | CONFIRMED |
| `neurons.csv` rows / unique bodyIds | 176,422 | 176,422 / 176,422, 0 dups, 0 nulls | CONFIRMED |

Reachability/min-cut/lesion/statistics values were **code-reviewed but not
independently recomputed** (a second from-scratch implementation of the
condensation reachability was out of scope). Sanity check: the reachability
denominator 60,201,504 = 26,972 × 2,232 (in-graph sensory × motor) exactly.

---

## Q3. Code skim — no correctness bugs; one methodological wart

- **Weight property:** pull uses neuPrint `c.weight` (`ConnectsTo.weight`), stored as
  `synapses` in the CSVs. Correct; matches MaleCNS semantics.
- **Thresholding:** `>=` in both builders and in the pull query (`c.weight >= min_weight`).
  Correct per config ("minimum synapses per edge").
- **Directed handling:** graphs built `directed=True` throughout; min-cut is a true
  directed s-t cut via super source/sink with infinite-capacity super edges
  (`mincut.py`). Betweenness/reachability all use directed mode. The undirected
  Stoer–Wagner helper exists but is unused (documented as skipped). Correct.
- **Self-loops:** removed *after* graph construction (`delete_edges`), vertices
  retained. Reported edge counts match this exactly. No bug; node counts include
  any self-loop-only vertices (0 such annotated vertices at w0, measured).
- **Stats:** permutation test (+1 correction), BH-FDR, and Cohen's d are standard
  and correctly implemented. FDR input set (control + null p-values, infeasible
  tests excluded) is handled properly.
- **Nulls:** double-edge swaps preserve in/out-degree exactly (asserted at runtime);
  region-constrained variant preserves region-pair counts (asserted); multi-edges
  never created. Correct.

**Wart (minor, does not change edge counts):** `build_graph_chunked` pass 1 collects
vertex names from *all* CSV rows without applying the threshold, so the **w11 graph
contains 6,149 isolated vertices** (173,023 vertices but only 166,874 have a
weight≥11 edge, measured). Consequences: the headline "173,023 nodes at w11"
overstates the effective graph, and w11 lesion fractions are computed over a pool
that includes isolates (mildly diluting targeted-removal fractions). Recommend
either filtering isolates at w11 or documenting the convention before the paper
leans on w11 node counts.

---

## Overall

- Every headline number the battery reports (edge counts, self-loop counts, node
  counts, paper-figure reconciliation) is **independently confirmed**.
- The node discrepancy is **fully explained by exact arithmetic**; it reflects a
  defensible-but-different counting convention (all DB objects vs annotated neurons),
  not a data or code error.
- Code skim found **no correctness bugs**; one minor wart (w11 isolated vertices)
  worth documenting.
- Not re-derived here: reachability pair counts, min-cut values, lesion curves,
  permutation/FDR numbers (reviewed, not recomputed). A deeper audit could
  re-implement condensation reachability independently as a final check.
