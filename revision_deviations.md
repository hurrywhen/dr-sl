# Revision deviations (2026-11-18/19)

These deviations concern the new `revision_20261118` track only. Earlier D1--D18 remain in `experiment_protocol_v1.md` and are historical.

- **D-R1 (generator bug, before evaluation).** `dataset/generate_holdout.py` initially treated entity dicts as tuples in `assemble`. Fixed before any holdout result was produced. No result was reused.
- **D-R2 (duplicate filter, before evaluation).** The initial near-duplicate threshold 0.78 rejected too many instances from the new field-list template family because the templates intentionally share structure. Threshold relaxed to 0.95 before evaluation; exact duplicates still rejected. This changes generation only, not thresholds or analysis.
- **D-R3 (online audit timeout).** The first external-audit run was stopped by a 120 s harness timeout before writing results. It was rerun with a longer timeout. No partial result from the stopped run was used.
- **D-R4 (local neural service unavailable).** The local LLM endpoint was unavailable during this revision. New end-to-end results therefore use the explicit deterministic local track. The neural local-LLM track is implemented but not rerun; no online call is labelled local.
