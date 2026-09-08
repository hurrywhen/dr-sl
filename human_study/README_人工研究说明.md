# 人工研究操作说明（两项，均为可选加分项）

所有材料均为**合成虚构数据**，无隐私合规负担；评分结果只用于论文的人工效标验证。

## 研究一：语义效用人工评分（决定性实验的人工锚点，约 1–1.5 小时/人，建议 2–3 人）

**目的**：验证"如实泛化"（如 84岁→80多岁、48500元→4万至5万区间）在真实咨询场景中的可用性——
自动精确值度量对此系统性低估，人工评分是最终裁决（评审意见 B4/建议 4）。

**操作**：
1. 打开 `utility_scoring_sheet.csv`（160 行 = 40 实例 × 4 个盲态变体 A/B/C/D，顺序已随机化）；
2. 每行对照【original_text】阅读【processed_text】，回答：
   *"仅凭处理后材料，AI 助手能否给出与原始材料几乎同样有用、有针对性且正确的答复？"*
3. 在 `score_0_or_0.5_or_1` 列填：
   - **1** = 关键信息全部保留（泛化形式可接受，只要仍能支撑同样的建议）；
   - **0.5** = 部分缺失/过度模糊，建议受限但仍有价值；
   - **0** = 关键信息缺失、被占位符替代、或被篡改为与原值不符（错误值按缺失计）；
4. `confidence_1_to_5` 填自评把握（1=很不确定，5=非常确定），`note` 可留空；
5. 多人评分：每人复制一份文件（命名 `utility_scoring_sheet_<姓名>.csv`），独立完成，不互相讨论。

**回收后**：把文件放回本目录，我会计算 Spearman ρ（人工 vs 自动 U_sem）、标注者间 Krippendorff α，
并按盲态映射（`utility_variant_key.json`，评分人勿看）分操作点汇总入论文 T23。

## 研究二：敏感属性人工标注复核（Cohen's κ 金标验证，约 40–60 分钟/人，建议 2 人）

**目的**：为"自动标注金标"提供人工 κ 证据（评审意见 B6）。

**操作**：
1. 打开 `annotation_sheet.csv`（50 条）；
2. 每条在 `sensitive_items(type=value;...)` 列出你认为的全部敏感项，格式 `类型=原文逐字值`，分号分隔；
   类型词表（尽量选用）：name, phone, id_card, email, address, bank_card, medical_record_no, passport,
   plate, case_no, age, gender, city, hospital, disease, drug, occupation, employer, income, amount,
   date, visit_date, school, detention, court, lawfirm, airline, hotel, flight_no, room_no,
   work_years, children_count, marriage_years, relation, charge, case_type, allergy, duration,
   deposit_no, order_no, ticket_no, insurance_id, fund_account, card_tail；
3. `combo_risk(y/n)`：这些属性组合起来能否在小范围人群中唯一定位当事人？
4. 两人独立完成后回收，我计算 Cohen's κ 与对自动金标的召回/精确率。

## 判定标准（预注册）

- 研究一：人工均分与自动 U_sem 的 Spearman ρ ≥ 0.8 → 自动指标效度成立；
  泛化点（generalized）人工均分显著高于精确值度量（0.033）→ 论文实用故事按人工结果改写；
- 研究二：κ ≥ 0.8 → 自动金标可信；κ ∈ [0.6, 0.8) → 报告并讨论分歧类别。
