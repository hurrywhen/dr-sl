# Declarations and Disclosure Statements — IEEE ISAICS 2026 (Accepted Version)

Manuscript: **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**
Authors: Ya Yu, Wen Hu, Xutong Wang

> **Positioning note (submission-final).** This condensed manuscript is a failure-analysis and reproducible-audit study of a runtime-S release chain, not a claim of a superior automatic sanitizer. The closed loop is an audited object; the title no longer uses "Reversibility-Verified". The audited artifact retains the legacy repository name DR-SL; self-learning is exploratory and excluded from the confirmatory release path. **All conclusions are scoped to the audited implementation and the author-constructed synthetic tests, not to other gates or real deployments.** Round 3 corrected the tied-rank Spearman error and reran the contaminated downstream experiment (invalid outputs archived). Round 4 corrected two paired-difference direction errors, reported both judges in full (2/40 vs 8/40), scoped zero-event claims (0/5 and 0/46 with Wilson upper bounds), and renamed the fallback to unmarked-context retention. Round 5 corrects the neural contrast's interpretation: three omitted gold types (automatic coverage test); FR decomposed into taxonomy-coverage gaps (all of h1/drift-p0, room number) vs within-taxonomy neural misses (h3, city); direction-specific bound scoping (recall conservative; FR conditional, no bound direction); income misses are partial-span extraction with three coverage layers. Pre-registered checks add stability repeats (identical release/FR sets across three qwen runs on a 60-instance subset), a second family (glm-5.2; different miss identity), and a complete-taxonomy holdout-4 contrast. Round 6 corrects GLM's zero-charge mechanism to an extended proposed/scrubbed fee span plus a short repeated-form residue; FR_gap=0 on h4 is definitional, while each added type is exactly extracted 10/10 with no released residue. City/county causation remains unresolved, and gold-literal residue is an audit proxy rather than demonstrated privacy harm; zero-charge exclusion changes only GLM FR (5/25→2/25). All neural conditions are cloud-assisted and diagnostic only (extraction discloses X); none is a deployable local gate. The venue is IEEE ISAICS 2026 and acceptance is confirmed; proceedings DOI/pages remain pending.

## 1. Author contributions (CRediT) — conference manuscript (author order: Ya Yu, Wen Hu, Xutong Wang)

- **Ya Yu (first author):** investigation (executed and consolidated the principal simulation experiments of this manuscript), software (experiment-pipeline runs and stage orchestration), validation, writing — original draft (conference manuscript), camera-ready preparation and the authors' recorded conference presentation role.
- **Wen Hu:** conceptualization, methodology, formal analysis, software (core verification loop, extractor, and proofs), supervision, writing — review & editing.
- **Xutong Wang:** validation (human-study rater/annotator), data curation, writing — review & editing.

Author order of this manuscript reflects the contributions listed above, as recorded in the per-version memo `../authorship_contribution_memo.md` (signatures pending); it differs from the author order of the journal version and of preprint v1 for the contribution-based reasons documented there and disclosed to the journal.

The contributions above are intended to satisfy the ICMJE authorship criteria (substantial contributions; drafting or critical revision; final approval; accountability). Final approval of this submission-final text and the required author signatures remain author-confirmation items.

## 2. Conflict of interest

Wen Hu holds a position at Jiangsu Yunhefeng Intelligent Technology Co., Ltd. (second affiliation); the public artifact repository is hosted on that company's Gitee organization. No author reports financial interests, patents, or commercial products whose value could be affected by the results of this work. The remaining authors declare no conflicts. [To be re-confirmed and signed by all authors before submission.]

## 3. Funding

[To be completed: grant numbers or "This research received no external funding."]

## 4. Data and code availability

All artifacts are public at https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl and https://github.com/hurrywhen/dr-sl : simulation pipeline and test suite (MIT), fully synthetic datasets including the development sets, the shared-vocabulary holdout-1, the constructive disjoint-vocabulary holdout-2, the natural-mix holdout-3, the taxonomy-validation holdout-4 and the vocabulary dose–response series (CC-BY-4.0), the pre-registered experimental protocols (v1–v6) with the complete deviation log (D1–D18 and D-R1–D-R35), the human-study package (scoring sheets, annotation sheets, analysis scripts, and a prepared-but-not-collected holdout utility packet), the controlled-disclosure raw audit outputs and freeze manifests (including the explicitly invalidated round-2 downstream archive, the byte-intact round-4 neural archive, the round-5 stability/second-family/holdout-4 raw responses, and the round-6 archived-output reanalysis), and the proof-verification suite. All sensitive values in all datasets are synthetic and fictional; no real personal data are included. MedQA-derived consultation stems are used under the MIT license (Jin et al., Appl. Sci. 11(14):6421, 2021) with every concrete value replaced by synthetic values.

## 5. Ethics statement

- **Human studies.** Two studies were conducted (semantic-utility scoring, 160 blinded development rows; annotation audit, 50 instances). The only human participants were co-authors Y. Yu and X. Wang, acting as expert raters/annotators; they participated voluntarily, were blinded to variant identities and automatic scores during scoring, and are co-authors aware of the use of their judgments. No third-party human subjects, no crowdsourced workers, and no personal or clinical data were involved; all evaluated text is fully synthetic. A blinded holdout utility packet is prepared but **not yet collected**; no synthetic "human" scores were invented. Under [INSTITUTION] policy such non-subject, synthetic-material evaluation is exempt from IRB review; [confirm exemption wording/number with the institution before submission].
- **Data.** No real personally identifiable information was collected, used, or released. Synthetic populations use placeholder marginals (documented; to be replaced by public statistics in future work).
- **Dual-use.** The attack/verification methodology is defensive (release gating); potential misuse is limited by design (all decisions local, artifacts synthetic).

## 6. Prior publication, preprint, and version-relationship disclosure

1. **Preprint.** The earlier preprint is **arXiv:2609.14883v1** (https://arxiv.org/abs/2609.14883), submitted 2026-09-14 with a different title and earlier claims. It is disclosed in the accepted manuscript's first-page publication note. The current submission-final text is not represented as the already-posted v1; any arXiv update is a separate author action.
2. **Acceptance and relationship to the journal version.** This condensed conference version is **accepted to IEEE ISAICS 2026**. Proceedings DOI/pages remain to be inserted when supplied. A journal-length version (full proofs, complete experimental record T1–T25, extended related work and discussion) exists as a separate prepared package (`../submission_journal/`) and is **not under review anywhere** in this record. Any journal submission will cite the conference paper and describe the extension explicitly (complete proofs, the full T1–T25 experimental record, distribution-shift framework and applicability-boundary analysis); overlapping simultaneous review is not represented or planned.
3. **No duplicate submission.** This manuscript is not under review by any other venue, and no substantially identical paper has been published in a peer-reviewed venue.
4. **Use of the public artifact repository.** Reviewers may consult the public repository; anonymity requirements of the venue (if double-blind) are respected: the repository is public prior to submission and is cited as a public artifact, and the manuscript footnote states its URL as required for reproducibility. [If the venue is double-blind and forbids identifiable links, remove/anonymous-proxy the URL in the review copy and restore it in the camera-ready.]
5. **Preprint versioning policy.** The online arXiv record remains v1 at reconciliation and carries no conference marking. Now that the conference version is accepted, an author may prepare arXiv v2 with a comment such as: "A condensed version of this work was accepted to IEEE ISAICS 2026; the preprint record contains the earlier extended version." Add proceedings DOI/pages only when assigned and follow publisher policy. A future journal update should likewise cite the final journal reference only after acceptance/publication. **No arXiv upload has been performed or claimed by this repository revision.**

## 7. Use of AI/LLM tools in manuscript preparation

Large language models appear in this work **as the object of study** (local evaluators, attackers, judges, and the cloud models under test). AI-based coding/writing assistants also supported language revision, code/analysis assistance and consistency checks during manuscript revisions. The authors remain responsible for verifying the scientific content and final text. **[Exact venue-specific disclosure scope and wording to be confirmed and signed by all authors; do not replace this with a claim that no generative AI was used.]** LLM tools do not qualify as authors.

## 8. Compliance checklist

- [x] Insert arXiv:2609.14883 in the manuscript's first-page publication note and this document.
- [x] Identify the accepted venue as IEEE ISAICS 2026 in the cover note and declarations.
- [ ] Insert proceedings DOI/pages when assigned; confirm the final camera-ready page limit (current condensed draft 4 pages).
- [ ] Confirm funding statement.
- [ ] Confirm IRB-exemption wording with institution.
- [ ] All authors sign COI and contribution statements.
- [ ] Verify venue policy on double-blind links and on preprints.

## 9. Author order and camera-ready plan (accepted version)

- **Final author order: Ya Yu, Wen Hu, Xutong Wang.** Basis: for this manuscript Y. Yu executed and consolidated the principal simulation experiments and drafted/organized the text (first-author-level contribution), W. Hu provided the conceptualization, method, proofs, and supervision, and X. Wang contributed validation and curation. The order decision is contribution-based per manuscript and is recorded in `../authorship_contribution_memo.md` (signatures pending); it is independent of conference-attendance arrangements (Y. Yu's presentation of the paper is a consequence of her authorship, not its basis).
- **Camera-ready corrections:** the human-study sentence now names the raters explicitly ("Y. Yu and X. Wang") instead of positional wording, since positional wording changed meaning with the order; author block and e-mail order updated accordingly.
- **Cross-version consistency:** preprint v1 and the journal version list W. Hu first; the difference is contribution-based per manuscript and is disclosed to the journal (see `../submission_journal/declarations.md` and its cover letter). For conference publication, an author may prepare arXiv v2 with the Comments-field note in §6(5); uploading remains a separate author action.
