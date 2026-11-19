# DR-SL — Revised English Manuscript Mirror

> This file is a concise English mirror of the revised manuscript. The authoritative full version is `latex/main.tex` / `latex/main.pdf`. Earlier v1 Markdown versions are historical process records and do not represent the current claims.

## Abstract

Cloud-local LLM inference must keep sensitive data on-device while using cloud reasoning. We revise DR-SL as an auditable release chain combining runtime sensitive-set extraction, truthful generalization, local attack/utility checks, deterministic all-occurrence scrubbing, and human fallback. Repeated probe copies are not independent trials; gold annotations are not runtime inputs; online semantic judges are offline criteria; external re-testing is controlled disclosure, not pre-egress prevention. We remove an invalid Fano threshold corollary, keep feasibility statements in mutual-information units, and implement the declared stability window.

On a frozen 80-instance synthetic holdout, a local deterministic runtime-S track releases 57.5% under a heuristic gate, but external gold-literal auditing finds residual exposure (mean gold hit rate 0.121) because extraction recall is 0.858. A controlled-disclosure LLM audit on 40 instances confirms residual hits (external max hit rate 0.130) and low semantic utility (0.363); the local utility surrogate correlates weakly with the offline judge (rho=0.326). Local release is not zero-leakage evidence. Oracle-S experiments are upper-bound references.

Human-study reanalysis shows overall utility correlation rho=0.839 but lower within-group correlations, and the original combination-risk annotation criterion failed (kappa=-0.083); construct-aligned kappa=0.696 is post hoc. Self-learning remains exploratory. The contribution is an auditable workflow and failure-mode account, not certified zero leakage or full automation.

## Key corrections

1. **Statistics.** Heuristic observed-hit-rate gate; instance-cluster bootstrap; no pooled Wilson zero-hit guarantee.
2. **Runtime-S.** Policy functions receive extractor output only; gold is external scoring only.
3. **Local utility.** Online reference-based judges are offline criteria; local release uses a local surrogate.
4. **Theory.** Fano bound at actual MAP success; no threshold corollary; MI-unit feasibility; finite-budget termination.
5. **Trust boundary.** External re-test is controlled disclosure, not pre-egress prevention.
6. **Baselines.** Consistent all-occurrence random replacement (PRISM-style, not LDP); INTACT-inspired candidate selection; deterministic ablations.
7. **Human studies.** Within-group correlations, cluster CIs, MAE, threshold confusion; failed original annotation criterion reported.

## Reproduction

See `README.md`, `revision_protocol.md`, and `sim/revision_experiment.py` / `sim/revision_online_audit.py`.
