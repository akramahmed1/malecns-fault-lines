# MaleCNS v1.0 Data Dictionary

Working reference for the resilience paper. Every entry traces to an official source listed at the end. Anything not stated by a source is marked UNKNOWN.

## 1. Dataset identity

- Name: MaleCNS, the complete adult male Drosophila central nervous system connectome.
- Version in use: v1.0, released June 8, 2026. v0.9 was the initial release, October 5, 2025. v1.0 brought minor proofreading changes and refined neuron annotations (release notes).
- License: CC BY (release notes).
- Collaboration: FlyEM (HHMI Janelia), University of Cambridge Department of Zoology, MRC Laboratory of Molecular Biology, Google Research (project hub).
- Primary publication: Berg et al., Cell 189(18), 5504-5526.e15, published September 3, 2026. DOI 10.1016/j.cell.2026.08.015.

## 2. Scale (proofread connectome, v1.0)

- 166,700 neurons identified, proofread, and annotated, including sensory axons (Cell Results).
- 11,710 unique cell types, defined by neuron morphology and connectivity (Cell Results).
- 124.2M synaptic connections in the proofread connectome, defining 25.6M graph edges between 166,483 connected neurons; 217 neurons without synapses are disconnected (Cell Results). STAR Methods gives the more precise figure of 25.58M edges.
- Dimorphism census: 8,069 isomorphic types, 138 dimorphic types, 289 male-specific types, 71 female-specific types (Cell Summary).

## 3. Imaging and reconstruction provenance

- Imaged on 7 enhanced focused ion beam scanning electron microscopy (eFIB-SEM) systems over 13 months (Cell Results).
- 160 teravoxel image volume at 8x8x8 nm isotropic resolution, covering central brain, optic lobes, and ventral nerve cord (Cell Results).
- Automatic segmentation with flood-filling networks. 46M presynapses connected to 312M postsynapses detected, at precision/recall 0.82/0.81 (Cell Results).
- Additional extracted features: nuclei and neurotransmitter predictions (Cell Results).

## 4. Proofreading and completeness

- Proofreading effort estimated at 44 person-years (Cell Results).
- Synaptic completion rates: 94% presynaptic, 42% postsynaptic (Cell Results).
- 40.1% of synaptic connections have both pre- and postsynaptic sites belonging to a proofread neuron (Cell Results).
- 98.9% of the 141,780 detected neuron-associated nuclei are part of a proofread neuron (Cell STAR Methods).
- Orphan fragments: 5,207 remaining fragments with 100 or more synaptic partners; 84.6M orphan fragments in total, most containing very few synapses (Cell STAR Methods).

## 5. Annotation schema

Hierarchical, from coarsest to most granular (Cell Results, Figure 1F/1G):

- superclass: direction of information flow, anatomical location, broad function.
- hemilineage: developmental origin; combines the fields itoleeHl and trumanHl.
- supertype, then type (11,710 types at the most granular level).
- side: combines somaSide and rootSide.
- somaNeuromere and entry/exitNerve: spatial location.
- class and subclass: putative function.
- synonyms: names from the literature.
- Cross-dataset match fields: mancType (male VNC), flywireType (FAFB/FlyWire), hemibrainType. 97.9% of neurons have a cell type match to FAFB/FlyWire, hemibrain, and/or MANC (Cell Results).
- fruitless/doublesex expression annotated (Cell Summary).
- Neurotransmitter predictions provided as a resource (Cell Results; project landing page).
- Sensory neurons: receptor subtypes annotated. Motor neurons: exit nerve and muscle innervation annotated (Cell Results).
- Neuropil innervation per neuron is retrievable via neuprint fetch_neurons (download page).
- The malecns R package exposes metadata columns including flywireType, mancType, and itoleeHl (hemilineage per Ito/Lee 2013) (malecns README).

## 6. Graph semantics and edge-weight thresholds

- Edges are directed neuron-to-neuron connections weighted by synapse count: 124.2M synaptic connections define 25.6M edges (Cell Results).
- Noise threshold used by the authors: edges below 11 synapses in the male CNS (below 8 in FAFB/FlyWire) are labeled noisy. This removes 80% of connections, while above-threshold edges still contain 90% of all synapses (Cell STAR Methods).
- Weak-edge instability: around 60% of single-synapse connections in one hemisphere are not present in another hemisphere of the same or another brain (Cell STAR Methods).
- At a 5-synapse threshold (a cutoff sometimes used to remove weak connections), the graph shrinks to 6.24M edges between 165,536 neurons (Cell STAR Methods).
- Implication for our study: every resilience result must be reported across thresholds (for example unfiltered, >=5 synapses, >=11 synapses).
- UNKNOWN until a live query is run: the exact neuprint property names for edge weights in bulk exports.

## 7. Known caveats

- Synapse detection is automated at 0.82/0.81 precision/recall; weak edges are the least reliable (Cell Results, STAR Methods).
- 2.1% of neurons remain unmatched to other datasets, partly due to limitations of earlier partial datasets (Cell Results).
- Cell type nomenclature is not yet fully consistent across datasets; 4.6% of FlyWire types were revised using whole-CNS information (Cell Results).
- Only one individual male was imaged. The unit of analysis is the neuron, cell type, type-to-type connection, or network cluster, not the animal; animal-level statistical analysis was not possible (Cell STAR Methods).
- The connectome is a static wiring map. It does not provide firing activity, membrane dynamics, neuromodulation, learning, or behavior (standing boundary for this project).

## 8. Access

- neuPrint, dataset 'male-cns:v1.0' (public read-only snapshot). Requires a neuPrint account and API token (download page, malecns README).
- Python: neuprint-python (fetch_neurons for annotations and neuropil innervation; fetch_adjacencies for connectivity). Morphology via navis; spatial transforms between male CNS space and template spaces via flybrains (download page).
- R: neuprintr, plus the malecns wrapper (default dataset male-cns:v1.0) (download page, malecns README).
- Interactive: neuPrint and Clio (filter by type, hemilineage, etc.); Male CNS Cell Type Explorer; Dimorphism Explorer (project hub).

## 9. Sources

- Cell full text: https://www.cell.com/cell/abstract/S0092-8674(26)00942-6
- Project hub: http://male-cns.janelia.org/
- Release notes: http://male-cns.janelia.org/release/
- Download page: http://male-cns.janelia.org/download/
- malecns R package: https://github.com/flyconnectome/malecns

Compiled 2026-09-12. Update if a new release or correction appears.
