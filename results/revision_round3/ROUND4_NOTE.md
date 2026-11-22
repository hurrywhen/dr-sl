# Round-4 note (protocol v4) — outputs in this directory

Round 4 corrects computations and adds one pre-registered diagnostic experiment.
No artifact, local decision, threshold, prompt (except the frozen neural-extraction
prompt, fixed before its calls), lexicon or template changed.

1. **D-R18 paired direction.** `downstream_summary.json` and `offline_h3_summary.json`
   were recomputed from archived raw outputs with the corrected `paired_delta(left,
   right)` = left−right API. Downstream CL−GEN is **+0.025 [0, 0.0625]** (primary
   judge online_alt; robustness online_fast +0.025 [−0.0375, 0.0875]); h3 U_delta is
   **−0.101** (original) / **−0.116** (fixed). Round-2 h1/h2 paired values are
   unchanged (verified identical to the archived `offline_summary.json`).
2. **D-R19 dual judges.** `downstream_summary.json` now contains `by_judge` blocks
   for both judges (strata, paired deltas, disagreement counts 2/40 vs 8/40).
   `downstream_r4.log` records the resume run: 0 new answer calls, 0 new judge calls.
3. **D-R20 rename.** `offline_h3.jsonl` rows are identical to round 3 except the
   `U_basis` label (`non_sensitive_context` → `unmarked_context`). Round-1
   reproduction verified 3200/3200 (D, release).
4. **D-R21 neural contrast (new).** `neural_extraction_cache.jsonl` (raw responses,
   model, submitted seed 20261124, per-instance proposals), `neural_extractor_rows.jsonl`
   (method rows under the same gates), `neural_extractor_summary.json`,
   `neural_extractor.log`. 200/200 calls, 0 errors. DIAGNOSTIC ONLY: cloud-assisted
   extraction discloses X; the frozen taxonomy omitted room_no/marriage_years
   (disclosed, not amended post hoc).
5. **D-R22.** `stratified_summary.json` regenerated (embeds corrected downstream/h3
   summaries, neural summary, Wilson intervals, fallback trichotomy fields);
   freeze manifest extended to 38 entries incl. protocol v4 and new scripts/tests.
