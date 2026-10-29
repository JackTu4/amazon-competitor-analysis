# Amazon 竞品分析系统 · 评估报告

- 生成时间：2026-10-29T09:49:53.789618+00:00（UTC）
- 代码版本：`30c9f2a28503f75b1a5d5be5439c89672f58ce5f`（未提交改动 128 个文件，dirty）
- 模型：`deepseek-v4-flash-0731`，Embedding：`qwen3.7-text-embedding-flash`
- 运行模式：真实模式（MOCK_MODE=False）

## 汇总

| 指标 | 数值 |
| --- | --- |
| 案例数 | 10（正向 7 / 负向 3） |
| 任务成功率 | 9/10 = 90.0% |
| 目标字段准确率（正向均值） | 0.286 |
| 竞品有效性得分（正向均值） | 0.925 |
| 信息完整度（全部均值） | 0.553 |
| 平均耗时 | 335.3 秒 |
| API 总成本 | $0.0000（单案例均值 $0.0000） |

## 逐案例

| 案例 | 商品 | 类型 | 状态 | 通过 | 耗时(s) | 目标准确率 | 竞品得分 | 有效竞品 | 成本($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case-01 | HUADISK 256GB NVMe SSD | positive | completed | 通过 | 388.8 | 0.600 | 0.944 | 3 | 0.0000 |
| case-02 | Samsung 980 1TB NVMe SSD | positive | completed | 通过 | 235.7 | 0.400 | 0.833 | 3 | 0.0000 |
| case-03 | Crucial P3 500GB NVMe SSD | positive | completed | 通过 | 207.5 | 0.200 | 0.944 | 3 | 0.0000 |
| case-04 | Kingston NV2 1TB NVMe SSD | positive | completed | 通过 | 250.8 | 0.000 | 0.867 | 3 | 0.0000 |
| case-05 | SanDisk 128GB microSD card | positive | completed | 通过 | 340.9 | 0.200 | 0.889 | 3 | 0.0000 |
| case-06 | Anker 20W USB-C charger | positive | completed | 通过 | 819.6 | 0.200 | 1.000 | 3 | 0.0000 |
| case-07 | Logitech M185 wireless mouse | positive | completed | 未通过 | 738.7 | 0.400 | 1.000 | 1 | 0.0000 |
| case-08 | 256GB NVMe SSD | negative | failed | 通过 | 46.5 |  | 0.000 | 0 | 0.0000 |
| case-09 | 罗技 M185 无线鼠标 | negative | failed | 通过 | 306.2 | 0.000 | 0.000 | 0 | 0.0000 |
| case-10 | XYZABC 999TB SSD | negative | failed | 通过 | 18.0 | 0.000 | 0.000 | 0 | 0.0000 |

## 未通过的案例

### case-07 · Logitech M185 wireless mouse

- 有效竞品 1 个，少于预期 2 个

## 结论

### 1. 能力：哪类输入稳定

7 个正向案例全部跑完（status=completed），其中 6 个通过；3 个负向案例全部按预期失败，整体 9/10。6 个通过的正向案例都产出了 3 个有效竞品，竞品有效性均值 0.925，覆盖 NVMe SSD、microSD、20W 充电器、无线鼠标四类英文查询；正向信息完整度均值 0.790。可以说的口径是「英文、品牌+型号明确、有稳定 Amazon listing 的 3C 标品」；不能说成「10 个案例 9 个通过 = 90% 准确率」，那是成败判定，不是字段准确率。

### 2. 边界：哪类会失败

最明显的失败不是模型答错，而是目标定位和元数据：

- 7 个正向案例解析出的目标 ASIN 与人工预期全部不同（0/7 命中）。case-01/02/05/07 解析到同系列但不同的 listing（例如 case-02 评论数预期 49、实际 16,441；case-07 预期 45,564、实际 1,524），case-03/04/06 的目标价格、评分、评论数三项全为空。现在无法区分是解析指错了 listing，还是人工标签本身指向另一个 listing；复跑前要用完整商品 URL 重新核对。
- 因此报告里的目标字段准确率 0.286 只能说明「解析结果与标签不是同一个 listing + 3 个案例元数据缺失」，不能当作字段抽取准确率引用。其中 case-05 的评分 4.6 vs 4.7 还是 `RATING_TOLERANCE=0.1` 的浮点边界误判（`evals/framework.py` 的评估脚本 bug，不是模型问题）。
- 价格 7 个正向案例全部判错（0/7）：case-01 抓到 346.51 CNY、预期 50.49 USD，脚本不换算币种；case-02/05 币种相同但价格与预期不一致（349.00 vs 189.99、35.99 vs 42.99），同样指向不同 listing；case-03/04/06/07 价格为空。修好币种和 listing 口径前，不要引用价格准确率。
- 竞品侧只有 case-07（Logitech M185，低客单价、评论量大）掉到 1 个有效竞品，低于预期的 2 个；这是唯一一个因竞品数量不达标的案例。
- 负向案例（无品牌、纯中文、虚构型号）3/3 都正确失败，没有出现「信息不足还硬编一个商品」。所以不能照抄模板里「无品牌输入仍强行产出」的说法，这轮数据不支持。

### 3. 代价：耗时、成本、钱花在哪

- 平均耗时 335.3 秒（10 个案例，含负向快速失败）；只看正向是 426.0 秒，中位数 340.9 秒，最慢 case-06 819.6 秒，最快正向 case-03 207.5 秒。负向失败很快（case-10 18.0 秒、case-08 46.5 秒），对外说「单次分析约 7 分钟」比引用 335 秒更接近真实体验。
- 单次正向分析平均 22.1 次 LLM 调用、约 82k prompt + 44.6k completion tokens、7.7 次 Tavily 搜索、1 个 Bright Data 评论采集任务。钱主要花在 LLM 的 token 上，其次是评论采集和搜索。
- 成本金额目前不能引用：`pricing.json` 的单价全是 0，report.md 里的 $0.0000 是占位符而不是账单。复跑前必须填单价，否则任何材料里都不要写「单次成本 $X」。

### 一条可以写进简历的结论

搭了 10 案例离线评估（7 正向 + 3 负向），一条命令复跑，覆盖成功率、竞品有效性、耗时与 token 消耗；正向 6/7 通过、负向 3/3 按预期拒绝，竞品有效性 0.925，并定位出目标 ASIN 解析与元数据缺失这一主要边界。

## 这份评估不能证明什么

- 案例数只有 10 个，是抽样检查，不是统计意义上的基准测试。
- 预期值来自人工录入的 Amazon 页面，价格和评论数会随时间变化，同一案例隔几周重跑可能不再一致。
- 竞品只按 ASIN 格式、去重、品牌差异、类目关键词判定，没有人工判断“是否真的好用”。
- 目标字段准确率没有校正 listing 版本和币种，本轮 0.286 不能当作字段抽取准确率；ASIN 命中率 0/7 同样受人工标签影响。
- 成本是本地按单价估算的，不是账单金额；单价见 `evals/pricing.json`（本轮单价全为 0，因此金额不可用）。
- 真实用户场景下的并发、稳定性和数据规模都没有覆盖。

## 下次复跑

```bash
cd "E:/Analysis System"
python -m evals.run_all --force     # 全量 10 个，约 40–100 分钟
python -m evals.summarize           # 重新生成 summary.csv / report.md
```

- 只验证一个修复：`python -m evals.run_all --only case-07 --force`（单案例约 3–14 分钟），再跑 `python -m evals.summarize`。
- 复跑前先做三件事：① 用完整商品 URL 重新核对 7 个正向案例的 `target_asin` / `price` / `reviews`；② 在 `evals/pricing.json` 填真实单价；③ 修 `RATING_TOLERANCE` 的浮点边界（比较时加 `1e-9`），并给价格加币种字段或统一换算成 USD。
- 复跑后对齐同一个 `case-XX.json` 的四个字段：`duration_seconds`、`cost_usd.total`、`scores.competitor.valid_count`、`scores.target_field_accuracy`。重点看 case-03/04/06 的元数据是否补齐、case-07 的有效竞品是否回到 ≥2。
- 注意：`evals.summarize` 会重新生成 report.md，覆盖本文件的结论段；复跑后需要根据新表重写结论，不要沿用旧数字。

