# Submission Package — Journal Version (≤20 pages, two-column IEEE)

Manuscript: **Reversibility-Verified De-identification for Cloud-Local LLM Inference: A Locally Certified Dehydrate-Rehydrate Loop with Layered Assurance (DR-SL)**
Author order: **Wen Hu, Ya Yu, Xutong Wang**; **corresponding author: Ya Yu**. Derived from the arXiv preprint version (`../latex/main.tex`, 40 pp. single-column) by restructuring and condensation into IEEE journal format; extends the accepted conference version (`../submission_conference/`, order Y. Yu, W. Hu, X. Wang), which it cites.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | Manuscript source (IEEEtran `[journal]`, two columns) |
| `main.pdf` | Compiled manuscript, **16 pages** incl. references and appendices (limit 20), verified |
| `figures/` | fig1.pdf, fig2.pdf (vector, cropped in-document); extractor_recall.png, delta_hist.png, fig_train_loop.png, fig_privacy_gain.png, k_vs_population.png |
| `cover_letter.md` | Cover letter to the Editor-in-Chief (fill placeholders; states preprint + conference-version relationship) |
| `declarations.md` | CRediT contributions, COI, funding, data/code availability, ethics, prior-publication & version-relationship disclosure, checklist |
| `highlights.md` | Optional highlights bullets (≤85 chars each) |
| `build.log` | Last compile log (for reference; not part of submission) |

## Build

```bash
pdflatex main.tex && pdflatex main.tex   # requires TeX Live with IEEEtran, cite, booktabs, algorithm2e, psnfss/courier
```

Verified: 16 pages, 0 overfull boxes; Algorithm 1 (lexicographic loop) set single-column; Appendices A (condensed proofs), B (executable proof-verification methodology), C (frozen semantic-utility judge rubric).

## Scope of this version (relative to the preprint and to the conference version)

- Retains the complete scientific record in journal-condensed form: full method (formalization, cascade extractor + recall ceiling, two-branch verification, lexicographic algorithm), self-learning loop and operationalized distribution-shift framework, five-layer theory and security model with the calibrated-certificate transfer assumption made explicit, layered assurance, limitations, the complete experimental narrative T1–T25 (extraction/annotation reliability and human audits, baseline leakage and calibration, main loop, release-chain audit and probe-format analysis, operating points and human utility anchor, mixed-coupling Pareto comparison, ablations, self-learning tests incl. honest negatives, cost, applicability boundary), condensed proofs, proof-verification methodology, and the judge rubric.
- Versus the 4-page conference version (`../submission_conference/`): adds complete proofs, the full experimental record, the shift framework, the applicability-boundary analysis, extended related work, and the rubric (well beyond the customary ≥30% extension).

## Before submitting (see `declarations.md` §8)

1. Insert the arXiv identifier (manuscript footnote + declarations) and the journal name (cover letter, `\markboth`).
2. Confirm funding, IRB-exemption wording, COI signatures.
3. **Submission order policy:** the conference version is accepted ([venue to be inserted]); this journal manuscript is submitted after the conference outcome, citing the conference paper and describing the extension. The author-order difference between versions (and vs preprint v1) is contribution-based per manuscript and is disclosed in the cover letter, `declarations.md` §6, and the signed memo `../authorship_contribution_memo.md`. No simultaneous review of overlapping content.
4. **Preprint versioning:** arXiv v1 (posted first) intentionally carries no conference/journal markings; do not add venue names to the preprint while any version is under review. Update the arXiv record only upon acceptance (v2 = conference acceptance note; v3 = journal reference/DOI), using the ready-to-paste texts in `declarations.md` §6.
