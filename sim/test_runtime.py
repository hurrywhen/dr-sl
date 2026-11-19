import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime import (external_gold_audit, local_literal_attack, local_utility,
                     prism_random_artifact, run_runtime_item, runtime_view,
                     stable_decision)
from runtime_extractor import runtime_extract


class GuardedItem:
    """Raises if policy code tries to read gold annotations."""
    def __init__(self, prompt, domain):
        self._data = {"prompt": prompt, "domain": domain, "id": "guarded"}

    def __getitem__(self, key):
        if key == "annotations":
            raise AssertionError("runtime policy must not read gold annotations")
        return self._data[key]

    def get(self, key, default=None):
        if key == "annotations":
            raise AssertionError("runtime policy must not read gold annotations")
        return self._data.get(key, default)


def test_runtime_view_no_gold():
    item = GuardedItem("患者张三，31岁，高血压，电话19012345678。请给建议。", "medical")
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents, task_profile="mixed")
    assert view["prompt"].startswith("患者")
    assert any(e["type"] == "age" for e in view["runtime_entities"])
    print("test_runtime_view_no_gold OK")


def test_local_attack_repeated_occurrences():
    item = {"prompt": "张三电话19012345678。再次联系19012345678。", "domain": "medical", "id": "x"}
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents)
    attack = local_literal_attack(view, item["prompt"])
    assert attack["hits"] > 0
    clean = "〔姓名〕电话〔联系方式〕。再次联系〔联系方式〕。"
    attack2 = local_literal_attack(view, clean)
    assert attack2["hits"] == 0
    print("test_local_attack_repeated_occurrences OK")


def test_local_utility_band_vs_placeholder():
    item = {"prompt": "患者31岁，高血压。请建议。", "domain": "medical", "id": "x"}
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents, task_profile="mixed")
    u_exact = local_utility(view, item["prompt"])
    assert u_exact["U"] == 1.0
    u_band = local_utility(view, "患者30多岁，某慢性疾病。请建议。")
    assert 0.0 < u_band["U"] < 1.0
    u_place = local_utility(view, "患者〔年龄信息〕，〔健康状况〕。请建议。")
    assert u_place["U"] == 0.0
    print("test_local_utility_band_vs_placeholder OK")


def test_prism_random_consistent_all_occurrences():
    item = {"prompt": "客户张三，张三的电话19012345678，再次拨打19012345678。",
            "domain": "banking", "id": "x"}
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents)
    art = prism_random_artifact(view, seed=123)
    assert "张三" not in art["D"]
    assert "19012345678" not in art["D"]
    # repeated original phone replaced by the same random phone
    import re
    phones = re.findall(r"190\d{8}", art["D"])
    assert len(phones) == 2 and phones[0] == phones[1]
    print("test_prism_random_consistent_all_occurrences OK")


def test_closed_loop_stable_and_no_gold():
    item = GuardedItem("贷款申请人李四，金额50000元，电话19012345678。请评估。", "banking")
    rec = run_runtime_item(item, method="closed_loop", task_profile="mixed")
    assert rec["status"] in ("PASS", "INFEASIBLE")
    assert rec["stable"] in (True, False)
    assert "19012345678" not in rec["D"]
    print("test_closed_loop_stable_and_no_gold OK", rec["status"])


def test_external_audit_separate():
    item = {"prompt": "患者王五，31岁。", "domain": "medical", "id": "x",
            "annotations": {"explicit_identifiers": [{"type": "name", "value": "王五", "category": "explicit", "span": [2, 4], "task_relevant": False}],
                            "quasi_identifiers": [{"type": "age", "value": "31岁", "category": "quasi", "span": [5, 8], "task_relevant": True}],
                            "combos": []}}
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents)
    D = "患者〔姓名〕，30多岁。"
    audit = external_gold_audit(item, D, ents)
    assert audit["gold_literal_hits"] == 0
    assert audit["n_gold"] == 2
    print("test_external_audit_separate OK")


if __name__ == "__main__":
    test_runtime_view_no_gold()
    test_local_attack_repeated_occurrences()
    test_local_utility_band_vs_placeholder()
    test_prism_random_consistent_all_occurrences()
    test_closed_loop_stable_and_no_gold()
    test_external_audit_separate()
    print("ALL RUNTIME TESTS PASSED")
