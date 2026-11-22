# Cover Letter — Conference Submission (Revised, Round 5)

Dear Program Committee,

We submit the revised condensed manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This is a failure-analysis and reproducible-audit study, not a claim of a superior automatic sanitizer. The closed loop is an *audited object*; all conclusions are scoped to the audited implementation and our author-constructed synthetic tests, and do not estimate failure rates of other gates or real deployments.

Three core findings: (1) missed extraction causes false release — 57.5% of a shared-vocabulary holdout is released, yet 78.3% of released instances (Wilson [64.4,87.7]) retain gold sensitive literals, with banking 20/20; (2) the utility gate rewards unknown task coverage — with no task attribute extracted, utility falls back to unmarked-context retention, so worse extraction makes release easier (65% of releases pass through this harmful fallback, all leaking); a coverage gate cuts releases to 5/80 with 0/5 observed false release (Wilson upper bound 43.4%), too few to validate safety; (3) the closed loop adds no benefit over one-shot deterministic generalization — paired release/leakage deltas are zero on three holdouts, local utility is lower for the loop on all three, and downstream reference-answer preservation shows no detectable mean difference (+0.025 [0,0.0625], primary judge; robustness judge +0.025 [−0.0375,0.0875]; both reported in full).

Supporting analyses: a constructive fully-disjoint-vocabulary stress test and dose–response series; a fixed-extractor contrast separating repairable software defects (0/46 observed false release on shared vocabulary) from structural blind spots (82.9% under natural drift); and a diagnostic cloud-assisted neural-extractor contrast (extraction itself discloses X, so not a deployable local gate) whose residue is now decomposed by source: holdout-1/drift-p0 false releases are entirely a room-number taxonomy-coverage gap, while holdout-3's city residue directly evidences within-taxonomy neural misses.

Round 5 corrects the neural contrast's interpretation (three omitted gold types with an automatic coverage test; direction-specific bound scoping — recall conservative under the prompt/taxonomy, FR conditional with no bound direction; income misses re-described as partial-span extraction with separate exact-span, character-coverage and literal-residue layers) and adds pre-registered credibility checks: sampling-stability repeats (identical release/FR instance sets across three runs on a 60-instance subset), a second model family (glm-5.2; different miss identity, same inheritance), and complete-taxonomy validation on new holdout-4 (gap FR 0/32; one within-taxonomy city miss 1/32 — the inheritance mechanism persists after the coverage fix). Earlier statistical and trust-boundary overclaims were removed in prior rounds and remain removed.

Code, synthetic data (including holdout-4), frozen protocols (v1–v5), deviation log (D-R1–D-R31), and raw outputs (including the invalidated round-2 downstream archive and the byte-intact round-4 neural archive) are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Declarations and author-order disclosure are in `declarations.md`. The current draft is 4 pages; the venue page limit is to be confirmed.

Sincerely,
The Authors
