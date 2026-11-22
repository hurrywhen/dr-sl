# Submission Package — Journal Version (two-column IEEE, 11 pages)

Manuscript: **Auditing Local Release Gates for Cloud-Local LLM Inference: Failure Modes of a Runtime-Sensitive-Set De-identification Chain**

Generated from the authoritative main version (`../latex/main.tex`, 19 pp. single-column, round 5) by `sim/make_journal_version.py` (IEEE journal format; the script also copies `revision_results.tex` and widens the 7-column neural table to `table*`). Author block follows the main version; author-order/corresponding-author disclosures and any fields requiring author confirmation are in `declarations.md` and the signed memo `../authorship_contribution_memo.md`. This is a failure-analysis and reproducible-audit study; all conclusions are scoped to the audited implementation and author-constructed synthetic tests.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | Manuscript source (IEEEtran `[journal]`, two columns; regenerated — do not edit by hand) |
| `main.pdf` | Compiled manuscript, **11 pages** incl. references and appendices, 0 overfull, 0 undefined references |
| `revision_results.tex` | Auto-generated merged result tables (10 tables; from `sim/make_revision_tables.py` — do not edit by hand) |
| `cover_letter.md` | Cover letter to the Editor-in-Chief (round 5; fill journal-name placeholder) |
| `declarations.md` | CRediT contributions, COI, funding, data/code availability, ethics, prior-version disclosure, checklist |
| `highlights.md` | Optional highlights bullets (≤85 chars each, round-5 findings) |
| `figures/` | Legacy figures from the pre-revision method paper; **not referenced** by the current manuscript |
| `build.log` | Last compile log (for reference; not part of submission) |

## Build

```bash
python3 ../sim/make_journal_version.py     # regenerate main.tex AND copy/widen revision_results.tex
pdflatex main.tex && pdflatex main.tex     # requires TeX Live with IEEEtran, cite, booktabs, algorithm2e
```

## Scope of this version

- Retains the complete round-5 audit record in journal format: release chain and trust boundaries, audit framework (conditional FalseRelease with gold/LLM/open scopes, stratification, instance-cluster inference, tied-rank Spearman), all results (false release, fallback mechanism, no-loop-benefit with corrected paired deltas, vocabulary stress and dose–response, fixed-extractor contrast, diagnostic neural-extractor contrast with FR source decomposition and round-5 stability/second-family/holdout-4 complete-taxonomy validation, external audit and calibration, dual-judge downstream reference-answer preservation, scoped residual reports and two-type probe, human-study reanalysis, exploratory self-learning), discussion, limitations, and appendices (compressed revision history, theory positioning with proof sketches, reproducibility).
- Versus the 4-page conference version (`../submission_conference/`): adds the full framework, mechanism and probe tables, open-ended attack, human-study reanalysis, theory appendix, revision-history appendix, and reproducibility appendix.

## Before submitting (see `declarations.md`)

1. Insert the journal name (cover letter, `\markboth`) and confirm the page limit (current draft 11 pages).
2. Confirm funding, IRB-exemption wording, COI signatures, and author-order/corresponding-author fields marked for confirmation.
3. **Venue/acceptance status is to be confirmed**; no acceptance is claimed by this package. Do not submit overlapping content simultaneously elsewhere (see `declarations.md`).
4. **Preprint versioning:** do not add venue names to the arXiv preprint while any version is under review; update the arXiv record only upon acceptance.
