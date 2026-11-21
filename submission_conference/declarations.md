# Declarations and Disclosure Statements — Conference Submission

Manuscript: **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**
Authors: Wen Hu, Ya Yu, Xutong Wang

> **Positioning note (round 3).** This condensed manuscript is a failure-analysis and reproducible-audit study of a runtime-S release chain, not a claim of a superior automatic sanitizer. The closed loop is an audited object; the title no longer uses "Reversibility-Verified". The audited artifact retains the legacy repository name DR-SL; self-learning is exploratory and excluded from the confirmatory release path. **All conclusions are scoped to the audited implementation and the author-constructed synthetic tests, not to other gates or real deployments.** Round 3 corrects the tied-rank Spearman error, reruns the contaminated downstream experiment (invalid outputs archived), and adds the utility-fallback mechanism, fixed-extractor contrast on holdout-3, dose–response series, two-type residual probe, and open-ended attack. The venue and acceptance status are to be confirmed before submission.

## 1. Author contributions (CRediT) — conference manuscript (author order: Ya Yu, Wen Hu, Xutong Wang)

- **Ya Yu (first author):** investigation (executed and consolidated the principal simulation experiments of this manuscript), software (experiment-pipeline runs and stage orchestration), validation, writing — original draft (conference manuscript), presentation of the paper at the conference.
- **Wen Hu:** conceptualization, methodology, formal analysis, software (core verification loop, extractor, and proofs), supervision, writing — review & editing.
- **Xutong Wang:** validation (human-study rater/annotator), data curation, writing — review & editing.

Author order of this manuscript reflects the contributions listed above, as recorded in the signed per-version memo `../authorship_contribution_memo.md`; it differs from the author order of the journal version and of preprint v1 for the contribution-based reasons documented there and disclosed to the journal.

All authors meet the ICMJE authorship criteria (substantial contributions; drafting or critical revision; final approval; accountability for the work). All authors have approved this version and its submission.

## 2. Conflict of interest

Wen Hu holds a position at Jiangsu Yunhefeng Intelligent Technology Co., Ltd. (second affiliation); the public artifact repository is hosted on that company's Gitee organization. No author reports financial interests, patents, or commercial products whose value could be affected by the results of this work. The remaining authors declare no conflicts. [To be re-confirmed and signed by all authors before submission.]

## 3. Funding

[To be completed: grant numbers or "This research received no external funding."]

## 4. Data and code availability

All artifacts are public at https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl and https://github.com/hurrywhen/dr-sl : simulation pipeline and test suite (MIT), fully synthetic datasets including the development sets, the shared-vocabulary holdout-1, the constructive disjoint-vocabulary holdout-2, the natural-mix holdout-3 and the vocabulary dose–response series (CC-BY-4.0), the pre-registered experimental protocols (v1–v3) with the complete deviation log (D1–D18 and D-R1–D-R17), the human-study package (scoring sheets, annotation sheets, analysis scripts, and a prepared-but-not-collected holdout utility packet), the controlled-disclosure raw audit outputs and freeze manifests (including the explicitly invalidated round-2 downstream archive), and the proof-verification suite. All sensitive values in all datasets are synthetic and fictional; no real personal data are included. MedQA-derived consultation stems are used under the MIT license (Jin et al., Appl. Sci. 11(14):6421, 2021) with every concrete value replaced by synthetic values.

## 5. Ethics statement

- **Human studies.** Two studies were conducted (semantic-utility scoring, 160 blinded development rows; annotation audit, 50 instances). The only human participants were co-authors Y. Yu and X. Wang, acting as expert raters/annotators; they participated voluntarily, were blinded to variant identities and automatic scores during scoring, and are co-authors aware of the use of their judgments. No third-party human subjects, no crowdsourced workers, and no personal or clinical data were involved; all evaluated text is fully synthetic. A blinded holdout utility packet is prepared but **not yet collected**; no synthetic "human" scores were invented. Under [INSTITUTION] policy such non-subject, synthetic-material evaluation is exempt from IRB review; [confirm exemption wording/number with the institution before submission].
- **Data.** No real personally identifiable information was collected, used, or released. Synthetic populations use placeholder marginals (documented; to be replaced by public statistics in future work).
- **Dual-use.** The attack/verification methodology is defensive (release gating); potential misuse is limited by design (all decisions local, artifacts synthetic).

## 6. Prior publication, preprint, and version-relationship disclosure

1. **Preprint.** An extended preprint of this work is posted on arXiv ([arXiv:XXXX.XXXXX — insert identifier upon assignment]); it is disclosed in the manuscript title footnote and will be cited in the camera-ready version. Posting a preprint does not constitute prior publication under the venue's policy; we disclose it here for transparency.
2. **Relationship to the journal version.** A journal-length version (full proofs, complete experimental record T1–T25, extended related work and discussion) exists as a separate submission package (`../submission_journal/`). At the time of this submission the journal version is **not** under review anywhere. We will not hold this manuscript and the journal manuscript under simultaneous peer review; the journal submission will be made only after this conference paper's outcome is known, will cite this paper, and will describe the extension explicitly (standard conference-to-journal extension practice, ≥30% additional material: complete proofs, the full T1–T25 experimental record, distribution-shift framework, applicability-boundary analysis).
3. **No duplicate submission.** This manuscript is not under review by any other venue, and no substantially identical paper has been published in a peer-reviewed venue.
4. **Use of the public artifact repository.** Reviewers may consult the public repository; anonymity requirements of the venue (if double-blind) are respected: the repository is public prior to submission and is cited as a public artifact, and the manuscript footnote states its URL as required for reproducibility. [If the venue is double-blind and forbids identifiable links, remove/anonymous-proxy the URL in the review copy and restore it in the camera-ready.]
5. **Preprint versioning policy (preprint posted first, carries no venue markings).** The arXiv record (v1) predates this submission and, by construction, contains no conference/journal markings; this is the correct chronological order and requires no retroactive change at submission time. The citation direction runs from this manuscript to the preprint (title footnote; camera-ready bibliography). The arXiv record will be updated only upon acceptance, as follows:
   - *On acceptance of this conference paper* — upload arXiv v2 with Comments field: "v2: a condensed version of this work appears in Proc. [CONFERENCE NAME, YEAR]; this preprint remains the extended technical version. v1: original preprint." and, if the camera-ready permits, a first-page footnote with the same content plus the DOI/URL of the proceedings article.
   - *On acceptance of the journal version* — upload arXiv v3 with Comments field: "v3: this work has been published in [JOURNAL NAME], vol. X, no. Y, pp. Z, [YEAR], doi:[DOI]; please cite the journal version." and add the journal reference/DOI to the preprint's first page.
   Until acceptance, no venue is named on the preprint, and no version under peer review is posted.

## 7. Use of AI/LLM tools in manuscript preparation

Large language models appear in this work **as the object of study** (local evaluators, attackers, judges, and the cloud models under test). [Statement on AI writing assistance to be confirmed by the authors before submission, e.g., "No generative AI tool was used to draft the scientific content; language editing tools, if any, are listed here."] LLM tools do not qualify as authors.

## 8. Compliance checklist

- [ ] Insert arXiv identifier in manuscript footnote and this document.
- [ ] Insert conference name/year in cover letter; confirm page limit (current condensed draft 3 pages).
- [ ] Confirm funding statement.
- [ ] Confirm IRB-exemption wording with institution.
- [ ] All authors sign COI and contribution statements.
- [ ] Verify venue policy on double-blind links and on preprints.

## 9. Author order and camera-ready plan (upon acceptance)

- **Intended final author order: Ya Yu, Wen Hu, Xutong Wang.** Basis: for this manuscript Y. Yu executed and consolidated the principal simulation experiments and drafted/organized the text (first-author-level contribution), W. Hu provided the conceptualization, method, proofs, and supervision, and X. Wang contributed validation and curation. The order decision is contribution-based per manuscript and is recorded in the signed memo `../authorship_contribution_memo.md`; it is independent of conference-attendance arrangements (Y. Yu's presentation of the paper is a consequence of her authorship, not its basis).
- **Camera-ready corrections:** the human-study sentence now names the raters explicitly ("Y. Yu and X. Wang") instead of positional wording, since positional wording changed meaning with the order; author block and e-mail order updated accordingly.
- **Cross-version consistency:** preprint v1 and the journal version list W. Hu first; the difference is contribution-based per manuscript and is disclosed to the journal (see `../submission_journal/declarations.md` and its cover letter). Upon conference publication, upload arXiv v2 with the Comments-field note in §6(5).
