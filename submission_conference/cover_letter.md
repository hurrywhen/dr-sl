# Cover Letter — Conference Submission (Revised, Round 4)

Dear Program Committee,

We submit the revised condensed manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This is a failure-analysis and reproducible-audit study, not a claim of a superior automatic sanitizer. The closed loop is an *audited object*; all conclusions are scoped to the audited implementation and our author-constructed synthetic tests, and do not estimate failure rates of other gates or real deployments.

Three core findings: (1) missed extraction causes false release — 57.5% of a shared-vocabulary holdout is released, yet 78.3% of released instances (Wilson [64.4,87.7]) retain gold sensitive literals, with banking 20/20; (2) the utility gate rewards unknown task coverage — with no task attribute extracted, utility falls back to unmarked-context retention, so worse extraction makes release easier (65% of releases pass through this harmful fallback, all leaking); a coverage gate cuts releases to 5/80 with 0/5 observed false release (Wilson upper bound 43.4%), too few to validate safety; (3) the closed loop adds no benefit over one-shot deterministic generalization — paired release/leakage deltas are zero on three holdouts, local utility is lower for the loop on all three, and downstream reference-answer preservation shows no detectable mean difference (+0.025 [0,0.0625], primary judge; robustness judge +0.025 [−0.0375,0.0875]; both reported in full).

Supporting analyses: a constructive fully-disjoint-vocabulary stress test and dose–response series; a fixed-extractor contrast separating repairable software defects (0/46 observed false release on shared vocabulary) from structural blind spots (82.9% under natural drift); and a diagnostic cloud-assisted neural-extractor contrast (extraction itself discloses X, so not a deployable local gate) showing recall 0.965 survives full vocabulary displacement while 13–17% false release persists — the gate inherits even neural misses.

Round 4 corrects two paired-difference direction errors with an explicit-direction API and identity regression tests, scopes all zero-event claims to their sample sizes, and expands related work to anonymization evaluation, NER distribution shift, selective prediction, and LLM-as-judge reliability. Earlier statistical and trust-boundary overclaims (independent-probe pooling, oracle-S as deployment, online judges as release gates, an invalid Fano threshold corollary) were removed in prior rounds and remain removed.

Code, synthetic data, frozen protocols (v1–v4), deviation log (D-R1–D-R24), and raw outputs (including the invalidated round-2 downstream archive) are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Declarations and author-order disclosure are in `declarations.md`. The current draft is 4 pages; the venue page limit is to be confirmed.

Sincerely,
The Authors
