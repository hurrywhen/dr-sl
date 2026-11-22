# Round-5 note (protocol v5) — outputs in this directory

Round 5 corrects the round-4 neural contrast's interpretation (P0, recomputation
from the byte-intact round-4 archive) and adds pre-registered credibility
experiments (P1). No round-4 artifact, decision, threshold or prompt was altered;
the round-4 neural archive (`neural_extraction_cache.jsonl`,
`neural_extractor_rows.jsonl`, `neural_extractor_summary.json`) is byte-intact.

1. **D-R25/D-R26 P0 re-analysis.** `neural_extractor_analysis.json`: taxonomy
   omission is THREE types (room_no, marriage_years, work_years) on h1/drift
   (h3 fully declared); FR decomposition — h1 5/31 and drift-p0 2/15 entirely
   room_no taxonomy gap, h3 4/24 entirely declared city misses (never proposed);
   three coverage layers (exact-span recall 0.965/0.973/0.965; sensitive char
   coverage 0.983/0.988/0.983; literal residue = FR); partial-span-only gold
   values 10/10/4 (all income, verbatim locatable substrings); n_unlocatable=0.
   Bound scoping: recall conservative under prompt/taxonomy; FR conditional, no
   general bound direction. Automatic coverage test: `sim/test_neural_taxonomy.py`.
2. **D-R27 stability (120 calls).** `neural_round5_cache.jsonl` (conditions
   stability_r1/r2, seeds 20261126/20261127, round-4 prompt byte-identical,
   60-instance subset). Entity-set agreement vs round-4: 95.0%/91.7%; release and
   FR instance sets identical across all three qwen runs (FR 3/20 [5.2,36.0]).
3. **D-R28 second family (60 calls).** Condition family_glm (glm-5.2, seed
   20261128, same subset/prompt). Agreement 68.3% (Jaccard 0.925); recall 0.959;
   FR 5/25 = same 2 room_no gap + 3 zero-valued charge misses (never proposed).
4. **D-R29 holdout-4 + complete taxonomy (80 calls).** New dataset
   `dataset/output/dr_sl_holdout_v4.jsonl` (template family #4, MixRng seed
   20261125 p_old 0.5, realized old fraction 0.393; contains the three omitted
   types, 10 instances each). Condition h4_complete: prompt v2 (43-type complete
   taxonomy, minimal delta), seed 20261129. Gap FR 0/32 [0,10.7] as
   pre-registered; total FR 1/32 [0.6,15.7] (one city miss, same literal as h3);
   recall 0.986, char coverage 0.993, release 40.0%, U delta −0.119.
   Deterministic reference: `offline_h4.jsonl` / `offline_h4_summary.json`
   (original FR 100% [93.0,100]; fixed 84.0% [71.5,91.7]; U deltas negative).
5. **Outputs.** `neural_round5_rows.jsonl`, `neural_round5_summary.json`,
   `neural_round5_subset.json` (pooled subset metrics incl. round-4 reference),
   `neural_round5.log` (260/260 calls, 0 errors), `neural_round5_rerun.log`
   (D-R30 grouping fix rerun, 0 new calls). `stratified_summary.json`
   regenerated: embeds the round-5 analyses and extends the freeze manifest to
   45 entries (protocol v5, h4 generator/dataset, new scripts/tests). The
   round-4 manifest (38 entries) is preserved in git history at commit 12846b7.
6. **Trust.** All round-5 neural conditions remain cloud-assisted DIAGNOSTIC
   contrasts (extraction discloses X); none is a deployable local gate. The
   local neural service remains unavailable; no local-neural claim is made.
