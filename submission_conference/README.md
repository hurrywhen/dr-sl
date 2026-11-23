# Camera-Ready Package — IEEE ISAICS 2026 Accepted Version (4 pages, two-column IEEE)

Manuscript: **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**

Condensed from the authoritative main version (`../latex/main.tex`, submission-final). **Accepted to IEEE ISAICS 2026**; proceedings DOI/pages remain pending. Author order is Ya Yu, Wen Hu, Xutong Wang. This is a failure-analysis and reproducible-audit study; the closed loop is an audited object, and all conclusions are scoped to the audited implementation and author-constructed synthetic tests. Earlier preprint: arXiv:2609.14883v1 (different title and earlier claims). See `../SUBMISSION_STATUS.md`.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | Manuscript source (IEEEtran `[conference]`, two columns) |
| `main.pdf` | Compiled manuscript, **4 pages** (body 3 pp.; references fill p. 4), 0 overfull, 0 undefined references |
| `revision_results_conf.tex` | Auto-generated four core result tables (domain/dose values in prose; from `sim/make_revision_tables.py` — do not edit by hand) |
| `cover_letter.md` | Cover note for the accepted IEEE ISAICS 2026 version |
| `declarations.md` | CRediT contributions, COI, funding, data/code availability, ethics, prior-version disclosure, checklist |
| `figures/` | Legacy figure from the pre-revision method paper; **not referenced** by the current manuscript |
| `build.log` | Last compile log (for reference; not part of submission) |

## Build

```bash
pdflatex main.tex && pdflatex main.tex   # requires TeX Live with IEEEtran, cite, booktabs
```

## Scope of this version (what was condensed vs the main version)

- Kept: the three core findings (false release with Wilson intervals; unmarked-context fallback mechanism and coverage-gate audit; no closed-loop increment with corrected paired deltas and full dual-judge reporting), vocabulary stress/dose–response, fixed-extractor contrast, diagnostic neural-extractor contrast with FR source decomposition and round-5 credibility checks plus round-6 repeated-mention, definitional-zero, direct-extraction and gold-literal-construct corrections, external audit and corrected calibration, downstream reference-answer preservation, scoped residual-report finding, and the merged result tables.
- Omitted or reduced to statements: full proof sketches and theory appendix, human-study details, two-type residual probe table, open-ended attack table, reproducibility appendix, and the revision-history appendix (all in `../latex/main.tex` and `../submission_journal/`).

## Before submitting (see `declarations.md`)

1. Insert the target conference name/year in the cover letter; confirm the page limit (current draft 4 pages).
2. Confirm funding, IRB-exemption wording, COI signatures, and the venue's double-blind/preprint policy.
3. Author order and any corresponding-author designation follow `declarations.md` and the per-version memo `../authorship_contribution_memo.md` (signatures pending); fields requiring author confirmation are marked there.
4. **Conference acceptance is confirmed for IEEE ISAICS 2026**; insert proceedings DOI/pages when assigned. The journal package is prepared separately; do not hold overlapping versions under simultaneous review (see `declarations.md`).
5. **Preprint versioning:** arXiv:2609.14883v1 is the earlier record. Any update should distinguish that text from the revised audit manuscript and follow publisher policy; no upload is claimed by this package.
