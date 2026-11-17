# Submission Package — Conference Version (4 pages, two-column IEEE)

Manuscript: **DR-SL: Reversibility-Verified De-identification for Cloud-Local LLM Inference with Layered Assurance**
Derived from the arXiv preprint version (`../latex/main.tex`, 40 pp. single-column) by condensation for a 4-page IEEE conference format.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | Manuscript source (IEEEtran `[conference]`, two columns) |
| `main.pdf` | Compiled manuscript, **4 pages** (limit 4), verified |
| `figures/fig1.pdf` | System-overview figure (vector, cropped in-document) |
| `cover_letter.md` | Cover letter to the TPC chairs (fill placeholders) |
| `declarations.md` | CRediT contributions, COI, funding, data/code availability, ethics, prior-publication & version-relationship disclosure, checklist |
| `build.log` | Last compile log (for reference; not part of submission) |

## Build

```bash
pdflatex main.tex && pdflatex main.tex   # requires TeX Live with IEEEtran, cite, booktabs, algorithm2e not needed here
```

Verified: 4 pages, 0 overfull boxes, all figures/tables placed, references [1]–[21].

## Scope of this version (what was condensed vs the preprint)

- Full proofs, the complete T1–T25 experimental record, the distribution-shift measurement framework, the five-layer theory table, and the applicability-boundary synthesis are **omitted or reduced to statements with pointers to the public preprint/artifacts**; they appear in full in the journal version (`../submission_journal/`).
- Kept: problem formalization (Pufferfish + task preservation), cascade extractor and recall ceiling, two-branch verification, lexicographic loop and mandatory release chain, the four theoretical results with honest scope statements, layered assurance, and the headline empirical results (leakage 0.457→0.304; egress literal leakage 0.000; leakage-utility plane; mixed-coupling 67.5% automatic release with measured Pareto dominance; human anchors ρ=0.839 and recall ≥0.987; honest negative self-learning results; probe-format finding).

## Before submitting (see `declarations.md` §8)

1. Insert the arXiv identifier (manuscript footnote + declarations).
2. Insert the target conference name/year in the cover letter.
3. Confirm funding, IRB-exemption wording, COI signatures, and the venue's double-blind/preprint policy.
4. **Submission order policy:** submit this conference version first; do not submit the journal version anywhere while this paper is under review (see `declarations.md` §6).
5. **Preprint versioning:** arXiv v1 (posted first) intentionally carries no conference/journal markings; do not add venue names to the preprint while any version is under review. Update the arXiv record only upon acceptance, using the ready-to-paste Comments/footnote texts in `declarations.md` §6.

## Post-acceptance record (current status)

- **Accepted.** Final author order: **Ya Yu, Wen Hu, Xutong Wang** (contribution-based for this manuscript; see `declarations.md` §9 and the signed memo `../authorship_contribution_memo.md`); Y. Yu presents at the conference.
- This folder now serves as the camera-ready/archive source: author block, e-mail order, and the named-rater sentence in `main.tex` reflect the final order; recompile before delivering camera-ready.
- The journal version (`../submission_journal/`) cites this paper and discloses the author-order difference; Y. Yu is its corresponding author.
