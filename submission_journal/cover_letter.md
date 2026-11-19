# Cover Letter — Journal Submission (Revised)

Dear Editor,

We submit the revised manuscript **Reversibility-Verified De-identification for Cloud-Local LLM Inference: A Runtime-Sensitive-Set Release Chain with Layered Assurance (DR-SL)**.

This revision responds to a major-revision review by narrowing the claim and correcting the evidence chain. The manuscript no longer claims statistical zero leakage, fully local automatic release based on an online judge, or that self-learning is the source of the final safe operating point. Specific changes:

1. Repeated probe bundles are no longer treated as independent Bernoulli trials; the release gate is a heuristic observed-hit-rate gate, and attack summaries use instance-cluster bootstrap.
2. Runtime-S and oracle-S are separated. Gold annotations are used only by external scoring after artifacts and local decisions are frozen.
3. Online reference-based semantic judges are offline criteria only; local release uses a fully local utility surrogate.
4. The invalid Fano threshold corollary is removed; feasibility statements remain in mutual-information units; termination is proved from finite budgets.
5. External re-testing is reclassified as controlled-disclosure audit, not pre-egress prevention.
6. The random baseline is fixed to replace all occurrences consistently and is renamed PRISM-style random replacement, not LDP. An INTACT-inspired candidate-selection baseline and deterministic ablations are added.
7. A frozen independent-template holdout (80 synthetic instances) is evaluated. The deterministic runtime-S track releases 57.5% locally, but external gold-literal auditing finds residual exposure (mean gold hit rate 0.121) due to extraction recall 0.858. This negative result is central.
8. Human-study reanalysis reports within-group correlations, instance-cluster intervals, MAE, threshold confusion, and the failed original combination-risk criterion (kappa=-0.083). The construct-aligned kappa=0.696 is labelled post hoc.

The supported contribution is an auditable cloud-local release workflow and failure-mode account. Code, synthetic datasets, frozen protocol, raw audit outputs, and analysis scripts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl.

Author order, conflict-of-interest, funding, ethics, and prior-version disclosures are provided in `declarations.md` and `../authorship_contribution_memo.md`. Funding/ethics/venue fields requiring author confirmation are explicitly marked.

Sincerely,
The Authors
