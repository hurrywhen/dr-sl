# DR-SL — Auditing Local Release Gates for Cloud-Local LLM Inference

面向云-本地 LLM 推理的**本地放行门控失效分析与可复现审计研究**。审计对象是一条运行时敏感集（runtime-S）发布链：确定性抽取、如实泛化、本地攻击/效用检查、全出现擦除、残余报告与人工回退。

**当前定位（Route A）：** 这是一篇审计/失效分析论文，不是"具有相对优势的新型自动脱敏方法"论文。闭环（closed loop）是**被审计对象**，而非被推荐的优越方法。标题已删除 "Reversibility-Verified"（确定性轨道没有水合/可逆性验证实验）。DR-SL 为仓库历史名称（原 Dehydrate–Rehydrate with Self-Learning），自学习为探索性内容、不进入确认性发布路径。

**主论文**：`latex/main.tex` → `latex/main.pdf`。  
**期刊版**：`submission_journal/main.tex`（由主论文转换，IEEE journal）。  
**会议版**：`submission_conference/main.tex`（condensed）。  
**协议**：`revision_protocol.md`（round 1）、`revision_protocol_v2.md`（round 2，冻结于新数据/分析之前）；偏离：`revision_deviations.md`（D-R1–D-R9）。

## 核心发现（round 2，`results/revision_20261121/`）

1. **本地放行与外部泄漏系统性错位（假放行）。** 共享词表 holdout-1：闭环放行 57.5%（46/80），但放行实例中 **78.3%（36/46）仍含金标敏感字面值**；放行子集平均金标命中率 0.147 高于全体 0.121。银行域 **20/20 全部放行且 20/20 有残留**；法律域放行 10/10 均有残留。
2. **闭环不优于简单确定性泛化。** 配对差：放行率差 0 [0,0]、金标泄漏差 0 [0,0]、本地效用差 −0.089 [−0.117,−0.061]（holdout-1）。闭环仅降低本地效用，无更安全工件。
3. **词表漂移使门控失效。** 新增**词表不相交** holdout-2（80 条，seed 20261121）：抽取召回 0.858→**0.526**，放行率 57.5%→**93.75%**，金标泄漏 0.121→**0.453**，金标假放行率→**100%**（每条放行实例都泄漏）。所有词表依赖类型召回降为 0。
4. **本地效用代理校准不足。** 与离线语义裁判总体 Spearman ρ 弱相关（实例聚类区间见 `stratified_summary.json`）；全体均值掩盖放行子群更高的泄漏与效用。
5. **残余报告不覆盖真实残余风险。** 残余报告对金标残留的召回为 **0**：危险残留恰是抽取器漏掉的属性，天然不在 runtime-S 报告中。
6. **审计计数修正。** "3888 unique questions" 实为**问题评估次数**；唯一实例–问题对 243、唯一问题文本 36、攻击调用 640、裁判调用 160（round 1）。"519 hits" 为重复评估命中总数，非 519 个不同泄漏值。

## 审计框架贡献

- 条件安全指标 `FalseRelease = Pr(外部审计发现残留 | 本地 PASS)`，及其金标字面类比。
- 按本地决策（ALL/PASS/INFEASIBLE）与领域分层；全体均值不单独报告。
- 实例聚类 bootstrap（2000 次，95% 百分位区间）；置换 p 用 (b+1)/(B+1)，禁止 p=0。
- runtime-S 与 oracle-S 分离；金标仅用于冻结后外部评分；在线裁判仅离线效标。
- 外部复测为**受控披露审计**，非出网前保证。
- 下游任务效用：云端模型基于 X 与 D 分别作答，独立模型评判正确性/可用性保持。
- 本地代理 vs 裁判：总体与逐方法 ρ/MAE/阈值一致率 + 实例聚类区间 + 逐方法混淆矩阵。

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成数据生成器；`generate_holdout.py`（holdout-1）、`generate_holdout2.py`（词表不相交 holdout-2）、`synth_values_v2.py`（不相交词表，含断言） |
| `sim/` | 发布链、runtime-S 抽取器、统计、`revision_experiment.py`（离线）、`revision_online_audit.py`（受控披露）、`revision_downstream.py`（下游任务）、`revision_stratified.py`（分层/校准/残余）、`make_revision_tables.py`、测试 |
| `results/revision_20261118/` | round 1 离线/在线原始输出与汇总（历史，被 round 2 复用） |
| `results/revision_20261121/` | round 2 离线/在线/下游原始输出、分层汇总、冻结清单 |
| `human_study/` | 人工评分/标注表、修订分析；`holdout_utility_packet/`（已准备、**未收集**） |
| `latex/` | 主论文与自动生成的结果表 `revision_results.tex` / `revision_results_conf.tex` |
| `submission_conference/`, `submission_journal/` | 会议/期刊投稿包 |

## 复现

```bash
python3 -m pip install -r requirements.txt
python3 dataset/generate_holdout.py
python3 dataset/generate_holdout2.py
python3 sim/revision_experiment.py          # 离线，无需 LLM
python3 sim/revision_online_audit.py        # 受控披露审计，需配置后端
python3 sim/revision_downstream.py          # 下游任务效用
python3 sim/revision_stratified.py          # 分层/校准/残余分析
python3 sim/make_revision_tables.py
python3 human_study/analyze_results.py
python3 human_study/prepare_holdout_packet.py
python3 sim/test_loop.py && python3 sim/test_pipeline.py && python3 sim/test_runtime.py && python3 sim/test_revision_stats.py && python3 sim/test_proof_checks.py
```

后端密钥运行时从本地配置读取，仓库不含密钥。本地模型端点通过 `DRSL_LOCAL_BASE_URL` 配置；历史内网地址已从当前文本移除。在线模型快照/权重未完全固定，是复现限制。

## 重要限定

- 新端到端结果仅覆盖**确定性本地轨道**；本地神经服务不可用，神经轨道未重跑。
- 确定性轨道中 N=3 稳定窗口为**幂等复查**（零方差、零筛选），已简化为 N=1（验证与 N=3 结果完全一致）；N=3 机制仅留待随机神经轨道。
- holdout-1 与抽取器**共享词表**，仅验证模板/表述泛化；holdout-2 隔离词表漂移，但仍是合成、非第三方/真实基准。
- 离线/下游裁判为**外部参照**，有测量误差，非客观任务效用金标准、非人工可接受性。
- holdout 人工效用评分**已准备未收集**，不伪造人工分数。
- 抽取器在看到 holdout 结果后**未做修改**（冻结要求）；发现的抽取缺口（如 amount/charge 未抽取）作为结论报告，任何改进须在新 holdout 验证。

## 合规声明

- 全部敏感值为程序合成虚构值，不含真实个人信息。
- MedQA 中文子集题干为医师资格考试题（MIT 许可），具体值已替换。
- 外部审计仅发送合成工件；原始 X 只用于离线效标/下游参照，不参与本地放行。
- 内部端点、密钥、本地凭据不上传。

## 许可

- 代码：MIT（`LICENSE`）
- 合成数据：CC-BY-4.0（`dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载
