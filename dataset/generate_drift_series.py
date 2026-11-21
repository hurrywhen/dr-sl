"""Vocabulary dose–response series (round 3, protocol v3 §4).

Holds the holdout-2 template family constant and varies ONLY the lexicon
overlap p ∈ {0, 0.25, 0.5, 0.75, 1.0}: each lexicon-dependent value is drawn
from the old pool with probability p, else from the disjoint v2 pool.
40 instances per level (10/domain), base seed 20261123 (level i uses
20261123+i).  Realized overlap is measured per instance and used as the dose
axis.  Endpoints are asserted: p=0 fully disjoint, p=1 fully old-vocabulary.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_holdout2 import (TEMPLATES, TASKS, AUTHORED_TASK_TEMPLATES,
                               assemble, check_task, load_existing_texts)
from vocab_mix import MixRng, is_old_lexicon_value, LEXICON_TYPES

BASE_SEED = 20261123
LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
DOMAINS = ("medical", "banking", "travel", "legal")
PER_DOMAIN = 10
OUTDIR = Path(__file__).resolve().parent / "output"


def gen_level(p, seed):
    import difflib
    rng = MixRng(seed, p)
    seen = load_existing_texts()
    items = []
    for domain in DOMAINS:
        accepted = []
        attempts = 0
        while len(accepted) < PER_DOMAIN and attempts < PER_DOMAIN * 50:
            attempts += 1
            fn = TEMPLATES[domain][attempts % len(TEMPLATES[domain])]
            text, ents = assemble(fn(rng))
            rel = [e for e in ents if e.get("task_relevant")]
            if rel:
                v = rel[attempts % len(rel)]["value"]
                text += f"补充说明：前述{v}情况请以本记录为准。"
            if text in seen:
                continue
            if any(difflib.SequenceMatcher(None, text, s).ratio() >= 0.95 for s in seen[-400:]):
                continue
            seen.append(text)
            accepted.append((text, ents, fn.__name__))
        assert len(accepted) == PER_DOMAIN, domain
        tag = f"P{int(round(p*100)):03d}"
        for i, (text, ents, tid) in enumerate(accepted, 1):
            task = TASKS[tid]
            check_task(task, text, ents, tid)
            ann = {
                "explicit_identifiers": [e for e in ents if e["category"] == "explicit"],
                "quasi_identifiers": [e for e in ents if e["category"] == "quasi"],
                "combos": [],
                "has_quasi_identifier": any(e["category"] == "quasi" for e in ents),
            }
            n_qi = len(ann["quasi_identifiers"])
            n_crit = sum(1 for e in ann["quasi_identifiers"] if e["task_relevant"])
            lex = [e for e in ann["quasi_identifiers"] + ann["explicit_identifiers"]
                   if e["type"] in LEXICON_TYPES]
            n_old = sum(1 for e in lex if is_old_lexicon_value(e["type"], e["value"]))
            # Endpoint assertions on lexicon-dependent values.
            if p == 0.0:
                assert n_old == 0, f"p=0 level has old-vocabulary value: {text}"
            if p == 1.0:
                assert lex and n_old == len(lex), f"p=1 level has new-vocabulary value: {text}"
            items.append({
                "id": f"DRSL-DRIFT-{tag}-{domain[:3].upper()}-{i:04d}",
                "domain": domain,
                "split": f"drift_{tag}_frozen",
                "prompt": text,
                "task": task,
                "task_meta": {"source": ("authored_dialogue_request"
                                         if tid in AUTHORED_TASK_TEMPLATES
                                         else "verbatim_request")},
                "template_id": f"holdout2_{tid}",
                "annotations": ann,
                "coupling_ratio": round(n_crit / n_qi, 3) if n_qi else 0.0,
                "nominal_old_vocab_prob": p,
                "realized_old_vocab_fraction": round(n_old / len(lex), 3) if lex else None,
                "source": "synthetic_vocab_drift_series",
                "license": "synthetic-fictional",
                "annotation_meta": {"annotator": "rule_based_task_critical",
                                     "needs_human_review": True,
                                     "frozen_before_evaluation": True},
            })
    return items


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    digest = {}
    for i, p in enumerate(LEVELS):
        items = gen_level(p, BASE_SEED + i)
        tag = f"p{int(round(p*100)):03d}"
        out = OUTDIR / f"dr_sl_drift_{tag}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        lex = [e for it in items
               for e in it["annotations"]["quasi_identifiers"] + it["annotations"]["explicit_identifiers"]
               if e["type"] in LEXICON_TYPES]
        realized = sum(1 for e in lex if is_old_lexicon_value(e["type"], e["value"])) / len(lex)
        digest[tag] = {"n": len(items), "nominal_p_old": p,
                       "realized_old_vocab_fraction": round(realized, 3),
                       "seed": BASE_SEED + i, "file": out.name}
    print(json.dumps(digest, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
