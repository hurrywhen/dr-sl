# Round-3 audit note for `revision_20261118` / `revision_20261121`

Round 3 (protocol v3, `results/revision_round3/`) touches this directory only as follows:

1. **D-R10 (task metadata).** `dataset/generate_holdout.py` and `generate_holdout2.py`
   now store an explicit `task` field. Before regeneration, prompts, annotations, IDs and
   every other field were verified byte-identical to the frozen files (0 differences on
   80+80 instances). The round-2 freeze-manifest hashes of these two generators therefore
   differ by design; all other round-2 manifest entries are unchanged. Re-running
   `sim/revision_experiment.py` with the current code reproduces all 3200 round-1
   (D, release) pairs exactly (0 mismatches, verified 2026-11-22).
2. **D-R11 (invalid downstream archive).** `downstream_invalid_round2/` holds the round-2
   downstream raw outputs, summary and log. They are INVALID: the last-sentence task
   heuristic returned nearly the full original prompt for 20/80 holdout-1 instances
   (8/40 audited), re-exposing sensitive X to the candidate answer model. The valid rerun
   is `results/revision_round3/downstream_*`. Do not mix the two.
3. **D-R12 (calibration recomputation).** `stratified_summary_round2.json` is the archived
   round-2 stratified summary with the double-argsort Spearman bug. The corrected
   tied-rank analysis is `results/revision_round3/stratified_summary.json`. MAE and
   threshold agreement were unaffected by the bug.
4. Round-2 online raw outputs (`online_audit_raw.jsonl`) are reused unchanged by round-3
   analyses; round-3 adds open-ended attack records in `results/revision_round3/`.

## Round-4 addendum (protocol v4, D-R18/D-R20)

- `sim/runtime.py` changed by a behavior-preserving rename only (fallback basis
  `non_sensitive_context` → `unmarked_context`; `_context_retention` →
  `_unmarked_context_retention`). Its round-2 manifest hash therefore differs by
  design; round-1 (D, release) reproduction was re-verified 3200/3200 after the
  rename. No artifact or decision changes.
- `sim/revision_stats.py` changed by the paired-API replacement
  (`paired_cluster_delta(a,b)`=b−a → `paired_delta(left,right)`=left−right, with a
  mean-identity assertion); all other statistics functions are unchanged.
  `sim/revision_experiment.py` paired call sites swapped arguments to match the new
  explicit-direction API; the recomputed h1/h2 paired estimates and CIs were
  verified **identical** to this directory's archived `offline_summary.json` before
  use. The archive itself was not modified.
- Round-4 outputs (corrected downstream/h3 summaries, neural-extractor contrast)
  live in `results/revision_round3/`; see `ROUND4_NOTE.md` there.
