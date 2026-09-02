# 规约：数据集扩充（test_ext + T_new）

对应协议 v1.1 §2 与论文 §6.1。输出 `dataset/output/dr_sl_expansion_v1.jsonl`，种子 20260829。

## test_ext（240 条）

- 每域 60 条（medical/banking/travel/legal），`split="test_ext"`；
- 复用 v1 生成器与 **test 划分专属模板**（模板-划分独占性不变），新种子重新实例化；
- 与 v2 全量样本去重（相似度 <0.85，difflib）；
- id 前缀 `DRSL-<DOM>-TSE-<序号>`；
- 字段与 schema.json 一致；span 与文本逐字一致（verify_spans）；
- 准标识符样本占比 ≥40%。

## T_new 受控变体集（240 条，剂量响应用）

每域 60 条 = 三类变换各 20 条；`split="tnew"`，`source="synthetic_shift_variant"`；
源实例取自 **v2 test 划分**（160 条，`annotation_meta.source_instance_id` 指向 v2 id；
240 > 160，允许同源不同变换，每源至多 2 个变体）。

| 变换 | 定义 | 不变量 |
|---|---|---|
| t1 词面扰动 | 仅改写不含实体的句子（连接词替换、无实体填充句重排） | 全部实体值与相对顺序不变；span 重对齐后逐字一致 |
| t2 新类型注入 | 追加一个源签名中不存在的准标识符类型句（如医疗+收入、旅游+疾病） | 新实体被正确标注；原实体不变；新类型 ∉ 源签名 |
| t3 格式迁移 | statement → 对话体（用户/助手轮次标记） | 实体值保留且 span 重对齐一致 |

`annotation_meta.transform_type ∈ {t1_lexical, t2_type_inject, t3_format}`。

## α-混合接口（sim/shift.py）

- `type_signature(item) -> frozenset`：准标识符类型集合（加 "EXPLICIT" 若含显式标识符）；
- `coverage(online_items, library_items)` → {exact, subset} 两个比例 + 未覆盖签名清单；
- `mix_ids(test_ids, tnew_ids, alpha, seed)` → 确定性按 α 混合的 id 列表（四舍五入取整）；
- `domain_auc(texts_s, texts_t, seed)` → TF-IDF(char 2–3 gram) + 逻辑回归 5 折 CV 的 AUC；
- `mmd_test(emb_s, emb_t, n_perm)` → (MMD², p)。
