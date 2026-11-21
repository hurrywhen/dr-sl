# DR-SL revision protocol v3 (frozen before round-3 data generation and analyses)

Freeze timestamp: 2026-11-21 (round 3). This addendum governs the round-3 corrections.
It does not alter round-1/2 confirmatory results except where a computation was
*wrong* (Spearman ties) or an experiment was *invalid* (downstream task contamination);
those are recomputed/rerun and the invalid outputs are archived, not mixed. No threshold,
prompt, lexicon or template is tuned in response to any result inspected after this freeze.
Deviations are logged in `revision_deviations.md` (D-R10 onward).

## 0. Scope of claims (P0)

- All conclusions are scoped to **the audited runtime-S implementation** on the synthetic
  benchmarks in this repository. The paper does not estimate failure rates of other local
  release gates or of real deployments.
- The residual-report finding is scoped to **recall of gold literal values still present in
  the artifact in this experiment**. PASS instances have no residual report by construction;
  PASS and INFEASIBLE are interpreted separately. A constructed two-type residue probe
  (extracted-but-unscrubbed vs never-extracted) tests the report mechanism itself.
- holdout-2 is a **constructive lexicon-ablation / vocabulary-shift stress test**: its 100%
  false-release is a stress-condition result, not a deployment failure rate. The abstract
  states this explicitly.
- `direct_forward = 1.0` is a reference **under the current gold-question protocol**, not a
  theoretical attacker ceiling.
- FalseRelease variants are distinguished: FR_gold-literal (offline gold literals),
  FR_LLM-literal (external LLM attacks graded on gold literals), FR_open-ended (open-ended
  inference attack, no gold question types; still literal-graded, exploratory).

## 1. Spearman tie correction (P0, recomputation only)

- Replace double-`argsort` ranking with **average tied ranks** in `revision_stratified.py`.
- Unit tests with heavy ties cross-validated against an independent implementation
  (`statistics.correlation` on independently computed average ranks, plus hand-checked
  reference cases). All bootstrap CIs are recomputed with the corrected function.
- MAE and threshold agreement are unaffected and retained. The "poorly calibrated" claim
  rests primarily on MAE, threshold confusion and release-decision disagreement, not on rho
  alone.
- The round-2 stratified summary is archived as `stratified_summary_round2.json`; the
  corrected file replaces it. No model output changes.

## 2. Explicit task field and downstream rerun (P0)

- Holdout generators store an explicit `task` field per instance (authored per template;
  for dialogue templates it is the user's actual request). Prompts, annotations, IDs and
  all previously evaluated quantities must remain **byte-identical**; only the metadata
  field is added. This is verified before use and logged as a deviation.
- Unit tests assert for every holdout instance: task is non-empty; task != prompt; task
  contains no gold sensitive value; task length is a small fraction of prompt length.
- The contaminated round-2 downstream outputs are moved to
  `results/revision_20261121/downstream_invalid_round2/` with an explanatory README and are
  never mixed with valid results.
- Downstream v2 (`sim/revision_downstream.py`, rewritten): uses the explicit task; asserts
  isolation at runtime (no gold value in task); caches answers by artifact SHA-256 so
  identical artifacts reuse one answer; submits a fixed paired seed to the answer backend
  (seed honoring by the provider is not guaranteed and is disclosed); archives task,
  artifact hash, material hash, model names, seed and raw responses.
- Two independent judge models score every candidate (multi-judge agreement reported).
- The metric is renamed **reference-answer preservation**: agreement with the answer obtained
  from full X, not absolute task correctness. Absolute quality requires expert rubrics /
  human scoring (prepared-but-not-collected; future work).
- Report per-instance paired closed_loop − generalization_only differences with
  instance-cluster CIs, the number of disagreeing instances, and the number of identical
  artifacts. "identical downstream" is forbidden wording; mean equality with a wide CI is
  reported as "no detectable mean difference".

## 3. Fixed-extractor contrast on new holdout-3 (P1)

- The original extractor `sim/runtime_extractor.py` remains **frozen and unchanged**; all
  round-1/2 results stand.
- A contrast variant `sim/runtime_extractor_fixed.py` fixes only clear implementation
  defects, with no lexicon additions: (a) wire the defined-but-unused money pattern
  (amount/charge by label context); (b) ASCII email local part (the Unicode `\w` class
  over-matches Chinese label prefixes); (c) allergy labeled form `过敏史：X` and the
  `孩子/患者` name-label collision with `对X过敏` (negative lookahead). Unit tests verify
  each fix and that name recall on holdout-1 does not degrade.
- New holdout-3 (`dataset/generate_holdout3.py`, seed 20261122, 80 instances, 20/domain,
  new template family #3, explicit task field): **natural vocabulary mix** — each
  lexicon-dependent value is drawn from the old pool with probability 0.5, else the disjoint
  v2 pool. Holdout-3 is the confirmatory set for the fixed-vs-original contrast; holdout-1/2
  fixed-extractor runs are diagnostic only (bugs were discovered there).
- Both extractors × all five methods are run offline on holdout-3, stratified as before.
  The contrast separates (i) software defects, (ii) vocabulary dependence, (iii) structural
  runtime-S blind spots. No extractor is tuned after seeing holdout-3 results.

## 4. Vocabulary dose–response series (P1)

- `dataset/generate_drift_series.py`: holdout-2 template family held constant; lexicon
  overlap p ∈ {0, 0.25, 0.5, 0.75, 1.0}; 40 instances per level (10/domain), seed 20261123.
  A mixing RNG draws each lexicon value from the old pool with probability p. Realized
  overlap (fraction of lexicon-dependent gold values actually from the old pool) is measured
  and used as the dose axis. Endpoints are asserted (p=0 fully disjoint, p=1 fully old).
- Offline only: recall, release rate, FR_gold-literal vs realized overlap, for the original
  extractor (closed_loop). This replaces the two-endpoint-only presentation.

## 5. Utility-gate fallback mechanism and coverage gate (P1)

- Mechanism analysis (no new model calls): when no runtime task-relevant attribute is
  found, `local_utility` falls back to non-sensitive context retention. Report per dataset:
  attribute-level recall, **task-relevant attribute recall**, fraction of instances entering
  the context fallback, and the fallback × false-release cross-tab.
- Audited mitigation variant (not a claimed fix): **coverage gate** — if the declared task
  profile expects task attributes but none were extracted, the decision is `UNSCORABLE`
  (no automatic release; human routing). Applied post-hoc to holdout-1/2 rows and as a
  variant on holdout-3. Report the release-rate cost and the false-release reduction.
  The frozen base methods are unchanged.

## 6. Intervals and merged tables (P1/P2)

- Wilson 95% intervals for every reported FalseRelease and domain residue fraction
  (36/46, 19/23, banking 20/20, legal 10/10, holdout-2 75/75, online holdout-2 subset).
- Tables merged: (methods + paired + external) into one method-comparison table;
  (calibration + confusion + downstream) into one utility-measurement table. Stratified,
  domain, vocabulary-shift/dose-response, coverage, residual tables remain.

## 7. Open-ended external attack (P2, new model calls)

- On the 40-instance holdout-1 subset, methods closed_loop / generalization_only /
  direct_forward: one open-ended inference call per instance ("infer and list any personal
  sensitive information you can recover from this material", no gold question types).
  Graded by normalized gold-literal substring recovery; reported as FR_open-ended
  (exploratory; still literal-graded, not full semantic/combinatorial risk).
- All online records gain `artifact_sha256`; raw logs already archive model outputs.

## 8. Statistics (unchanged unless noted)

- Instance-cluster bootstrap, 2000 resamples, percentile 95% CIs; round-3 seed 20261121.
  Permutation p uses (b+1)/(B+1); p=0 forbidden. Wilson intervals at the independent-instance
  level. Zero hits remain zero *observed* hits with coverage counts.

## 9. Human evaluation (unchanged status)

- Holdout human utility scoring remains prepared-but-not-collected; no synthetic human
  scores. Absolute task-quality rubrics and expert review are listed as future work.
