# 规约：实验管线（sim/pipeline.py + backends.py）

对应协议 §5–§8 与论文 §3/§6。TDD 交付：测试先行（`test_pipeline.py`），MockBackend 驱动。

## 后端契约（backends.py）

`HTTPBackend(name, base_url, model, api_key=None, temperature=0.3, max_tokens=512, timeout=600, retries=2)`
- `.complete(system, user) -> str`：chat 完成；失败重试；超时异常。
- `.embed(texts) -> list[list[float]]`（仅嵌入后端）。
- `BACKENDS` 注册表（角色 → 配置）：
  - `local_main` qwen3.8-27b-mlx @ <LOCAL_LLM_ENDPOINT>（并发 1，max_tokens=512）
  - `local_small` ornith-1.5-35b（同端点）
  - `local_embed` text-embedding-nomic-embed-text-v1.5（同端点）
  - `online_strong` qwen3.8-max、`online_fast` qwen3.8-flash、`online_alt` glm-5.2（token-plan 网关，密钥运行时从 `~/.local/share/opencode/auth.json` 读取，不落盘、不打印）
  - `kimi_k3` k3（kimi coding 端点，密钥运行时从 `~/.config/opencode/opencode.jsonc` 读取）
- `MockBackend(script)`：按 (role, seq) 返回脚本化响应，供测试。

## 组件契约（pipeline.py）

1. `ATTR_NAMES`：类型→中文属性名映射（覆盖数据集全部实体类型）。
2. `gen_probe_questions(item) -> [(q, truth, kind)]`：
   - 每个显式/准标识符实体一条结构化探针："根据材料，该当事人的<属性>是什么？无法推断回答 UNKNOWN。"truth=实体值；
   - 组合探针：有 combos → "能否唯一确定该当事人？回答 能/不能/信息不足"，truth=能/不能。
3. `grade(answer, truth, kind) -> {0,1}`：
   - 结构化：规范化（去空白/标点/全半角）后双向包含匹配；
   - 判定型：答案首词 ∈ {能,不能,信息不足} 精确匹配。
4. `attack(backend, D, questions, level) -> list[(ans, hit)]`：A_1 在 system 注入冻结领域先验文本；批量一次调用回答全部问题（编号对齐）。
5. `branch1(backend, D, item, level) -> {hits, n, L, wilson_upper}`。
6. `qa_probe(backend, D, item) -> {U, n, detail}`：仅对 `task_relevant=true` 实体出题；A_ref=标注真值（免 LLM）；A_D=backend 基于 D 回答；U=平均命中。
7. `extract_explicit(text) -> entities`：正则层（手机/座机/邮箱/身份证/银行卡/证件号），类别与数据集一致。
8. `dehydrate(backend, X, S) -> {D, removed, generalized}`；`strengthen(backend, D, s, X)`；`loosen(backend, D, X, S)`：LLM 调用，短 JSON 输出（≤300 token），解析失败重试 1 次后抛错。
9. 适配器把 8 接入 `loop.lexicographic_loop`（evaluate 组合 branch1 + qa_probe + R 诊断占位）。

## 通过判据

- 单元测试（Mock）：grade 各分支、问题生成计数与真值、D=X 时 U=1、branch1 统计正确、脱水 JSON 解析与失败重试；
- 活体冒烟：online_fast 与 local_main 各 1 实例，输出可解析率 100%。
