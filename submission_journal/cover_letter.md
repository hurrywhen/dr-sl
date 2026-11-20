# Cover Letter — Journal Submission (Revised, Round 2)

Dear Editor,

We submit the revised manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

In response to the major-revision review, we have repositioned the paper as a **failure-analysis and reproducible-audit study** (the review's Route A), which the evidence supports, rather than a claim of a superior automatic privacy-release method. The closed loop is now an *audited object*, not a recommended superior method. The title drops "Reversibility-Verified" because no rehydration/reversibility experiment is run in the deterministic track. Specific changes:

1. **Release-stratified risk and a conditional safety metric.** We introduce FalseRelease = Pr(external residue | local PASS) and report every leakage/utility metric stratified by local decision and by domain. On the shared-vocabulary holdout the chain releases 57.5% of instances, yet 78.3% of released instances retain gold sensitive literals; banking releases 20/20 with 20/20 residue. Whole-set averages are shown to mask the released subgroup's risk.

2. **No closed-loop advantage, reported honestly.** Paired closed-loop minus generalization-only differences are exactly zero for release rate and gold leakage, and negative for local utility (−0.089 [−0.117,−0.061]). Online, generalization-only has the same external leakage but higher judge utility. We demote the loop accordingly and replace "supported components" with "evaluated components".

3. **A disjoint-vocabulary holdout-2.** Holdout-1 shared the extractor's exact lexicons; we add holdout-2 (80 instances, new templates, entity values asserted disjoint from every extractor lexicon). Recall collapses 0.858→0.526, release rises 57.5%→93.75%, and gold FalseRelease reaches 100%. We rename holdout-1 "independent-template, shared-vocabulary" and do not claim open-world NER.

4. **Corrected audit counting.** "3888 unique questions" was repeated question evaluations; we now report 243 unique instance–question pairs, 36 unique question texts, attack/judge call counts, and label hits as hit evaluations.

5. **Extended online audit and downstream-task utility.** We add generalization-only and direct-forward (unprocessed-X reference) online, and a downstream task measure (answers-from-D judged against answers-from-X). The offline judge is treated as an external reference with measurement error, not ground-truth utility.

6. **Calibration and residual reports.** Local-surrogate vs judge validation now reports instance-cluster CIs for rho/MAE/threshold agreement and per-method confusion. Residual-report recall of true gold residue is 0, because the dangerous leftovers are exactly the extractor-missed attributes.

7. **Theory hygiene and narrative.** The Fano statement handles |V_i|=1; the recall "identity" is renamed an inequality; the Pufferfish witness states prior/pairs/channel; every bibliography entry is cited. Theory is trimmed to background positioning with a descriptive coupling link. The revision history is moved to an appendix so the main text reads as a self-contained study. Overfull tables are split into narrow single-column tables.

8. **Stability window.** The deterministic N=3 window is idempotent (zero range, zero filtering); we simplify to N=1 (verified identical on 400 pairs) and reserve N=3 for a future stochastic track, no longer describing it as a validated robustness mechanism.

A blinded holdout human-utility packet is prepared but not yet collected; we do not invent human scores and list this as future work. The extractor was not modified in response to holdout results (freeze); discovered extraction gaps are reported as findings.

Code, synthetic datasets, frozen protocols, raw audit outputs, and analysis scripts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Author order, conflict-of-interest, funding, ethics, and prior-version disclosures are in `declarations.md` and `../authorship_contribution_memo.md`; fields requiring author confirmation are explicitly marked.

Sincerely,
The Authors
