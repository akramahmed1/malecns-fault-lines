# Fault Lines pipeline: test-graph run summary

SYNTHETIC DATA ONLY. No MaleCNS data was used in this run.

Config hash: `c7102bd50e44c14c31a29940fe8fc5749edc06b131b631e8c8a26ea3e6627f4b`
Timestamp (UTC): 2026-09-12T15:34:55.367160+00:00
Elapsed: 18.4 s

## Graph scale per threshold

| threshold | nodes | edges | largest weak comp | reachability |
|---|---|---|---|---|
| 0 | 74 | 290 | 74 | 36/36 (1.000) |
| 5 | 73 | 258 | 73 | 36/36 (1.000) |
| 11 | 70 | 172 | 35 | 0/36 (0.000) |

## Minimum cuts (verified against planted ground truth)

threshold 0: value=84, cut edges=22, match=PASS
threshold 5: value=34, cut edges=6, match=PASS
threshold 11: value=0, cut edges=0, match=PASS

## Lesion highlights (nodes, max fraction)

threshold 0, fraction 0.2: out_degree newly disconnected=36, random mean=15.1
threshold 5, fraction 0.2: out_degree newly disconnected=36, random mean=16.9
threshold 11, fraction 0.2: out_degree newly disconnected=0, random mean=0.0

## Null-model comparison

threshold 0, degree_preserving: null reach 1.000, p=1.0000
threshold 0, region_constrained: null reach 1.000, p=1.0000
threshold 5, degree_preserving: null reach 1.000, p=1.0000
threshold 5, region_constrained: null reach 1.000, p=1.0000
threshold 11, degree_preserving: null reach 0.940, p=1.0000
threshold 11, region_constrained: null reach 0.000, p=1.0000

## FDR summary

0 of 38 tests rejected at alpha 0.05.

## Package versions

- python: 3.12.3
- igraph: 1.0.0
- numpy: 1.26.4
- scipy: 1.11.4
- pandas: 2.1.4
- yaml: 6.0.1
