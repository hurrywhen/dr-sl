# Cover Letter — Journal Submission (Revised, Round 3)

Dear Editor,

We submit the revised manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This round addresses the third review's two P0 errors and its scope concerns, while keeping the audit positioning (Route A) that the evidence supports. The closed loop remains an *audited object*. All conclusions are now explicitly scoped to the audited implementation and our synthetic tests; we do not estimate failure rates of other gates or real deployments.

**P0 corrections (recomputed / rerun, not cosmetic):**

1. **Spearman tied ranks.** The calibration correlation used double-argsort ranks, which break ties arbitrarily on scores concentrated at {0, 0.5, 1}. We now use average tied ranks, with regression tests cross-validated against an independent implementation (400 configurations). All calibration estimates and bootstrap CIs are recomputed: overall rho 0.450 [0.242, 0.634] (was 0.356); the PRISM-random group flips sign (−0.071 → +0.303). MAE (0.352 [0.265, 0.448]) and threshold agreement (0.680) were unaffected; the "poorly calibrated" claim now rests primarily on absolute error and threshold disagreement. The buggy summary is archived, not deleted.

2. **Downstream task contamination.** The last-sentence task heuristic returned nearly the full original prompt for 20/80 field-list instances (8/40 audited), re-exposing sensitive X to the candidate answer model. The round-2 downstream outputs are archived as INVALID and never mixed with the rerun. The generators now store an explicit `task` field (prompts/annotations verified byte-identical; only metadata added), with unit tests asserting task ≠ prompt and no gold value in task. The rerun uses runtime isolation assertions, artifact-hash answer caching (identical artifacts reuse one answer), a submitted paired seed, and two independent judges; raw logs archive task, hashes, models, seed and responses. The metric is renamed **reference-answer preservation** (not absolute task correctness).

3. **"Identical downstream" removed.** Per-instance scores differed on 12/40 instances in the invalid run; the valid rerun reports a paired mean difference of −0.025 [−0.062, 0.000] with 2/40 disagreeing instances and 23/40 identical artifacts — "no detectable mean difference", not equivalence.

4. **Scoped conclusions.** The conclusion now states that the audited runtime-S implementation exhibits systematic false release on our synthetic tests, without extrapolating to other gates or deployments. The residual-report finding is scoped to gold-literal residue in this experiment; PASS instances have no report by construction. A constructed two-type probe shows the report mechanism covers detectable-but-unfixed residue (65.5% in evasion mode, all refused release) while never-extracted residue is invisible.

**P1 additions:**

5. **Bug-vs-architecture separation.** A fixed-extractor contrast (clear defects only: defined-but-unused money pattern, Unicode-\w email over-match, allergy label form/collision; no lexicon additions) is validated on the NEW holdout-3 (natural 50/50 vocabulary mix, new template family). Diagnostic holdout-1: recall → 1.000, false release 78.3% → 0 with unchanged decisions — the banking failure was a repairable software defect. Confirmatory holdout-3: false release remains 82.9% [68.7, 91.5] after fixes — the structural runtime-S blind spot. The original extractor is frozen and hash-verified.

6. **Utility-fallback mechanism.** Task-relevant recall (0.493) is far below attribute recall (0.858); 65% of holdout-1 releases pass through harmful context fallback and all leak (FR 1.000 vs 0.375). An audited coverage gate (UNSCORABLE → human routing) eliminates false release on holdout-1 at a large release-rate cost (57.5% → 6.2%), and cannot fix partial-coverage blind spots on holdout-2.

7. **Intervals and dose–response.** Wilson intervals accompany every false-release proportion (36/46, 19/23, banking 20/20, legal 10/10, holdout-2 75/75, online holdout-2 subset). A vocabulary dose–response series (templates held constant, overlap 0 → 1) replaces the two-endpoint presentation; holdout-2 is explicitly labelled a constructive lexicon-ablation stress test, not a deployment failure rate.

8. **Open-ended attack and FR taxonomy.** An exploratory open-ended inference attack (no gold question types) is added; FR variants (gold-literal / LLM-literal / open-ended) are distinguished; direct-forward = 1.0 is a protocol reference, not a theoretical attacker ceiling.

**Presentation:** result tables are merged (methods + paired + external; calibration + confusion + downstream); all three versions compile with zero overfull boxes and zero undefined references; README, declarations, EN mirror and arXiv abstract are synchronized. Human holdout scoring remains prepared-but-not-collected (no fabricated ratings); absolute task-quality rubrics and expert review are listed as future work.

Code, synthetic datasets, frozen protocols (v1–v3), deviation log (D-R1–D-R17), raw audit outputs including the invalidated downstream archive, and analysis scripts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Author order, conflict-of-interest, funding, ethics, and prior-version disclosures are in `declarations.md` and `../authorship_contribution_memo.md`; fields requiring author confirmation are explicitly marked.

Sincerely,
The Authors
