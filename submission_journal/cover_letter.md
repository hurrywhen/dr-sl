# Cover Letter — Journal Submission (Revised, Round 5)

Dear Editor,

We submit the revised manuscript **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**.

This round addresses the fifth review's interpretation corrections for the neural-extractor contrast and its credibility suggestions. The audit positioning (Route A) is unchanged: the closed loop remains an *audited object*, and all conclusions are scoped to the audited implementation and our author-constructed synthetic tests. The reviewer independently reproduced our round-4 offline experiments and tests byte-for-byte; the six main findings stand unchanged.

**P0 corrections (recomputed from the byte-intact round-4 archive; no new model calls for these):**

1. **Taxonomy coverage.** The frozen declared taxonomy omitted **three** gold types, not two: room number, marriage duration and work tenure (holdout-1/drift; holdout-3 fully declared). Work-tenure values were in fact proposed under the declared type "duration" and scrubbed, so they caused no residue — the coverage claim was nonetheless wrong. A new automatic test compares every dataset's gold type set against the declared taxonomy and pins the documented omission sets, so manual disclosure cannot drift again.

2. **FR decomposition by failure source.** All holdout-1 false releases (5/31) and drift-p0 false releases (2/15) are values of the undeclared room-number type — a *taxonomy-coverage gap*, a pessimistic conditional outcome of the incomplete prompt. Only holdout-3's 4/24 residue (all city; the gold string never proposed) directly demonstrates *within-declared-taxonomy neural misses*. The neural table now carries both components with Wilson intervals, and the narrative no longer lumps them into "the neural extractor still misses".

3. **Bound scoping.** The blanket "neural numbers are a lower bound" claim is removed. Exact gold-span recall is a conservative measurement *under the current prompt and taxonomy*; FR is an observation *conditional on the incomplete taxonomy* with no general upper/lower-bound direction (omitted types leave values in the artifact and can raise FR).

4. **Partial-span extraction.** All income misses are verbatim, locatable proper substrings of the gold span (e.g., the numeric amount inside a "monthly income about …" phrase), not non-verbatim output; n_unlocatable = 0 over all 200 calls. We now report three layers separately: exact-span recall (0.965/0.973/0.965), sensitive character coverage (0.983/0.988/0.983), and final gold-literal residue. Partial-span-only gold values: 10/10/4, all income.

**P1 credibility experiments (pre-registered in protocol v5 before any call; 260 calls, 0 errors; all cloud-assisted and diagnostic only):**

5. **Sampling stability.** Two repeats of the same frozen prompt on a deterministic 60-instance subset agree with the round-4 run on 95.0%/91.7% of exact entity sets (Jaccard 0.991/0.985), yet the release set and FR instance set are *identical* across all three runs (FR 3/20 [5.2, 36.0]): sampling perturbs spans, not the audited decisions on this subset.

6. **Second model family.** glm-5.2 under the same prompt matches only 68.3% of exact entity sets (Jaccard 0.925) with similar recall (0.959); its FR 5/25 shares the two room-number gap instances but has *different* declared-type misses (three zero-valued charges never proposed). Miss identity is family-dependent; the inheritance mechanism is not.

7. **Complete-taxonomy validation on new data.** Holdout-4 (new template family #4, natural vocabulary mix, 80 instances authored before any result was inspected) contains the three previously omitted types; prompt v2 adds exactly their declarations (43 types; minimal-delta test). The pre-registered expectation is confirmed: taxonomy-gap FR vanishes (0/32 [0, 10.7]); total FR is 1/32 [0.6, 15.7] — a single never-proposed city value, the *same* literal missed on holdout-3 (a value-specific blind spot). Recall 0.986, character coverage 0.993. Taxonomy completion removes the coverage-gap component but **not** the inheritance mechanism. Round-4 results remain diagnostic under the original incomplete taxonomy and were not relabelled or recomputed with prompt v2; no prompt was amended after inspection.

**Organization.** The abstract's neural sentence is rewritten by failure source; the revision-history appendix is compressed ~50% (full detail in the archived protocols and deviation log); stability/family subset metrics are archived and reported in prose rather than a new table. Page counts: main 19 pp. (+1 while absorbing all P0/P1 content), journal 11 pp. and conference 4 pp. (both unchanged from round 4); zero overfull boxes, zero undefined references.

**Verification:** 13 test suites pass (including the new taxonomy-coverage test and holdout-4 task isolation; 520 instances covered); round-1 reproduces 3200/3200 with current code; the round-4 neural archive is byte-intact; freeze manifest extended to 45 entries and consistent; README, declarations, EN mirror and arXiv abstract synchronized; no internal endpoints or keys in the tree.

**Remaining limitations (disclosed, unchanged):** no third-party corpus (TAB is the natural next step); holdout human scoring prepared-but-not-collected (no fabricated ratings); the local neural service remains unavailable, so no local-neural end-to-end claim — every neural condition is a cloud-assisted diagnostic contrast, single-run per condition, with instance-level intervals that do not cover model sampling variation beyond the characterized subset; model snapshots unpinned and submitted seeds may not be honored; open-ended attacks remain literal-graded.

Code, synthetic datasets (including holdout-4), frozen protocols (v1–v5), deviation log (D-R1–D-R31), raw audit outputs (including the invalidated downstream archive, the byte-intact round-4 neural archive, and the round-5 extraction cache), and analysis scripts are public at https://github.com/hurrywhen/dr-sl and https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl. Author order, conflict-of-interest, funding, ethics, and prior-version disclosures are in `declarations.md` and `../authorship_contribution_memo.md`; fields requiring author confirmation are explicitly marked.

Sincerely,
The Authors
