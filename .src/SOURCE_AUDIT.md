# Source audit for Fault Lines in a Fly Brain

Audit date: 2026-09-12

## Verified dataset facts

- The final peer-reviewed article reports 166,700 neurons and 11,710 neuron types. These values supersede the earlier preprint counts of 166,691 neurons and 11,691 types.
- The final Cell Results section states that the proofread connectome contains 124.2 million synaptic connections and defines a graph of 25.6 million edges between 166,483 neurons. Direct full text: https://www.cell.com/cell/abstract/S0092-8674(26)00942-6
- Google Research independently describes the dataset as having 125 million synaptic connections; the document treats this as a rounded public figure, not a replacement for the Cell paper's exact count.
- The final Cell article already includes sensorimotor max-flow analysis. Basic flow analysis is therefore treated as prior work, not as the proposed novelty.
- The dataset spans the male brain and ventral nerve cord and comes from one adult male specimen.
- MaleCNS v1.0 was released on June 8, 2026, according to the official project page.
- The final Cell article was published September 3, 2026.
- The project page lists public access to annotations, synapses, skeletons, images, explorers, neuPrint, and Clio.
- HHMI Janelia presents R1-R6 visual neurons to DNg13 as an example visual-to-motor pathway. The outline now describes it as a structural pathway example, not evidence of dynamic behavior.

## Verified publication status

- Berg et al., *Cell* 189(18):5504-5526.e15 (2026), DOI 10.1016/j.cell.2026.08.015: final peer-reviewed article.
- Wang-Chen et al., *Nature Methods* 21(12):2353-2362 (2024), DOI 10.1038/s41592-024-02497-y: peer reviewed.
- FlyGM, arXiv:2602.17997v3: preprint, not represented as peer reviewed.
- FLYNN, arXiv:2607.00025v1: preprint, not represented as peer reviewed.

## Corrections made in this revision

- Replaced all preprint-era counts with the final Cell counts.
- Added the final Cell volume, issue, pagination, DOI, and official Janelia publication record.
- Replaced reconstructed preprint PDF links with verified arXiv abstract URLs.
- Kept FlyGM and FLYNN labeled as non-peer-reviewed preprints.
- Reframed R1-R6 to DNg13 as Janelia's official visual-to-motor example, not proof that the connectome reproduces behavior.
- Reframed the paper question as a candidate requiring a formal novelty review rather than an established publishable gap.
- Kept the single-specimen and static-wiring limitations explicit.

## Boundary between facts and proposals

The hypotheses, pathway thresholds, 1,000-draw perturbation plan, null models, architecture choices, figures, and 12-week schedule are proposed methods. They are not findings from the MaleCNS paper. The structural connectome does not by itself provide neural dynamics, firing rates, physiology, neuromodulation, learning, consciousness, or authentic behavior.
