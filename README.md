# DR-SL — Auditing Local Release Gates for Cloud-Local LLM Inference

面向云-本地 LLM 推理的**本地放行门控失效分析与可复现审计研究**。审计对象是一条运行时敏感集（runtime-S）发布链：确定性抽取、如实泛化、本地攻击/效用检查、全出现擦除、残余报告与人工回退。

**定位与范围（Route A，round 6）：** 这是一篇审计/失效分析论文，不是"具有相对优势的新型自动脱敏方法"论文。闭环（closed loop）是**被审计对象**。全部结论**限定于本文审计的实现与作者构造的合成测试**，不估计其他门控或真实部署的失败率。标题不含 "Reversibility-Verified"（确定性轨道没有水合/可逆性验证实验）。DR-SL 为仓库历史名称（原 Dehydrate–Rehydrate with Self-Learning），自学习为探索性内容、不进入确认性发布路径。

**主论文**：`latex/main.tex` → `latex/main.pdf`（19 页）。  
**期刊版**：`submission_journal/main.tex`（由主论文转换，IEEE journal，11 页）。  
**会议版**：`submission_conference/main.tex`（condensed，4 页）。  
**协议**：`revision_protocol.md`（round 1）、`revision_protocol_v2.md`（round 2）、`revision_protocol_v3.md`（round 3）、`revision_protocol_v4.md`（round 4）、`revision_protocol_v5.md`（round 5）、`revision_protocol_v6.md`（round 6，均先冻结后实验/重算）；偏离：`revision_deviations.md`（D-R1–D-R34）。

## 三条核心发现（round 3/4/5/6）

1. **漏抽取导致假放行。** 共享词表 holdout-1：闭环放行 57.5%（46/80），放行实例中 **78.3%（36/46，Wilson [64.4,87.7]）仍含金标标注字面值（审计代理，非已证实隐私损害）**；放行子集金标命中率 0.147 > 全体 0.121。**银行 20/20 放行且 20/20 残留**（[83.9,100]），法律放行 10/10 残留（[72.2,100]）。外部审计放行子集 FR_LLM=0.826（19/23，[62.9,93.0]）。
2. **效用门控奖励"未知任务覆盖"（反向激励机制）。** 无任务相关属性被抽取时，效用代理退化为**未标记上下文保留率**（unmarked-context retention；该上下文未被抽取器标记，但可能含漏抽取的敏感值，并非"非敏感"）：holdout-1 任务相关召回仅 **0.493**（属性召回 0.858），37.5% 实例进入**有害 fallback**；**65% 的放行（30/46）经由有害 fallback，且全部有金标字面残留**（FR=1.000 vs 其他放行 0.375）。覆盖门控（UNSCORABLE→人工）使 holdout-1 放行 46→5（57.5%→6.2%），5 个放行中**未观测到**假放行（**0/5，Wilson [0, 0.434]**——样本太少，不足以验证安全性）；holdout-2 FR 仍 1.0（部分覆盖仍盲区）——是有真实放行成本的路由策略，不是安全证书。
3. **闭环无增量收益。** 三个 holdout 上配对放行率差与金标字面残留差均为 0[0,0]；本地效用差**三个 holdout 均为负**（h1 −0.089[−0.117,−0.061]、h2 −0.017[−0.032,−0.003]、h3 −0.101[−0.130,−0.071]；修复版 h3 −0.116[−0.149,−0.084]）；在线 generalization-only 泄漏相同（0.130）但裁判效用更高（0.438 vs 0.362）；下游参考保持配对差 **+0.025[0, 0.0625]**（主裁判 online_alt；稳健性裁判 online_fast +0.025[−0.0375,0.0875]），逐实例分歧 **2/40（主）vs 8/40（稳健）**，23/40 工件相同——**无可辨识均值差，非等价**。

## 支撑分析（round 3/4/5/6 新增/修正）

- **软件缺陷 vs 结构盲区**：修复版抽取器（仅修明确缺陷：金额模式未接入、email Unicode `\w` 过度匹配、allergy 标签形式与"孩子/患者"标签冲突；**不加词表**）在 holdout-1 诊断中召回→1.000、46 个放行中**未观测到金标假放行（0/46，Wilson [0, 0.077]）**（放行决策 80/80 不变；剩余 13.8% fallback 全部为**良性**——金标本就无任务属性，有害 fallback 为 0）；在**新 holdout-3**（自然 50/50 词表混合，seed 20261122，模板族 #3）确认性验证：FR 100%→**82.9%**（[68.7,91.5]），任务召回 0.427→0.792，有害 fallback 30%→5%。修复后仍显著假放行 = 结构性 runtime-S 盲区。原抽取器冻结未动（哈希核验）。fallback 三分类（全部/良性/有害）在对照表中分列。
- **神经抽取器对照（round 4 新增，round 5 口径修正，诊断性）**：云端 LLM（qwen3.8-max，冻结 prompt、声明类型表、无金标无词表，200/200 调用成功，0 不可定位）在 holdout-1/holdout-3/全漂移 p0 上跑同一门控：精确跨度召回 0.965/0.973/0.965、任务召回 1.000/0.971/1.000、FR **16.1%[7.1,32.6] / 16.7%[6.7,35.9] / 13.3%[3.7,37.9]**、有害 fallback 全 0。**完全词表置换下神经召回不塌缩**（确定性 0.522）——灾难性漂移失败主要是确定性实现的词表依赖。**FR 来源分解（round 5 P0）**：h1 的 5/31 与 drift-p0 的 2/15 假放行**全部**来自未声明的 `room_no` 类型（**类型表覆盖缺口**，是不完整 prompt 下的悲观条件结果）；只有 h3 的 4/24（全部 `city`；无任何提议包含金标城市串，其中 1 例有词汇相关酒店名）直接证明**已声明类型内的神经漏检**。冻结类型表实际遗漏**三种**金标类型（room_no/marriage_years/work_years；h3 类型全声明；work_years 值被以 duration 类型抽出故无残留），自动覆盖测试已钉住该披露。**income 为部分跨度抽取**（金标"月收入约1.2万元"→提议"1.2万元"，逐字可定位子串，非"非逐字"）：金标实体字符覆盖率 0.983/0.988/0.983 高于精确跨度召回，部分跨度-only 金标值 10/10/4（全 income）。**界定方向**：精确跨度召回是当前 prompt/类型表下的保守测量；FR 是条件于不完整类型表的观测，**无一般上下界方向**（遗漏类型会抬高 FR）。**信任披露**：云端抽取本身即披露 X，属诊断性对照、非可部署本地门控；单运行、区间仅覆盖实例间变异。看到结果后**未修改** prompt（冻结纪律）；类型表补全在**新 holdout-4** 上预先注册验证（round 5）。
- **神经对照可信度实验（round 5，260 次调用，先冻结后运行，均诊断性）**：(1) **采样稳定性**——同一冻结 prompt 在 60 实例子集重复 2 次（seed 20261126/20261127）：精确实体集一致率 95.0%/91.7%（Jaccard 0.991/0.985），三次 qwen 运行的**放行集与 FR 实例集完全相同**（FR 3/20[5.2,36.0]）——采样扰动跨度、不扰动本文审计的决策。(2) **第二模型家族**——glm-5.2（同 prompt、同子集，seed 20261128）：实体集一致率 68.3%（Jaccard 0.925），召回相近（0.959），FR 5/25——相同 2 个 room_no 缺口实例，加 3 个零手续费短形式残留（机制由 round 6 更正，见下条）；漏检/跨度身份依家族而异，门控继承机制相似而非失败身份相同。(3) **完整类型表新 holdout**——holdout-4（新模板族 #4、自然混合 seed 20261125、80 实例，先于结果编写）；prompt v2 仅增加三种类型声明（43 类）。三类新增实体均 **10/10 精确类型+值抽取且放行残余 0**；总 FR 1/32[0.6,15.7]，召回 0.986、字符覆盖 0.993、放行 40.0%、U 差 −0.119。h4 确定性参照复现 h3 模式（原版 FR 100%[93.0,100]、修复版 84.0%[71.5,91.7]）。round-4 结果保留为原不完整类型表下的诊断记录，未用 v2 重算。
- **round-6 机制与 construct 修正（仅归档重算，0 新调用）**：GLM 原始输出实际包含 `charge=0元手续费`，该扩展跨度已定位并擦除，但补充说明中的短形式 `0元` 残留；因此三例是 **`gold_substring_of_proposal`／跨度变体与重复提及**，不是“从未提议”。`fr_decomposition` 已改为识别五类关系（精确、提议⊂金标、金标⊂提议、相关但互不包含、从未提议），并加入长短重复形式回归测试。h4 完整类型表下 **`FR_gap=0` 是定义恒等式而非安全成效**；有效证据是三类新增实体各 10/10 抽取且无放行残余。城市值按既有值级召回口径为 **59/60** 精确抽取，若要求 `city` 标签也正确则 **54/60**（5 个标为 `address`）；唯一放行残余仍为同一县名，但**值/模板盲点与 city／县／address 类型边界两种原因尚未区分**。**敏感性代理**：`FR_gold` 是金标任务/敏感字面残留代理，不等于已证实隐私损害；`0元` 依据个人财务金额与银行任务规则保守标注，不声称零费用单独具有识别性。冻结小额费用生成器按千元取整，名义 5–200 元会产生 `0元`，数据不事后改写；附加排除零值手续费后，仅 GLM 子集 FR **5/25→2/25**（两项均 room_no 缺口），主体确定性及其他神经条件计数全部不变。
- **词表漂移剂量-反应**：holdout-2 为**构造性完全不相交词表消融压力测试**（100% 假放行是压力条件结果，非部署失败率）；漂移序列固定模板、仅变词表重叠 p∈{0,.25,.5,.75,1}（40 条/级）：实际重叠 0→1 时召回 0.522→0.845、放行 92.5%→57.5%、FR 100%→82.6%，单调梯度。
- **校准修正（P0）**：Spearman 改用**平均并列秩**（原双重 argsort 错误处理并列；新增 400 组独立交叉验证回归测试）。总体 ρ=**0.450[0.242,0.634]**、MAE=0.352[0.265,0.448]、阈值一致率 0.680[0.565,0.790]；闭环混淆 TP17/FP6/FN5/TN12；PRISM 组符号翻转 −0.071→+0.303。"校准不足"结论主要依据 MAE 与阈值分歧，而非仅相关系数。
- **下游重跑（P0）**：round-2 下游**无效**（末句任务启发式对 20/80 实例返回近完整原文，候选端重新看到 X；8/40 审计实例受影响），已归档至 `results/revision_20261121/downstream_invalid_round2/`。round-3 用显式 `task` 字段（运行时隔离断言）、工件哈希缓存答案（相同工件复用）、提交配对 seed、双独立裁判：参考保持 CL 0.725[0.613,0.838]、GEN 0.700[0.575,0.825]，PASS 均 0.826；裁判一致率 72.5%。**round 4 修正配对差方向**：`paired_delta(left,right)` 显式计算 left−right（旧函数实为 b−a，两处调用点标反），CL−GEN=**+0.025**；主裁判（online_alt，预先指定）分歧 2/40、区间 [0,0.0625]，稳健性裁判（online_fast）分歧 8/40、区间 [−0.0375,0.0875]，两者完整报告；新增方向+均值恒等式回归测试。指标更名为 **reference-answer preservation**（非绝对任务正确性）。
- **残余报告限定结论 + 两类型探针**：round-2 "报告召回 0" 限定为**本实验中仍留在工件中的金标字面值**（全部来自漏抽取属性；PASS 组无报告是构造必然）。构造探针（55 例）：已抽取值回注（精确模式）100% 被检测、100% 被擦除；归一化等价规避变体 100% 被检测、72.7% 留存至出口、**55/55 拒绝放行**、报告阳性覆盖 65.5%；漏抽取残留 100% 留存、报告覆盖 0。报告机制对"可见残留"有效，危险残留恰是不可见部分。
- **开放式攻击（探索性）**：无金标问题类型的开放推断攻击，FR_open：CL 0.725（PASS 条件 0.826）、GEN 0.675（0.783）、DF 1.0（**协议参照，非理论上攻击者上限**）。仍为字面评分，释义/多跳/公共知识链接攻击留待未来。
- **计数与区间**：唯一实例–问题对 243、唯一问题文本 36；round-2 holdout-1 960 攻击+240 裁判调用、5832 问题评估；hits 为命中评估总数。所有 FalseRelease 与领域比例附 Wilson 区间；均值/配对差附实例聚类区间。

## 审计框架贡献

- 条件安全指标 `FalseRelease = Pr(残留 | 本地 PASS)`，区分 FR_gold-literal / FR_LLM-literal / FR_open-ended 三种测量范围；**FR_gold 是金标字面残留审计代理，不等于已证实隐私损害**，并区分显式标识符、准标识符与单独敏感性依上下文而定的任务关键值。
- 按本地决策（ALL/PASS/INFEASIBLE）与领域分层；全体均值不单独报告。
- 实例聚类 bootstrap（2000 次，95% 百分位区间）；平均并列秩 Spearman；置换 p 用 (b+1)/(B+1)，禁止 p=0；配对差 API 显式方向 `paired_delta(left,right)`=left−right，调用点带均值恒等式断言与回归测试。
- runtime-S 与 oracle-S 分离；金标仅用于冻结后外部评分；在线裁判仅离线效标。
- 外部复测为**受控披露审计**，非出网前保证。
- 效用 fallback 机制分析 + 覆盖门控审计；修复版抽取器对照；词表剂量-反应；两类型残余探针。

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成数据生成器；holdout-1/2/3/4、漂移序列、`vocab_mix.py`（混合 RNG）、`synth_values_v2.py`（不相交词表，含断言）；所有 holdout 含显式 `task` 字段 |
| `sim/` | 发布链、冻结原抽取器 + `runtime_extractor_fixed.py`（对照）、统计、round-1/2/3/4/5/6 实验与分析脚本、测试（含 `test_spearman_ties.py`、`test_task_fields.py`、`test_extractor_fixed.py`、`test_neural_parser.py`、`test_neural_taxonomy.py`、`test_neural_residue.py`） |
| `results/revision_20261118/` | round 1 原始输出（历史，被复用；当前代码 3200/3200 逐实例复现） |
| `results/revision_20261121/` | round 2 原始输出；`downstream_invalid_round2/`（**无效**下游归档）；`stratified_summary_round2.json`（含并列秩错误的旧汇总归档）；`ROUND3_AUDIT_NOTE.md` |
| `results/revision_round3/` | round 3–6：h3/漂移离线、下游 v2、开放式攻击、残余探针、**神经对照**（round-4 raw 与 round-5 cache 逐字节保留）、FR 分解/三层覆盖、稳定性/第二家族/h4（`neural_round5_*`、`offline_h4*`）、**round-6 对称关系+h4 直接证据+零手续费敏感性**（`neural_round6_analysis.json`）、修正分层汇总、冻结清单（48 项）、`ROUND4_NOTE.md`/`ROUND5_NOTE.md`/`ROUND6_NOTE.md` |
| `human_study/` | 人工评分/标注表与分析；`holdout_utility_packet/`（已准备、**未收集**） |
| `latex/` | 主论文与自动生成的合并结果表（`make_revision_tables.py`，勿手改） |
| `submission_conference/`, `submission_journal/` | 会议/期刊投稿包 |

## 复现

```bash
python3 -m pip install -r requirements.txt
python3 dataset/generate_holdout.py
python3 dataset/generate_holdout2.py
python3 dataset/generate_holdout3.py
python3 dataset/generate_holdout4.py
python3 dataset/generate_drift_series.py
python3 sim/revision_experiment.py          # round-2 离线，无需 LLM
python3 sim/revision_online_audit.py        # round-2 受控披露审计，需配置后端
python3 sim/revision_h3_experiment.py       # round-3 离线（双抽取器/覆盖门控/漂移）
python3 sim/revision_downstream.py          # round-3 下游（显式 task，可断点续跑）
python3 sim/revision_open_attack.py         # 开放式攻击
python3 sim/revision_residual_probe.py      # 两类型残余探针
python3 sim/revision_neural_extractor.py    # round-4 神经抽取器对照（诊断性，需在线后端）
python3 sim/revision_neural_analysis.py     # round-5 P0 重分析（FR 分解/覆盖层，无需 LLM）
python3 sim/revision_neural_round5.py       # round-5 稳定性/第二家族/h4 完整类型表（需在线后端）
python3 sim/revision_neural_subset.py       # round-5 子集池化指标（无需 LLM）
python3 sim/revision_neural_round6.py       # round-6 对称关系/h4 直接证据/零手续费敏感性（无需 LLM）
python3 sim/revision_stratified_v3.py       # 修正分层/校准/机制汇总
python3 sim/make_revision_tables.py
python3 human_study/analyze_results.py
python3 human_study/prepare_holdout_packet.py
# 测试
python3 sim/test_loop.py && python3 sim/test_pipeline.py && python3 sim/test_runtime.py \
  && python3 sim/test_revision_stats.py && python3 sim/test_proof_checks.py \
  && python3 sim/test_spearman_ties.py && python3 sim/test_task_fields.py \
  && python3 sim/test_extractor_fixed.py && python3 sim/test_neural_parser.py \
  && python3 sim/test_neural_taxonomy.py && python3 sim/test_neural_residue.py
```

后端密钥运行时从本地配置读取，仓库不含密钥。本地模型端点通过 `DRSL_LOCAL_BASE_URL` 配置。在线模型快照未固定、提交的 seed 不保证被服务端采纳，是复现限制；原始响应、task 文本、工件哈希、模型名与提交 seed 均归档可审计。

## 重要限定

- 结论限定于**本文审计的实现与合成测试**；不估计其他门控/真实部署失败率。未使用第三方语料（TAB 等列为未来工作）。
- **神经抽取器对照为诊断性**：云端抽取本身披露 X，非可部署本地门控；单运行、区间仅覆盖实例间变异（采样/模型家族变异在 60 实例子集上刻画）。冻结类型表遗漏三种金标类型：精确跨度召回是该 prompt/类型表下的保守测量，FR 是条件观测、无一般上下界方向；看到结果后未修改 prompt，类型表补全在新 holdout-4 上验证。
- 新端到端结果仅覆盖**确定性本地轨道**；本地神经服务不可用，神经轨道未重跑；N=3 稳定窗口为幂等复查（已验证简化为 N=1 结果不变），仅留待随机神经轨道。
- holdout-1 与抽取器**共享词表**；holdout-2 是**构造性完全不相交压力测试**（100% 非部署失败率）；holdout-3 为自然混合但仍合成、非第三方/真实基准。
- 离线/下游裁判为**外部参照**，有测量误差（双裁判一致率 72.5%）；下游为参考保持，非绝对正确性；holdout 人工评分**已准备未收集**，不伪造人工分数。
- 原抽取器在看到 holdout 结果后**未修改**（冻结）；修复版为独立对照模块，仅修明确缺陷、不加词表，确认性验证在新 holdout-3；任何进一步改进须在新 holdout 验证。
- 开放式攻击仍为字面评分；释义/多跳/公共知识链接攻击未覆盖。
- **金标敏感性为 construct 限定**：字面残留不自动等于隐私损害或重识别；`0元` 手续费属于保守审计标注，排除它的附加分析仅改变 GLM 子集（5/25→2/25），主指标不改。持续县名残留的值/模板盲点与行政区划类型边界原因未区分，需最小对照实验。

## 合规声明

- 全部敏感值为程序合成虚构值，不含真实个人信息。
- MedQA 中文子集题干为医师资格考试题（MIT 许可），具体值已替换。
- 外部审计仅发送合成工件；原始 X 只用于离线效标/下游参照，不参与本地放行；下游 task 字段经断言不含金标值。
- 内部端点、密钥、本地凭据不上传。

## 许可

- 代码：MIT（`LICENSE`）
- 合成数据：CC-BY-4.0（`dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载
