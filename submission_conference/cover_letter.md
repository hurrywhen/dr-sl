# Cover Letter — Conference Submission

> **Record note (post-acceptance).** The paper has been accepted. The final author order is **Ya Yu, Wen Hu, Xutong Wang**, decided on contribution grounds for this manuscript (Y. Yu executed and consolidated the principal simulations and drafted the text; see `declarations.md` §9 and the signed memo `../authorship_contribution_memo.md`); Y. Yu presents the paper at the conference. The letter body below is the submission-time record.

[Date]

To the Program Committee / TPC Chairs,
[CONFERENCE NAME AND YEAR — to be filled]

**Manuscript title:** DR-SL: Reversibility-Verified De-identification for Cloud-Local LLM Inference with Layered Assurance
**Authors:** Wen Hu (Nanjing University of Aeronautics and Astronautics; Jiangsu Yunhefeng Intelligent Technology Co., Ltd.), Ya Yu (NUAA), Xutong Wang (NUAA)
**Corresponding author:** Wen Hu, huwen@nuaa.edu.cn
**Format:** IEEE conference template, two columns, 4 pages including references (page limit: 4)

Dear Chairs,

We submit the above manuscript for consideration as a [regular/short] paper. The paper addresses the release-decision gap in cloud-local LLM inference: existing sanitizers (placeholder substitution, differential-privacy perturbation, skill distillation) provide no decision mechanism that is simultaneously safe and utility-preserving. We propose DR-SL, which (i) formalizes de-identification completeness as two measurable conditions (de-identification sufficiency under Pufferfish semantics; task-information preservation via QA probes) verified by a fully local, terminating lexicographic loop; (ii) proves Fano-type leakage lower bounds, a Pufferfish witness, a rate-privacy feasibility criterion, and termination, stating plainly that these bounds certify leakage and never safety; and (iii) backs the soft certificate with a deterministic hard line, an external strong-attacker re-test, and human fallback. Experiments were executed under a pre-registered protocol with a public deviation log: leakage falls 0.457→0.304 on a worst-case fully task-coupled benchmark, the mandatory release chain delivers 0.000 literal leakage at egress (160 instances, two strong attackers), and on a mixed-coupling benchmark the same safe point automatically releases 67.5% of instances at zero measured leakage, Pareto-dominating placeholder and selective-LDP corners under an identical release rule. Two human studies anchor the semantic utility metric (Spearman ρ = 0.839) and the annotation gold (type-level recall ≥ 0.987); an exploratory self-learning hypothesis was tested and not supported, and is reported as such. All code, synthetic datasets, the protocol, and the human-study packages are public.

**Prior-publication and dual-submission disclosure (required by policy).**
1. A preprint of an extended version of this work has been posted on arXiv (identifier: [arXiv:XXXX.XXXXX — insert upon assignment]; the preprint is cited in the manuscript footnote and will be cited in the camera-ready version). This submission is not a duplicate of any peer-reviewed publication. The preprint was posted before this submission and therefore carries no conference or journal markings; per standard practice the citation direction runs from this manuscript to the preprint, and the arXiv record will be updated with venue information only upon acceptance (versioning policy in `declarations.md` §6).
2. A journal version containing the full proofs, the complete experimental record (T1–T25), and extended discussion is prepared in parallel as a separate submission package. It has **not** been submitted elsewhere at the time of this submission, and will not be submitted to any journal while this manuscript is under review by your committee; any future journal submission will cite this conference paper and disclose the overlap, in accordance with standard practice for extended versions. Should the committee prefer the reverse order, we will withdraw accordingly.
3. The manuscript is not under review by any other venue at this time.

We confirm that all authors have approved the manuscript and its submission, that the reported human studies involved only author raters evaluating fully synthetic text (see the Ethics Statement in `declarations.md`), and that no real personal data were used. We are grateful for the committee's time and consideration.

Sincerely,
Wen Hu, on behalf of all authors
huwen@nuaa.edu.cn
