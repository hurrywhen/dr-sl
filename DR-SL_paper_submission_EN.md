# DR-SL — Revised English Manuscript Mirror (Round 3, Route A)

> Concise English mirror of the revised manuscript. The authoritative full version is `latex/main.tex` / `latex/main.pdf` (15 pages). This work is a **failure-analysis and reproducible-audit study** of local release gates. **All conclusions are scoped to the audited implementation and author-constructed synthetic tests; they do not estimate failure rates of other gates or real deployments.** Earlier Markdown versions are historical process records.

## Title

Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain

## Three core findings

1. **Missed extraction → false release.** Holdout-1 (shared vocabulary): 46/80 released; 36/46 (78.3%, Wilson [64.4,87.7]) retain gold literals; PASS gold L 0.147 > ALL 0.121. Banking 20/20 released with 20/20 residue ([83.9,100]); legal PASS 10/10 with residue ([72.2,100]). External FR_LLM|PASS 0.826 (19/23, [62.9,93.0]).
2. **Utility gate rewards unknown task coverage (perverse incentive).** Task-relevant recall 0.493 vs attribute recall 0.858; 37.5% harmful context fallback; 30/46 releases (65%) via harmful fallback, ALL leaking (FR 1.000 vs 0.375 other releases). Coverage gate (UNSCORABLE→human): h1 release 57.5%→6.2%, FR→0; h2 release 93.8%→37.5%, FR still 1.0 (partial coverage blind). A routing policy with real cost, not a certificate.
3. **No closed-loop increment.** Paired release/gold-L deltas 0[0,0] on three holdouts; local-utility delta varies (h1 −0.089[−0.117,−0.061], h2 −0.017, h3 +0.101); online GEN equal leakage, higher judge utility (0.438 vs 0.362); downstream preservation paired Δ −0.025[−0.062,0.000], 2/40 disagree, 23/40 identical artifacts — no detectable mean difference, not equivalence.

## Supporting analyses (round 3)

- **Bugs vs architecture.** Fixed extractor (clear defects only: money pattern wiring, ASCII email local part, allergy label/collision; no lexicon additions; original frozen, hash-verified). Diagnostic h1: recall→1.000, FR 78.3%→0, decisions unchanged 80/80, over-extraction 0.300→0.188. Diagnostic h2: recall 0.668, FR still 1.0. Confirmatory h3 (natural 50/50 mix, seed 20261122, template family #3, realized old fraction 0.389): FR 100%[92.0,100]→82.9%[68.7,91.5], recall 0.542→0.713, task recall 0.427→0.792, fallback 30%→5%. Persistent false release after fixes = structural runtime-S blind spot.
- **Vocabulary dose–response.** Holdout-2 = constructive fully-disjoint lexicon ablation (stress-condition result, NOT deployment failure rate). Drift series (h2 templates constant, overlap p∈{0,.25,.5,.75,1}, 40/level, seeds 20261123–27): realized overlap 0→1 gives recall 0.522→0.845, release 92.5%→57.5%, FR 100%→82.6% (monotonic).
- **Calibration corrected (P0).** Average tied ranks (double-argsort bug fixed; 400-config cross-validated tests). Overall ρ 0.450[0.242,0.634], MAE 0.352[0.265,0.448], agreement 0.680[0.565,0.790]; CL confusion TP17/FP6/FN5/TN12; PRISM sign flip −0.071→+0.303[0.031,0.508]. Claim rests on MAE/threshold disagreement, not ρ alone.
- **Downstream rerun (P0).** Round-2 INVALID (last-sentence task re-exposed full X for 20/80; 8/40 audited; archived under `downstream_invalid_round2/`). Round-3: explicit task fields (isolation asserted), hash-cached answers, submitted paired seed 20261121, two judges; 91 answer + 160 judge calls, 0 errors. Reference-answer preservation: CL 0.725[0.613,0.838], GEN 0.700[0.575,0.825]; PASS 0.826 both; INFEAS 0.588/0.529; judge exact agreement 72.5% (MAE 0.138). Preservation ≠ absolute correctness; human holdout scoring prepared-but-not-collected.
- **Residual reports scoped + two-type probe.** Round-2 "recall 0" scoped to gold-literal residue in this experiment (all never-extracted; PASS has no report by construction). Probe (55 instances): exact re-insertion detected 100%, scrubbed 100%; evasion variant detected 100%, persists at exit 72.7%, 55/55 refused release, report coverage 65.5%; never-extracted residue persists 100%, reported 0%.
- **Open-ended attack (exploratory).** No gold question types; FR_open CL 0.725 (|PASS 0.826), GEN 0.675 (0.783), DF 1.0 (protocol reference, not theoretical ceiling). Still literal-graded; paraphrase/multi-hop/public-knowledge attacks future work.
- **Counting & intervals.** 243 unique instance–question pairs, 36 texts; round-2 h1 960 attack + 240 judge calls, 5832 question evaluations; hits = hit evaluations. Wilson intervals on all FR proportions; instance-cluster CIs on means/deltas.

## Key corrections vs earlier versions (Appendix A of the paper)

Heuristic point-rate gate + instance-cluster inference; runtime-S/oracle-S separated; online judges offline-only; Fano threshold corollary removed (counterexample test), |V_i|=1 handled; MI-unit feasibility; finite-budget termination; controlled-disclosure framing; consistent all-occurrence PRISM-style baseline (not LDP); deterministic stability window N=1 (verified identical to N=3 on 400 pairs); "supported"→"evaluated" components; title drops "Reversibility-Verified"; round-3 tied-rank Spearman correction, downstream invalidation+rerun, scoped conclusions, mechanism/contrast/dose/probe/open-attack additions, merged tables.

## Reproduction

See `README.md`, protocols v1–v3, and `sim/revision_h3_experiment.py` / `revision_downstream.py` / `revision_open_attack.py` / `revision_residual_probe.py` / `revision_stratified_v3.py`. Round-1 results reproduce 3200/3200 (D, release) pairs with current code. Freeze manifests: round-2 (12 entries) and round-3 (28 entries).
