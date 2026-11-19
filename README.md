# DR-SL — Runtime-Sensitive-Set Release Chain for Cloud-Local LLM Inference

面向云-本地 LLM 推理的敏感信息隔离发布链：运行时敏感集抽取、如实泛化、本地攻击/效用检查、确定性全出现擦除、稳定门限、残余报告与人工回退。

**当前修订版主论文**：`latex/main.tex` → `latex/main.pdf`（11 页）。  
**会议版**：`submission_conference/main.tex` → `main.pdf`（3 页 condensed）。  
**期刊版**：`submission_journal/main.tex` → `main.pdf`（6 页 IEEE journal）。  
**修订协议**：`revision_protocol.md`；修订偏离：`revision_deviations.md`。  
历史协议 `experiment_protocol_v1.md`（D1–D18）与旧 Markdown 版本仅作过程记录，不代表当前结论。

## 修订核心变化

- 删除“75 次重复问题束 = 独立伯努利试验”的 Wilson 推断；改为启发式观测命中率门限 + 实例聚类 bootstrap。
- 主实验区分 oracle-S 与 runtime-S；金标只用于外部评分，不进入运行时策略。
- 混合基准旧 67.5% 改标为离线 oracle 语义路由率；在线语义裁判不参与本地放行。
- 删除错误 Fano 阈值推论；可行性判据仅保留互信息量纲；终止证明改为有限预算。
- 外部强攻击者复测改为受控披露审计，不再称为出网前安全保证。
- 随机替换基线修复为全出现一致替换，并改称 PRISM-style random replacement，不再冒称 LDP。
- 新增 INTACT-inspired 候选选择基线、确定性泛化/硬线/闭环公平消融。
- 新增未触碰独立模板 holdout（80 条，seed 20261118）。
- 人工研究补充组内相关、实例聚类区间、MAE、阈值混淆；明确原始组合风险 κ 未通过。
- 自学习降为探索性组件；H1 未支持，H1′ 未显著。

## 当前主要结果（修订版）

- 冻结 holdout（n=80）全本地确定性 runtime-S 闭环：本地启发式放行率 **57.5%**，但外部金标字面审计平均命中率 **0.121**，runtime 抽取召回 **0.858**。这说明本地放行不等于出网零泄漏。
- 40 条 holdout 子集在线受控披露审计：2 攻击器 × 2 策略，640 次模型调用、3888 个唯一问题，观测命中 **519**（非零）；闭环外部最大命中率 **0.130**，离线语义裁判效用 **0.363**。本地效用代理与裁判总体 ρ=0.326、MAE=0.358、阈值一致率 68.1%。
- test-160 / mixed-120 的 oracle-S 与 runtime-S 结果分开报告；旧 37.5%/43.8%/5.0%/67.5% 不再作为修正后门限下的最终结论。
- 人工效用研究：总体 ρ=0.839（实例聚类 CI [0.774, 0.892]），MAE=0.133；组内相关 generalized 0.661、placeholder 0.784、random 0.626。
- 标注研究：类型级召回 1.000/0.987；原始组合风险 κ=−0.083（预注册未通过）；构念对齐 κ=0.696 为事后分析。
- 理论数值测试为回归/反例搜索，包含已删除 Fano 阈值推论的反例。

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成数据生成器、标注手册、审计器；新增 `generate_holdout.py` 与 `output/dr_sl_holdout_v1.jsonl` |
| `sim/` | 发布链、runtime-S 抽取器、稳定门限、统计、公平消融、在线受控披露审计、测试 |
| `results/revision_20261118/` | 修订版离线结果、冻结清单、在线审计原始输出与汇总 |
| `human_study/` | 人工评分/标注表、修订分析脚本与结果 |
| `latex/` | 主论文与自动生成的修订结果表 `revision_results.tex` |
| `submission_conference/`, `submission_journal/` | 会议/期刊投稿包 |

## 复现

```bash
python3 -m pip install -r requirements.txt
python3 dataset/generate_holdout.py
python3 sim/revision_experiment.py          # 离线，无需 LLM
python3 sim/revision_online_audit.py        # 在线受控披露审计，需配置后端
python3 sim/make_revision_tables.py
python3 human_study/analyze_results.py
python3 sim/test_loop.py && python3 sim/test_pipeline.py && python3 sim/test_runtime.py && python3 sim/test_revision_stats.py && python3 sim/test_proof_checks.py
```

后端密钥运行时从本地配置读取，仓库不含密钥。本地模型端点通过 `DRSL_LOCAL_BASE_URL` 配置；历史内网地址已从当前文本中移除。在线模型快照/权重版本未完全固定，是复现限制。

## 合规声明

- 全部敏感值为程序合成虚构值，不含真实个人信息。
- MedQA 中文子集题干为医师资格考试题（MIT 许可），具体值已替换。
- 外部审计仅发送合成工件；原始 X 只用于离线语义效标验证，不参与本地放行。
- 内部端点、密钥、本地凭据不上传。

## 许可

- 代码：MIT（`LICENSE`）
- 合成数据：CC-BY-4.0（`dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载
