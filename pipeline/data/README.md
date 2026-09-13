# Raw data tables (gzip-compressed)

Source: MaleCNS v1.0, `neuprint.janelia.org`, dataset `male-cns:v1.0`
(released 2026-06-08, CC BY). Paper: Berg et al., Cell 189(18), 2026,
doi:10.1016/j.cell.2026.08.015.

| file | contents | uncompressed | sha256 (uncompressed) |
|---|---|---|---|
| `edges_w5.csv.gz` | directed edges, weight >= 5 (6,287,789 rows) | 98 MB | `60b4adb6f3b9f96a290e192f23e2822ea3ab96020edef5ed6cd5ff354cd40182` |
| `edges_w0.csv.gz` (2 parts) | directed edges, weight >= 1 (25,862,574 rows) | 394 MB | `440a096c8110c25b9bc0153c6925112924edd86bac5c999d1701795e95d6702e` |
| `neurons.csv.gz` | neuron metadata (176,422 rows) | 9.3 MB | `41b08d255e7a41747af40a5559b139db7efeefb21096cd8285c44c19915e7681` |

`edges_w0.csv.gz` exceeds GitHub's 100 MB file limit, so it is stored as five
split parts. Reassemble before use:

```bash
cat edges_w0.csv.gz.part-* > edges_w0.csv.gz
gunzip edges_w0.csv.gz edges_w5.csv.gz neurons.csv.gz
sha256sum edges_w0.csv edges_w5.csv neurons.csv   # compare with table above
```

Edge weight property in neuPrint is `c.weight`. The battery drops self-loops
(40 at threshold 5, 11 at threshold 11) before building graphs.
