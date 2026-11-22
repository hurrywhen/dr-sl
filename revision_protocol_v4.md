# DR-SL revision protocol v4 (frozen before round-4 recomputation and new model calls)

Freeze timestamp: 2026-11-22 (round 4). This addendum governs the round-4 corrections
requested by the fourth review. It does not alter any confirmatory artifact, decision,
threshold, prompt, lexicon or template. Two classes of change are permitted:
(a) correction of *wrong computations* (paired-difference direction) with recomputation
from archived raw outputs, and (b) one new pre-registered diagnostic experiment
(cloud-assisted neural extractor contrast). No extractor, gate or prompt is tuned in
response to any result inspected after this freeze. Deviations are logged in
`revision_deviations.md` (D-R18 onward).

## 0. Scope of claims (unchanged)

All conclusions remain scoped to the audited runtime-S implementation on the
author-constructed synthetic benchmarks. The paper is positioned as an audit case
study; it does not estimate failure rates of other gates or real deployments. The
neural contrast added in §7 is explicitly *diagnostic*: cloud-assisted extraction
itself discloses X to the cloud, so it is not a deployable local gate and supports
no local-neural-gating claim.

## 1. Paired-difference direction correction (P0, recomputation only)

- `paired_cluster_delta(a, b)` computed b−a while two call sites (downstream, h3)
  passed (CL, GEN) and labelled the result CL−GEN. The API is replaced by
  `paired_delta(left, right)` computing **left−right**, with the direction stated in
  the name and docstring. All call sites are updated:
  - round-2 `revision_experiment.py` passed (GEN, CL) under b−a semantics and was
    therefore *correct*; arguments are swapped to (CL, GEN) under left−right so the
    archived h1/h2 paired values must remain **identical** (verified before use).
  - downstream and h3 call sites become left=CL, right=GEN; signs correct to
    downstream +0.025 and h3 U_delta −0.101 (original) / −0.116 (fixed).
- Every call site asserts the identity mean(Δ) = mean(left) − mean(right) on the
  observed instances. Regression tests cover (i) an asymmetric hand case fixing the
  direction, and (ii) the mean identity on random tied data. Bootstrap seed unchanged
  (20261118) so corrected CIs are exact sign flips of the archived ones.
- Affected summaries are recomputed from archived raw outputs (no new model calls):
  `downstream_summary.json`, `offline_h3_summary.json`, the round-3 stratified
  summary, and all generated tables. The paper narrative changes from "local-utility
  delta sign varies by dataset" to "negative on all three holdouts".

## 2. Dual-judge complete reporting (P0)

- Primary judge: `online_alt` (glm-5.2); robustness judge: `online_fast`
  (qwen3.8-flash). The primary role was pre-specified in the round-3 code
  (`JUDGE_ROLES` order and comment); this protocol makes it explicit.
- Report for EACH judge: per-method ALL/PASS/INFEASIBLE means, the paired CL−GEN
  mean difference with instance-cluster CI, and the number of instances whose CL and
  GEN scores differ (primary 2/40; robustness 8/40). No judge is selected post hoc;
  no new judge calls are made (all scores are archived).
- The headline downstream statement uses the primary judge and discloses the
  robustness judge alongside it. "only 2/40" without judge qualification is forbidden.

## 3. Zero-event scoping and intervals (P1)

- Coverage gate on holdout-1: releases drop 46→5; among the 5 released instances no
  gold-literal false release is observed: **0/5, Wilson [0, 0.434]**. Wording:
  "no observed false release among too few releases to validate safety", never
  "eliminates false release".
- Fixed extractor on holdout-1 (diagnostic): **0/46, Wilson [0, 0.077]**; wording
  "no observed gold-literal false release", not unconditional elimination.
- Every FalseRelease in the fixed-extractor contrast table carries a Wilson interval
  (table or immediately adjacent text), per the standing "all FR with intervals" rule.

## 4. Unmarked-context terminology (P1, behavior-preserving)

- The fallback scores retention of context the extractor did NOT mark; that context
  may contain missed sensitive values. The basis label `non_sensitive_context` is
  renamed `unmarked_context` and `_context_retention` → `_unmarked_context_retention`.
  Paper/README terminology becomes "unmarked-context retention" (未标记上下文保留率).
- Behavior must be unchanged: round-1 (D, release) reproduction 3200/3200 and h3 row
  identity (except the basis label) are verified. Freeze-manifest hash changes for
  `sim/runtime.py` are logged as a deviation.

## 5. Fallback trichotomy (P1)

Contrast tables and JSON distinguish: all fallback (no runtime task attribute),
benign fallback (no gold task attribute either), harmful fallback (gold task
attributes exist but none extracted). The fixed-extractor holdout-1 13.8% is ALL
fallback and is entirely benign; it must not be presented as harmful.

## 6. Task-isolation test coverage (P2)

`test_task_fields.py` is extended to holdout-3 and all five drift-series files
(same assertions: task non-empty, ≠ prompt, short, no gold value, verbatim or
authored-dialogue source).

## 7. Cloud-assisted neural extractor contrast (P2, new model calls, diagnostic)

- Purpose: test whether the audited failures are specific to the deterministic
  regex/lexicon implementation, and whether a neural extractor is robust to the
  constructive vocabulary displacement.
- Extractor: `online_strong` (qwen3.8-max), frozen prompt (below), no gold
  annotations, no lexicon lists. Submitted seed 20261124 (provider honoring not
  guaranteed; disclosed). Temperature is the backend default 0.3.
- Frozen extraction prompt (system): the model is a PII extractor for Chinese
  synthetic records; it must output ONLY JSON `{"entities":[{"type":..., "value":...}]}`
  using the declared type taxonomy (the union of types used by the benchmark:
  name, phone, email, id_card, bank_card, address, medical_record_no, passport,
  plate, case_no, deposit_no, order_no, card_tail, ticket_no, insurance_id,
  fund_account, city, hospital, bank, employer, school, airline, hotel, lawfirm,
  court, disease, drug, allergy, occupation, insurance_type, case_type, amount,
  charge, income, date, visit_date, age, flight_no, duration, children_count);
  values must be verbatim substrings of the input; no invention.
- Localization interface: each proposed value is located by EXACT substring search
  (all occurrences); unlocatable proposals are discarded and counted; overlapping
  spans are resolved longest-first exactly as in the deterministic extractor.
  Categories follow the same explicit-type set. This interface is part of the
  frozen design, not tuned afterwards.
- Sets: holdout-1 (80), holdout-3 (80), drift p000 (40) = 200 extraction calls.
  Methods: closed_loop and generalization_only under the SAME gates and "mixed"
  task profile, plus coverage-gate variants. Metrics: attribute recall,
  task-relevant recall, over-extraction, release rate, FR_gold with Wilson,
  fallback trichotomy, U_local, paired CL−GEN with the §1 identity assertion.
- Trust disclosure: extraction sends X to the cloud API; this is a first disclosure
  and the condition is DIAGNOSTIC ONLY. It is not a local gate, not deployable
  under the paper's trust model, and supports no claim about local neural gating.
- Raw responses, model name, submitted seed, parse failures and unlocatable counts
  are archived; extraction is cached by SHA-256(X) and resumable. No tuning after
  results are inspected.

## 8. Related work and organization (P2)

Add four literature categories: (i) text anonymization and privacy-leakage
evaluation; (ii) NER distribution shift / open vocabulary; (iii) selective
prediction, abstention and coverage–risk trade-offs; (iv) LLM-as-judge reliability
and reference-based evaluation. Revision history is removed from the abstract
(it remains in Appendix A). Information-theoretic statements stay in Appendix B
as positioning; the main text focuses on the five core findings.

## 9. Statistics (unchanged)

Instance-cluster bootstrap, 2000 resamples, percentile 95% CIs; paired seed 20261118
(unchanged so corrected CIs are exact sign flips); round-3 analysis seed 20261121;
Wilson intervals at the independent-instance level; average tied ranks for Spearman;
permutation p uses (b+1)/(B+1).

## 10. Human evaluation (unchanged)

Holdout human utility scoring remains prepared-but-not-collected; no synthetic
human scores. Absolute task-quality rubrics and expert review remain future work.
