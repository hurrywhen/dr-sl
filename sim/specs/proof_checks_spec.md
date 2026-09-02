# 规约：证明数值验证（proof_checks）

对应论文 v1_2 附录 A/B。被测对象为三个理论界，测试方法为"参数已知合成机制上的反例搜索"。

## 输入/输出契约

- `exact_mi(joint) -> float`：离散联合分布表（任意维数，末两轴视为两变量）的精确互信息。
- `exact_entropy(p) -> float`：离散分布熵。
- `fano_lower_bound(H_S, hit_rates, value_sizes) -> float`：定理 2′ 右端。
- `pufferfish_epsilon_true(channel, prior) -> float`：机制真实最小 ε（最大绝对对数似然比）。
- `map_accuracy(channel, prior) -> float`：最优（MAP）攻击者命中率。
- `pufferfish_witness_bound(L, p_min, p_max) -> float`：命题 2 右端。

## 性质（每个 ≥1000 随机配置，固定种子 20260829）

1. **T-B（Fano 下界）**：随机联合分布 P(D, S_1..S_m)，最优攻击者命中率 L_i。断言
   I(D;S) ≥ H(S) − Σ_i [H_2(1−L_i) + (1−L_i)log(|V_i|−1)] − 1e-9。
2. **T-A（Pufferfish 见证）**：随机信道 P(d|v) + 正值先验。断言
   ε_true ≥ ln(L*/(1−L*)) + ln(p_min/p_max) − 1e-9；
   且对任意 L ≤ L*，界关于 L 单调（用 L 的界 ≤ 用 L* 的界）。
   边界：独立信道（P(d|v)=P(d)）时界 ≤ 0（空界）。
3. **T-C（可行性判据）**：随机 P(X)，S、T 取 X 的确定性函数（可退化），随机信道 P(D|X,S)。断言
   I(D;T) ≤ I(D;S) + I(X;T|S) + 1e-9。

## 通过判据

全部配置通过 → 归档测试报告（配置数、种子、边界用例清单）；任何反例 → 停止并报告最小反例。
