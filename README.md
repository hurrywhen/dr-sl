# DR-SL — Auditing Local Release Gates for Cloud-Local LLM Inference

面向云-本地 LLM 推理的**本地放行门控失效分析与可复现审计研究**。审计对象是一条运行时敏感集（runtime-S）发布链：确定性抽取、如实泛化、本地攻击/效用检查、全出现擦除、残余报告与人工回退。

**定位与范围（Route A，round 3）：** 这是一篇审计/失效分析论文，不是"具有相对优势的新型自动脱敏方法"论文。闭环（closed loop）是**被审计对象**。全部结论**限定于本文审计的实现与作者构造的合成测试**，不估计其他门控或真实部署的失败率。标题不含 "Reversibility-Verified"（确定性轨道没有水合/可逆性验证实验）。DR-SL 为仓库历史名称（原 Dehydrate–Rehydrate with Self-Learning），自学习为探索性内容、不进入确认性发布路径。

**主论文**：`latex/main.tex` → `latex/main.pdf`（15 页）。  
**期刊版**：`submission_journal/main.tex`（由主论文转换，IEEE journal，9 页）。  
**会议版**：`submission_conference/main.tex`（condensed，3 页）。  
**协议**：`revision_protocol.md`（round 1）、`revision_protocol_v2.md`（round 2）、`revision_protocol_v3.md`（round 3，均先冻结后实验）；偏离：`revision_deviations.md`（D-R1–D-R17）。

## 三条核心发现（round 3）

1. **漏抽取导致假放行。** 共享词表 holdout-1：闭环放行 57.5%（46/80），放行实例中 **78.3%（36/46，Wilson [64.4,87.7]）仍含金标敏感字面值**；放行子集金标命中率 0.147 > 全体 0.121。**银行 20/20 放行且 20/20 残留**（[83.9,100]），法律放行 10/10 残留（[72.2,100]）。外部审计放行子集 FR_LLM=0.826（19/23，[62.9,93.0]）。
2. **效用门控奖励"未知任务覆盖"（反向激励机制）。** 无任务相关属性被抽取时，效用代理退化为上下文保留率：holdout-1 任务相关召回仅 **0.493**（属性召回 0.858），37.5% 实例进入**有害 fallback**；**65% 的放行（30/46）经由有害 fallback，且全部泄漏**（FR=1.000 vs 其他放行 0.375）。覆盖门控（UNSCORABLE→人工）使 holdout-1 放行 57.5%→6.2%、FR→**0**，但 holdout-2 FR 仍 1.0（部分覆盖仍盲区）——是有真实放行成本的路由策略，不是安全证书。
3. **闭环无增量收益。** 三个 holdout 上配对放行率差与金标泄漏差均为 0[0,0]；本地效用差依数据集而异（h1 −0.089[−0.117,−0.061]、h2 −0.017、h3 +0.101）；在线 generalization-only 泄漏相同（0.130）但裁判效用更高（0.438 vs 0.362）；下游参考保持配对差 −0.025[−0.062,0.000]，仅 2/40 实例评分不同——**无可辨识均值差，非等价**。

## 支撑分析（round 3 新增/修正）

- **软件缺陷 vs 结构盲区**：修复版抽取器（仅修明确缺陷：金额模式未接入、email Unicode `\w` 过度匹配、allergy 标签形式与"孩子/患者"标签冲突；**不加词表**）在 holdout-1 诊断中召回→1.000、FR 78.3%→**0**（放行决策 80/80 不变）；在**新 holdout-3**（自然 50/50 词表混合，seed 20261122，模板族 #3）确认性验证：FR 100%→**82.9%**（[68.7,91.5]），任务召回 0.427→0.792，fallback 30%→5%。修复后仍显著假放行 = 结构性 runtime-S 盲区。原抽取器冻结未动（哈希核验）。
- **词表漂移剂量-反应**：holdout-2 为**构造性完全不相交词表消融压力测试**（100% 假放行是压力条件结果，非部署失败率）；漂移序列固定模板、仅变词表重叠 p∈{0,.25,.5,.75,1}（40 条/级）：实际重叠 0→1 时召回 0.522→0.845、放行 92.5%→57.5%、FR 100%→82.6%，单调梯度。
- **校准修正（P0）**：Spearman 改用**平均并列秩**（原双重 argsort 错误处理并列；新增 400 组独立交叉验证回归测试）。总体 ρ=**0.450[0.242,0.634]**、MAE=0.352[0.265,0.448]、阈值一致率 0.680[0.565,0.790]；闭环混淆 TP17/FP6/FN5/TN12；PRISM 组符号翻转 −0.071→+0.303。"校准不足"结论主要依据 MAE 与阈值分歧，而非仅相关系数。
- **下游重跑（P0）**：round-2 下游**无效**（末句任务启发式对 20/80 实例返回近完整原文，候选端重新看到 X；8/40 审计实例受影响），已归档至 `results/revision_20261121/downstream_invalid_round2/`。round-3 用显式 `task` 字段（运行时隔离断言）、工件哈希缓存答案（相同工件复用）、提交配对 seed、双独立裁判：参考保持 CL 0.725[0.613,0.838]、GEN 0.700[0.575,0.825]，PASS 均 0.826；裁判一致率 72.5%。指标更名为 **reference-answer preservation**（非绝对任务正确性）。
- **残余报告限定结论 + 两类型探针**：round-2 "报告召回 0" 限定为**本实验中仍留在工件中的金标字面值**（全部来自漏抽取属性；PASS 组无报告是构造必然）。构造探针（55 例）：已抽取值回注（精确模式）100% 被检测、100% 被擦除；归一化等价规避变体 100% 被检测、72.7% 留存至出口、**55/55 拒绝放行**、报告阳性覆盖 65.5%；漏抽取残留 100% 留存、报告覆盖 0。报告机制对"可见残留"有效，危险残留恰是不可见部分。
- **开放式攻击（探索性）**：无金标问题类型的开放推断攻击，FR_open：CL 0.725（PASS 条件 0.826）、GEN 0.675（0.783）、DF 1.0（**协议参照，非理论上攻击者上限**）。仍为字面评分，释义/多跳/公共知识链接攻击留待未来。
- **计数与区间**：唯一实例–问题对 243、唯一问题文本 36；round-2 holdout-1 960 攻击+240 裁判调用、5832 问题评估；hits 为命中评估总数。所有 FalseRelease 与领域比例附 Wilson 区间；均值/配对差附实例聚类区间。

## 审计框架贡献

- 条件安全指标 `FalseRelease = Pr(残留 | 本地 PASS)`，区分 FR_gold-literal / FR_LLM-literal / FR_open-ended 三种测量范围。
- 按本地决策（ALL/PASS/INFEASIBLE）与领域分层；全体均值不单独报告。
- 实例聚类 bootstrap（2000 次，95% 百分位区间）；平均并列秩 Spearman；置换 p 用 (b+1)/(B+1)，禁止 p=0。
- runtime-S 与 oracle-S 分离；金标仅用于冻结后外部评分；在线裁判仅离线效标。
- 外部复测为**受控披露审计**，非出网前保证。
- 效用 fallback 机制分析 + 覆盖门控审计；修复版抽取器对照；词表剂量-反应；两类型残余探针。

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成数据生成器；holdout-1/2/3、漂移序列、`vocab_mix.py`（混合 RNG）、`synth_values_v2.py`（不相交词表，含断言）；所有 holdout 含显式 `task` 字段 |
| `sim/` | 发布链、冻结原抽取器 + `runtime_extractor_fixed.py`（对照）、统计、round-1/2/3 实验与分析脚本、测试（含 `test_spearman_ties.py`、`test_task_fields.py`、`test_extractor_fixed.py`） |
| `results/revision_20261118/` | round 1 原始输出（历史，被复用；当前代码 3200/3200 逐实例复现） |
| `results/revision_20261121/` | round 2 原始输出；`downstream_invalid_round2/`（**无效**下游归档）；`stratified_summary_round2.json`（含并列秩错误的旧汇总归档）；`ROUND3_AUDIT_NOTE.md` |
| `results/revision_round3/` | round 3：h3/漂移离线、下游 v2、开放式攻击、残余探针、修正分层汇总、冻结清单（28 项） |
| `human_study/` | 人工评分/标注表与分析；`holdout_utility_packet/`（已准备、**未收集**） |
| `latex/` | 主论文与自动生成的合并结果表（`make_revision_tables.py`，勿手改） |
| `submission_conference/`, `submission_journal/` | 会议/期刊投稿包 |

## 复现

```bash
python3 -m pip install -r requirements.txt
python3 dataset/generate_holdout.py
python3 dataset/generate_holdout2.py
python3 dataset/generate_holdout3.py
python3 dataset/generate_drift_series.py
python3 sim/revision_experiment.py          # round-2 离线，无需 LLM
python3 sim/revision_online_audit.py        # round-2 受控披露审计，需配置后端
python3 sim/revision_h3_experiment.py       # round-3 离线（双抽取器/覆盖门控/漂移）
python3 sim/revision_downstream.py          # round-3 下游（显式 task，可断点续跑）
python3 sim/revision_open_attack.py         # 开放式攻击
python3 sim/revision_residual_probe.py      # 两类型残余探针
python3 sim/revision_stratified_v3.py       # 修正分层/校准/机制汇总
python3 sim/make_revision_tables.py
python3 human_study/analyze_results.py
python3 human_study/prepare_holdout_packet.py
# 测试
python3 sim/test_loop.py && python3 sim/test_pipeline.py && python3 sim/test_runtime.py \
  && python3 sim/test_revision_stats.py && python3 sim/test_proof_checks.py \
  && python3 sim/test_spearman_ties.py && python3 sim/test_task_fields.py \
  && python3 sim/test_extractor_fixed.py
```

后端密钥运行时从本地配置读取，仓库不含密钥。本地模型端点通过 `DRSL_LOCAL_BASE_URL` 配置。在线模型快照未固定、提交的 seed 不保证被服务端采纳，是复现限制；原始响应、task 文本、工件哈希、模型名与提交 seed 均归档可审计。

## 重要限定

- 结论限定于**本文审计的实现与合成测试**；不估计其他门控/真实部署失败率。
- 新端到端结果仅覆盖**确定性本地轨道**；本地神经服务不可用，神经轨道未重跑；N=3 稳定窗口为幂等复查（已验证简化为 N=1 结果不变），仅留待随机神经轨道。
- holdout-1 与抽取器**共享词表**；holdout-2 是**构造性完全不相交压力测试**（100% 非部署失败率）；holdout-3 为自然混合但仍合成、非第三方/真实基准。
- 离线/下游裁判为**外部参照**，有测量误差（双裁判一致率 72.5%）；下游为参考保持，非绝对正确性；holdout 人工评分**已准备未收集**，不伪造人工分数。
- 原抽取器在看到 holdout 结果后**未修改**（冻结）；修复版为独立对照模块，仅修明确缺陷、不加词表，确认性验证在新 holdout-3；任何进一步改进须在新 holdout 验证。
- 开放式攻击仍为字面评分；释义/多跳/公共知识链接攻击未覆盖。

## 合规声明

- 全部敏感值为程序合成虚构值，不含真实个人信息。
- MedQA 中文子集题干为医师资格考试题（MIT 许可），具体值已替换。
- 外部审计仅发送合成工件；原始 X 只用于离线效标/下游参照，不参与本地放行；下游 task 字段经断言不含金标值。
- 内部端点、密钥、本地凭据不上传。

## 许可

- 代码：MIT（`LICENSE`）
- 合成数据：CC-BY-4.0（`dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载
