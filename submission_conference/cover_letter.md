# Cover Letter — Conference Submission (Revised, Round 6)

Dear Program Committee,

We submit the revised condensed manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This is a failure-analysis and reproducible-audit case study, not a claim of a superior automatic sanitizer. The closed loop is an audited object; conclusions are scoped to the audited implementation and author-constructed synthetic tests, not other gates or real deployments.

The three core findings are unchanged: (1) missed extraction causes false release—57.5% of holdout-1 is released and 78.3% of released instances (Wilson [64.4,87.7]) retain gold-annotated literals, an audit proxy rather than demonstrated privacy harm; (2) unmarked-context fallback rewards missed extraction—65% of releases pass through harmful fallback and all have gold-literal residue; coverage gating leaves only 0/5 observed false releases (Wilson upper bound 43.4%), too few to validate safety; (3) the closed loop has no detectable benefit over one-shot deterministic generalization—paired release/leakage differences are zero on three holdouts, local utility is lower on all three, and downstream reference-answer preservation shows no detectable mean difference under either judge.

Round 6 makes four corrections without new model calls or changes to primary FR values:

1. **Zero-charge mechanism.** GLM did propose and scrub the extended `0元手续费` span; the short `0元` repeated in the clarification remained. The three cases are span-variant/repeated-mention residues (`gold_substring_of_proposal`), not “never proposed.” A symmetric five-way classifier and regression tests now pin this behavior.
2. **Holdout-4 evidence.** Complete-taxonomy `FR_gap=0/32` is a definitional identity, not a safety improvement. The direct evidence is 10/10 exact type-and-value extraction and zero released residue for each of room number, marriage duration and work tenure. Total FR is 1/32, so within-taxonomy residue persists.
3. **City explanation.** The repeated county literal may reflect value/template-specific omission or a city/county/address type boundary; the current experiments do not distinguish these explanations. City values are 59/60 exact by value and 54/60 with a city label.
4. **Construct scope.** Gold-literal residue is not equated with confirmed privacy damage. Zero-valued charges are conservative personal-financial/task annotations, not claims of stand-alone identifiability. Excluding them changes only GLM-subset FR (5/25→2/25, both taxonomy gaps); all main deterministic and other neural counts are unchanged.

The second-family conclusion is accordingly limited to similar inheritance with different miss/span identity, not identical failures across models. All neural conditions remain cloud-assisted diagnostic contrasts (extraction itself discloses X), not deployable local gates. Third-party corpora, local neural execution, holdout human scoring and non-literal attacks remain disclosed future work.

Code, synthetic data, protocols v1–v6, deviation log D-R1–D-R34, byte-intact raw neural archives and the new archived-output analysis are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Declarations and author-order disclosure are in `declarations.md`. The current draft is 4 pages; the venue page limit and acceptance status are to be confirmed.

Sincerely,
The Authors
