# DR-SL revision protocol v6 (frozen before round-6 code changes and revised outputs)

Freeze timestamp: 2026-11-23 (round 6). This addendum governs the corrections
requested by the sixth review. It does not alter the audited runtime, any frozen
prompt/taxonomy, any dataset, any release decision, or rounds 1–5 raw outputs.
The reviewer-identified facts were verified read-only before this freeze; the
rules below are fixed before changing classifiers or generating revised analysis
files. There are **no new model calls** and no new holdout. Round-4 neural raw
archives and the round-5 extraction cache remain byte-intact. Derived summaries
may be regenerated deterministically; round-6-specific analyses are written to a
new file. Deviations are logged from D-R32 onward.

## 1. Symmetric proposal–residue classification (P0)

Replace the asymmetric declared-miss classifier. For each residual gold literal,
compare it with all raw proposals (before localization/scrubbing) and record all
matching proposals plus one primary relation, using this precedence:

1. `exact_proposal`: a proposal value equals the gold value;
2. `gold_substring_of_proposal`: the gold value is a proper substring of a
   proposed longer/extended span (e.g. gold `0元`, proposal `0元手续费`);
3. `proposal_substring_of_gold`: a proposal is a proper substring of the gold
   span (the income partial-span case);
4. `related_but_noncontaining_proposal`: no containment relation above, but a
   proposal of the same declared type exists, or a proposal shares a contiguous
   substring of at least two characters covering at least half the gold literal
   (a lexical diagnostic only, not semantic equivalence);
5. `never_proposed`: none of the above.

This classification explains proposal/span relations only; it does not by itself
prove the root cause of residue. The three GLM zero-charge cases must be
`gold_substring_of_proposal`, with the extended proposal and final short-form
residue archived. The mechanism description is: the extended fee span was
proposed and scrubbed, while the short form repeated in the appended
clarification remained. FR counts and release decisions must not change.

Add regression tests for all five relations and for a repeated long/short mention
where scrubbing the extended span leaves the short gold literal. Also pin the
three archived GLM examples so `never_proposed` cannot be reintroduced for them.

## 2. Holdout-4: definitional zero versus direct extraction evidence (P0)

`FR_taxonomy_gap = 0` under the complete taxonomy is a **definitional identity**:
the coverage test asserts that every h4 gold type is declared, so no residual can
be taxonomy-gap by definition. It is not independent evidence of extraction or
safety improvement and must not be described as a pre-registered performance
success. The Wilson interval for that structural zero may remain in the table,
but its caption must state this interpretation.

The direct validation evidence is instead computed from the archived h4 outputs:
for every gold type, report (a) value-level exact extraction (existing recall
convention, label ignored), (b) type-and-value exact extraction, and (c) residual
instances among released closed-loop artifacts. In particular, verify and report
room number, marriage duration and work tenure extraction and residue directly.
For city, keep the value-level and type-consistent counts separate; an `address`
label is not a `city` label even when the value/span is exact.

## 3. Persistent city residue: competing explanations (P1)

Do not call the repeated `望海县` residue an established value-specific blind
spot. Describe it as a reproducible city-literal omission with at least two
unresolved explanations: value/template-specific omission and a
`city`/county/administrative-region (`address`) type-boundary mismatch. The
current experiments do not identify which explanation holds. A minimal
county/city and broader-location controlled comparison is future work; no such
new model experiment is performed in this round.

## 4. Gold-literal residue as an audit proxy, and zero-charge sensitivity (P1)

Clarify at metric definition and limitations that `FR_gold` measures residue of
gold-annotated task/sensitive literals, not demonstrated privacy damage or
re-identification. Distinguish explicit identifiers, quasi-identifiers, and
task-critical values whose stand-alone sensitivity can be context-dependent.
Sensitivity depends on context, combinations, auxiliary knowledge and linkability.

The annotation handbook already classifies personal financial amounts as quasi-
identifiers and banking charges as task-relevant. Document that this conservative
annotation rule also covers `0元`; it is not a claim that a zero fee alone is
private or identifying. Also disclose that the frozen small-fee generator's
whole-thousand quantization makes its nominal 5–200 range produce `0元`; the
frozen datasets are not retroactively changed.

As an additional archived sensitivity analysis (not a replacement metric), remove
residual hits whose gold type is `charge` and whose value is the exact zero-yuan
form `0元`, keeping release denominators fixed. Recompute affected FR counts for
the core deterministic contrasts and all round-5 neural conditions. Report the
GLM subset result explicitly, including if its declared-type-miss component
vanishes under this stricter proxy. State whether the main deterministic FR
counts change. Do not silently apply this exclusion to the primary FR metric.

## 5. Scope, organization and synchronization (P0/P1)

The Route-A audit-case-study positioning, cloud-only diagnostic disclosure,
single-run/instance-level interval limitations, and family-dependence of miss
identity remain unchanged. The second-family result supports similar inheritance
and different miss/span identity, not identical failures across models. No
third-party corpus, human utility labels, local-neural track or new attack family
is added, consistent with the user's prior scope decisions; these remain stated
limitations/future work.

Update derived JSON, automatic tests, main paper, conference version, generated
journal version, README, English mirror, declarations, cover letters, highlights,
arXiv abstract and archive notes. Preserve historical protocols/deviation entries
as history and add an explicit round-6 correction record. Length must not grow:
target main 19 pages, journal 11 pages, conference 4 pages, with zero overfull
boxes and zero undefined references. Extend the freeze manifest to protocol v6
and the new analysis/test scripts; verify all test suites and raw-archive hashes.
