# Downstream round-2 outputs — INVALID (task contamination)

These files are the round-2 downstream experiment outputs. They are **invalid** and
must not be used or mixed with the round-3 rerun (`results/revision_round3/downstream_*`).

**Reason (review round 3, P0):** `extract_task` inferred the task from the last sentence
of the prompt. For single-sentence field-list templates (20/80 holdout-1 instances; 8/40
audited), the "last sentence" was nearly the entire original prompt, so the candidate
answer model received both the de-identified artifact D **and** the full sensitive
original X via the task string. This breaks candidate/reference isolation. Dialogue
templates also misidentified staff/symptom utterances as the task.

The reported round-2 values (0.750 / 0.848 / 0.618) are therefore not valid evidence.
The contamination direction cannot be assumed; the experiment was fully rerun with
explicit task fields, runtime isolation assertions, artifact-hash answer caching, a
submitted paired seed, and two independent judges. See `revision_protocol_v3.md` §2,
`revision_deviations.md` D-R11, and `sim/revision_downstream.py`.

Files:
- `downstream_raw.jsonl` — invalid judged records (round 2)
- `downstream_summary.json` — invalid summary (round 2)
- `downstream.log` — round-2 run log
