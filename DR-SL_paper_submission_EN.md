# A Self-Learning De-identification Loop with Reversibility Verification: Sensitive-Information Isolation for Cloud-Local LLM Inference

**Dehydrate-Rehydrate with Reversibility-Guided Self-Learning Loop (DR-SL)**

*(Author list and affiliations to be added at submission.)*

Wen Hu¹'², Ya Yu¹, Xutong Wang¹
¹ College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China
² Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Jiangsu, China
huwen@nuaa.edu.cn · 15949116139@163.com · wsgxt@outlook.com

*(Submission version v1.2-EN. The Chinese working version with full revision history is maintained in the companion repository.)*

* * *

## Abstract

Cloud-local LLM inference must keep sensitive user data on-device while exploiting cloud-grade reasoning, yet existing sanitization approaches—placeholder substitution, differential-privacy perturbation, skill distillation—lack a release decision that is simultaneously safe and utility-preserving. We propose **DR-SL (Dehydrate-Rehydrate with Self-Learning loop)**, which formalizes de-identification completeness as two measurable conditions—**de-identification sufficiency** under Pufferfish semantics and **task-information preservation** via QA probes—and decides releases with a fully local two-branch verifier under a lexicographic gate with guaranteed termination, backed by a deterministic hard line, an external strong-attacker re-test, and human fallback. Theoretically we prove Fano-type lower bounds, a Pufferfish witness, and a rate-privacy feasibility criterion, and we state their scope plainly: the bounds certify leakage, never safety, and are near-vacuous at our operating point—release safety rests on empirical calibration, the hard line, and human review. On a worst-case fully task-coupled benchmark, the loop reduces leakage 0.457→0.304 (p≈0) and the release chain delivers **0.000** literal leakage at egress (160 instances, two strong attackers), with the system honestly degrading to a certification-and-routing mode exactly as the feasibility criterion predicts. On a mixed-coupling benchmark the same safe point releases **67.5%** of instances automatically at zero measured leakage, Pareto-dominating placeholder and selective-LDP corners under an identical release rule. Two human studies anchor the semantic utility metric (Spearman ρ=0.839) and the annotation gold (type-level recall ≥0.987). The exploratory self-learning hypothesis was not supported and is reported as such. All theory bounds pass executable numerical verification; code, synthetic datasets, protocol, and human-study packages are public.

* * *

## 1 Introduction

### 1.1 Background and Motivation

A fundamental security tension exists between the reasoning capability of large language models and their deployment paradigms. Cloud models (proprietary APIs or large open-weight models) offer stronger reasoning, planning, and tool use, but user requests must leave the local device, exposing sensitive data to interception, retention, and misuse by the service provider; local small models (SLMs) protect data on-device but reason weakly. Cloud-local LLM inference systems [1,2,3,4] seek both cloud-grade reasoning and on-device data protection, under the core constraint that **cloud-bound requests must exclude personally identifiable information (PII) to prevent external data leakage** [5,6]. Yet the question "how to guarantee the cloud receives only non-sensitive content" still lacks a decision mechanism that is both safe and practical: a lax decision leaks; a strict one strips task semantics and degrades reasoning quality.

The problem is acute in real scenarios such as medical consultation and financial services. For example, a user types on a local device: "I am 67, had a stent procedure in the cardiology department of XX Hospital three months ago, and take aspirin daily; I would like advice on post-operative exercise." The combination of age, hospital, surgical history, and medication uniquely identifies the individual even without a name or ID number. Forwarding it to the cloud constitutes quasi-identifier-level leakage [28]; crudely deleting all details leaves the cloud unable to give any useful advice.

### 1.2 Three Fundamental Defects of Existing Approaches

Existing methods fall into three classes. First, entity-level placeholder substitution [7,8,9] (e.g., Rehydra, Presidio) replaces names, emails, and keys with placeholders and restores them later. It is deterministic and auditable, but covers only *declared* identifiers; it cannot handle semantic/quasi-identifier leakage—where the dehydrated text contains no explicit identifier yet a combination of non-sensitive attributes still uniquely points to an individual. Placeholder substitution also destroys task-critical context, and restoration depends on a local mapping table, failing for semantically equivalent but literally different content. Second, differential-privacy perturbation [10,11] protects privacy by injecting noise, which necessarily harms the semantic coherence of downstream reasoning, with an inherent privacy-utility trade-off [12]; text-level DP rewriting (e.g., SANTEXT [34]) is subject to the same trade-off. Third, the recent skill-distillation method P2Skill [13] has a local SLM perform decomposition, routing, paraphrasing, and reconstruction while a cloud model guides skill refinement in a loop. P2Skill is closest to our problem, but has two key gaps:

- **(i) Cloud dependence during refinement.** Verbatim verification ([13] §3.3, "Iterative refinement loop", steps 2–3) shows that in P2Skill's refinement loop the cloud LLM, in its *reference* role, "answers the original prompt directly", and in its *evaluator* role scores the triple **(x, y_s, y_r)**, where x is the PII-bearing original input; its refinement corpus explicitly mixes in PII samples ([13] §4.1). That is, **before skill refinement completes, PII-bearing refinement data must leave the device.** For fairness: during *deployment*, P2Skill's outbound requests pass a deterministic identifier matcher and contain only sanitized content, and its supervisor role receives only aggregate statistics—its leakage point lies in the refinement phase, not the inference phase.
- **(ii) Coverage and decision gaps.** Its deterministic matcher covers only declared identifiers, missing semantic/quasi-identifier leakage and context loss from over-redaction ([13] §4.4 itself attributes residual leakage to missed detections at the decomposition stage).

All three classes additionally share a third defect: sanitization pipelines are one-shot scripts lacking cross-instance reuse and self-improvement. Every new input restarts strategy design or iteration from scratch; the system cannot learn from past successes/failures nor converge over deployment time to fewer iterations and higher success rates.

### 1.3 This Work

We propose **DR-SL (Dehydrate-Rehydrate with Self-Learning loop)**, addressing these gaps at three levels:

1. **Decision level (reversibility verification).** De-identification completeness is formalized as two complementary, measurable conditions—**de-identification sufficiency** (Pufferfish semantics [25,26]: the dehydrated artifact alone cannot support re-identification of sensitive information) and **task-information preservation** (measured by QA probes)—with the cascade extractor's recall explicitly delimiting the guarantee boundary. The decision mechanism runs entirely locally, driven by a local model and prompts; **nothing leaves the device before the completeness decision is made.** We state honestly: the leakage score produced by a local evaluator is a **lower-bound witness** of true leakage (Theorem 2′)—a heuristic certificate, not an absolute upper bound; we strengthen it via offline empirical calibration (§5.2) and a layered assurance model (§5.4).

2. **Mechanism level (self-learning loop).** Instance-level fixes are elevated to prompt-level global optimization through attribution, experience accumulation, prompt distillation, and versioned updates, with typed prompt libraries and hot-start, so that loop counts tend to decrease with accumulated experience (a design expectation, tested as hypothesis H1).

3. **Theory level (information-theoretic grounding).** A five-layer theoretical architecture characterizes the method's limits and boundaries—Pufferfish target semantics, Maximal Leakage as the attacker-independent limit [27], the rate-privacy frontier (utility-privacy Pareto limit), Wyner-Ziv conditional rate-distortion (fidelity limit), and an empirically calibrated approximation layer; we prove a leakage lower-bound theorem (Fano-type), a Pufferfish witness proposition, a feasibility criterion, and a termination theorem.

### 1.4 Contributions

- A two-branch de-identification-completeness framework centered on **reversibility verification**, covering de-identification sufficiency (including semantic/quasi-identifier leakage) and task-information preservation (including over-redaction detection), together with a runtime cascade extractor for S and a recall-ceiling analysis;
- The **theoretical positioning** of the method: lower-boundedness of the leakage score (correcting a directional error), the Pufferfish witness, the rate-privacy feasibility criterion, termination of the lexicographic iteration, and the explicit stance of "an empirically calibrated heuristic certificate approaching theoretical limits";
- A **fully local self-learning loop** (the offline stage touches only non-sensitive corpora) and a **layered assurance model** (soft certificate + deterministic hard line + human fallback), with a complete pre-registered experimental design.

### 1.5 Organization

Section 2 surveys related work; Section 3 formalizes the problem, the runtime extraction of S, the two-branch reversibility verification, and theoretical properties; Section 4 presents the self-learning loop and an operationalized measurement framework for offline-online distribution shift (§4.7); Section 5 gives the theoretical grounding and discussion (security model, layered assurance, model selection, limitations); Section 6 presents the experimental design and results (including shift and proof-verification experiments); Section 7 concludes. Appendix A contains complete proofs; Appendix B the proof-verification methodology.

* * *

## 2 Related Work

### 2.1 Cloud-Local LLM Inference and Privacy Protection

Cloud-local inference systems deploy a small model on-device and a large model in the cloud, routing simple or privacy-sensitive sub-tasks locally and forwarding complex reasoning to the cloud [1,2,3,4]. Representative work includes hybrid SLM/LLM edge-cloud collaborative inference [1], the adaptive cloud-edge framework CE-COLLM [2], a survey of edge-SLM/cloud-LLM collaborative inference and learning [3], and PAPILLON [4], which formulates Privacy-Conscious Delegation with a local privacy-aware proxy deciding which requests to forward—a canonical "local routing" design.

For privacy-preserving inference, cryptographic approaches [16,17] offer strong guarantees but require specialized primitives and complex multi-party infrastructure, with high latency and deployment cost; NER-based de-identification [7,8] strips identifiable spans but loses task-critical context; local differential privacy (LDP) [10,11,12] perturbs tokens before transmission, but noise harms coherence and the privacy-utility trade-off is inherent; PrivacyRestore [9] removes privacy spans client-side and restores them server-side via meta-vectors—a "server-side restoration" paradigm complementary to, but different from, our "decide-before-egress" local loop; its restoration relies on cloud processing of meta-vectors, whose own sensitivity warrants assessment (this is our inference; see the table note in §2.7). Overall, privacy modules are trained as separate components requiring per-deployment adaptation [13], and a unified "is de-identification complete?" decision mechanism is missing.

### 2.2 The Sanitize-Rehydrate Paradigm and Reversible Anonymization

Reversible anonymization is an emerging direction, represented by Rehydra [8] and Presidio [7]. Their strengths are reversibility, conversational coherence, and session-level identity persistence; but they are essentially per-entity substitution, unprotected against uncovered sensitive types and semantic leakage, and restoration depends on local mapping tables, failing for semantically equivalent but literally different content.

### 2.3 P2Skill and Skill Distillation

P2Skill [13] has a frozen local SLM perform decomposition, PII-aware routing, paraphrasing, and reconstruction via four skill prompts, while a cloud model plays reference, evaluator, and supervisor roles in an iterative loop, distilling "privacy skills" into prompts rather than weights. Its merits: no fine-tuning, no learned auxiliary detectors, and a deterministic identifier matcher as the final gate for cloud-bound content; on 160 PRISM prompts (medical, banking, tourism, general knowledge) it improves privacy-preserved inference quality by 1.69× and 3.66× over baselines. As stated in §1.2 (verbatim-verified and scope-limited): during **skill refinement**, its reference/evaluator branches require the cloud to read original inputs ([13] §3.3, steps 2–3), constituting a refinement-phase leakage point; deployment-phase egress is gated by the matcher; the supervisor receives only aggregate statistics. Its matcher also covers only declared identifiers, and its self-reported residual leakage stems mainly from missed detections at decomposition ([13] §4.4)—mutually corroborating our recall-ceiling analysis in §3.2.

### 2.4 Information-Theoretic Quantification and Privacy Measures

Mutual information (MI) is the classic framework for measuring privacy leakage [14,18]; MINE [14] estimates high-dimensional MI with neural networks; the privacy funnel [15] optimizes the privacy-utility trade-off by minimizing I(sensitive;output) and maximizing I(task;output). Neural MI estimation requires training and per-dataset iteration, unsuitable for real-time per-instance decisions. Closer to this work are two operational theoretical tools: **Pufferfish privacy** [25,26] explicitly declares a secret set and discriminative pairs, bounding how much released data can amplify an attacker's posterior odds—fitting "inference protection over declared secrets"; **Maximal Leakage** [27] is the supremum, over all randomized functions of the source, of the multiplicative increase in guessing probability upon observing the release—attacker-independent, giving a theoretical ceiling on leakage. We anchor our theory in these two and use reversibility verification as the empirical approximation.

### 2.5 Utility Evaluation for Text Sanitization

For utility evaluation, Text Preserved Similarity (TPS) [19] defines sanitization utility as preserved task-relevant information, aligning with our task-information-preservation goal; BERTScore [20] and TAE [21] provide semantic-similarity measures. QA-based evaluation (e.g., QAFactEval [31]) measures information preservation by "can task questions be answered from the text"—the methodological source of our QA probe (§3.3). We take the QA probe as the primary utility metric, the rehydration score as a secondary diagnostic, and validate metric effectiveness with human-substitute cross-model studies.

### 2.6 Self-Learning and Prompt Optimization

Related to our self-learning mechanism are self-refinement methods and automatic prompt optimization, whose shared challenge is preventing prompts from overfitting training/validation cases. Our memorization check (§4.3) and independent generalization scoring target exactly this problem.

### 2.7 Positioning

**Table 1: Comparison of representative methods**

| Method | Leakage coverage | Over-redaction detection | Evaluation/refinement leakage | Cross-instance reuse |
| --- | --- | --- | --- | --- |
| Placeholder substitution (Rehydra/Presidio) [7,8] | Declared identifiers (fact) | None (fact) | None (fact) | None (fact) |
| LDP perturbation [10,11] | Probabilistic (fact) | None (inherent noise loss, fact) | None (fact) | None (fact) |
| PrivacyRestore [9] | Declared identifiers (fact) | Partial (restoration fidelity, fact) | **Yes (cloud processes meta-vectors; our inference)** | None (fact) |
| P2Skill [13] | Declared identifiers + rewriting (fact) | Partial (reconstruction skill, fact) | **Yes: during refinement, cloud reference/evaluator branches read original inputs (fact, [13] §3.3 steps 2–3); none at deployment (fact)** | Limited (skill distillation, fact) |
| **DR-SL (this work)** | **Declared + quasi-identifiers within extractor recall (our claim, conditioned on recall)** | **Yes (task-information-preservation metric)** | **None (offline stage only non-sensitive corpora; online fully local)** | **Yes (prompt library + hot start)** |

*Table note: each cell is marked "fact" (from the cited source) or "our inference/claim". The DR-SL row states our method's claims, substantiated by the experiments in §6.*

* * *

## 3 Problem Definition and Method

### 3.1 Problem Formalization

Let the original material be a random variable X, the sensitive set S = {s_1,…,s_n} (each s_i a sensitive attribute with domain V_i; explicit identifiers or quasi-identifiers), the attacker's auxiliary knowledge A, and the task-relevant variable T. The dehydrator 𝒟 maps X to the dehydrated artifact D = 𝒟(X). At runtime S is produced by the cascade extractor (§3.2). Target conditions:

**De-identification sufficiency (Pufferfish semantics).** We adopt the Pufferfish framework [25,26]: the secret set 𝒮 is induced by S—for each s_i and value v ∈ V_i, the secret proposition σ_{i,v} := "s_i = v"; the discriminative-pair set 𝒬 contains all same-attribute distinct-value pairs {(σ_{i,v}, σ_{i,v′})} and identity pairs (a quasi-identifier combination pointing to a unique individual); Θ is the attacker's prior-belief set. The dehydration mechanism P(D|X) satisfies (ε, 𝒬, Θ)-Pufferfish de-identification sufficiency iff for all (σ,σ′)∈𝒬, θ∈Θ, and outputs d:

    e^{−ε} ≤ P(D=d | σ,θ) / P(D=d | σ′,θ) ≤ e^{ε}        (1)

Semantics: releasing D amplifies the attacker's prior odds on any discriminative pair by at most e^ε. Unlike differential privacy, Pufferfish directly constrains inference about declared secrets without adding noise—precisely what the re-identification branch aims to prevent. Note that the conditional probabilities in (1) are relative to attacker knowledge A (operationalized as graded attackers in §3.3).

**Task-information preservation.** The fidelity goal changes from "restore the original text" to "preserve task-relevant information": maximize I(D;T). Its operational measure is the QA-probe utility score U (§3.3). The original rehydration score R (similarity of X̂ reconstructed from (D,S) to X) is demoted to a secondary diagnostic signal.

**Notation.** Normalized mutual information I_norm(D;S) := I(D;S)/H(S) ∈ [0,1]; binary entropy H_2(·). The mapping between the information-theoretic threshold ε and the operational threshold τ_L is given by Theorem 2′ (τ_L corresponds to a leakage **lower-bound** guarantee).

**Definition 1 (Reversible compression).** If there exists a map f with f(D,S)=X, D is a reversible compression of X with respect to S. This definition is retained as the theoretical object of the rehydration branch (diagnostic).

**Definition 2 (De-identification completeness).** 𝒟's de-identification of (X,S) is complete iff D=𝒟(X) satisfies: (i) the operational criteria L ≤ τ_L (in the Wilson-interval upper-bound sense, §3.3) and U ≥ τ_U; (ii) these criteria hold under extractor recall ρ̂ and attacker class A_3 (conditionality of the guarantee in §5.2).

### 3.2 Runtime Extraction of the Sensitive Set S (Cascade Extractor)

The key premise raised in review—"where does S come from at runtime?"—is answered by a cascade extractor:

- **(a) Regex/NER high-precision layer**: explicit identifiers (ID numbers, phone numbers, emails, names, accounts, etc.), with finite pattern classes and near-complete recall;
- **(b) Local-LLM high-recall layer**: quasi-identifiers (age, department, surgical history, and their normalizations), via an extraction prompt plus a self-critique second pass dedicated to missed items;
- **(c) Combination layer** (DetectCombinable): decides which combinations of extracted attributes constitute quasi-identifiers, emitting combination candidates for the Branch-1 combination questions (§3.3) and the synthetic-population k test (§6).

**Extraction recall**: on a gold-annotated set, Recall = |S_found ∩ S_gold|/|S_gold|, reported stratified (explicit / quasi / overall).

**Proposition 0 (Recall ceiling of system leakage).** Branch 1 probes only extracted attributes; missed attributes are never probed. Worst-case decomposition:

    L_system ≤ L_measured + (1 − Recall)        (2)

Hence every system-level safety conclusion must be conditioned on the measured recall ρ̂: "given extractor recall ≥ ρ̂, system residual leakage ≤ L_measured + (1−ρ̂)". Theoretical limits: explicit-identifier recall can approach 1 (finite pattern class); quasi-identifier recall has no finite upper bound—whether an attribute is identifying depends on the attacker's auxiliary knowledge A, so recall can only be defined relative to a given A as Recall(A). §3.3/§6 therefore report recall and leakage curves over graded attackers A_0–A_3.

### 3.3 Two-Branch Reversibility Verification

**Branch 1 (re-identification branch / de-identification sufficiency).** The evaluator receives only the dehydrated artifact D and general knowledge (plus graded auxiliary knowledge, below), and answers a question set Q constructed from S (Algorithm 1). Probing each attribute m times yields per-attribute hit rates L_i and the overall leakage score:

    L = (1/|S|) Σ_i L_i ∈ [0,1]

**Statistical protocol.** Per-attribute probes m = ceil(75/|S|) (total ≥75, ensuring the gate is passable even at zero hits); L is reported as the mean over probes, and the decision uses a **Wilson confidence interval** [30]: pass iff the 95% Wilson upper bound of L ≤ τ_L. τ_L thus means "a threshold on the interval upper bound of the hit rate", resolving the excessive binomial noise at small |S| (e.g., at |S|=5 a single-point granularity of 0.2 would otherwise be equivalent to zero tolerance).

**Graded attackers (operationalizing A).** The "supremum over A" is operationalized as a maximum over a finite nested attacker set:

| Level | Auxiliary knowledge | Implementation |
| --- | --- | --- |
| A_0 | General knowledge only | Bare local re-identification |
| A_1 | Domain statistical priors | Re-identification prompt injected with domain frequency knowledge |
| A_2 | Public-data retrieval | Re-identification branch augmented with public-corpus RAG |
| A_3 | Linkage-attack database | Synthetic-population k counting (no LLM) |

Knowledge sets satisfy A_0 ⊆ A_1 ⊆ A_2 ⊆ A_3, so the L(A_i) curve should be monotone; non-monotonicity is treated as evaluation instability and triggers review. The system reports the four-level leakage curve (x-axis: attacker level; y-axis: per-instance mean hit rate ± 95% Wilson interval, by domain).

**A_3 k-anonymity test [28]**: for the quasi-identifier combination q extracted from D, count matching records in a synthetic population (§6; the controlled world reuses the dataset generator's distribution, the real-statistics world is built from public marginal distributions via iterative proportional fitting (IPF) [32]; fully synthetic and reproducible):

    k(q) = |{ r ∈ DB : r's quasi-identifier combination matches q }|

Semantics: the attacker can at best narrow the target to a set of k individuals; k=1 means unique identification. The A_3 hit event is defined as k ≤ k* (k*=5 frozen in the protocol), unifying semantics across the four-level curve.

**Branch 2 (rehydration branch / diagnostic).** The evaluator receives (D, S) and reconstructs X̂; Sim(X̂, X) (literal matching primary, BERTScore [20] fallback) gives the restoration score R. R is demoted to a secondary diagnostic: it detects rehydrator hallucination and over-redaction but is no longer the primary fidelity criterion.

**Primary utility metric: QA probes [19,31].** Fully decoupled from restoring the original text; directly measures "task-information availability from the cloud's viewpoint":

1. Generate a task-relevant question set Q_T from X plus the task description (n_q questions, not targeting sensitive attributes themselves; filtered and spot-checked);
2. Reference answers A_ref = ans(q|X) (fixed reference model; self-consistency sampling for open questions; known ground truth for structured ones);
3. Target answers A_D = ans(q|D) (same model, same sampling parameters—exactly the deployment condition);
4. Per-item scoring Agree_j: structured items by exact/tolerance match {0,1}; open items by judge rubric {correct 1, partial 0.5, wrong 0, contradicted 0}, the judge seeing only (q, A_ref, A_D); "cannot determine" counts 0.25 (frozen in the protocol);
5. Utility **U = (1/|Q_T|) Σ_j Agree_j**, reported as per-instance/per-domain means with bootstrap confidence intervals.

**Completeness criterion (operational).** Dehydration succeeds ⟺ WilsonUpperBound(L) ≤ τ_L and U ≥ τ_U (lexicographic; see Algorithm 2′).

### 3.4 Question-Set Generation

**Algorithm 1 (QuestionSetGen)** (as in v1.0, omitted—input S and a typed template library T; instantiate template questions per attribute by type; generate "can the individual be uniquely identified?" questions for DetectCombinable outputs; deduplicate and return Q).

### 3.5 Lexicographic Iteration and Convergence Criteria

The bidirectional same-round update of v1.0 could oscillate without termination guarantees. We switch to **lexicographic optimization**: utility as a hard gate, leakage as a soft objective, single-attribute strengthening, single-step rollback.

**Algorithm 2′: DR-SL per-instance main loop (lexicographic)**

```
Input: original material X, sensitive set S (extractor output, recall ρ̂), thresholds τ_L, τ_U,
       round budget B = 3|S|+5, stability window N, prompt library P, local evaluator M
Output: PASS(D*) or INFEASIBLE(residual_leak_report)

 1: P_init ← HotStart(P, S)                      // type-matched hot start
 2: D ← Dehydrate(X, S, P_init)
 3: Q ← QuestionSetGen(S)                         // Algorithm 1
 4: (L, CI, U) ← Evaluate(M, D, Q, S, X)          // L with Wilson interval; U = QA probe
 5: while U < τ_U and t < B do                    // Phase 1: satisfy the utility gate first
 6:     D ← LoosenDehydrate(D, X, S, P)           // loosen only; no leakage strengthening
 7:     exit phase if two consecutive loosens fail to improve U (no-progress)
 8:     (L, CI, U) ← Evaluate(M, D, Q, S, X)
 9: end while
10: skipped ← ∅; triedLoosen ← ∅
11: while not Pass(L, CI, τ_L, U, τ_U) and t < B do   // Pass := Wilson upper ≤ τ_L and U ≥ τ_U
12:     s* ← argmax_{s_i ∈ S \ skipped} LeakContrib(s_i, D)
13:     D' ← StrengthenAttribute(D, s*, X, S, P)       // single-attribute step
14:     (L', CI', U') ← Evaluate(M, D', Q, S, X)
15:     if U' ≥ τ_U then                              // hard gate: utility never regresses
16:         D ← D'; accept; update stability window
17:     else if s* ∉ triedLoosen then                  // compensatory loosen (one chance)
18:         triedLoosen ← triedLoosen ∪ {s*}
19:         D'' ← LoosenDehydrate(D, X, S, P)
20:         if U(D'') > U then D ← D''; triedLoosen ← ∅; continue
21:         end if
22:         skipped ← skipped ∪ {s*}                   // not strengthenable within gate → residual
23:     else
24:         skipped ← skipped ∪ {s*}; attribute failure → experience store
25:     end if
26:     t ← t + 1
27: end while
28: if Pass(L, CI, τ_L, U, τ_U) and window stable then
29:     return PASS(D)                                 // egress (audit log retained)
30: else
31:     return INFEASIBLE(skipped ∪ failing attributes, with hit-question details)
                                                       // to human review; egress refused
```

Key points: every accepted step maintains U ≥ τ_U (gate invariant; the fidelity criterion *is* task-information preservation, with the rehydration score R as diagnostic only, not part of the gate); after a successful compensatory loosen, triedLoosen resets (new headroom available); skipped attributes permanently enter the residual set, avoiding infinite retries; consecutive no-improvement loosens terminate Phase 1; the hard round budget B guarantees termination (Theorem 3).

**Definition 3 (Stable pass).** Over window W={t−N+1,…,t}: max CI upper bound ≤ τ_L, min U ≥ τ_U, and fluctuations of L (and diagnostic R) ≤ δ.

**Differences from v1.0**: same-round bidirectional updates removed; the utility gate admits only Phase-1 loosening and non-regression thereafter; the loop has a hard budget B; the failure path is a formal INFEASIBLE branch (residual-leakage report), not a deadlock.

### 3.6 Theoretical Properties (Graded)

Grading rule: **Theorem** = full proof (appendix); **Proposition** = proof sketch; **Hypothesis** = to be tested experimentally.

**Proposition 1 (Directional correctness of the two-branch alarm)** [Proposition]. Fix the evaluator's capability. (i) If I(D;S)=0 (D independent of S), then for any template family 𝒬, Branch-1 hit rate does not exceed the prior guessing rate (no information gain); (ii) if H(X|D,S) > η, then any rehydrator has expected restoration score 𝔼[R] < 1. Each branch thus alarms in the correct direction when its sufficiency condition is violated.
_Proof sketch._ (i) Independence ⇒ posterior = prior; no answer beats prior guessing. (ii) Some values of X are not uniquely determined given (D,S); the optimal reconstruction error is positive. ∎
(The strong existential claim "there exists Q with 𝔼[L]>0" of v1.0 Theorem 1(i) is deleted and weakened to the operational correlation statement above; the corrupted formula is fixed.)

**Theorem 2′ (Lower-boundedness of the leakage score, Fano-type)** [Theorem]. Let an attacker (including the local evaluator) achieve per-attribute hit rate L_i on s_i (domain size |V_i|). Then

    I(D;S) ≥ H(S) − Σ_i [ H_2(1−L_i) + (1−L_i)·log(|V_i|−1) ]        (3)

and hence I_norm(D;S) ≥ 1 − Σ_i[·]/H(S).

_Proof._ For each attribute, the optimal attacker's error rate satisfies P_{e,i} ≤ 1−L_i (the measured attacker attains L_i; the optimum is no worse). By Fano's inequality [35]: H(S_i|D) ≤ H_2(P_{e,i}) + P_{e,i}·log(|V_i|−1) ≤ H_2(1−L_i) + (1−L_i)·log(|V_i|−1) (the right side is monotone increasing in the error rate over the relevant range). By entropy subadditivity H(S|D) ≤ Σ_i H(S_i|D); hence I(D;S) = H(S) − H(S|D) ≥ H(S) − Σ_i H(S_i|D), and substitution yields (3). ∎

_Interpretation_ (directional correction): measured attack success gives a **lower bound** on true leakage; stronger attackers can only raise the bound. A local evaluator's failure to re-identify **cannot** prove that no attacker can—the v1.0 "upper bound / err on the strict side" phrasing is revoked. The operational threshold τ_L corresponds to an information-theoretic lower-bound guarantee: L ≤ τ_L ⇒ I(D;S) ≥ H(S) − Σ_i[H_2(1−τ_L)+(1−τ_L)log(|V_i|−1)]. Certificate strength increases monotonically with evaluator capability—the theoretical basis of the "heuristic certificate + empirical calibration" design (§5.2).

**Proposition 2 (Pufferfish witness: hit rate → ε lower bound)** [Proposition]. Let the optimal attacker's hit rate on attribute s_i be L, with prior p_max = max_v P(s_i=v), p_min = min_v P(s_i=v). Then there exists a discriminative pair (σ*, σ′) such that any mechanism satisfying (1) must have

    ε ≥ ln( L/(1−L) ) + ln( p_min/p_max );  with a uniform prior, ε ≥ ln( L/(1−L) ).

_Proof sketch._ For an output d with maximal posterior ≥ L, take v* = argmax_v p(v|d); for any v′: odds_post = p(v*|d)/p(v′|d) ≥ L/(1−L). Bayes gives odds_post = [P(d|v*)/P(d|v′)]·[p(v*)/p(v′)], so the likelihood ratio ≥ (L/(1−L))·(p(v′)/p(v*)) ≥ (L/(1−L))·(p_min/p_max); taking logs gives the ε lower bound for that pair. ∎
_Interpretation_: attacks give a lower bound on the required ε (a leakage witness), same direction as Theorem 2′. Numerically: L=0.9 ⇒ ε ≥ 2.2 (uniform prior); L=0.05 gives only a loose bound—honest phrasing: the certificate is strong only when the evaluator is strong.

**Proposition 3 (Feasibility criterion, rate-privacy frontier)** [Proposition]. For any dehydrator, task-information preservation satisfies

    I(D;T) ≤ I(D;S) + I(X;T|S)        (4)

so the rate-privacy function U*(ε) := max_{p(D|X): I(D;S|A)≤ε} I(D;T) satisfies U*(ε) ≤ ε + I(X;T|S).
_Proof sketch._ Chain rule: I(D;T) ≤ I(D;T,S) = I(D;S) + I(D;T|S); conditional data processing (D generated from (X,S); T a function of X): I(D;T|S) ≤ I(X;T|S). ∎
_Interpretation_: if the utility requirement satisfies τ_U > τ_L + I(X;T|S), the (τ_L, τ_U) feasible region is empty and Algorithm 2′ necessarily outputs INFEASIBLE. When task information is strongly coupled to sensitive information (the medical example: removing age/surgical history makes advice worthless; I(X;T|S) small), the feasible region shrinks or empties—**infeasibility is a property of the problem, not a defect of the method**.

**Theorem 3 (Termination of the lexicographic iteration)** [Theorem]. Algorithm 2′ terminates within finitely many rounds, outputting PASS or INFEASIBLE; and after Phase 1, every accepted step maintains U ≥ τ_U (gate invariant).
_Proof._ See Appendix A.5. ∎

**Hypothesis H1 (Loop-count decrease; to be tested)** [Hypothesis]. Let n_c^{(v)} be the expected initial iteration rounds for type-c material under prompt version v. If distilled rules eliminate generalizable failure modes for type c, then n_c^{(v+1)} ≤ n_c^{(v)}, and expected total iterations decrease across versions. v1.0 stated this as Proposition 2 and claimed the memorization check "guarantees generalization"—too strong; it is now a hypothesis tested by the convergence experiments in §6 (the memorization check only prevents memorizing concrete instances; it does not guarantee generalization).

* * *

## 4 The Self-Learning Loop

### 4.1 Two Levels of Optimization Objects

(As in v1.0: instance-level vs prompt-level; the core principle is elevating instance-level fixes to prompt-level optimization.)

### 4.2 The Attribution–Accumulation–Distillation–Update Loop

(As in v1.0: attribution → accumulation → distillation → update, with the memorization-check constraint.)

### 4.3 Memorization Check

**Definition 4 (Memorization check)** and Algorithm 3 as in v1.0 (literal/normalized value check + quote-length threshold ℓ + generalization-score threshold θ_g), with two corrections:

- **Scoped responsibility**: the memorization check intercepts only literal/quotation leakage; it **no longer claims to "guarantee generalization"** (v1.0 overclaim);
- **Independent GenScore**: the generalization score θ_g is produced by an **independent scorer**—an offline strong model (on non-sensitive corpora) or a local model from a different family than the distiller; self-scoring is forbidden, eliminating circular reasoning.

### 4.4 Prompt Library and Hot-Start Reuse

(As in v1.0: global baseline + typed prompt libraries + hot start.) The loop-count-decrease prediction is demoted to **Hypothesis H1** (§3.6); the abstract says "tends to decrease, to be empirically tested".

### 4.5 Overall Architecture

(Architecture as in v1.0; the decision branch becomes Algorithm 2′'s two exits PASS/INFEASIBLE.)

### 4.6 Two Boundaries

- **Generalization ceiling**: uncovered new types require cold starts; on convergence failure the system identifies a new type and triggers distillation. Loop-count decrease is asymptotic, not one-shot.
- **Overfitting risk**: mitigations are the memorization check, distillation from diverse cases, independent generalization scoring, and version rollback.

### 4.7 Offline-Online Distribution Shift: An Operationalized Measurement Framework

Prompt libraries distilled offline face domain shift relative to the online distribution. This section gives the physical meaning of each theoretical quantity and frozen measurement recipes (protocol §8.1), turning "the generalization problem" into a repeatably measurable object rather than a verbal concern.

**Key claim (safety-efficiency separation)**: distribution shift affects only *efficiency* (iteration rounds) and *utility*, not *safety decisions*—the release decision (re-identification branch + deterministic hard line) is computed online per current instance; the offline prompt library only initializes and never participates in release decisions. The risk of shift is therefore "bounded cost", not "a safety breach". We quantify the efficiency side.

**Theoretical hook (domain-adaptation bound [29])**: let S be the offline distillation distribution, T the online distribution, and h the prompt policy. Then

    ε_T(h) ≤ ε_S(h) + ½·d_{HΔH}(S,T) + λ(S,T)        (5)

Physical meaning and measurement of each term:

1. **ε_T(h) (online expected loss)**: expected loss when the offline-distilled prompt library serves requests drawn from the online distribution. The loss is instantiated per instance (two frozen forms, both reported): ℓ₁ = normalized rounds (actual rounds / budget B); ℓ₂ = 1 − Pass (0-1 convergence failure). Physical meaning: when the offline library meets real traffic, how many extra iterations per request, and what failure probability.
2. **ε_S(h) (offline error)**: mean loss of the same pipeline, same prompts, same loss definition on the offline held-out corpus (the calibration split, non-sensitive by construction). Sharing one loss definition makes the difference comparable. The dataset splits support this natively: calibration→train act as "historical traffic" (visible offline), test(+adversarial) as "online traffic"—**Δ is measurable without real deployment**.
3. **d_{HΔH} (computable proxy of the divergence)**: the sup over the full function class is incomputable. We freeze a finite probe class H_probe (TF-IDF + logistic regression; frozen sentence embeddings + logistic regression; LLM zero-shot discrimination; fixed in the protocol) and compute
   d̂_H = 2·max_{h′∈H_probe} |P_S(h′=1) − P_T(h′=1)|.
   d̂_H is a **lower-bound estimate** of the true divergence on the probe class (sub-class sup ≤ full-class sup) and must not be cited as the true divergence; stronger probe classes give tighter estimates.
4. **λ (joint optimal error)**: generally incomputable; handled by availability: (i) back-computed residual λ ≥ Δ − ½d̂ (primary report); (ii) oracle approximation—distill a domain-specific prompt h* on pooled data and take λ̂ = ε_S(h*)+ε_T(h*) as an upper approximation; (iii) no independent claim otherwise.

**Three measurable proxies** (none touching sensitive values):

- **Domain-discriminator AUC**: sample n=200 from each of offline/online → TF-IDF vectorize → logistic regression, 5-fold CV → AUC ± 95% CI; d̂_H ≥ 2|AUC−0.5|. Reading: AUC ≤ 0.6 negligible shift; 0.6–0.8 moderate; >0.8 severe.
- **Embedding MMD**: maximum mean discrepancy, MMD² = E[k(x,x′)] + E[k(y,y′)] − 2E[k(x,y)] (Gaussian kernel), permutation test with 1000 resamples for the p-value; corroborating evidence for AUC.
- **Type coverage**: instance signature sig(x) = set of sensitive types; library signature set 𝒞 = signatures covered by the prompt library; Coverage = fraction of online instances whose signature is exactly matched (primary) or subset-matched (optimistic) in 𝒞. Zero model calls, most interpretable, primary reported quantity; the uncovered-signature list directly guides library expansion.

**Dose-response experiment (empirical core of the argument)**: construct intermediate distributions T_α = (1−α)·S + α·T_new (T_new a controlled new-type variant set, §6.1), α ∈ {0, 0.25, 0.5, 0.75, 1}; measure Δ(α) and d̂(S,T_α) jointly and verify monotonicity. If monotonicity holds, the control relation (5) gains empirical support; report the full table (ε_S, ε_T, Δ, AUC, MMD p, coverage) plus the dose-response figure.

* * *

## 5 Theoretical Grounding and Discussion

### 5.1 The Five-Layer Theoretical Architecture: From Semantics to Empirical Approximation

The paper's theoretical positioning comprises five layers (full proofs in Appendix A):

| Layer | Tool | Quantity | Role |
| --- | --- | --- | --- |
| L1 Target semantics | Pufferfish [25,26] | posterior odds ≤ e^ε | The **definition** of de-identification sufficiency (Eq. (1)) |
| L2 Attacker-independent limit | Maximal Leakage [27] | MaxL(X→D) = log Σ_d max_x P(d\|x) | Theoretical ceiling of what Branch 1 measures; explains why empirical L can only be a lower-bound approximation |
| L3 Utility-privacy frontier | rate-privacy function [15] | U*(ε) = max I(D;T) s.t. I(D;S\|A) ≤ ε | Theoretical limit of information separation; feasibility criterion (Proposition 3) |
| L4 Fidelity limit (secondary) | Wyner-Ziv conditional rate-distortion [33] | R_{X\|S}(δ) | Theoretical positioning of the rehydration branch |
| L5 Empirical approximation | heuristic certificate + calibration | L_local, Δ̂, L̂ = L_local + Δ̂ | The empirically calibrated certificate of §5.2 |

**Positioning statement**: DR-SL approaches the theoretical limit characterized by the rate-privacy frontier under Pufferfish semantics, via an empirically calibrated heuristic certificate; the closeness of approximation improves with evaluator capability (measured by Δ̂). We do not claim to reach the limit.

Compared with MINE [14] / the privacy funnel [15], reversibility verification is training-free and usable online; its price is dependence on evaluator capability—exactly the trade-off characterized by Theorem 2′ (lower-bound direction) and empirical calibration (§5.2).

### 5.2 Security Model: A Two-Phase Threat Model and the Empirically Calibrated Certificate

**Two-phase threat model.**

- **Offline phase**: the cloud strong model acts **only** on corpora containing **no sensitive data** (public/synthetic data; a data audit guarantees no real PII; see the dataset compliance statement), serving as an **offline attacker benchmark and calibrator** for distilling the general prompt library and measuring evaluator bias. The non-sensitivity of the offline corpus is guaranteed by construction (all synthetic values/public sources), so the offline phase constitutes no leakage channel.
- **Online phase**: all decisions and iterations are local. Attacker assumptions: (A1) obtains every egressed request D; (A2) has general domain knowledge and public corpora, but knows neither the local S nor the experience store; (A3) can invoke arbitrarily strong models for analysis. The attacker class is operationalized as the four levels A_0–A_3 (§3.3), and safety conclusions are conditioned on "attacker knowledge ⊇ A_3".

**Nature of the guarantee: an empirically calibrated heuristic certificate.**

1. **Lower-boundedness** (Theorem 2′): L_local ≤ L_true. A local pass (Wilson upper bound ≤ τ_L) is a lower-bound witness against attackers no weaker than the evaluator—not an absolute safety upper bound.
2. **Empirical calibration**: run the re-identification branches of the local model and a cloud strong model on non-sensitive corpora; measure Δ̂ = L_cloud − L_local (stratified by domain/type, with confidence intervals), yielding the calibrated certificate **L̂ = L_local + Δ̂**. Δ̂ quantifies how much the local evaluator systematically underestimates leakage, upgrading the "heuristic certificate" to an "empirically calibrated heuristic certificate".
3. **Attacker-independent anchor**: Maximal Leakage [27] takes the supremum over arbitrary attackers; we report the gap between the empirical max L(A_3) and a MaxL upper-bound estimate as an explicit measure of residual uncertainty about the attacker class.
4. **Post-processing safety**: by the data-processing inequality (strong form: SDPI), any cloud-side post-processing of D does not increase leakage: I(g(D);S) ≤ I(D;S). Post-egress processing cannot worsen leakage—a free but important safety property.

**Difference from P2Skill (verified and scope-limited).** P2Skill's deployment-phase egress is likewise gated by its matcher, but its skill-refinement loop requires the cloud to read PII-bearing original inputs (the reference branch answers the original prompt directly; the evaluator branch scores (x, y_s, y_r); [13] §3.3 steps 2–3), so refinement data must leave the device before refinement completes. DR-SL's offline phase touches only non-sensitive corpora and all online decisions are local: **no phase requires sensitive data to leave the device**.

**Honest boundary**: DR-SL does not guarantee absolute safety against arbitrary attackers outside the class—consistent with all model-based privacy decision methods. For high-sensitivity scenarios the guarantee comes from the layered assurance model of §5.4.

### 5.3 Local Model Selection and Capability Dependence

(As in v1.0: Qwen3.8-27B as the primary evaluator [22], Ornith-1.5-35B-A3B as the low-resource alternative [23], DeepSeek V4 Flash as the high-capacity option [24]. Addition: the effect of model capability is itself an experimental object—the size-gradient ablation in §6 quantifies "certificate strength vs evaluator capability", corresponding to the stratified Δ̂ estimates.)

### 5.4 Layered Assurance Model (Core Safety Argument)

v1.0 treated multi-layer defense as an engineering footnote; this version elevates it to the core safety argument. DR-SL's safety claim is **layered and conditional**:

1. **Soft-decision layer (quantitative lower bound)**: two-branch reversibility verification yields the calibrated certificate L̂, task utility U, and k values—quantitative, auditable, strengthening with evaluator capability;
2. **Hard-line layer (deterministic)**: a deterministic identifier matcher (regex/declared identifiers) rejects all declared identifiers before egress, with a network allowlist as backstop—this layer does not depend on model capability and gives deterministic guarantees for declared identifiers;
3. **Human-fallback layer**: INFEASIBLE (empty feasible region per Proposition 3, or budget exhaustion) → residual-leakage report (attribute set + hit questions) → human risk judgment; automatic egress is refused.

Total-leakage decomposition (Proposition 0): system residual leakage ≤ residual on declared parts (measured by the soft layer) + missed-extraction part (conditioned on recall ρ̂). This model is more honest and stronger than a single claim of "fully local safety": each layer's guarantee type, conditions, and residual risks are explicitly statable.

### 5.5 Limitations

- **Capability dependence**: certificate strength is bounded by the local evaluator's capability; Δ̂ calibration only partially compensates (and calibration itself depends on the availability of an offline strong model).
- **Recall dependence**: system guarantees are conditioned on extractor recall ρ̂; quasi-identifier recall has no finite upper bound (§3.2).
- **Attacker-class conditionality**: guarantees are conditioned on A_3-level attacker knowledge; attackers outside the class are not covered.
- **Threshold calibration cost**: τ_L, τ_U, τ_R, δ, N, k* require per-domain calibration.
- **Inherent infeasibility**: when task information is strongly coupled to sensitive information the feasible region is empty (Proposition 3); such problems can only take the human fallback.
- **Gold-standard caveats**: annotations are audited automatic labels; reliability is triangulated by dual-model agreement (T11) and a two-rater human study (§6.10: type-level recall 0.987–1.000, precision 0.959–0.991 against the gold; combination-risk κ=0.696 under a construct-matched gold, divergence analysed), and utility-metric validity by cross-model correlation (T12) plus a two-rater human utility study (§6.10: row-level Spearman ρ=0.839 vs automatic U_sem, meeting the pre-registered ρ≥0.8).

* * *

## 6 Experimental Design and Results

This section gives the empirical blueprint and results; full details are governed by the pre-registered protocol `experiment_protocol_v1.md` (v1.1, frozen 2026-08-28/29), with every deviation recorded in the protocol's deviation log (D1–D12) and reported honestly.

### 6.1 Datasets

A four-domain benchmark (medical / banking / travel / general-legal)—isomorphic to P2Skill's 160-prompt PRISM benchmark [13]. The DR-SL dataset comprises:

- **Core test set**: test 160 (PRISM-isomorphic, 40 per domain) + **test_ext 240** (60 per domain, same-generator synthetic extension) → 100 test instances per domain for statistical power; the PRISM-isomorphic subset is reported separately to preserve comparability.
- **Other splits**: calibration 290 (doubling as the **offline calibration corpus**, non-sensitive by construction) / train 400 (simulated online stream) / adversarial 80.
- **Controlled new-type variant set T_new** (for dose-response, §4.7): generated from test templates via three controlled transformations—lexical perturbation, new-type-combination injection, format transfer; the mixing ratio α with test is experiment-controlled.
- The sensitive set S is annotated per the handbook with an audit pipeline; inter-annotator reliability uses the dual-model substitute (T11); quasi-identifiers are annotated as a separate subset. All synthetic values are fictional; compliance statement in the dataset documentation.

### 6.2 Metrics

- **L(A_i)**: four-level attacker leakage curve (mean hit rate + 95% Wilson interval [30], by domain);
- **k**: A_3 synthetic-population count (median k, P(k<5), share of k=1) [28];
- **U**: QA-probe utility (primary utility metric, §3.3);
- **R**: rehydration score (secondary diagnostic);
- **PQ = IQ×PP**: comparable reference score on P2Skill's scale [13]; primary results are the (U, L) plane + Pareto scatter;
- **Process metrics**: round distributions, infeasibility rate, token/latency cost (hot vs cold start separated; budget table in protocol §11);
- **Calibration**: Δ̂ = L_cloud − L_local (non-sensitive corpus, stratified);
- **Extractor recall**: explicit / quasi / overall (system conclusions conditioned on it).

### 6.3 Baselines

Direct forwarding (upper bound), all-local small model (lower bound), Rehydra-style placeholder substitution [8], Uniform/Selective LDP and P2Skill (prefer citing [13]'s same-scale numbers—its Table 3 reports IQ/Leak/PQ on PRISM-160; if reproduced, the same judge is used; cross-scale comparison is forbidden).

### 6.4 Ablations and Self-Learning Evaluation

Remove Branch 1 / Branch 2 (testing Proposition 1's direction), remove the memorization check, remove hot start, local-model size gradient (answering "capability dependence"), offline-online dose-response (α ∈ {0,0.25,0.5,0.75,1}, testing H4 and Δ̂ stability [29]). The self-learning convergence curve tests Hypothesis H1 (Stage 2) and its corrected form H1′ (Stage 3).

### 6.5 Safety Evaluation

Semantic-level leakage (quasi-identifier combinations; Branch 1 + k test), over-redaction (detected by the task-information-preservation metric), adversarial tests ("seemingly harmless but combination-identifiable" texts), and a human leakage-review subset (≥50, pending).

### 6.6 Implementation and Hyperparameters

All hyperparameters frozen in protocol §6: τ_L=0.05 (Wilson-upper-bound semantics), τ_R=0.9 (diagnostic), N=3, δ=0.05, ℓ=16, θ_g≥4/5 (independent scoring), K=50, k*=5, temperature 0.3 fixed, 3 random seeds.

**Model roster and role mapping** (protocol §3, frozen; deviation log D4/D10):

| Role | Model | Deployment |
| --- | --- | --- |
| Local main evaluator/dehydrator (Stages 1–3) | ornith-1.5-35b [23] | Mac Studio (LM Studio, OpenAI-compatible) |
| Local capability reference | qwen3.8-27b-mlx [22] | Mac Studio |
| Frozen embeddings | text-embedding-nomic-embed-text-v1.5 | Mac Studio |
| Offline strong model (Δ̂ calibration, independent GenScore, distiller) | qwen3.8-max | Online free-tier gateway |
| Low-cost attackers / batch probes | qwen3.8-flash | Online free-tier gateway |
| Cross-family attacker / scorer | glm-5.2 | Online free-tier gateway |

Statistics: mean±std, Wilcoxon signed-rank, bootstrap intervals; permutation tests for paired comparisons. Validity: dual-model annotation agreement (T11) and cross-model utility correlation (T12) as zero-human substitutes; a human utility study (≥100 instances, Spearman ρ ≥ 0.8) remains future work [31].

### 6.7 Distribution-Shift Experiments (§4.7 realized)

- Measurement table: (ε_S, ε_T, Δ, AUC±CI, MMD² p-value, type coverage) on test/test_ext vs T_new;
- Dose response: α ∈ {0, 0.25, 0.5, 0.75, 1}; report the Δ(α)–d̂(S,T_α) curve with monotonicity tests (Spearman ρ and sign test);
- Safety-efficiency separation check: per α, report false-release rate (should stay unchanged) and rounds/infeasibility (efficiency side).

### 6.8 Proof-Verification Experiments (Appendix B realized)

`sim/proof_checks.py`: numerical property tests of Theorem 2′, Proposition 2, and Proposition 3 on ≥1000 random synthetic mechanisms each (exact enumeration of true quantities + bound-direction assertions), boundary-case checks, and cross-consistency checks; all results archived as a test report (cited in Appendix B).

### 6.9 Results (Stages 1–3, executed under the pre-registered protocol)

Backends: local ornith-1.5-35b / qwen3.8-27b-mlx (Mac Studio, LM Studio); online qwen3.8-flash / qwen3.8-max / glm-5.2 (free-tier gateway, `enable_thinking:false`). All parameters and deviations: protocol deviation log D1–D12.

**T1 Proof numerical verification.** Theorem 2′, Proposition 2, Proposition 3: 1000 random synthetic-mechanism configurations each (exact enumeration + counterexample search) **all pass**; boundary cases (independent channel → vacuous bound; L→1 → divergence; uniform-prior special case) verified.

**T2 Regex-layer extractor recall (480 test/adversarial/extension instances).** Regexable types: **97.4%** (ID card 206/206, bank card 31/31, medical-record numbers 23/23, phone 173/177, passport 26/30, case numbers 26/31); overall explicit recall including name/address/card-tail (which need the LLM layer): 46.1%—quantitatively confirming the necessity of the cascade design (high-precision regex layer + high-recall LLM layer). System-level conclusions are conditioned on this recall per Proposition 0.

**T3 Direct-forwarding leakage baseline (Branch 1, structured probes, strict privacy grading per D9):**

| Attacker | Level | n | mean L | 95% CI |
| --- | --- | --- | --- | --- |
| ornith-1.5-35b (local) | A_0 | 400 | 0.574 | 0.539–0.610 |
| ornith-1.5-35b (local) | A_1 (domain priors) | 400 | 0.502 | 0.466–0.538 |
| qwen3.8-flash | A_0 | 160 | 0.768 | 0.741–0.795 |
| qwen3.8-flash | A_1 | 160 | 0.765 | 0.738–0.791 |
| glm-5.2 (cross-family) | A_0 | 160 | 0.789 | 0.756–0.818 |
| qwen3.8-max | A_0 | 160 | 0.779 | 0.754–0.803 |
| Synthetic population (skewed 10^5, conservative convention) | A_3 | 240 | 0.079 (all) / 0.167 (with quasi-identifiers) | — |

Reading: the direct-forwarding leakage baseline is high and consistent across attacker families (0.57–0.79; the local small model is the weakest attacker); highest in the medical domain (strong attacker 0.90), lowest in travel (~0.60). A_1 shows no gain over A_0 on raw text (and slightly lower: prior injection makes models more conservative; the value of priors is expected on dehydrated text and was re-tested there in Stage 2). A_3 provides an independent quasi-identifier measure consistent with the k distributions of §6.5. Graded-curve figure: `results/pilot_20260829/fig_attacker_curve.png`.

**T4 QA-probe utility (direct forwarding, D=X).** mean U = **0.917** (n=160)—a near-ceiling sanity result verifying the probe pipeline does not depress perfect cases.

**T5 Evaluator calibration Δ̂ (Stage 1, 290 calibration instances, ≥75 probes, strict grading).** Local ornith attack hit 0.490; strong model qwen3.8-max 0.670; **Δ̂ = +0.181** (95% CI 0.149–0.215); by domain: banking 0.202 / legal 0.202 / medical 0.184 / travel 0.129. The local evaluator systematically underestimates leakage by ≈0.18—the external certificate uniformly uses L̂ = L_local + Δ̂.

**T6 Offline-online distribution shift (§4.7 framework).** Between test and T_new: TF-IDF domain-discriminator AUC = **0.725** (CI 0.66–0.79; moderate shift); embedding MMD permutation p = 0.0; type-signature coverage: exact 25.6% / subset 31.9% (on T_new: 18.8%/22.9%). The uncovered-signature list is archived and directly guides prompt-library expansion; ε_S/ε_T and the dose-response curve are completed in T15.

**T7 k-anonymity (recap of §6.5).** Under skewed reference populations, 16.7%–21.1% of instances have k̃<5 (conservative convention); under uniform large populations ≈0–5.3%—the relativity of k is quantitatively demonstrated.

**T8 Local closed-loop pilot (8 instances, Algorithm 2′, deterministic conservative dehydration, pilot gate τ_L=0.20, deviations D8/D9).** Loop mechanics verified: all instances terminate within budget with structured outputs (PASS or INFEASIBLE + residual report); the utility gate holds (U ≥ τ_U on every accepted step; most instances keep U=1.0); leakage falls substantially on some instances (e.g., Wilson upper bound 0.833→0.39). **Key finding (fed back into the protocol)**: with only 5–6 probes per instance, the zero-hit Wilson upper bound remains ≈0.39–0.44—the instance-level τ_L gate is statistically unreachable. This directly evidences deviation D1's ≥75-probe requirement; the pilot is thus positioned as mechanism/direction verification, with formal PASS/INFEASIBLE adjudication deferred to full-probe experiments. Defects exposed and fixed in earlier rounds (reasoning exhausting max_tokens; Phase-1 spinning; grading-semantics conflation; unstable free-form LLM rewriting) are all logged (D8/D9).

**T9 Cascade-extractor full evaluation (Stage 1, 480 instances: test+test_ext+adversarial, local ornith-1.5-35b).** Overall recall **0.951** (95% CI 0.941–0.960); explicit identifiers 0.977 (0.965–0.987); quasi-identifiers 0.931 (0.915–0.945); on average 2.03 extra values per instance (over-extraction, conservative direction). By domain: medical 0.970 / travel 0.985 / legal 0.934 / banking 0.914. System-level conclusions are conditioned on ρ̂=0.951 per Proposition 0: residual leakage ≤ L_measured + 0.049.

**T10 Main closed-loop experiment (Stage 1, train 400, ornith-1.5-35b, deterministic conservative dehydration, real gates τ_L=0.05 + ≥75 probes):**

| Metric | Result |
| --- | --- |
| PASS rate | **37.5%** (150/400); by domain: legal 57%, banking 53%, medical 30% (67/220), travel 28% |
| Mean rounds | 3.08; stream first half 3.52 → second half 2.62 (decreasing trend) |
| Leakage (paired) | L 0.457 → **0.304** (permutation p≈0, including INFEASIBLE instances) |
| Task utility (paired) | U 0.973 → **0.980** (gate invariant holds; only 2/400 instances with U-drop >0.1) |
| INFEASIBLE | 250 instances, all emitting residual-leakage reports (attributes + hit questions), routed to humans by design |

Reading: (1) the lexicographic gate works—leakage drops significantly while task utility does not fall (slightly rises), validating "hard utility gate + soft leakage objective"; (2) the medical domain has the lowest PASS rate, consistent with Proposition 3: task information strongly coupled to sensitive attributes (small I(X;T|S)) shrinks the feasible region—infeasibility is inherent to the problem; (3) rounds decrease along the stream (3.52→2.62), directional evidence for H1, but Stage 1 did not enable prompt updates and the decrease is partly explained by domain composition (medical concentrated early in the stream); the formal H1 test is Stage 2's version-paired comparison; (4) the 37.5% pass rate is the honest number under strict gates (τ_L=0.05 + ≥75 probes): non-passing instances are not "method failures" but designed early warnings with residual lists. Figure: `results/pilot_20260829/fig_train_loop.png`.

**T11 Annotation reliability (Stage 2, zero-human substitute, 480 instances).** Value-level Jaccard agreement between two model families (qwen3.8-max vs ornith-1.5-35b) independently extracting: **0.845**; recalls against the automatic gold: 0.986 / 0.949. Dual-model agreement substitutes for human Cohen's κ, and the paper states plainly that the gold standard is audited automatic annotation.

**T12 Cross-model validity of the utility metric (Stage 2, zero-human substitute; 100 instances × 4 degradation levels × 2 answerers).** Spearman correlation of U between answerers: **0.958**; degradation monotonicity holds: U(D0 original)=0.916, U(D1 explicit-removed only)=0.923, U(D2 conservative dehydration)=0.034, U(D3 aggressive removal)=0.0. The metric sharply distinguishes "generalization that preserves task information" from "deletion that destroys it". Note the low D2 score reveals a real privacy-utility tension: once task-relevant quasi-identifiers are generalized to valueless tokens (city → "some city"), exact-value utility is lost—exactly the over-generalization the U gate of §3.5 exists to prevent, and it explains the medical domain's low pass rate. No human criterion study was conducted (stated in Limitations).

**T13 Self-learning test (Stage 2, formal H1 test).** A fresh-seed stream of 120 instances (60 distillation + 60 validation). Distillation produced 5 rules (from 172 failure experiences; all passing the memorization check). Paired comparison on the validation stream: **rounds v0 2.82 vs v1 2.90 (Δ=+0.08, permutation p=0.68, not significant); PASS rate 46.7% vs 41.7%.** **Honest conclusion: H1 is not supported**—a single distillation round brought no loop-efficiency gain. Attribution: the distilled rules concern "recognition/recall" strategies (entity baselines, terminology dictionaries, etc.), decoupled from the loop's dehydration actions (strengthen/loosen); and loop behavior is dominated by the deterministic policy, leaving little margin for prompt rules. H1 remains an "unproven hypothesis"; the abstract and conclusion are downgraded accordingly.

**T14 Ablations (Stage 2, 30 instances each):**

| Ablation | Result | Conclusion |
| --- | --- | --- |
| Remove Branch 1 (no attack evaluation) | True leakage of final D: L=0.327 | Quantified false-release risk: Branch 1 indispensable |
| Remove Branch 2 (no U gate) | Final U=0.111 | Over-redaction runs away: the U gate is indispensable |
| Remove hot start | Rounds 2.90 (control 2.82) | Under the deterministic policy, hot start's marginal contribution ≈0 (reported as-is) |
| Remove memorization check | 0 of 5 rules contaminated | No rejection triggered in this batch (weak evidence, reported as-is) |

**T15 Dose-response and safety-efficiency separation (Stage 2, 5α × 20 instances).** Rounds are flat across α (3.6–4.65); pass rate 0.25–0.35 (efficiency robust to shift); **at every α, PASS outputs' Wilson upper bound is 0.049 ≤ τ_L**—release safety does not degrade with distribution shift, empirically supporting the safety-efficiency separation claim of §4.7.

**T16 Post-dehydration attacker re-test (Stage 2, test 160, v0 loop with archived D).** PASS 70/160 (43.8%), mean 4.0 rounds; LLM-refinement success only 11% (the rest falls back to deterministic dehydration; reported as-is). Four-level attackers re-tested on **dehydrated text** vs the direct-forwarding baseline:

| Attacker | L direct | L dehydrated | Privacy gain |
| --- | --- | --- | --- |
| qwen3.8-flash A_0 | 0.768 | **0.436** | −0.33 |
| qwen3.8-flash A_1 | 0.765 | 0.435 | −0.33 |
| qwen3.8-flash A_2 (RAG over synthetic population) | — | 0.432 | no gain over A_0 |
| glm-5.2 A_0 | 0.789 | **0.412** | −0.38 |
| glm-5.2 A_1 | 0.789 | 0.422 | −0.37 |
| Synthetic population A_3 | 0.119 (test-160 baseline) | same (computed from original annotations; upper-bound convention) | — |

Reading: (1) closed-loop dehydration achieves ~45% relative leakage reduction against strong attackers, consistent across attacker families; (2) the retrieval-augmented A_2 attack gains nothing on dehydrated text—public-population retrieval cannot recover generalized/removed attributes; (3) residual leakage (0.41–0.44) comes mainly from task-relevant quasi-identifiers protected by the U gate, consistent with T12's privacy-utility tension and the medical domain's low pass rate; (4) A_3 is computed from original annotations as an upper bound; k re-measurement on dehydrated D (risk should drop as attributes are removed) is future work. Figure: `results/stage2_20260902/fig_privacy_gain.png`.

**T17 Corrected self-learning hypothesis H1′ (Stage 3: rules targeting the extractor).** The attribution of H1's negative result (rule target decoupled from loop decisions) yields the corrected hypothesis H1′ (pre-registered in deviation D12): rules distilled from extraction-failure experience and injected into the extractor should raise recall and reduce miss-driven system leakage.

- **P21 distillation**: from 55 missed-detection experiences (dominant missed types: income 28, address 7, amount 6), 4 rules passed the memorization check and independent GenScore; 1 was rejected—evidencing the check's effectiveness;
- **P22 paired recall validation (n=240; validation set disjoint from the distillation source)**: quasi-identifier recall 0.928→**0.943** (Δ=+1.5pp, one-sided permutation p=**0.059**); overall recall 0.954→0.962 (p=0.077); over-extraction cost +0.04 values/instance (far below the ≤1 criterion);
- **P23 end-to-end (n=30 paired; the loop uses extractor-derived S; system leakage measured against all gold attributes)**: extraction recall 0.975→**0.992**; system-level leakage L_system 0.420→**0.398** (Δ=−2.2pp, one-sided p=0.69, not significant); blind-spot hits (un-extracted attributes re-identified) are 0 for both versions—baseline recall is already high (0.975), leaving no room for the blind-spot mechanism on this subset (ceiling effect).

**Verdict (honest reporting)**: H1′ obtains **directional support without statistical significance**—all three indicators (quasi recall, end-to-end recall, system leakage) move consistently in the right direction with controlled cost, but the effect size (+1.5pp) is small relative to variance, p=0.059 being borderline; per pre-registered criterion (a) (p<0.05) it is judged **unproven (borderline)**. Power analysis: with Δ=0.015 and per-instance recall SD ~0.10, detection requires n≈700+ validation instances; the 0.93–0.95 baseline-recall ceiling further limits improvement headroom. Contrasted with H1: H1's direction was negative (Δrounds +0.08) with clear mechanistic decoupling; H1′ is directionally positive with aligned mechanism (rule content *is* extraction strategy), indicating that **the correct target of self-learning is indeed the extractor**, though gains are limited at high baseline recall—further testing requires a harder extraction benchmark (more covert quasi-identifiers).

### 6.10 Human Studies (completed; pre-registered in `human_study/README_人工研究说明.md`)

> Note: the LaTeX submission (`latex/main.tex`) is the authoritative full version (includes revision-round T18–T25 and §6.10 applicability boundary); this Markdown covers Stages 1–3 plus this addendum.

**Study 1 — human anchor for the semantic utility metric (T23 follow-through).** Two annotators independently scored 160 rows (40 test instances × 4 blinded operating points; blind key held back until scoring finished), judging whether the processed text still supports essentially the same useful advice as the original (1 / 0.5 / 0). Inter-rater agreement: Krippendorff's α=0.780 (ordinal). Human-vs-automatic row-level Spearman **ρ=0.839** (n=160) — meets the pre-registered ρ≥0.8 validity bar; the four operating-point means rank identically under both measurements (point-level ρ=1.000). Human means vs automatic U_sem: direct 0.988 vs 1.000; principled generalization **0.487** vs 0.406; placeholder 0.144 vs 0.175; selective LDP 0.181 vs 0.200. Consequences: (i) the LLM semantic judge is a valid proxy for human usefulness judgements; (ii) humans credit honest generalization even more than the semantic judge does — the safe point's human-rated utility (0.487) is 1.8× the current exact-value metric (0.276 after the generalization-lexicon completion; the superseded pre-completion value 0.033 is no longer a comparison basis), confirming that exact-value scoring systematically undervalues generalization. Subset context: auto means here are on the 40-instance human-study subset (generalized 0.406 vs 0.431 on the full test-160); the placeholder/LDP ordering flips between subset and full set—a small-n composition effect, not a contradiction. The two annotators are the second and third authors, independent of the pipeline implementation and blind to variant identities and automatic scores.

**Study 2 — human verification of the automatic annotation gold (T11 follow-through).** Two annotators independently listed all sensitive items (`type=value`) and judged combination re-identification risk on 50 test instances. Item-level (type) agreement with the automatic gold: precision **0.959**/0.991, recall **1.000**/0.987 (raters 1/2) — the gold's sensitive-item coverage is human-validated. Combination-risk judgements: inter-rater **κ=1.000**; vs the automatic quasi-only `combos` label κ=−0.083 — a construct mismatch (the automatic label fires only on quasi-identifier localizer×demographic combinations, while humans also count explicit identifiers, which trivially locate a person). Under a construct-matched gold (combos *or* any explicit identifier present): 94% agreement, **κ=0.696** — inside the pre-registered [0.6, 0.8) fallback band, so we report and analyse divergence: all 3 residual disagreements are pure-quasi-identifier banking instances (occupation+income+city+work_years+amount) that the rule flags but both humans judged non-unique — the automatic label errs on the conservative (safe) side exactly where no explicit identifier exists. We also note the prevalence effect on κ at a 92% gold positive rate.

* * *

## 7 Conclusion and Future Work

This paper proposed DR-SL, a self-learning sensitive-information isolation method centered on reversibility verification with prompts as the optimization object. We placed de-identification sufficiency under Pufferfish semantics, proved the lower-boundedness of the leakage score (Fano-type) and the witness relation from hit rates to privacy parameters, gave a rate-privacy feasibility criterion and a termination theorem for the lexicographic iteration, positioned the method as "approaching theoretical limits via an empirically calibrated heuristic certificate", and verified all theoretical bounds with numerical property tests on 3000 synthetic mechanisms. Engineering-wise, the offline stage calibrates only on non-sensitive corpora while all online decisions are local, and the layered assurance model (soft certificate + hard line + human fallback) explicitly characterizes each layer's guarantee and residual risk. Full-scale Stage 1–2 experiments (400-instance main loop + 480-instance extraction evaluation + 290-instance calibration + four-level attacker baselines) show that the loop significantly reduces leakage (0.457→0.304, p≈0) while preserving task utility (U≥0.97); 37.5% of instances obtain a complete certificate under strict gates, and the rest emit residual-leakage warnings by design; the medical domain's low pass rate corroborates the feasibility criterion's prediction for strongly task-coupled sensitive information.

Future work (with Stage 3 completed): (i) two rounds of self-learning testing (H1 unproven; corrected H1′ directionally consistent but not significant, T17)—re-test H1′ on harder extraction benchmarks (covert quasi-identifiers, adversarial formats) and larger validation sets (n≥700 for power), and explore multi-round iterative distillation; (ii) re-measure A_3's k risk on dehydrated text (quantifying the drop after attribute removal); (iii) replace the W2 example marginals with real public statistical tables; (iv) scaling up the now-completed human studies (§6.10: utility ρ=0.839 passed its pre-registered bar; annotation type-level recall ≥0.987) to more raters, real-user populations, and harder covert-identifier benchmarks; (v) computable Maximal Leakage upper-bound estimation; (vi) composition with structured-field isolation.


* * *

## Appendix A: Complete Proofs

Notation: log is base 2; H_2(p) = −p log p − (1−p) log(1−p); ln is the natural logarithm. Every proof step cites its justification.

### A.1 Proposition 0 (Recall decomposition of system leakage)

**Statement.** Let the true sensitive set be S_gold, the extracted set S_found, and recall = |S_found∩S_gold|/|S_gold|. Branch 1 probes only attributes in S_found, measuring hit rate L_measured (over S_found). Then system-level leakage satisfies

    L_system ≤ L_measured + (1 − Recall)

**Proof.** Let leak(s) ∈ [0,1] denote the degree to which attribute s is successfully re-identified by the attacker. System leakage averages over all true attributes:

    L_system = (1/|S_gold|) · [ Σ_{s∈S_found} leak(s) + Σ_{s∉S_found} leak(s) ]    (definition)

First term: by definition of L_measured, Σ_{s∈S_found} leak(s) = |S_found|·L_measured.
Second term: bounding leak(s) ≤ 1, Σ_{s∉S_found} leak(s) ≤ |S_gold| − |S_found|.

Substituting:

    L_system ≤ (|S_found|/|S_gold|)·L_measured + (|S_gold|−|S_found|)/|S_gold|
             ≤ L_measured + (1 − Recall)                     (since |S_found|/|S_gold| ≤ 1)  ∎

### A.2 Theorem 2′ (Lower-boundedness of the leakage score, Fano-type)

**Statement.** Let attribute s_i have domain size |V_i| and let any attacker achieve per-attribute hit rate L_i. If L_i ≥ 1/|V_i| (the attacker is no worse than blind guessing; always assumable for an optimal attacker, which can ignore D and guess the prior mode), then

    I(D;S) ≥ H(S) − Σ_i [ H_2(1−L_i) + (1−L_i)·log(|V_i|−1) ]

**Proof.**
(1) Let the optimal attacker's error rate for attribute i be P*_{e,i} = inf_ĝ P(ĝ_i(D) ≠ S_i). The measured attacker achieves hit rate L_i, so its error rate 1−L_i is feasible; hence **P*_{e,i} ≤ 1−L_i** (definition of optimality).
(2) By "no worse than blind guessing", P*_{e,i} ≤ 1−1/|V_i| = (|V_i|−1)/|V_i|.
(3) **Fano's inequality** [35]: H(S_i|D) ≤ H_2(P*_{e,i}) + P*_{e,i}·log(|V_i|−1).
(4) **Monotonicity lemma**: g(p) := H_2(p) + p·log(k−1) is non-decreasing on p ∈ [0, (k−1)/k]. Verification: g′(p) = log((1−p)/p) + log(k−1) = log((k−1)(1−p)/p) ≥ 0 ⟺ p ≤ (k−1)/k. (differentiation and elementary inequality)
(5) By (1)(2)(4): H(S_i|D) ≤ g(P*_{e,i}) ≤ g(1−L_i) = H_2(1−L_i) + (1−L_i)·log(|V_i|−1).
(6) **Subadditivity of conditional entropy**: H(S|D) ≤ Σ_i H(S_i|D).
(7) Combining: I(D;S) = H(S) − H(S|D) ≥ H(S) − Σ_i H(S_i|D) ≥ H(S) − Σ_i g(1−L_i). ∎

**Corollary (threshold mapping).** If all per-attribute hit rates are ≤ τ_L, then I(D;S) ≥ H(S) − Σ_i g(1−τ_L); normalized: I_norm(D;S) ≥ 1 − Σ_i g(1−τ_L)/H(S). That is, τ_L corresponds to a leakage **lower-bound** guarantee.

### A.3 Proposition 2 (Pufferfish witness: hit rate → ε lower bound)

**Setting.** A single attribute with domain V, prior p(v) > 0 (∀v). The mechanism is a channel P(d|v). Let the smallest Pufferfish parameter the mechanism actually satisfies be

    ε_true := max_{v₁,v₂∈V, d} | ln P(d|v₁)/P(d|v₂) |

(convention: 0/0 pairs excluded; if P(d|v₁)>0=P(d|v₂), record +∞). Let the optimal (MAP) attacker's hit rate be L*, and any measured attacker's hit rate L ≤ L*. Let p_max = max_v p(v), p_min = min_v p(v).

**Statement.** ε_true ≥ ln( L/(1−L) ) + ln( p_min/p_max ). With a uniform prior, ε_true ≥ ln(L/(1−L)).

**Proof.**
(1) The optimal attacker guesses the posterior mode for output d: v*(d) = argmax_v p(v|d); its hit rate is **L\* = E_d[ max_v p(v|d) ]** (MAP optimality, Bayesian decision theory).
(2) Since max_v p(v|d) ≤ 1, if max_v p(v|d) < L* held almost everywhere, its expectation would be < L*, contradicting (1). Hence **there exists an output d₀ with m := max_v p(v|d₀) ≥ L\***.
(3) At d₀ take v* = argmax_v p(v|d₀); then p(v*|d₀) ≥ L*; for any v′ ≠ v*, p(v′|d₀) ≤ 1 − p(v*|d₀) ≤ 1 − L*. Thus the **posterior odds**:
    odds_post := p(v*|d₀)/p(v′|d₀) ≥ L*/(1−L*).
(4) **Bayes expansion**: p(v|d₀) = P(d₀|v)p(v)/P(d₀), hence
    odds_post = [P(d₀|v*)/P(d₀|v′)] · [p(v*)/p(v′)].
(5) From (3)(4): P(d₀|v*)/P(d₀|v′) = odds_post · p(v′)/p(v*) ≥ (L*/(1−L*)) · (p_min/p_max).
    (If P(d₀|v′)=0 while P(d₀|v*)>0, the ratio is +∞ and the conclusion holds trivially.)
(6) By definition of ε_true: ε_true ≥ ln P(d₀|v*)/P(d₀|v′) ≥ ln(L*/(1−L*)) + ln(p_min/p_max).
(7) x ↦ ln(x/(1−x)) is strictly increasing on (0,1) and L* ≥ L, hence ε_true ≥ ln(L/(1−L)) + ln(p_min/p_max). ∎

**Interpretation.** Attacks yield a lower bound on the mechanism's required ε (a leakage witness). Uniform prior: L=0.9 ⇒ ε_true ≥ 2.20; L=0.5 ⇒ ε_true ≥ 0 (vacuous); L=0.05 ⇒ negative (vacuous)—the certificate is non-trivial only when the evaluator is strong, consistent with "closeness of approximation improves with evaluator capability".

### A.4 Proposition 3 (Feasibility criterion)

**Setting.** The task variable T is a function of the original material X (task information is contained in the source); the dehydrated artifact D is generated from (X, S); the attacker's auxiliary knowledge A is fixed as conditioning.

**Statement.** For any dehydration mechanism, I(D;T|A) ≤ I(D;S|A) + I(X;T|S,A). Hence the rate-privacy function satisfies

    U*(ε) := max_{p(D|X): I(D;S|A) ≤ ε} I(D;T|A) ≤ ε + I(X;T|S,A)

**Proof.**
(1) **Monotonicity of mutual information**: I(D;T|A) ≤ I(D;(T,S)|A).
(2) **Chain rule**: I(D;(T,S)|A) = I(D;S|A) + I(D;T|S,A).
(3) **Conditional data-processing inequality**: given (X,S), D provides no additional information about T (T is a function of X), i.e., T—X—D forms a Markov chain conditioned on (S,A); hence I(D;T|S,A) ≤ I(X;T|S,A).
(4) Combining (1)(2)(3): I(D;T|A) ≤ I(D;S|A) + I(X;T|S,A) ≤ ε + I(X;T|S,A) (for mechanisms in the feasible set). Taking the supremum over the feasible set gives U*(ε) ≤ ε + I(X;T|S,A). ∎

**Corollary (INFEASIBLE criterion).** If the utility requirement satisfies τ_U > τ_L + I(X;T|S,A), the (τ_L, τ_U) feasible region is empty and Algorithm 2′ necessarily outputs INFEASIBLE. When task information is strongly coupled to sensitive information (I(X;T|S,A) small, e.g., medical consultation where conclusions depend on age and history), the feasible region shrinks—infeasibility is a property of the problem, not a defect of the method.

### A.5 Theorem 3 (Termination of the lexicographic iteration)

**Statement.** Algorithm 2′ terminates in finitely many rounds, outputting PASS or INFEASIBLE; and after Phase 1, every accepted step maintains U ≥ τ_U (gate invariant).

**Proof.**
(1) **Phase 1**: each round either strictly increases U (loosen accepted) or fails to improve; two consecutive no-improvement rounds exit (no-progress exit), and a None return from loosen also exits. U is bounded above by 1, so strictly increasing rounds are bounded; the no-progress exit consumes at most 2 rounds; hence Phase 1 ends finitely. If it ends with U < τ_U, no strengthening can satisfy the gate (strengthening cannot raise U), and the algorithm quickly outputs INFEASIBLE via the Phase-2 skip mechanism (utility gate unreachable).
(2) **Phase 2**: each round does exactly one of the following, each incrementing the round counter t: accept a strengthening; accept a loosening; permanently add one attribute to skipped; record a failed strengthening.
(3) **Termination**: t has the hard upper bound B = 3|S|+5 and the while-condition includes t < B, so the loop terminates finitely.
(4) **Gate invariant**: at Phase-1 exit either U ≥ τ_U or the exit is by no-progress; strengthenings are accepted only if U′ ≥ τ_U; accepted loosenings can only increase U. Hence U ≥ τ_U at all subsequent times (task information never regresses).
(5) Upon termination, PASS or INFEASIBLE (with residual report) is output per the criteria. ∎

Note: evaluation noise (LLM sampling) does not affect termination (the round budget and decisions are finitely many deterministic checks); it affects only the statistical reliability of decisions, handled by the stability window and Wilson intervals (§3.3).

### A.6 Proposition 1 (Directional correctness of the two-branch alarm)

**Proof.** (i) If I(D;S)=0, i.e., D ⊥ S, then p(v|d) = p(v) for all v (definition of independence). No answer function exceeds the prior guessing rate (Bayesian decision theory), so the hit rate does not exceed the prior level—no information gain. (ii) If H(X|D,S) > η ≥ 0, there exist (d,s) with positive probability on which X is not uniquely determined; any rehydrator's (including the optimal one's) expected reconstruction error is positive, so the error-complement restoration score satisfies 𝔼[R] < 1. ∎

* * *

## Appendix B: Proof-Verification Methodology

The correctness of theoretical results cannot rest on manual review alone. For every bound in Appendix A we establish a three-layer executable verification (implemented in `sim/proof_checks.py`, delivered test-first: propositions are implemented as tested properties):

1. **Numerical property tests (counterexample search; core).** If a proposition is true, no concrete instance may falsify it. Method: construct synthetic mechanism families with fully known parameters—binary symmetric channels, naive-Bayes text models, arbitrary discrete joint distributions P(D,S)—whose true quantities (true ε = maximum log-likelihood ratio, true mutual information, true posteriors) are exactly enumerable. Simulate attackers on these mechanisms to obtain hit rates and assert the proposition's bound has the correct direction (bound ≤ true quantity) and is non-trivial. Each proposition: ≥1000 random configurations, all passing.
2. **Boundary-case checks.** Zero information gain (L = prior maximum) ⇒ the bound degenerates to vacuous; L→1 ⇒ the bound diverges; uniform-prior special cases checked line-by-line against manual derivations.
3. **Cross-consistency.** On the same synthetic families, Theorem 2′'s Fano bound and Proposition 2's Pufferfish witness must point in the same direction without mutual contradiction; aligned with known results (differential privacy's odds semantics; numerical instances of the data-processing inequality).

If any test finds a counterexample, the proposition is corrected before submission and all tests regressed. Verification results are archived as a test report accompanying the paper (pass rates, configuration distributions, boundary-case lists).

* * *

## References

[1] Hao Z, Jiang H, Jiang S, et al. Hybrid SLM and LLM for edge-cloud collaborative inference. 2024.
[2] Jin H, Wu Y. CE-COLLM: efficient and adaptive large language models through cloud-edge collaboration. IEEE ICWS, 2025.
[3] Li S, Wang H, Xu W, et al. Collaborative inference and learning between edge SLMs and cloud LLMs: a survey. 2025.
[4] Siyan L, Raghuram V C, Khattab O, et al. PAPILLON: privacy preservation from internet-based and local language model ensembles. NAACL, 2025. (arXiv:2410.17127)
[5] Das B C, Amini M H, Wu Y. Security and privacy challenges of large language models: a survey. ACM Computing Surveys, 2025.
[6] Lukas N, Salem A, Sim R, et al. Analyzing leakage of personally identifiable information in language models. IEEE S&P, 2023.
[7] data-privacy-stack/presidio. Open-source framework for detecting, redacting, and anonymizing PII. GitHub.
[8] rehydra-ai/rehydra-sdk. PII security for AI workflows, coding agents and browser workloads. GitHub, MIT.
[9] Zeng Z, Wang J, Yang J, et al. PrivacyRestore: privacy-preserving inference in large language models via privacy removal and restoration. ACL, 2025. (arXiv:2406.01394)
[10] Mai P, Yan R, Huang Z, et al. Split-and-denoise: protect large language model inference with local differential privacy. 2023.
[11] Shi W, Cui A, Li E, et al. Selective differential privacy for language modeling. NAACL, 2022.
[12] Duchi J C, Jordan M I, Wainwright M J. Local privacy and statistical minimax rates. IEEE ISIT, 2013.
[13] Ryu M, Park G, Lee S, Piao X, Kim J. P2Skill: privacy preserving skill distillation for cloud-local LLM inference systems. arXiv:2608.14094, 2026. (Key citations: §3.3 "Iterative refinement loop" steps 2–3; §4.1 refinement-corpus composition; §4.4 residual-leakage analysis.)
[14] Belghazi M I, et al. MINE: mutual information neural estimation. ICML, 2018. (arXiv:1801.04062)
[15] Data privacy and utility trade-off based on mutual information neural estimator. Expert Systems with Applications, 2022.
[16] Gilad-Bachrach R, et al. CryptoNets: applying neural networks to encrypted data with high throughput and accuracy. ICML, 2016.
[17] Mohassel P, Zhang Y. SecureML: a system for scalable privacy-preserving machine learning. IEEE S&P, 2017.
[18] Zhang S, et al. Neural estimation of information leakage for secure communication. 2025.
[19] Pilán I, Manzanares-Salor B, Sánchez D, Lison P. Truthful text sanitization guided by inference attacks. Applied Soft Computing, 185:114013, 2025. doi:10.1016/j.asoc.2025.114013.
[20] Zhang T, et al. BERTScore: evaluating text generation with BERT. ICLR, 2020.
[21] TAE: text anonymization evaluator. SoftwareX, 2026. (Metadata to be re-verified before submission.)
[22] Qwen/Qwen3.8-27B. Hugging Face, 2026.
[23] ornith-ai/Ornith-1.5-35B-A3B. Hugging Face, 2026.
[24] DeepSeek-V4-Flash. DeepSeek, 2026.
[25] Kifer D, Machanavajjhala A. A rigorous and customizable framework for privacy. PODS, 2012, 77–88. doi:10.1145/2213556.2213571.
[26] Kifer D, Machanavajjhala A. Pufferfish: a framework for mathematical privacy definitions. ACM Trans. Database Systems, 39(1), 3:1–3:36, 2014. doi:10.1145/2514689.
[27] Issa I, Wagner A B, Kamath S. An operational approach to information leakage. IEEE Transactions on Information Theory, 66(12), 2020. (arXiv:1807.07878)
[28] Sweeney L. k-Anonymity: a model for protecting privacy. Int. J. Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5):557–570, 2002. doi:10.1142/S0218488502001648.
[29] Ben-David S, Blitzer J, Crammer K, Kulesza A, Pereira F, Wortman Vaughan J. A theory of learning from different domains. Machine Learning, 79(1–2):151–175, 2010. doi:10.1007/S10994-009-5152-4.
[30] Wilson E B. Probable inference, the law of succession, and statistical inference. JASA, 22(158):209–212, 1927.
[31] Fabbri A R, Wu C, Liu W, Xiong C. QAFactEval: improved QA-based factual consistency evaluation for summarization. NAACL-HLT, 2022, 2587–2601.
[32] Deming W E, Stephan F F. On a least squares adjustment of a sampled finite contingency table. Annals of Mathematical Statistics, 11(4):427–444, 1940.
[33] Wyner A D, Ziv J. The rate-distortion function for source coding with side information at the decoder. IEEE Transactions on Information Theory, 22(1):1–10, 1976.
[34] Yue X, Du M, Wang T, Li Y, Sun H, Chow S S M. Differential privacy for text analytics via natural text sanitization (SANTEXT). Findings of ACL/IJCNLP, 2021, 3853–3866. doi:10.18653/v1/2021.findings-acl.337.
[35] Cover T M, Thomas J A. Elements of Information Theory. Wiley-Interscience, 2006.
