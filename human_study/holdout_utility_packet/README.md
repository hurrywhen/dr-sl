# Holdout utility scoring packet — PREPARED, NOT COLLECTED

Status: **prepared but not collected.** No human ratings exist yet for the holdout; this packet is published so the scoring design is transparent and reproducible. No synthetic "human" scores were invented.

- 40 holdout-1 instances × 3 variants (direct / closed_loop / generalization_only) = 120 blinded rows, shuffled with seed 20261121.
- Raters: the two co-author expert raters (Y. Yu, X. Wang), blinded to variant identity.
- Scale: 0 = unusable, 0.5 = partially usable, 1 = fully usable for the embedded task.
- `scoring_sheet.csv` has empty score columns to be filled independently by each rater.
- `blind_key.json` is included for reproducibility. Because this packet is prepared-but-not-collected and the shuffle is seed-deterministic, any future real scoring should regenerate blinding with a fresh seed and withhold the key from raters until both finish.

Planned analysis (future work): inter-rater agreement, human vs local-surrogate and human vs offline-judge correlation with instance-cluster CIs, and threshold confusion. Until collected, holdout utility claims rest on the offline judge and downstream-task judge only, both external references with measurement error.
