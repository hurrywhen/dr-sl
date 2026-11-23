# Round-6 note (protocol v6) — archived-output corrections, no new calls

Round 6 corrects mechanism/construct interpretations from round 5. It introduces
no model calls, datasets, prompts, release decisions or primary FR changes. The
round-4 neural archive and `neural_round5_cache.jsonl` were SHA-256 verified
byte-intact after all reanalysis. Derived summaries were regenerated; the new
round-6 evidence is in `neural_round6_analysis.json`.

1. **Symmetric residue relations (D-R32).** `sim/revision_neural_analysis.py`
   now distinguishes exact_proposal, gold_substring_of_proposal,
   proposal_substring_of_gold, related_but_noncontaining_proposal and
   never_proposed. GLM's three bank cases proposed and scrubbed `0元手续费`;
   the appended short `0元` remains. They are repeated-mention span variants,
   not never-proposed omissions. Same-type matches are primary; incidental
   cross-type numeric substrings are retained as secondary matches.
   `sim/test_neural_residue.py` pins all five relations, the archived examples,
   and a long/short repeated-mention scrub regression.
2. **Holdout-4 direct evidence (D-R33).** Complete-taxonomy FR_gap=0/32 is a
   definitional identity, not performance evidence. room_no, marriage_years and
   work_years each have 10/10 exact type-and-value extraction and zero released
   residue. City has 60 gold values: 59 exact by value, 54 exact with a city
   label (five address), and one released residue (DRSL-H4-TRA-0004).
3. **City explanation remains open.** The repeated county literal may be a
   value/template omission or a city/county/administrative-region/address type
   boundary. Current outputs do not distinguish these explanations. No new
   causal experiment was run; a minimal controlled comparison is future work.
4. **Construct and zero-charge sensitivity (D-R34).** FR_gold is a gold-
   annotated literal-residue audit proxy, not demonstrated privacy damage.
   `0元` is a conservative personal-financial/task annotation, not a claim of
   stand-alone identifiability. Whole-thousand quantization in the frozen
   small-fee generator produces zero values; data were not changed. Excluding
   exact zero-yuan charge residues changes only family_glm FR (5/25→2/25, both
   room_no gaps). All deterministic and other neural FR counts are unchanged:
   det h1 36/46 original and 0/46 fixed; det h3 44/44 original and 34/41 fixed;
   det h4 51/51 original and 42/50 fixed; det h2 75/75 original and 70/70 fixed;
   deterministic drift 37/37, 32/32, 29/31, 24/26, 19/23; neural h1 5/31,
   h3 4/24, drift 2/15, qwen subset repeats 3/20 and h4 1/32. The primary
   metric is unchanged.
5. **Reproduce.** `python3 sim/revision_neural_analysis.py`,
   `python3 sim/revision_neural_round5.py` (cache only in this round),
   `python3 sim/revision_neural_subset.py`, then
   `python3 sim/revision_neural_round6.py` and
   `python3 sim/test_neural_residue.py`. `stratified_summary.json` embeds the
   round-6 analysis and carries the extended 48-entry freeze manifest.
6. **Trust/scope.** All neural conditions remain cloud-assisted DIAGNOSTIC
   contrasts, not deployable local gates. Second-family evidence means similar
   inheritance with different miss/span identity, not identical failures.
   Third-party data, human holdout scoring, local neural execution and
   non-literal attacks remain outside this round.
