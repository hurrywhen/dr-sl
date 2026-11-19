# Cover Letter — Conference Submission (Revised)

Dear Program Committee,

We submit the revised condensed manuscript **DR-SL: A Runtime-Sensitive-Set Release Chain for Cloud-Local LLM Inference with Layered Assurance**.

The revision narrows the claim to an auditable cloud-local release workflow. It corrects earlier statistical and trust-boundary overclaims: repeated probes are not independent trials; gold annotations are not runtime inputs; online semantic judges are offline criteria; external re-testing is controlled disclosure. We remove an invalid Fano threshold corollary and keep feasibility statements in mutual-information units.

On a frozen 80-instance synthetic holdout, a fully local deterministic runtime-S track releases 57.5% under a heuristic gate, yet external gold-literal auditing finds residual exposure (mean gold hit rate 0.121) because extraction recall is 0.858. We report this negative result explicitly: local release is not zero-leakage evidence. Human-study reanalysis shows overall utility correlation rho=0.839 but lower within-group correlations, and the original combination-risk annotation criterion failed (kappa=-0.083). Self-learning is exploratory.

Code and synthetic artifacts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Declarations and author-order disclosure are in `declarations.md`.

Sincerely,
The Authors
