# Cover Letter — Journal Submission (Revised, Round 4)

Dear Editor,

We submit the revised manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This round addresses the fourth review's numerical and reporting corrections and its completeness suggestions. The audit positioning (Route A) is unchanged: the closed loop remains an *audited object*, and all conclusions are scoped to the audited implementation and our author-constructed synthetic tests. The reviewer independently reproduced our round-3 offline experiments byte-for-byte; the core findings stand.

**P0 corrections (recomputed from archived outputs; no new model calls for these):**

1. **Paired-difference direction.** The bootstrap helper `paired_cluster_delta(a,b)` computed b−a while the downstream and holdout-3 call sites passed (CL, GEN) and labelled the result CL−GEN. We replaced it with an explicit-direction API `paired_delta(left, right)` = left−right, added an internal mean-identity assertion, updated every call site, and added regression tests (an asymmetric hand case fixing the direction; 200 random configurations checking mean(Δ) = mean(left) − mean(right)). Corrected values: downstream CL−GEN **+0.025 [0, 0.0625]**; holdout-3 local utility **−0.101 [−0.130, −0.071]** (original extractor) and **−0.116 [−0.149, −0.084]** (fixed). The round-2 h1/h2 call sites were directionally correct under the old semantics; after the argument swap their archived values were verified *identical* (estimate and CI) before use. The narrative now states the local-utility delta is **negative on all three holdouts**, strengthening the "no loop benefit" conclusion.

2. **Complete dual-judge reporting.** The primary judge (online_alt, glm-5.2) was pre-specified in the round-3 design; online_fast (qwen3.8-flash) is the robustness judge. We now report both in full: identical method means (0.725/0.700) and paired mean (+0.025), but primary CI [0, 0.0625] with **2/40** disagreeing instances vs robustness CI [−0.0375, 0.0875] with **8/40**. No judge is selected post hoc; "only 2/40" without qualification is removed.

**P1 corrections:**

3. **Zero-event scoping.** The coverage gate on holdout-1 is now stated as 46→5 releases with **0/5 observed false release (Wilson [0, 0.434])**—too few releases to validate safety; "eliminates false release" is removed everywhere. The fixed extractor on holdout-1 is **0/46 (Wilson [0, 0.077])**, "no observed gold-literal false release". Every FR in the fixed-extractor contrast table now carries a Wilson interval.

4. **Unmarked-context terminology.** The fallback basis is renamed from "non-sensitive context" to **unmarked-context retention** (code label, docstrings, paper, README): the scored context is extractor-unmarked, not certified non-sensitive—it may contain exactly the missed sensitive values. The rename is behavior-preserving: round-1 reproduction re-verified 3200/3200 (D, release), and holdout-3 rows are identical except the label.

5. **Fallback trichotomy.** Tables and JSON now distinguish all / benign / harmful fallback. The fixed extractor's 13.8% holdout-1 fallback is entirely benign (no gold task attributes); harmful fallback is 0.

**P2 additions:**

6. **Neural-extractor contrast (new experiment, 200 calls, pre-registered in protocol v4).** A cloud LLM (qwen3.8-max) with a frozen extraction prompt (declared taxonomy, verbatim values, no gold, no lexicons) replaces the deterministic extractor under the *same* gates on holdout-1, holdout-3 and the fully-displaced drift level. Recall stays at 0.965 under full vocabulary displacement (deterministic: 0.522), task recall reaches 1.000, harmful fallback vanishes, and FR drops to 13–17%—the failure *magnitude* is largely implementation-specific. Yet false release *persists* even with a strong neural extractor: the gate inherits whatever the extractor misses. Two honest qualifications are stated: (i) extraction itself discloses X to the cloud, so the condition is **diagnostic only**, not a deployable local gate; (ii) the frozen taxonomy omitted two gold types (room number, marriage duration), so the neural numbers are lower bounds—the prompt was not amended after inspection.

7. **Related work and organization.** Four literature categories added with verified citations: text anonymization/leakage evaluation (Lison et al. ACL 2021; TAB, CL 2022; RLTA, EMNLP 2019), NER distribution shift (CoNLL-2003; CrossNER, AAAI 2021; Fu et al. survey), selective prediction/coverage–risk (Chow 1970; El-Yaniv & Wiener 2010; Geifman & El-Yaniv 2017; Hendrycks & Gimpel 2017; Kamath et al. ACL 2020), and LLM-as-judge reliability (Zheng et al. NeurIPS 2023; G-Eval, EMNLP 2023; Wang et al. 2023). Revision history is removed from the abstract (retained in Appendix A); information-theoretic statements remain appendix positioning. Task-isolation tests now cover holdout-3 and all five drift levels (440 instances).

**Verification:** 12 test suites pass (including the new direction/identity and neural-parser tests); round-1 reproduces 3200/3200 with current code; freeze manifests consistent (round-3/4: 38 entries; round-2 hash differences for runtime.py, revision_stats.py, revision_experiment.py and the two generators are documented behavior-preserving/metadata-only changes); main 18 pp / conference 4 pp / journal 11 pp, zero overfull boxes, zero undefined references; README, declarations, EN mirror and arXiv abstract synchronized; no internal endpoints or keys in the tree.

**Remaining limitations (disclosed, unchanged):** no third-party corpus yet (TAB is the natural next step); holdout human scoring prepared-but-not-collected (no fabricated ratings); local neural service unavailable, so no local-neural end-to-end claim; model snapshots unpinned and submitted seeds may not be honored; open-ended attacks remain literal-graded.

Code, synthetic datasets, frozen protocols (v1–v4), deviation log (D-R1–D-R24), raw audit outputs including the invalidated downstream archive and the neural-extraction cache, and analysis scripts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Author order, conflict-of-interest, funding, ethics, and prior-version disclosures are in `declarations.md` and `../authorship_contribution_memo.md`; fields requiring author confirmation are explicitly marked.

Sincerely,
The Authors
