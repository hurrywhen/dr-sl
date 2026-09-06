# DR-SL — Dehydrate-Rehydrate with Reversibility-Guided Self-Learning Loop

面向云-本地 LLM 推理的敏感信息隔离方法：以可逆性验证为核心的脱敏判定闭环，
Pufferfish 语义 + Fano 下界证书 + rate-privacy 可行性判据，全本地在线判定，
离线阶段仅接触非敏感语料。

**Paper (v1.2, Chinese working version)**: `DR-SL 论文（基于可逆性验证的自学习脱敏闭环）v1_2.md`
**Pre-registered protocol**: `experiment_protocol_v1.md`（含偏离记录 D1–D12，全程留痕）

## 仓库结构

| 目录/文件 | 内容 |
|---|---|
| `dataset/` | 合成评测数据集 v2（930 条）+ 扩充（test_ext 240 / T_new 240）+ 阶段 2 流（120 条）；生成器、标注手册、审计器、规约与测试 |
| `sim/` | 实验框架：字典序闭环（`loop.py`）、级联抽取器（`extractor.py`）、QA 探针/攻击者/脱水管线（`pipeline.py`）、合成人口库与 k-匿名（`synthpop.py`）、分布差异测量（`shift.py`）、理论界数值验证（`proof_checks.py`）、阶段编排（`run_experiments.py`, `stage2.py`, `stage3.py`）、规约（`specs/`）与全部测试 |
| `results/` | 全部实验产出（JSON/JSONL/PNG）：k-匿名、阶段 1（pilot_20260829）、阶段 2（stage2_20260902）、阶段 3（stage3_20260905） |
| `DR-SL 论文 v1_0_*.md` | 审稿意见、两轮讨论与回复、执行记录（预注册过程全记录） |

## 主要结果速览

- 主闭环（train 400，严格门限 τ_L=0.05 + ≥75 探测）：泄漏 0.457→0.304（p≈0），任务效用 U 保持 ≥0.97，PASS 率 37.5%，INFEASIBLE 实例全部输出残余泄漏报告；
- 脱水后强攻击者泄漏 0.77–0.79 → 0.41–0.44（约 45% 相对削减）；
- 级联抽取器召回 0.951（显式 0.977 / 准标识符 0.931）；
- 评估器校准 Δ̂ = +0.181（本地 vs 强模型，证书 L̂ = L_local + Δ̂）；
- 偏态参考人口下 16.7% 实例 k̃<5（准标识符泄漏首次可测量）；
- 消融：去反推分支 → 假放行泄漏 0.327；去 U 闸门 → 效用崩至 0.111；
- 剂量响应：效率平稳且 PASS 输出安全性跨分布差异恒定（安全-效率分离）；
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
```

后端密钥运行时从 `~/.config/opencode/opencode.jsonc` / `~/.local/share/opencode/auth.json`
读取，仓库内不含任何密钥。

## 合规声明

- 全部敏感值（姓名/证件号/卡号/电话/地址/机构名等）为程序合成的**虚构值**
  （手机号 190 号段、邮箱 example.com、地名/机构名为虚构），不含任何真实个人信息；
- MedQA 中文子集题干为医师资格考试题（非真实患者信息，MIT 许可，引用 Jin et al. 2020）；
  源数据 `dataset/data_raw/` 不入库，按 `dataset/README.md` 说明自行获取；
- 合成人口库 W2 示例边际分布为占位数据，正式使用须替换为公开统计表并登记来源。

## 许可

- 代码：MIT（见 `LICENSE`）
- 数据集（合成部分）：CC-BY-4.0（见 `dataset/LICENSE-DATA`）
- 论文文本：版权保留，投稿前请勿转载

## 引用

```bibtex
@article{drsl2026,
  title   = {Dehydrate-Rehydrate with Reversibility-Guided Self-Learning Loop:
             Sensitive Information Isolation for Cloud-Local LLM Inference},
  author  = {(see paper)},
  journal = {arXiv preprint (to appear)},
  year    = {2026}
}
```
