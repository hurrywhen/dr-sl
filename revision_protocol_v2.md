# DR-SL revision protocol v2 (frozen before holdout-2 generation and new analyses)

Freeze timestamp: 2026-11-21. This addendum governs the `revision_20261121` round. It
supersedes nothing in `revision_protocol.md` (round `revision_20261118`); it adds new
analyses and a second holdout, and repositions the paper as a **failure-analysis and
reproducible-audit study** (review Route A). The closed loop is an *audited object*, not a
claimed superior method. No threshold, prompt, lexicon or template is tuned in response to
any result inspected after this freeze; process corrections are logged in
`revision_deviations.md`.

## 0. Positioning and naming

- The paper is repositioned as an audit of local release gates: the central claims are
  (i) runtime-S misses cause false local release, (ii) the closed loop does not beat simple
  deterministic generalization, (iii) the local utility surrogate is poorly calibrated, and
  (iv) whole-set averages mask release-subgroup risk.
- The title drops "Reversibility-Verified" (no rehydration/reversibility experiment is run in
  the deterministic track). The audited artifact keeps the legacy repository name DR-SL
  (originally Dehydrate–Rehydrate with Self-Learning); self-learning is exploratory and is
  excluded from the confirmatory release path. The method is described as the
  "runtime-S release chain".
- "supported components" is replaced by "evaluated components" throughout.

## 1. Primary safety metric and stratification (no new model calls)

- Define the primary conditional risk metric
  `FalseRelease = Pr(external audit finds >=1 residual hit | local PASS)`,
  estimated on the audited subset, and its gold-literal analogue
  `Pr(gold_literal_hits>0 | local PASS)` on the full holdout.
- Every headline leakage/utility metric is reported **stratified by local decision**
  (ALL / PASS / INFEASIBLE) and **by domain**. Whole-set means are reported only alongside
  the strata, never alone.
- Banking "20/20 released and 20/20 with gold residue" and legal "10/10 PASS with residue"
  must be surfaced, not hidden in averages.
- Paired closed_loop minus generalization_only deltas (release, gold_L, U_local) are reported
  with instance-cluster 95% CIs. The expected finding (release delta 0, gold_L delta 0,
  U_local delta < 0) is stated as a negative result.

## 2. Audit coverage counting fix (no new model calls)

- `n_unique_questions` is renamed `n_question_evaluations` (it counts repeated evaluations).
- Coverage reports separately: unique instance–question pairs, unique question texts, attack
  model calls, judge model calls, attacker×strategy combinations, and total hit *evaluations*.
- "519 hits" is labelled total hits across repeated attack evaluations, not 519 distinct
  leaked values.

## 3. Holdout-2: disjoint-vocabulary, independent-template (offline; small online subset)

- New generator `dataset/generate_holdout2.py`, seed 20261121, 80 instances (20/domain),
  `dataset/output/dr_sl_holdout_v2.jsonl`.
- Entity **values** come from a new vocabulary module `dataset/synth_values_v2.py` that is
  asserted disjoint from `synth_values.py` for every lexicon the runtime extractor uses
  (surnames, given names, cities, hospitals, banks, companies, schools, hotels, lawfirms,
  courts, diseases, drugs, occupations, case_types). Explicit identifiers (phone/id/email/
  bank_card/address/etc.) remain pattern-based.
- Templates are a new phrasing family, not copies of holdout-1. Per-domain template counts
  and distribution are reported.
- Purpose: measure extractor recall and false-release under **vocabulary shift**, i.e. the
  limitation that holdout-1 shared the extractor's exact lexicons. This is a stress test, not
  an open-world NER claim. No extractor change is made in response to holdout-2 outcomes.
- Offline: all five runtime-S methods on holdout-2, stratified as in §1.
- Online: first 5 holdout-2 instances per domain after ID sort (20 instances), methods
  `closed_loop` and `generalization_only`, same 2 attackers × 2 strategies + judge.

## 4. Extended online audit on holdout-1 (new model calls, frozen artifacts reused)

- Add `generalization_only` (the strongest simple baseline, previously absent online) and
  `direct_forward` (unprocessed X, attacker-capability reference) to the 40-instance holdout-1
  subset. Existing raw outputs for the other four methods are reused unchanged.
- `direct_forward` discloses synthetic X to the audit trust class; this is controlled
  disclosure of fictional data only.

## 5. Downstream task utility (new model calls)

- On the 40-instance holdout-1 subset, for methods `closed_loop` and `generalization_only`:
  a strong cloud model answers the embedded task from X (reference, once per instance) and
  from each D; an independent alt model judges each D-answer against the X-reference on a
  0/0.5/1 correctness/usefulness scale. This is a task-level utility measure, distinct from
  the artifact-level semantic judge.
- The judge is an external reference with measurement error; it is not ground-truth task
  success, not a local release input, and not a human-acceptability gold standard.

## 6. Calibration and residual-report analyses (no new model calls)

- Local-surrogate vs offline-judge validation adds instance-cluster 95% CIs for Spearman rho,
  MAE and threshold agreement, and a **per-method** threshold confusion matrix (not only the
  pooled four-method matrix). The positive finding (PASS judge mean > INFEASIBLE judge mean)
  is reported alongside the calibration gap.
- Residual-report recall: for INFEASIBLE closed-loop instances, compare the attributes named
  in the residual report against gold attributes still literally present in D. Report that
  extractor-missed attributes are absent from runtime-S residual reports by construction.

## 7. Stability window in the deterministic track

- The deterministic attack/utility functions are idempotent: the N=3 same-artifact window has
  exactly zero L/U range and filters nothing. The deterministic track is therefore declared
  to use a single effective evaluation (N=1); the N=3 machinery is retained only for a future
  stochastic neural track. We verify N=1 and N=3 give identical release decisions/artifacts
  on holdout-1 before adopting N=1, and log this as a deviation. The window is NOT described
  as a validated robustness mechanism.

## 8. Theory hygiene

- Fano statement explicitly excludes/handles |V_i|=1 (log(|V_i|-1) undefined); the code
  already skips singletons and a regression test is added.
- "recall sensitivity identity" is renamed "recall sensitivity inequality".
- Pufferfish witness states the prior set, discriminative pairs and channel explicitly.
- Theory is trimmed to background positioning; a measured per-domain task–sensitive overlap
  (coupling) statistic is reported descriptively to link the feasibility inequality to the
  observed domain release pattern, without claiming quantitative confirmation.
- Bibliography: every entry is cited in text or removed (Pufferfish, Fano/ Cover–Thomas,
  maximal leakage, k-anonymity, Wilson checked).

## 9. Human utility on holdout (prepared, not fabricated)

- A blinded holdout utility scoring packet is prepared for the two co-author raters. Real
  ratings cannot be collected in this automated revision; the packet is published as
  prepared-but-not-collected and listed as future work. No synthetic "human" scores are
  invented.

## 10. Statistics (unchanged from v1 unless noted)

- Instance-cluster bootstrap, 2000 resamples, percentile 95% CIs, seed 20261121 for new
  analyses (round-1 files keep seed 20261118). Permutation p uses (b+1)/(B+1); p=0 forbidden.
- Zero hits are zero *observed* hits under specified attackers/grading, with coverage counts.
- Release-rate Wilson intervals only at the independent-instance level.
