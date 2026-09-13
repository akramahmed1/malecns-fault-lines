# Fault Lines: Structural Resilience of the Complete Fly CNS Connectome

A lesion and minimum-cut benchmark of sensory-to-motor structural resilience on
the complete male *Drosophila* central nervous system connectome (MaleCNS v1.0).

Status: **preliminary, unpublished research code and results.** Nothing here is
peer reviewed. An independent reproducibility audit is complete
(`pipeline/AUDIT_REPORT.md`); sensitivity checks (e.g. threshold 0) are still
pending, so treat findings as provisional.

Interactive companion: **MaleCNS Structural Atlas**,
`https://akramahmed1.github.io/malecns-fault-lines/`
(source in `docs/`, generated from the same results files as the paper).

## What this is

The pipeline builds the full brain-plus-VNC directed graph from MaleCNS v1.0,
then runs a structural-resilience battery:

- sensory-to-motor reachability over ~60M neuron pairs
- edge-disjoint path counts (sampled)
- a minimum s-t cut from the sensory population to the motor population
  (the failure-point atlas: the smallest set of edges whose removal
  disconnects all sensory-to-motor routes)
- targeted vs random node and edge lesion curves, with degree-matched
  controls, rewired null models, bootstrap CIs, and FDR correction

## Data

Raw edge and neuron tables are in `pipeline/data/` as gzip-compressed CSVs
(`edges_w0.csv.gz` is split in two parts because of GitHub's 100 MB file
limit; see `pipeline/data/README.md` for reassembly and SHA256 hashes).
They come from the public MaleCNS v1.0 release via neuPrint:

- Source: `neuprint.janelia.org`, dataset `male-cns:v1.0`, released 2026-06-08 (CC BY)
- Paper: Berg et al., Cell 189(18), 5504-5526.e15 (2026), doi:10.1016/j.cell.2026.08.015

To reproduce, pull the tables with the neuPrint API (edge weight property is
`c.weight`) into `pipeline/data/` as `edges_w5.csv`, `edges_w0.csv`, and
`neurons.csv`, then verify against the SHA256 hashes in
`pipeline/data/manifest.json` and `pipeline/data/manifest_w0.json`:

- `edges_w5.csv`: `60b4adb6f3b9f96a290e192f23e2822ea3ab96020edef5ed6cd5ff354cd40182`
- `edges_w0.csv`: `440a096c8110c25b9bc0153c6925112924edd86bac5c999d1701795e95d6702e`
- `neurons.csv`: `41b08d255e7a41747af40a5559b139db7efeefb21096cd8285c44c19915e7681`

## Reproduce the battery

```bash
cd pipeline
python3 run_real.py   # real-data battery, thresholds 5 and 11 (config_real.yaml)
```

The run checkpoints every unit and resumes after interruption.
`supervise.sh` keeps it alive; `watchdog_once.sh` relaunches it after a reboot.

## Headline results (preliminary)

From `pipeline/real_run_w5_w11/results_summary.md`:

- 173,023 neurons; 6.29M edges at weight >= 5, 2.45M at weight >= 11
- Sensory-to-motor reachability: 99.3% (w5), 92.6% (w11)
- Min-cut: 4.32M / 267,027 cut edges (w5); 3.25M / 117,267 cut edges (w11)
- Targeted lesions disconnect far more pairs than random, but after FDR
  correction 0 of 24 tests survive at alpha 0.05 (adjusted p = 0.057).
  The targeted-vs-random gap is suggestive, not significant by the
  pre-registered bar.

## Caveats

- This is structural wiring, not neural activity, physiology, or behavior.
  Structural routes do not prove behavioral use.
- Threshold 0 (unfiltered graph) has not been run yet.
- The 173,023 graph nodes vs the paper's 166,700 neurons is an open,
  documented discrepancy (see data-dictionary.md).
- Edge betweenness lesions were dropped as a scale adaptation (did not finish
  on 6.29M edges); node betweenness (approx, cutoff 2) remains.

## Layout

- `pipeline/` - analysis code, configs, run scripts
- `pipeline/real_run_w5_w11/` - results, manifest, sensory/motor mapping
- `data-dictionary.md`, `novelty-matrix.md` - variable definitions and novelty audit
- `fly-connectome-paper-outline.pdf` - paper blueprint (draft, not a manuscript)
