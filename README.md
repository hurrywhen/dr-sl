# DR-SL — Dehydrate-Rehydrate with Reversibility-Guided Self-Learning Loop

面向云-本地 LLM 推理的敏感信息隔离方法：以可逆性验证为核心的脱敏判定闭环，
Pufferfish 语义 + Fano 下界证书 + rate-privacy 可行性判据，全本地在线判定，
离线阶段仅接触非敏感语料。

**Paper (投稿版, LaTeX)**: `latex/main.tex`（中文工作版：`DR-SL 论文（基于可逆性验证的自学习脱敏闭环）v1_2.md`；英文 Markdown 镜像：`DR-SL_paper_submission_EN.md`）
**Pre-registered protocol**: `experiment_protocol_v1.md`（含偏离记录 D1–D17，全程留痕）

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成评测数据集 v2（930 条）+ 扩充（test_ext 240 / T_new 240）+ 阶段 2 流（120 条）+ 混合耦合基准（`output/dr_sl_mixed.jsonl` 120 条）；生成器、标注手册、审计器、规约与测试 |
| `sim/` | 实验框架：字典序闭环（`loop.py`）、级联抽取器（`extractor.py`）、QA 探针/攻击者/脱水管线（`pipeline.py`，含枚举式探针 `attack_enum_bundle`）、合成人口库与 k-匿名（`synthpop.py`）、分布差异测量（`shift.py`）、理论界数值验证（`proof_checks.py`）、阶段编排（`run_experiments.py`, `stage2.py`–`stage5.py`）、规约（`specs/`）与全部测试 |
| `results/` | 全部实验产出（JSON/JSONL/PNG）：k-匿名、阶段 1（pilot_20260829）、阶段 2（stage2_20260902）、阶段 3（stage3_20260905）、修订轮（stage4_20260907、stage5_20260907，含 T18–T25 与 P41 基线）、枚举探针全管线复跑（stage6_20260911，进行中） |
| `human_study/` | 两项人工研究包：盲态评分表、标注复核表、分析脚本（`analyze_results.py`）、结果（`analysis_results.json`）与操作说明（含预注册判定标准） |
| `latex/` | 投稿版论文（`main.tex` → `main.pdf`，40 页）与 arXiv 源码包（`drsl_arxiv_source.tar.gz`） |
| `DR-SL 论文 v1_0_*.md` | 审稿意见、讨论与回复、执行记录（预注册过程全记录） |

## 主要结果速览

- 主闭环（train 400，严格门限 τ_L=0.05 + ≥75 探测）：泄漏 **0.457→0.304**（p≈0，前后同测量基础），PASS 率 37.5%，INFEASIBLE 实例全部输出残余泄漏报告；*注：硬线擦除前工件上的效用数值部分由残余字面值承载，效用结论按 T18/T21 口径仅在擦除后工件上报告*；
- 强制三段放行链（本地门限 → 确定性硬线 → 外部强攻击者复测）下，test-160 出网字面泄漏 **0.000**（flash/glm 双强攻击者；汇集 95% 上界 <0.001）；
- 安全点（如实泛化）语义效用 **U_sem=0.431**（全耦合最坏基准）/ **0.571**（混合耦合基准）；混合基准自动放行率 **67.5%**（严格口径 24.2%），并在同一放行规则下对 placeholder（58.3%）与选择性 LDP（25.0%，L=0.070 越限）实测 Pareto 占优（P41）；
- 两项人工研究达标：效用人工锚点 ρ=**0.839**（预注册 ≥0.8，2 评分员×160 行盲态）；标注复核类型级召回 **1.000/0.987**、精确率 0.959/0.991（2 标注员×50 实例）；
- 级联抽取器召回 0.951（显式 0.977 / 准标识符 0.931；跨家族复核 glm-5.2 召回 0.983）；
- 评估器校准 Δ̂ = +0.181（本地 vs 强模型）；T25 机制诊断：本地证书的体制差距系**探针格式**伪影；枚举式探针全管线复跑（T25c, test-160）：PASS 率 43.8%→5.0%、轮数 4.0→7.8、成本不变——旧 PASS 大多为探针盲假放行；外部复测显示银行工件真干净（L=0.000）、法律工件残余开放词表类目字面值（L=0.320），硬线后全部 0.000——软证书诚实化，硬线/外部复测对类目类承重；train-400 配对复跑（n=372）：raw L 0.452→0.763、配对削减 −0.155→−0.409、PASS 38.4%→7.8%——泄漏削减对探针格式稳健；
- 偏态参考人口下 16.7%–21.1% 准标识符携带实例（全实例 7.9%–11.9%）k̃<5；
- 消融：去反推分支 → 假放行泄漏 0.327；去 U 闸门 → 效用崩至 0.111；
- 理论界数值验证：3×1000 合成机制配置零反例；
- 自学习：H1 未获支持、修正假设 H1′ 边际（p=0.059）——预注册负结果如实报告。

## 复现

```bash
cd dataset && python3 generate_dataset.py && python3 rewrite_medqa.py \
  && python3 generate_expansion.py && python3 generate_stage2_stream.py
cd ../sim && python3 test_loop.py && python3 test_pipeline.py \
  && python3 test_extractor.py && python3 test_proof_checks.py \
  && python3 test_shift.py && python3 test_distill.py
python3 run_kanonymity.py          # k-匿名（无需 LLM）
# LLM 阶段需配置后端（OpenAI 兼容端点），见 sim/backends.py BACKENDS 注册表
python3 run_experiments.py p0      # 正则层召回（无需 LLM）
python3 stage2.py p12              # 需在线后端
python3 stage5.py p38              # 混合耦合基准（T24）；p41 为同基准基线
cd ../human_study && python3 analyze_results.py   # 人工研究统计（ρ/κ/Wilson）
```

后端密钥运行时从 `~/.config/opencode/opencode.jsonc` / `~/.local/share/opencode/auth.json`
读取，仓库内不含任何密钥。

## 合规声明

- 全部敏感值（姓名/证件号/卡号/电话/地址/机构名等）为程序合成的**虚构值**
  （手机号 190 号段、邮箱 example.com、地名/机构名为虚构），不含任何真实个人信息；
- MedQA 中文子集题干为医师资格考试题（非真实患者信息，MIT 许可，引用 Jin et al. 2021,
  Applied Sciences 11(14):6421, arXiv:2009.13081）；
  源数据 `dataset/data_raw/` 不入库，按 `dataset/README.md` 说明自行获取；
- 合成人口库 W2 示例边际分布为占位数据，正式使用须替换为公开统计表并登记来源。

## 许可

- 代码：MIT（见 `LICENSE`）
- 数据集（合成部分）：CC-BY-4.0（见 `dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载

## 引用

```bibtex
@article{drsl2026,
  title   = {Reversibility-Verified De-identification for Cloud-Local LLM Inference:
             A Locally Certified Dehydrate-Rehydrate Loop with Layered Assurance (DR-SL)},
  author  = {Hu, Wen and Yu, Ya and Wang, Xutong},
  journal = {arXiv preprint (to appear)},
  year    = {2026}
}
```
