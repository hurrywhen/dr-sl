# Cover Note — IEEE ISAICS 2026 (Accepted Version)

Dear IEEE ISAICS 2026 Program Committee,

This repository package records the submission-final version of the accepted condensed manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

The manuscript is a failure-analysis and reproducible-audit case study, not a claim of a superior automatic sanitizer. Its conclusions remain scoped to the audited implementation and author-constructed synthetic tests. The three core findings are unchanged: (1) missed extraction causes false release under the stated metric—57.5% of holdout-1 is released and 78.3% of released instances retain gold-annotated literals, an audit proxy rather than demonstrated privacy harm; (2) unmarked-context fallback rewards missed extraction, with 65% of releases passing through harmful fallback and all having gold-literal residue; and (3) the closed loop shows no detectable benefit over one-shot deterministic generalization, including zero paired release-rate and gold-residue differences on three holdouts and lower local utility.

Submission-final editing makes no new model calls, changes no data or results, and performs four limited corrections: the abstract now states that full-displacement residue comes only from undeclared `room_no` (the other two omitted types caused no released residue); core text distinguishes gold-literal residue from external attack hits and actual privacy harm; dramatic wording is removed; and the conference layout retains four core tables, with domain and dose–response values reported in prose to avoid a floats-only page. Detailed stability, second-family and holdout-4 evidence remains in the public archive rather than being expanded in the paper.

**Preprint and authorship disclosure.** The earlier preprint is **arXiv:2609.14883v1** (https://arxiv.org/abs/2609.14883), submitted 2026-09-14 under a different title and with earlier claims. It is not represented as the current submission-final text. The conference author order is **Ya Yu, Wen Hu, Xutong Wang**; the prepared journal version uses **Wen Hu, Ya Yu, Xutong Wang**, with Ya Yu as corresponding author. The contribution-based reason for this difference is recorded in `../authorship_contribution_memo.md` and `declarations.md`; signatures remain pending.

Proceedings DOI/pages will be inserted when assigned. Funding, institution-specific ethics wording, conflict-of-interest signatures and final AI-assistance disclosure remain author-confirmation items, as listed in `declarations.md` and `../SUBMISSION_STATUS.md`. No arXiv update is claimed by this repository revision.

Sincerely,
The Authors
