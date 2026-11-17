# Cover Letter — Journal Submission

[Date]

To the Editor-in-Chief,
[JOURNAL NAME — to be filled]

**Manuscript title:** Reversibility-Verified De-identification for Cloud-Local LLM Inference: A Locally Certified Dehydrate-Rehydrate Loop with Layered Assurance (DR-SL)
**Authors:** Wen Hu (NUAA; Jiangsu Yunhefeng Intelligent Technology Co., Ltd.), Ya Yu (NUAA), Xutong Wang (NUAA)
**Corresponding author:** Ya Yu, 15949116139@163.com
**Format:** IEEE journal template (IEEEtran `[journal]`), two columns, 16 pages including references and appendices (limit 20)

Dear Editor,

We submit the above manuscript for consideration as a regular research article. Cloud-local LLM inference must keep sensitive user data on-device while exploiting cloud-grade reasoning, yet existing sanitization approaches lack a release decision that is simultaneously safe and utility-preserving. The manuscript contributes: (1) a two-branch reversibility-verification framework that formalizes de-identification completeness as de-identification sufficiency under Pufferfish semantics plus task-information preservation via QA probes, decided fully locally by a terminating lexicographic loop with a runtime cascade extractor and an explicit recall-ceiling guarantee boundary; (2) a graded theoretical account — Fano-type leakage lower bounds, a Pufferfish witness, a rate-privacy feasibility criterion, and a termination theorem — together with an unusually explicit statement of scope: the bounds certify leakage and never safety, are near-vacuous at the operating point, and release safety therefore rests on empirical calibration, a deterministic hard line, and human fallback (layered assurance); (3) a fully local self-learning loop whose offline stage touches only non-sensitive corpora; and (4) a complete pre-registered experimental record (deviation log D1–D18 public) including two human studies, an executable proof-verification suite, and honestly reported negative results (the self-learning hypothesis H1 was not supported; the corrected H1′ is borderline, p = 0.059).

Headline results: on a worst-case fully task-coupled benchmark the loop reduces leakage 0.457→0.304 (p ≈ 0) and the mandatory release chain (local gate → deterministic hard line → external strong-attacker re-test) delivers 0.000 literal leakage at egress on 160 instances under two strong attackers, the system degrading to certification-and-routing exactly as the feasibility criterion predicts; on a mixed-coupling benchmark the same safe point automatically releases 67.5% of instances at zero measured leakage, Pareto-dominating placeholder and selective-LDP corners measured under an identical release rule; the semantic utility metric is human-anchored (Spearman ρ = 0.839 against a preregistered bar of 0.8) and the annotation gold is human-audited (type-level recall ≥ 0.987).

**Prior-publication and version-relationship disclosure.**
1. A preprint of this work is posted on arXiv ([arXiv:XXXX.XXXXX — insert upon assignment]); it is disclosed in the title footnote and cited where appropriate. This submission adds the peer-review-ready presentation, condensed-but-complete proofs with an executable verification appendix, and the full experimental record. The preprint was posted before this submission and before the conference submission, and therefore carries no venue markings; per standard practice the citation direction runs from this manuscript to the preprint, and the arXiv record will be updated with venue information (conference, then journal, with DOI) only upon the respective acceptances (versioning policy in `declarations.md` §6).
2. A condensed 4-page conference version of this work has been **accepted** at [CONFERENCE NAME — to be inserted] with author order Y. Yu, W. Hu, X. Wang, and will be cited in this manuscript. We disclose proactively that the author order of that version differs from this manuscript's (W. Hu, Y. Yu, X. Wang) and from preprint v1 (W. Hu first): the orders are contribution-based per manuscript — Y. Yu executed and consolidated the principal simulations and drafted the conference manuscript (hence first author there), while W. Hu led the extended theory, the full experimental record, and the writing of this journal manuscript (hence first author here); Y. Yu serves as corresponding author of this manuscript by team agreement and genuine assumption of the corresponding role. A signed per-version contribution memo documenting these bases accompanies the submission declarations. The conference version is not under review anywhere; this submission follows the conference outcome and exceeds the customary extension threshold (complete proofs, full T1–T25 record, shift framework, applicability boundary, judge rubric).
3. The manuscript is not under review by any other venue; no substantially identical version has been published in a peer-reviewed venue.

All authors approve this submission. Code, synthetic datasets, the pre-registered protocol with deviation log, and the human-study packages are public (MIT / CC-BY-4.0); all data are fully synthetic and fictional, and the only human participants were two author raters evaluating synthetic text (Ethics Statement in `declarations.md`). We thank you for your consideration.

Sincerely,
Ya Yu (corresponding author), on behalf of all authors
15949116139@163.com
