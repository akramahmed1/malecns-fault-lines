# Fault Lines pipeline: REAL MaleCNS v1.0 run summary

REAL DATA: male-cns:v1.0 from neuprint.janelia.org. Not synthetic.

Config hash: `e78136c8b96c6a9ab7bb68381174daf414ee739b5d5b9e0c1472dd6c8fe747be`
Timestamp (UTC): 2026-09-13T06:00:26.086457+00:00
Elapsed: 1056.0 s

## Graph scale per threshold

| threshold | nodes | edges | largest weak comp | sensory in-graph | motor in-graph | reachability |
|---|---|---|---|---|---|---|
| 5 | 173023 | 6287749 | 172872 | 26972 | 2232 | 59795264/60201504 (0.9933) |
| 11 | 173023 | 2446815 | 166366 | 26972 | 2232 | 55738955/60201504 (0.9259) |

## Minimum s-t cuts (sensory to motor)

threshold 5: value=4321207, cut edges=267027
threshold 11: value=3248164, cut edges=117267

## Lesion highlights (nodes, max fraction)

threshold 5, fraction 0.2, out_degree: newly disconnected=34808168, random mean=21719660.9
threshold 5, fraction 0.2, betweenness_approx: newly disconnected=37378367, random mean=21719660.9
threshold 5, fraction 0.2, mincut_membership: newly disconnected=56019030, random mean=21719660.9
threshold 11, fraction 0.2, out_degree: newly disconnected=49300676, random mean=20785323.9
threshold 11, fraction 0.2, betweenness_approx: newly disconnected=53768009, random mean=20785323.9
threshold 11, fraction 0.2, mincut_membership: newly disconnected=55738955, random mean=20785323.9

## Null-model comparison

threshold 5, degree_preserving: null reach 0.9936, p=1.0000
threshold 5, region_constrained: null reach 0.9937, p=1.0000
threshold 11, degree_preserving: null reach 0.9269, p=1.0000
threshold 11, region_constrained: null reach 0.9272, p=1.0000

## FDR summary

0 of 24 tests rejected at alpha 0.05.

## Package versions

- python: 3.12.3
- igraph: 1.0.0
- numpy: 1.26.4
- scipy: 1.11.4
- pandas: 2.1.4
- yaml: 6.0.1
