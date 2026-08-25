# DR-SL 实证数据集 v2

配套论文 §6 实验设计框架的脱敏评测数据集。合成模板样本 680 条 + MedQA 中文子集
改写样本 250 条，共 930 条。所有显式敏感值均为程序生成的虚构值，不包含任何真实
个人的真实敏感信息。

## 文件构成

| 文件 | 说明 |
|---|---|
| `output/dr_sl_dataset_v2.jsonl` | 主数据集（v2），930 条 |
| `output/dr_sl_dataset_v1.jsonl` | 纯合成版本，680 条 |
| `output/medqa_rewrite.jsonl` | MedQA 改写样本单独副本，250 条 |
| `output/stats_report.json` | v2 分布统计报告 |
| `output/medqa_rewrite_report.json` | 改写流水线报告（筛选/拒绝原因计数） |
| `schema.json` | 单条样本的 JSON Schema |
| `validate_schema.py` | 校验脚本（schema + 配额 + 跨集隔离 + 准标识符占比） |
| `audit_annotations.py` | 标注手册规则审计器（§2–§5 机器可查规则） |
| `annotation_handbook.md` | 标注员手册 v1 |
| `synth_values.py` | 虚构敏感值生成器 |
| `templates.py` | 四领域场景模板（每领域 12 主模板 + 4 对抗模板） |
| `generate_dataset.py` | 合成生成脚本（种子 20260825，可复现） |
| `rewrite_medqa.py` | MedQA 改写脚本（种子 20260826，可复现） |
| `data_raw/medqa_zh_4options_train.jsonl` | MedQA 大陆 4 选项中文子集（源数据，不入库，见下方获取方式） |

## 数据构成（930 条）

| 划分 | 数量 | 构成 | 用途 |
|---|---|---|---|
| calibration | 290 | 合成 200（四领域各 50）+ MedQA 改写 90 | 提示词热启动、门限标定 |
| train | 400 | 合成 240（各 60）+ MedQA 改写 160 | 模拟在线流 |
| test | 160 | 纯合成（各 40） | 基线对比，与 P2Skill/PRISM 160-prompt 基准同构 |
| adversarial | 80 | 纯合成（各 20） | 准标识符组合 / 混淆格式 / 过度披露诱导 / 过度脱敏陷阱 |

MedQA 改写样本仅进入 calibration/train（医疗领域），测试集保持纯合成以维持
PRISM 同构口径。

## MedQA 改写流水线（rewrite_medqa.py）

1. **加载**：MedQA 大陆 4-options 中文训练集（27400 题，MIT 许可）；
2. **场景筛选**：保留含患者叙事（岁/患儿/患者/孕妇等）且长度 40–260 字的题干，
   剔除纯知识题（7871 题候选）；
3. **剥离考试问句**：正则删除"最可能的诊断是（　）"类考试尾巴；
4. **准标识符抽取**：年龄（岁/月龄/孕周）、性别、疾病（内置 130+ 常见病词典，
   最长匹配，≤2 个）；
5. **第一人称化改写**：三种口吻模板（患者本人/家属/接诊医生），划分独占模板
   （calibration: med_rw01–03，train: med_rw04–06）保证跨集隔离；
6. **敏感值注入**：按密度目标注入 0–2 个虚构显式标识符（姓名/电话/身份证/
   门诊号/邮箱），`task_relevant=false`；
7. **去重**：与已有全量样本相似度 < 0.85；
8. **溯源**：每条带 `source_id`（原始行号），`source=open_dataset_rewrite`。

## 标注规范与手册一致性

标注体系见 `annotation_handbook.md`。v2 相对 v1 的手册合规修正：

- **§三 task_relevant**：全部联系/证件/账号类显式标识符统一置 `false`
  （原 218 处误标已修复）；对抗样本不受诱导措辞影响；
- **§4 combos**：规则收紧为"定位性属性（城市/单位/学校/医院/羁押场所）+
  人口学或敏感属性（年龄/性别/职业/疾病/收入等）"才标组合，
  泛化知识问答（med_t11、bank_t07、legal_t08）不标；combo 数由 555 降至 203；
- **§2.3.2 机构名**：bank_t07 中泛泛比较的银行名不再标注；
- **§五 over_redaction_trap**：med_a04、legal_a04 补充了 task_relevant=true 实体；
- `audit_annotations.py` 对 v2 全量审计 0 问题。

当前标注仍为自动标注（`auto_v1`），正式实验前须按手册执行双人标注
（Cohen's κ ≥ 0.8）+ 仲裁后写回。

## 质量门槛落实情况

- 字段完整性、span 一致性、id 唯一性、划分配额：`validate_schema.py` 强制校验
  （配额仅约束 `synthetic_template` 样本，改写样本额外计数；测试集禁止非合成来源）；
- 跨集隔离：合成模板与改写模板均按划分独占；
- 去重：合成与改写均在生成阶段做相似度去重（0.85，difflib 近似 BERTScore）；
- 准标识符样本占比：100%（≥40% 门槛）；
- 手册合规：`audit_annotations.py` 0 问题。

## 与规格书的偏差（需在论文中如实报告）

- 敏感密度目标 低/中/高 = 30/50/20，v2 实际 17.7%/73.8%/8.5%
  （v1 为 5%/83%/12%，MedQA 改写后明显改善但未完全达标）；
- 难度分布无 easy 档改写样本（准标识符存在即判 medium 以上）；
- 长度分布受改写短文本影响偏移为 短/中/长 = 42.7%/35.4%/21.9%。

## 复现与使用

```bash
cd dataset
# 源数据（不入库）：从 MedQA 官方发布包解压 data_clean/questions/Mainland/4_options/train.jsonl
# 至 data_raw/medqa_zh_4options_train.jsonl
#   https://drive.google.com/file/d/1ImYUSLk9JbgHXOemfvyiDiirluZHPeQw/view
python3 generate_dataset.py                          # 生成 v1 合成集（680 条）
python3 rewrite_medqa.py                             # MedQA 改写并合并出 v2（930 条）
python3 validate_schema.py output/dr_sl_dataset_v2.jsonl
python3 audit_annotations.py output/dr_sl_dataset_v2.jsonl
```

## 合规声明

- 全部显式敏感值（姓名、证件号、卡号、电话、地址、机构名等）为程序合成的虚构值，
  手机号使用 190 号段、邮箱使用 example.com、地名/机构名为虚构名称；
- MedQA 中文子集题干为医师资格考试题（非真实患者信息），MIT 许可，论文中须引用
  Jin et al. (2020)；改写样本仅注入虚构 PII；
- 若后续引入 PRISM 同构样本，须逐项核验其开源许可限制（商业使用/再版/训练）。
