# Novelty Matrix: "Fault Lines in a Fly Brain"

## Mapping Structural Resilience in the Complete Male Drosophila Connectome

**Review date:** 2026-09-12
**Reviewer:** Groot (research subagent), literature research only
**Proposed contribution under review:** the first whole-CNS structural resilience and failure-point benchmark on the complete adult male Drosophila CNS connectome (MaleCNS v1.0; Berg et al., Cell 189(18), 5504-5526.e15, published September 3 2026; 166,700 neurons; 11,710 types; 124.2M synapses forming 25.6M graph edges between 166,483 neurons). Planned analyses: directed weighted graph of the full CNS; reachability and redundant routes along sensory-to-motor pathways; minimum cuts; random vs targeted (degree/betweenness) node and edge lesions with degree-matched controls; degree-preserving and region-constrained rewired null graphs; threshold, weighting, and hop-limit sensitivity; confidence intervals, permutation tests, effect sizes, false-discovery control.

**Method:** Nine query families run on 2026-09-12 via web search covering scholarly articles, preprints (arXiv, bioRxiv), publisher pages, PubMed records, and code repositories. Every included item was verified by opening a primary source (publisher full text, arXiv abstract page, PMC, PubMed, accepted-manuscript PDF, or repository README). One API fetch (Europe PMC) failed and was not retried; PubMed records were verified directly instead. Google Scholar was not queried as a separate interface; scholarly coverage came from web search plus direct publisher, PubMed, and arXiv verification. No paper, author, result, or date below is invented; where a search returned nothing, that is stated explicitly.

**Relevance labels used:**
- **Overlapping:** prior work that runs the same or essentially the same analysis, which would directly compete with the proposed contribution.
- **Adjacent:** prior work in the same territory (same dataset, same method family, or same question framed differently) that must be cited and differentiated, but does not run the proposed benchmark.
- **Unrelated:** surfaced by the searches but not relevant to the resilience question.

---

## Search log

| # | Date | Database / route | Exact primary query | Alternative queries | Hits screened / outcome |
|---|------|------------------|---------------------|---------------------|-------------------------|
| 1 | 2026-09-12 | Web search | Drosophila connectome resilience network robustness lesion analysis | "Drosophila" connectome "minimum cut" OR "targeted attack" OR "percolation" network robustness; fly brain connectome lesion simulation structural robustness hemibrain FAFB | Surfaced Zhang et al. (Fundamental Research, regional node deletions); Lin et al. (whole-brain network statistics, degree-removal); C. elegans control-theory paper; visual-system modeling paper. No whole-CNS lesion benchmark. |
| 2 | 2026-09-12 | Web search | MaleCNS Berg 2026 Cell male Drosophila connectome maximum flow sensory motor analysis | FlyGM Drosophila foundation model connectome arXiv; FLYNN Drosophila brain emulation arXiv | Surfaced news coverage of Berg et al. Cell 2026 and a MaleCNS-based demo repo (AbijahKaj/fruit-fly-brain-research, a WebGPU rate-model demo, not a paper). |
| 3 | 2026-09-12 | Web search | bioRxiv MaleCNS male connectome robustness lesion analysis preprint | "targeted attack" OR percolation fly brain connectome node removal robustness network science | Returned only human-connectome lesion studies (stroke, DTI). No fly-connectome lesion or robustness preprint found. |
| 4 | 2026-09-12 | Web search | Lin Yang Dorkenwald "network statistics" whole-brain connectome Drosophila Nature published | "2025.03.27.644751" male CNS connectome bioRxiv | Confirmed Lin et al., Nature 634, 153-165 (2024), DOI 10.1038/s41586-024-07968-y, PMID 39358527. |
| 5 | 2026-09-12 | Web search | "minimum cut" OR min-cut Drosophila connectome analysis | male CNS connectome preprint "2025.03.27.644751" | No minimum-cut analysis on any Drosophila connectome found. Surfaced the Minimum Feedback Arc Set Challenge (different objective, see item 12). |
| 6 | 2026-09-12 | Web search | targeted attack percolation Drosophila brain connectome node removal resilience | "Network structure governs Drosophila brain functionality" Zhang Fundamental Research published volume | Surfaced the mrwp-fly-brain GitHub repo (targeted attacks, percolation, configuration-model nulls on hemibrain sub-circuits; unpublished code) and extended Lin et al. removal-curve details. |
| 7 | 2026-09-12 | Web search | Shiu "Drosophila computational brain model" sensorimotor perturbation lesion inactivation | "Network structure governs Drosophila brain functionality" fmre.2025.01.017 | Confirmed Shiu et al., Nature 634, 210-219 (2024), PMID 39358519, with in silico single-neuron silencing in specific circuits. |
| 8 | 2026-09-12 | Web search | Drosophila connectome structural robustness node deletion giant component fragmentation study | Drosophila brain network "error tolerance" OR "attack tolerance" hub removal simulation | Surfaced Zhang et al. arXiv:2509.26019 (structural heterogeneity, no lesions) and further Lin et al. survival-curve detail. |
| 9 | 2026-09-12 | Web search | "Structural Heterogeneity of the Drosophila Brain Network" arXiv | (none) | Confirmed arXiv:2509.26019v1 [q-bio.NC], October 1 2025, preprint. |

**Primary sources opened and read on 2026-09-12:**
- Berg et al. Cell full text: https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6 (including full-text search for "lesion", "ablat", "robust")
- Lin et al. preprint full text (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC10402125/
- Zhang et al. accepted-manuscript PDF (author-hosted): https://fengjiawei126.github.io/uploads/FR.pdf
- FlyGM arXiv abstract: https://arxiv.org/abs/2602.17997
- FLYNN arXiv abstract: https://arxiv.org/abs/2607.00025
- NeuroMechFly v2 PubMed record: https://pubmed.ncbi.nlm.nih.gov/39533006/

---

## Per-item matrix

| # | Citation | Venue / status | Relevance | Key differentiator |
|---|----------|----------------|-----------|--------------------|
| 1 | Berg et al., "Sexual dimorphism in the complete Drosophila male central nervous system connectome," Cell 189(18), 5504-5526.e15, September 3 2026. DOI: 10.1016/j.cell.2026.08.015 | Peer-reviewed | Adjacent (with a precise technical overlap to disclose) | Same MaleCNS graph, but max-flow characterization only; no lesions, no cuts, no nulls, no robustness testing |
| 2 | Lin et al., "Network statistics of the whole-brain connectome of Drosophila," Nature 634, 153-165 (2024). DOI: 10.1038/s41586-024-07968-y. PMID: 39358527 | Peer-reviewed | Adjacent (nearest methodological neighbor) | Degree-ordered node removal on whole-brain FlyWire; no VNC, no min-cuts, no edge lesions, no null-model benchmarking, no sensory-to-motor framing |
| 3 | Zhang et al., "Network structure governs Drosophila brain functionality," Fundamental Research, accepted January 24 2025. DOI: 10.1016/j.fmre.2025.01.017 | Peer-reviewed (accepted; final volume and pages not confirmed in this review) | Adjacent | Functional/dynamical regional-lesion study on FlyWire; no structural min-cut or null-model resilience benchmark |
| 4 | Shiu et al., "A Drosophila computational brain model reveals sensorimotor processing," Nature 634, 210-219 (2024). DOI: 10.1038/s41586-024-07763-9. PMID: 39358519 | Peer-reviewed | Adjacent | Circuit-level in silico silencing for necessity/sufficiency; not a structural resilience benchmark |
| 5 | Zhang, Yang, Zhang, Qin, Luo, Lin, Lu, "Structural Heterogeneity of the Drosophila Brain Network," arXiv:2509.26019v1 [q-bio.NC], October 1 2025. DOI: 10.48550/arXiv.2509.26019 | Preprint | Adjacent | Structural/spatial heterogeneity and Kuramoto simulations on FlyWire; no lesion or robustness analysis |
| 6 | Jin et al. (FlyGM), "Whole-Brain Connectomic Graph Model Enables Whole-Body Locomotion Control in Fruit Fly," arXiv:2602.17997v3 [cs.LG], submitted February 20 2026, revised June 14 2026 | Preprint | Adjacent | Connectome as graph-neural controller for locomotion via deep RL; no lesion or robustness analysis of the connectome itself |
| 7 | Wang and Chen (FLYNN), "FLYNN: Robust Neural Network for Robot Navigation using Fly Brain Topology," arXiv:2607.00025 [cs.RO], submitted June 21 2026 | Preprint | Adjacent | "Robustness" refers to an artificial agent's tolerance to sensory loss, not structural lesion analysis of the connectome |
| 8 | Wang-Chen et al. (NeuroMechFly v2), "NeuroMechFly v2: simulating embodied sensorimotor control in adult Drosophila," Nature Methods 21(12), 2353-2362 (2024). DOI: 10.1038/s41592-024-02497-y. PMID: 39533006 | Peer-reviewed | Adjacent to unrelated | Neuromechanical simulation platform with a connectome-constrained visual network; no whole-CNS lesion or robustness benchmark |
| 9 | cosimo-radler/mrwp-fly-brain, "Drosophila Neural Circuit Robustness Analysis," GitHub repository, https://github.com/cosimo-radler/mrwp-fly-brain | Code/demo, unpublished, peer-review status unknown | Adjacent | Targeted attacks, percolation, betweenness attacks, configuration-model nulls, but only on hemibrain sub-circuits (ellipsoid body, fan-shaped body, mushroom body Kenyon cells); no publication |
| 10 | Yan et al., "Network control principles predict neuron function in the Caenorhabditis elegans connectome," Nature 2017 | Peer-reviewed | Unrelated | Different organism (C. elegans), different question (controllability); link deletion/rewiring robustness is methodologically reminiscent but not applicable |
| 11 | Lappalainen et al., "Connectome-constrained networks predict neural activity across the fly visual system," Nature 2024. DOI: 10.1038/s41586-024-07939-3 | Peer-reviewed | Unrelated | Visual-system activity prediction (45,669 neurons); no resilience question |
| 12 | Minimum Feedback Arc Set Challenge (Drosophila brain) | Algorithmic challenge, status varies by entry | Unrelated | Edge removal to eliminate cycles (direction of information flow); a different objective from resilience |

**No item above is overlapping.** No prior work runs a whole-CNS (or whole-brain) structural lesion and minimum-cut resilience benchmark with null-model comparisons on any fly connectome.

---

## Detailed notes

### 1. Berg et al., Cell 2026 (the dataset paper itself)

The final Cell full text was read in full. The Results section "Information flow from sensory to motor" reports a max-flow analysis: normalized edge weights establish information-flow capacities between nodes, max-flow values are assigned across each edge with flow constrained by the minimum capacity along a path, and pairwise sensory-to-motor flow is calculated for all neurons across all sensorimotor pairings (Figure 2C). Descending and ascending neuron types are then embedded and clustered by sensorimotor flow (Figure 2E-F).

Critically, full-text searches confirm the paper contains no lesion, ablation, or robustness experiments: "lesion" appears only inside two reference titles, "ablat" appears only inside one reference title, and "robust" appears only in the sense of drawing robust conclusions about cell-type identity.

**Precise statement of the overlap:** by the max-flow min-cut theorem, the maximum flow value between a sensory source set and a motor sink set is dual to the capacity of the minimum cut separating them. Berg et al. therefore computed quantities that are mathematically dual to cut capacities on the same MaleCNS graph, within the same sensory-to-motor framing. What they did not do: identify minimum cut *sets* as failure points, remove any nodes or edges, measure degradation of reachability or redundancy under damage, or compare against any null model. Max-flow characterization asks how much capacity exists and which neurons carry it; the proposed benchmark asks which nodes and edges are failure points and how the network degrades. The proposed paper must disclose the duality explicitly and position the cut-set identification, lesion battery, and null-model benchmarking as the new contribution.

### 2. Lin et al., Nature 2024 (strongest competing work)

This is the nearest methodological neighbor and the single strongest competing work. On the whole-brain FlyWire connectome (127,978 neurons; 2.6M thresholded connections at a 5-synapses-per-connection threshold), the authors removed neurons in degree order (2,500 per step; 1 per step for weakly connected components) and tracked the sizes of the first two strongly and weakly connected components against a random-removal-order baseline. Finding: the giant strongly connected component persists until neurons of about degree 50 begin to be removed, at which point the network splits into two components corresponding to the left and right hemispheres; the components do not split into separate networks until about 60 percent of neurons are removed. Removing neurons by smallest degree never splits the giant component. Results were qualitatively consistent for in-degree and out-degree orderings.

**Why it is adjacent, not overlapping:** (a) brain only, no ventral nerve cord and no neck connective, so no complete sensory-to-motor axis; (b) the outcome metric is component fragmentation, not sensory-to-motor reachability, redundant routes, or failure points; (c) node removal is ordered by degree only, with no betweenness targeting, no edge lesions, and no degree-matched controls; (d) the only comparator is random removal order, with no degree-preserving or region-constrained rewired null graphs; (e) no minimum cuts are identified; (f) no statistical inference framework (no confidence intervals, permutation tests, effect sizes, or false-discovery control). The proposed paper extends beyond Lin et al. on the dataset (whole CNS including VNC), the question (sensory-to-motor failure points), the methods (min-cuts, edge lesions, nulls), and the statistics. This is a real but bridgeable gap, which is why the verdict is NARROW rather than NOVEL.

### 3. Zhang et al., Fundamental Research 2025

Peer-reviewed (received November 29 2024, revised January 20 2025, accepted January 24 2025, DOI 10.1016/j.fmre.2025.01.017; the accepted-manuscript PDF dated March 21 2025 was read; final volume and pages were not confirmed). Using the FlyWire adult Drosophila connectome (nearly 130,000 neurons, 50 million synapses), the authors built a large-scale network communication model with threshold, sigmoid, and leaky integrate-and-fire dynamics, then deleted nodes inside spherical regions of varying radii (about 12,000 nodes, roughly one tenth of the network, in the largest deletions) and recorded activation response curves, concluding the network shows strong robustness to local attacks and that a sufficient reconnect rate disrupts established activation patterns.

**Why it is adjacent, not overlapping:** this is a functional/dynamical lesion study (does simulated activity survive regional damage?), not a structural graph-theoretic resilience benchmark. It has no minimum cuts, no centrality-targeted attacks, no null-model comparisons, and no sensory-to-motor failure-point framing. It must be cited as the closest *functional* lesion study on a whole-brain fly connectome.

### 4. Shiu et al., Nature 2024

A leaky integrate-and-fire computational model of the whole-brain FlyWire connectome used to study sensorimotor processing. The paper includes in silico experiments that activate sensory populations while individually silencing top responsive neurons to test necessity and sufficiency in specific circuits (gustatory and mechanosensory pathways, antennal grooming, proboscis extension), with selected experimental validation. This is circuit-level functional perturbation aimed at identifying neurons required for specific behaviors, not a structural resilience benchmark: no minimum cuts, no systematic lesion battery, no null models, no whole-CNS scope.

### 5. Zhang et al., arXiv:2509.26019 (2025)

Preprint analyzing structural and spatial heterogeneity of the FlyWire brain connectome (modular organization, community structure, bilateral symmetry, spatial clustering of somata) with Kuramoto-model simulations of hemispheric functional asymmetry. No lesion, attack, or robustness analysis. Adjacent as a structural network study on the same class of data.

### 6. FlyGM (Jin et al., arXiv:2602.17997v3)

Preprint (submitted February 20 2026, revised June 14 2026) that instantiates the whole-brain connectome of an adult Drosophila as a graph-structured neural controller for a simulated biomechanical fly, trained with deep reinforcement learning for locomotion tasks. The abstract does not name MaleCNS, and the initial submission predates the MaleCNS v1.0 release (June 8 2026). No lesion or robustness analysis of the connectome itself is reported. Adjacent as connectome-based sensorimotor work; unrelated to the resilience question.

### 7. FLYNN (Wang and Chen, arXiv:2607.00025)

Preprint (submitted June 21 2026) describing a recurrent neural network whose architecture is derived from fly brain connectome topology, trained for vision-based navigation, with reported tolerance to out-of-distribution data and total vision loss. The "robustness" claim concerns the artificial agent, not structural lesion analysis of the biological connectome. Adjacent only in the loosest sense; the word "robust" here means something entirely different from the proposed benchmark.

### 8. NeuroMechFly v2 (Wang-Chen et al., Nature Methods 2024)

Peer-reviewed neuromechanical simulation platform for embodied sensorimotor control in adult Drosophila (vision, olfaction, ascending motor feedback, complex terrain, reinforcement-learned controllers, and a connectome-constrained visual network for fly-following). No whole-CNS lesion or robustness benchmark. Adjacent to unrelated.

### 9. mrwp-fly-brain (GitHub, unpublished)

A code repository (author handle cosimo-radler) whose README describes targeted attacks, random failures, percolation analysis, betweenness-based attacks, and comparison against configuration models with preserved degree distributions, using hemibrain data for three sub-circuits: ellipsoid body, fan-shaped body, and mushroom body Kenyon cells. This is methodologically the closest in spirit (attack curves plus degree-preserving nulls), but it is unpublished code, not a paper; it covers only three hemibrain sub-circuits rather than a whole brain or whole CNS; and it has no sensory-to-motor framing and no minimum cuts. If the proposed paper proceeds, this repository should be cited as related work to preempt any claim of missed prior art.

### 10-12. Unrelated items

Listed for completeness since they surfaced in the searches: Yan et al. 2017 on C. elegans network controllability (different organism and question); Lappalainen et al. 2024 on visual-system activity prediction (no resilience question); and the Minimum Feedback Arc Set Challenge on the Drosophila brain (edge removal to eliminate cycles, a different optimization objective from resilience).

---

## Negative results (explicit)

- **No minimum-cut analysis on any Drosophila connectome was found** across all nine query families.
- **No bioRxiv-indexed fly-connectome lesion or robustness study was found**; the bioRxiv-flavored query returned only human-connectome lesion work.
- **No MaleCNS-based lesion or robustness work was found**, which is expected given the v1.0 release on June 8 2026 and the Cell paper on September 3 2026.
- **No whole-CNS (brain plus ventral nerve cord) structural resilience benchmark was found** on any dataset.

---

## Verdict: NARROW

**The exact proposed benchmark does not exist, but the novelty claim must be scoped, not stated broadly.**

Two peer-reviewed works occupy the nearest territory. Lin et al. (Nature 2024) already ran degree-ordered node removal on the whole-brain FlyWire connectome and showed the giant component survives until about 60 percent of neurons are removed. Berg et al. (Cell 2026) already characterized sensory-to-motor maximum flow on the exact same MaleCNS graph the proposal would use, and max-flow values are dual to min-cut capacities. A reviewer familiar with either paper will ask what is new. The honest, defensible answer has four parts, and the paper must claim only these:

1. **First whole-CNS scope:** brain plus ventral nerve cord with the intact neck connective, which neither Lin et al. (brain only) nor any other lesion study has analyzed. This is the only unqualified "first" available.
2. **First minimum-cut failure-point identification:** Berg et al. computed flow values but never identified cut sets as failure points; no fly-connectome study has.
3. **First systematic lesion battery with proper comparators:** random vs targeted node *and edge* lesions, degree-matched controls, and degree-preserving plus region-constrained rewired null graphs. Lin et al. used random removal order only; nobody has run the null-model comparison.
4. **First statistically rigorous benchmarking:** confidence intervals, permutation tests, effect sizes, and false-discovery control applied to fly-connectome resilience.

**Single strongest competing work:** Lin et al., "Network statistics of the whole-brain connectome of Drosophila," Nature 634, 153-165 (2024), DOI 10.1038/s41586-024-07968-y.

**Risk:** a reviewer may judge a whole-CNS extension of Lin et al.'s whole-brain degree-removal analysis as incremental unless the minimum-cut failure-point atlas and the null-model benchmarking deliver clearly new findings. **Mitigation:** lead the paper with the failure-point atlas (which specific neurons and edges are cut sets for which sensory-to-motor pathways), which is a genuinely new artifact that neither Lin et al. nor Berg et al. produced; disclose the max-flow/min-cut duality with Berg et al. proactively in the introduction rather than letting a reviewer discover it; cite Zhang et al. (functional lesions), Shiu et al. (circuit-level silencing), and the mrwp-fly-brain repository as related work. **Fallback framing if results underwhelm:** a resource paper presenting the sensory-to-motor failure-point atlas of MaleCNS, with the resilience benchmark as validation.

**Not PIVOT:** no existing work runs this benchmark, so there is no direct collision that would force abandoning the project. **Not unqualified NOVEL:** Lin et al. 2024 means a broad "first lesion analysis of the fly connectome" claim would be false.

---

## Positioning checklist for the manuscript

- Cite Berg et al. 2026 for the dataset and disclose the max-flow/min-cut duality in the introduction.
- Cite Lin et al. 2024 as the nearest prior lesion-style analysis; differentiate on CNS scope, min-cuts, edge lesions, nulls, sensory-to-motor outcomes, and statistics.
- Cite Zhang et al. 2025 as the nearest functional lesion study; differentiate on structural vs dynamical framing.
- Cite Shiu et al. 2024 for circuit-level in silico perturbation; differentiate on scope and question.
- Cite the mrwp-fly-brain repository as unpublished related work using configuration-model nulls on hemibrain sub-circuits.
- Never claim "first lesion analysis of the fly connectome" without the whole-CNS and min-cut qualifiers.
- Label FlyGM, FLYNN, and the heterogeneity preprint as preprints if cited; label NeuroMechFly v2 as peer-reviewed prior work, not a competitor.
