# DR-SL revision protocol v5 (frozen before round-5 recomputation, holdout-4 generation and new model calls)

Freeze timestamp: 2026-11-22 (round 5). This addendum governs the round-5 corrections
requested by the fifth review. It does not alter any confirmatory artifact, decision,
threshold, lexicon or template of rounds 1–4. Three classes of change are permitted:
(a) correction of *wrong descriptions and computations* about the round-4 neural
contrast, recomputed from archived raw outputs; (b) pre-registered credibility
experiments for the neural contrast (sampling-stability repeats, a second model
family); (c) one pre-registered validation of the taxonomy completion on a NEW
holdout (holdout-4, new template family #4). No prompt, taxonomy or template is
tuned in response to any result inspected after this freeze. Deviations are logged
in `revision_deviations.md` (D-R25 onward). The round-4 archive
(`neural_extraction_cache.jsonl`, `neural_extractor_rows.jsonl`,
`neural_extractor_summary.json`) is kept byte-intact; round-5 analyses are written
to new files alongside it.

## 0. Scope of claims (unchanged)

All conclusions remain scoped to the audited runtime-S implementation on the
author-constructed synthetic benchmarks (audit case study, Route A). Every neural
condition in this paper — round 4 and round 5 — is cloud-assisted and therefore
DIAGNOSTIC ONLY: extraction itself discloses X to the cloud, so none of these
conditions is a deployable local gate or supports any local-neural-gating claim.
The local neural service remains unavailable (`DRSL_LOCAL_BASE_URL` unset, verified
this round); no local-neural end-to-end result is claimed. Per the user's round-4
decision (reaffirmed this round), no third-party corpus is added, holdout human
utility scoring remains prepared-but-not-collected, and attacks remain literal-graded.

## 1. P0 corrections to the round-4 neural contrast (recomputation only, no new calls)

1. **Taxonomy omission is THREE types, not two.** The round-4 frozen declared
   taxonomy (`TYPES` in `sim/revision_neural_extractor.py`, 40 types) omits
   `room_no`, `marriage_years`, `work_years` relative to the gold types of
   holdout-1 and drift-p000; holdout-3's gold types are fully declared. Protocol v4
   §7's description "the union of types used by the benchmark" was incorrect and is
   corrected here (v4 itself remains frozen as a historical record). Note:
   `work_years` values were in fact proposed under the declared type `duration`
   and scrubbed, so they caused no residue; the coverage *claim* was still wrong.
   An automatic test (`sim/test_neural_taxonomy.py`) compares each dataset's gold
   type set against the declared taxonomy and pins the documented per-dataset
   omission sets, so manual disclosure cannot silently drift again.
2. **FR decomposition by failure source.** For every released instance with gold
   literal residue, each residual value's gold type is classified: taxonomy gap
   (type not declared) vs declared-type miss (type declared). Report
   `FR_taxonomy_gap` and `FR_declared_type_miss` (instance-level among releases,
   Wilson intervals) per dataset. Verified from the archive: holdout-1 5/31 all
   `room_no` (gap), drift-p000 2/15 all `room_no` (gap), holdout-3 4/24 all `city`
   (declared-type miss; the gold city string was never proposed — 3 instances have
   no related proposal, 1 proposes only a hotel name containing the city stem).
   The narrative must not lump these into "the neural extractor still misses":
   h1/drift-p0 residuals demonstrate that *taxonomy coverage gaps cause false
   release*; only h3 directly demonstrates *within-declared-taxonomy neural misses*.
3. **Bound direction.** "Neural numbers are a lower bound" is removed as a blanket
   statement. Correct scoping: exact gold-span recall is a conservative measurement
   *under the current prompt and incomplete taxonomy*; FR is an observation
   *conditional on the incomplete taxonomy* with no general upper/lower-bound
   direction (omitted types leave values in the artifact and can RAISE FR — the
   h1/drift-p0 FR is exactly such a pessimistic conditional outcome). Completing
   the taxonomy also changes the runtime sensitive set, utility scores and release
   decisions, so no unverified claim is made about the FR of a complete-typed system
   on the same data; that question is tested on holdout-4 (§4).
4. **Income is partial-span extraction, not non-verbatim.** All income misses are
   cases like gold `月收入约1.2万元` → proposal `1.2万元`: a verbatim, locatable
   proper substring of the gold span (`n_unlocatable = 0`, `n_unknown_type = 0`
   over all 200 calls). The sensitive numeric content is scrubbed even though the
   full gold span is not recalled. Report three layers separately: (i) exact
   gold-span recall (the existing value-based recall); (ii) sensitive character
   coverage — fraction of gold-entity characters covered by the union of extracted
   spans; (iii) final gold-literal residue (gold_L / FR, unchanged). Also report
   partial-span-only gold value counts (h1 10, h3 10, drift-p000 4; all income)
   and unlocatable counts. Exact-span recall must not be presented as actual
   privacy coverage.
5. **Single-run disclosure.** The round-4 contrast is a single-run cloud-assisted
   diagnostic: Wilson/bootstrap intervals cover instance variation only, not model
   sampling, prompt sensitivity, version or family variation. §2–§3 characterize
   sampling and family variation on a subset; full population-level stability
   intervals remain out of scope.
6. All affected text (abstract, §res-neural, table captions, discussion,
   limitations, README, EN mirror, declarations, cover letters, highlights, arXiv
   abstract, both submission versions) is synchronized. The abstract's neural
   sentence is rewritten by failure source (or reduced), not kept as an
   unqualified "13–17% persists".

## 2. Sampling-stability repeats (new calls, pre-registered)

- Subset: 60 instances — the first 5 instances per domain in sorted-id order from
  each of holdout-1, holdout-3, drift-p000 (4 domains each, 20 per dataset).
  Deterministic selection, fixed before any call.
- Extractor: `online_strong` (qwen3.8-max), the round-4 frozen prompt
  byte-identical (original incomplete taxonomy, for comparability), temperature
  backend default 0.3. Two repeat runs with submitted seeds 20261126 and 20261127
  (round-4 run used 20261124; provider honoring not guaranteed).
- Metrics: per-instance exact entity-set agreement (type, value, span) and Jaccard
  vs the round-4 run; per-run exact-span recall, character coverage, release rate
  and FR on the subset; per-run FR decomposition. 120 calls.
- No tuning in response to results; all raw responses archived.

## 3. Second model family (new calls, pre-registered)

- Extractor: `online_alt` (glm-5.2, GLM family — different from Qwen), same 60-instance
  subset, same round-4 frozen prompt byte-identical, submitted seed 20261128.
- Same metrics as §2 plus the full metric set (task recall, over-extraction,
  fallback trichotomy, paired CL−GEN with the mean-identity assertion). 60 calls.
- Diagnostic only; no claim about local deployment of either family.

## 4. Holdout-4 and complete-taxonomy validation (new data + new calls)

- **Holdout-4** (`dataset/generate_holdout4.py`, output `dr_sl_holdout_v4.jsonl`):
  NEW template family #4 (2 templates/domain × 4 domains × 10 accepted draws = 80
  instances), values drawn from the v2 pools through `MixRng(seed=20261125,
  p_old=0.5)` (natural vocabulary mix, same mechanism as holdout-3). Templates are
  authored BEFORE any h4 result is inspected, in the same memo/dialogue style as
  families #1/#3, and deliberately include the three previously omitted types
  (`room_no` in travel, `work_years` and `marriage_years` in legal/banking) so the
  taxonomy-completion test is non-vacuous; they also include income phrasings and
  city mentions. Explicit verbatim task per template (same TASK_TYPES as
  `runtime.MIXED_TASK_TYPES`); task-isolation assertions; dedup against all existing
  datasets (exact + 0.95 similarity). Gold types must be a subset of the complete
  taxonomy (no new type may be introduced by h4).
- **Complete taxonomy** `TYPES_V2 = TYPES ∪ {room_no, marriage_years, work_years}`
  (43 types), mechanically derived as the union of gold types over all datasets
  including h4 (verified by the coverage test). **Prompt v2** = round-4 prompt with
  exactly three added type declarations (room_no 房间号, marriage_years 婚龄,
  work_years 工作年限); all other instructions byte-identical. Frozen before any
  h4 call.
- **Neural run**: qwen3.8-max, prompt v2, submitted seed 20261129, 80 extraction
  calls; same localization interface (exact substring, all occurrences,
  longest-first overlap resolution), same gates, task profile "mixed", methods
  closed_loop / generalization_only + coverage-gate variants. Same metric set as
  round 4 plus §1's decomposition and coverage layers.
- **Deterministic reference on h4** (offline, no calls): original AND fixed
  extractor, same methods/gates, same metrics — for context only.
- **Pre-registered expectation**: with the complete taxonomy, `FR_taxonomy_gap` on
  h4 is 0 by construction (coverage asserted); any residual FR is a
  declared-type miss. This validates the taxonomy fix on NEW data; round-4 results
  on h1/h3/drift remain diagnostic under the original incomplete taxonomy and are
  NOT relabelled or recomputed with prompt v2. No prompt amendment after inspection.
- Trust disclosure unchanged: cloud-assisted, diagnostic only.

## 5. Statistics (unchanged)

Instance-cluster bootstrap, 2000 resamples, percentile 95% CIs; paired seed 20261118
with the explicit `paired_delta(left,right)` = left−right API and mean-identity
assertions; Wilson intervals at the independent-instance level for every
FalseRelease proportion (including the two decomposition components); average tied
ranks for Spearman; permutation p uses (b+1)/(B+1). Stability/family comparisons on
the 60-instance subset are descriptive (agreement rates, per-run estimates), not
population CIs.

## 6. Call budget and archiving

260 new extraction calls total (120 stability + 60 second family + 80 holdout-4).
All raw responses, model names, submitted seeds, prompt versions, parse failures,
unlocatable/unknown-type counts are archived in
`results/revision_round3/neural_round5_cache.jsonl` (keyed by prompt-sha256 × model
× seed × prompt version; resumable). Round-5 outputs: `neural_round5_rows.jsonl`,
`neural_round5_summary.json`, `neural_extractor_analysis.json` (P0 recomputation),
`offline_h4.jsonl`, `offline_h4_summary.json`, `ROUND5_NOTE.md`. The freeze manifest
is extended with protocol v5, the h4 generator/dataset, and the new scripts/tests.

## 7. Organization

Length control: the neural subsection is rewritten in place (no net growth target);
round-5 detail tables go to the results archive, with only the decomposition columns
and a compact stability/family/h4 summary in the paper. Revision history stays in
Appendix A. No new main-text experiment beyond §2–§4.
