# 规约：级联抽取器（LLM 层）与阶段 1 编排

## 抽取器（sim/extractor.py）

级联两层（组合判别层在 k 实验中已覆盖，此处不重复）：

1. `regex_layer(text) -> entities`：即 `pipeline.extract_explicit`。
2. `llm_layer(backend, text, known) -> entities`：LLM 抽取准标识符（及正则漏掉的显式标识符）。
   - 两遍：第一遍直接抽取；第二遍 self-critique（给出第一遍结果查漏）。
   - 输出严格 JSON 数组：`[{"type": <类型词表>, "value": <原文逐字片段>}]`；
     类型词表 = `ATTR_NAMES` 的键；`value` 必须是输入文本的子串（解析时校验，非法丢弃）。
3. `cascade_extract(backend, text) -> entities`：正则 + LLM 合并，按值去重，span 用
   `text.find(value)` 对齐；返回按 span 排序的实体列表。
4. `eval_extraction(found, gold_annotations) -> report`：
   - 值级召回（显式/准标识符/总体）：金标值被找到值集合覆盖的比例；
   - 值级精确率（防过度抽取）；
   - 按类型分层召回。

## 阶段 1 编排（run_experiments.py 新阶段）

| 阶段 | 内容 | 后端 | 断点续跑 |
|---|---|---|---|
| p6 | 抽取器评测（480 条：test/test_ext/adversarial） | ornith | 按 id |
| p5_full | Δ̂ 校准（calibration 290，ornith vs qwen3.8-max，严格口径） | 双后端 | 按 id |
| p2_local | 本地攻击者 A_0/A_1（test+test_ext 400×2） | ornith | 按 (id,role,level) |
| p7 | train 400 闭环（确定性初始 + U 闸门循环；经验日志；轮数曲线数据） | ornith | 按 id |

- p7 单实例记录：`{id, domain, status, rounds, L_before, L_wilson_after, U_before, U_after, n_attrs, seconds}`；
  全部实例级评估调用与命中明细追加到 `p7_eval.jsonl`（供后续分层分析）。
- 经验库：失败三元组 `(id, cause, action_hint)` 追加 `p7_experience.jsonl`（归因字段由
  残余报告生成；阶段 1 不做提示词更新，仅积累，论文如实说明）。
- 顺序（本机并发 1）：p6 → p5_full → p2_local → p7。

## 通过判据（TDD）

- 抽取器：Mock 后端脚本化 JSON → 合并去重正确；非法 span 值丢弃；self-critique 第二遍被调用；
  recall 计算与手算一致；
- p7 适配器：Mock 后端驱动单实例跑通，记录 schema 完整。
