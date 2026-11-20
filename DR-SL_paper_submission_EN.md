# DR-SL — Revised English Manuscript Mirror (Round 2, Route A)

> Concise English mirror of the revised manuscript. The authoritative full version is `latex/main.tex` / `latex/main.pdf`. This round repositions the work as a **failure-analysis and reproducible-audit study** of local release gates, not a claim of a superior automatic sanitizer. Earlier v1 Markdown versions are historical process records.

## Title

Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain

## Abstract

Cloud-local LLM inference forwards a de-identified artifact only after a local release gate approves it. We audit whether such approval is trustworthy, studying a runtime-S release chain (deterministic extraction, truthful generalization, local attack/utility checks, all-occurrence scrubbing, human fallback). Four findings: (1) local release is misaligned with external leakage — 57.5% released on a shared-vocabulary holdout, yet 78.3% of released instances retain gold literals; under vocabulary shift, 93.75% released and every released instance leaks; (2) the closed loop gives no advantage over one-shot deterministic generalization (paired release/leakage deltas zero, local utility lower); (3) the local utility surrogate is poorly calibrated against an offline judge, and whole-set averages mask released-subgroup risk; (4) residual reports cover none of the true residual risk, because the dangerous leftovers are exactly the extractor-missed attributes. We contribute a reproducible release-audit framework with a conditional false-release metric, release/domain stratification, corrected coverage counting, calibration and residual-report analyses, and public raw outputs — not certified zero leakage or a superior method.

## Core findings (round 2, `results/revision_20261121/`)

1. **False release.** Holdout-1 closed loop: 46/80 released; 36/46 (78.3%) retain gold literals; PASS gold L 0.147 > ALL 0.121. Banking 20/20 released with 20/20 residue; legal PASS 10/10 with residue. External (audited subset) PASS FalseRelease 0.826.
2. **No loop advantage.** Paired closed−generalization: release Δ 0 [0,0], gold-L Δ 0 [0,0], U_local Δ −0.089 [−0.117,−0.061]. Online, generalization-only has the same external leakage (0.130) but higher judge utility (0.438 vs 0.363). Downstream task utility identical (0.75).
3. **Vocabulary shift.** Disjoint-vocabulary holdout-2: recall 0.858→0.526, release 57.5%→93.75%, gold L 0.121→0.453, gold FalseRelease→100%; external FalseRelease 1.0. All lexicon-dependent types recall→0.
4. **Calibration gap.** Local surrogate vs offline judge: overall ρ 0.356 [0.254,0.646], MAE 0.352 [0.265,0.448], threshold agreement 0.680 [0.565,0.790]. Closed-loop confusion TP17/FP6/FN5/TN12.
5. **Residual reports.** Report recall of true gold residue = 0 (PASS and INFEASIBLE): missed-by-extractor attributes cannot appear in runtime-S reports.
6. **Downstream task utility.** 0.75 overall (PASS 0.848 vs INFEASIBLE 0.618), higher than artifact-judge 0.363 — the artifact judge understates task utility; both are external references with error.
7. **Corrected counting.** 243 unique instance–question pairs, 36 unique question texts; round-2 holdout-1: 960 attack + 240 judge calls, 5832 question evaluations; hits are hit evaluations, not distinct leaked values.

## Key corrections vs earlier versions (see Appendix A of the paper)

Heuristic point-rate gate + instance-cluster inference (no pooled Wilson zero-hit bound); runtime-S/oracle-S separated; online judges offline-only; Fano threshold corollary removed (counterexample test), |V_i|=1 handled; MI-unit feasibility; finite-budget termination; controlled-disclosure framing; consistent all-occurrence PRISM-style random baseline (not LDP); deterministic stability window simplified to N=1 (verified identical to N=3 on 400 pairs); "supported"→"evaluated" components; title drops "Reversibility-Verified".

## Reproduction

See `README.md`, `revision_protocol.md`, `revision_protocol_v2.md`, and `sim/revision_experiment.py` / `revision_online_audit.py` / `revision_downstream.py` / `revision_stratified.py`. Holdout human-utility packet prepared but not collected.
