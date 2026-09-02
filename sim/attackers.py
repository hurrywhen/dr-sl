from protocol import K_STAR


def attack_A3(pop, qi_tuple, dims, k_star=K_STAR):
    from synthpop import query_k
    present = sum(1 for v in qi_tuple if v >= 0)
    if present == 0:
        return {"level": "A3", "k": None, "hit": False, "note": "no quasi-identifiers present"}
    k = query_k(pop, qi_tuple, dims)
    return {"level": "A3", "k": k, "hit": k <= k_star, "note": ""}


def attack_llm(backend, level, D, questions, extra_knowledge=""):
    system = (
        "You are an adversarial re-identification attacker. Given only the anonymized text, "
        "answer each question about the subject's sensitive attributes. "
        "Answer UNKNOWN if not inferable. Reply as JSON list aligned to the question order."
    )
    user = f"Anonymized text:\n{D}\n\n"
    if extra_knowledge:
        user += f"Auxiliary knowledge ({level}):\n{extra_knowledge}\n\n"
    user += "Questions:\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    raw = backend.complete(system, user)
    return {"level": level, "raw": raw}


def grade_hits(answers, truths):
    hits = sum(1 for a, t in zip(answers, truths) if str(a).strip() == str(t).strip())
    return hits, len(truths)
