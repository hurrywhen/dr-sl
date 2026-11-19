# DR-SL major-revision protocol (frozen before holdout evaluation)

Freeze timestamp: 2026-11-18. This protocol governs the new `revision_20261118` experiments. Earlier T1--T25/P1--P41 results are method-development evidence only and are not confirmatory evidence for the revised claims.

## 1. Corrections that do not depend on new results

1. Repeated copies of a question and repeated scores from one enumeration response are not independent Bernoulli trials. The revised release gate is a **heuristic observed-hit-rate gate**, not a Wilson-confidence gate. No pooled zero-hit upper bound is reported.
2. The statistical sampling unit for LLM audit summaries is the instance. Multiple attackers, prompt formats, attributes and repeated calls remain nested within that instance; instance-cluster bootstrap is used. The number of instances, attackers, strategies, model calls and unique questions is reported separately.
3. Runtime policy code receives only `prompt`, `domain`, a declared task-relevance profile, and extractor output. Gold annotations are read only by the external evaluator after the artifact and local decision are frozen.
4. Reference-based online semantic judges are offline criteria only. They never determine local release. External attacks are controlled-disclosure audits, not pre-egress guarantees.
5. Fano bounds are evaluated at the attacker's actual MAP success probability. There is no threshold substitution corollary. Empirical template hit rates are not called MAP probabilities without an explicit sampling model.
6. The rate--privacy statement is expressed only in mutual-information units. QA scores and observed hit rates are not substituted for MI budgets. Low release in medicine is treated as qualitative consistency, not confirmation of the theorem.
7. Termination follows from the finite round budget and finite skip set, not from boundedness of a continuous utility score.

## 2. Frozen runtime configuration

- `N_STABLE = 3`, `DELTA = 0.05`, `TAU_L = 0.05` (point observed hit rate), `TAU_U_LOCAL = 0.50`, and round budget `B = 3 |S| + 5`.
- Stability means three evaluations of the **same frozen artifact**; all three must pass and the ranges of both `L` and `U` over the window must be at most `DELTA`. A changed artifact resets the window. The returned artifact must itself have a complete stable window.
- Local deterministic audit strategies: verbatim occurrence, whitespace/punctuation-normalized occurrence, and full normalized-value enumeration. Strategy hit rates are not concatenated into a larger sample; the maximum strategy rate is the conservative local summary.
- The deterministic runtime extractor combines explicit patterns, public synthetic-domain lexicons and generic labeled-span rules. It does not read item annotations.
- The local utility surrogate is reference-based but fully local: exact retention scores 1, a frozen truthful numeric/date band scores 0.5, and deletion/placeholders/random wrong values score 0 for each runtime task-relevant attribute. Instances without such attributes use non-sensitive context retention. This is a surrogate, not a human-equivalent semantic judge.
- Local release requires both the privacy and local-utility gates plus a complete stability window. The final deterministic all-occurrence scrub is applied before rechecking the gates. Failed or unscorable cases route to human review.

## 3. Frozen methods and fairness

All methods receive the same runtime entities, task profile, local attack strategies, utility surrogate, and release rule:

1. `hardline_only`: typed placeholders for every runtime entity and every occurrence.
2. `generalization_only`: deterministic truthful generalization for task-relevant values, placeholders otherwise, without a closed-loop decision.
3. `closed_loop`: the same generalization operator followed by the stable local gate, final all-occurrence scrub and gate recheck.
4. `intact_style`: an INTACT-inspired abstraction-candidate selector (not the official INTACT implementation), choosing the highest-local-utility candidate that passes the same local privacy gate.
5. `prism_random`: PRISM-style random same-type replacement, with consistent replacement for repeated occurrences of the same entity. It is not labelled LDP and no DP guarantee is claimed.

Self-learning is not a confirmatory condition: its previous preregistered hypotheses were not supported. Existing LLM baselines remain historical exploratory results. The candidate selector is not presented as a reproduction of INTACT, PAPILLON, Presidio, Rehydra or P2Skill.

## 4. Data separation

- Development/exploratory: all previously used test-160, mixed-120, train, calibration, expansion and adversarial data.
- New frozen holdout: 80 newly generated synthetic instances (20 per domain), seed 20261118, independent template family and phrasing, `dataset/output/dr_sl_holdout_v1.jsonl`.
- The holdout generator, runtime configuration, analysis script and this protocol are frozen before summary results are inspected. No threshold, prompt, lexicon or template may be tuned in response to holdout outcomes. Any error correction is logged in `revision_deviations.md` and affected results are regenerated in full.
- External LLM audit subset: the first 10 holdout instances per domain after sorting by ID (40 instances), fixed before model calls.

## 5. Analyses

- Report oracle-S and runtime-S separately on development test-160 and mixed-120; report runtime-S on the untouched holdout.
- Report extraction recall/over-extraction, missed-gold literal exposure, observed local and external attack hits, local utility, offline semantic-judge utility, release rate and human-route rate.
- Means and paired differences use 2,000 instance-cluster bootstrap resamples with percentile 95% intervals and seed 20261118. Release rates use instance-level Wilson intervals only when instances are the independent generated units.
- Permutation/resampling p-values use the finite correction `(b+1)/(B+1)`; `p=0` is forbidden.
- Zero hits are written as **zero observed hits under the specified attackers and grading protocol**, with attack coverage. They are not a statistical guarantee against missed extraction, paraphrase, composition or arbitrary attackers.
- Semantic-judge validation reports overall and within-method Spearman correlations, MAE, instance-cluster intervals, and release/threshold confusion around `U=0.5`. Four-point rank correlation is descriptive only.

## 6. Reproducibility and disclosure

- External models receive synthetic artifacts only and only during the controlled-disclosure audit. Original `X` is supplied to the online reference-based judge solely for offline criterion evaluation, never to the runtime policy.
- Local neural services were unavailable for this revision. The new end-to-end results therefore concern the explicit deterministic local track, not a claimed rerun of the neural local-LLM track.
- Raw prompts, outputs, parse failures, configuration, dataset/result hashes and dependency versions are archived. API keys, private endpoints and local credentials are excluded from the repository.
