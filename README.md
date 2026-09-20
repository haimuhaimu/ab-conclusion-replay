# AB Conclusion Replay

一个真实小模型 post-training smoke 实验的**离线结果复算案例**，不是新训练、不是模拟分数，也不是通用聊天模型。

核心发现：100 条 LoRA SFT 明显改善了输出格式，但没有改善恢复 JSON 后的类别识别。负结果保留在报告中。

| 120 条固定 benchmark | Base | 100-row LoRA smoke |
|---|---:|---:|
| Strict exact accuracy | 0.0% | 18.3% |
| Macro F1 | 0.0000 | 0.1419 |
| Plain JSON schema compliance | 0.0% | 100.0% |
| Strict contract（schema + 字段一致性） | 0.0% | 98.3% |
| Recovered category accuracy，仅诊断 | 20.0% | 18.3% |

Base 的 120 个回答都带 Markdown 代码围栏。LoRA 的 120 个回答都是合规 JSON，但 2 个回答的 `valid` 与 `failure_type` 矛盾。不能把 0% → 18.3% 全部解释为推理能力提升。

## 五分钟复算

Python 3.11+，仅标准库，无 `pip install`、模型下载、GPU、API key 或付费服务。`-S` 禁用 site-packages；本地运行不需要网络。

```bash
python3 -S -m unittest discover -s tests -v
python3 -S replay.py --check reports
python3 -S replay.py --output recomputed
python3 -S replay.py --example benchmark.selection_bias.000
```

`recomputed` 必须不存在；程序拒绝覆盖。换一个新目录即可再次生成。所有输入通过审计之后才写报告。`--check reports` 将复算结果与已保存报告逐字节比较，不是直接展示旧分数。

- [比较报告](reports/comparison.md)：所有类别、严格指标、诊断指标、限制。
- [metrics.json](reports/metrics.json)：完整机器可读指标与输入哈希。
- [badcases.jsonl](reports/badcases.jsonl)：全部 218 条 strict 错例（Base 120 + LoRA 98），包含题目、原始回答、重新解析结果。
- [评分定义与来源](METHOD.md)、[可检查的例子](EXAMPLES.md)、[下一轮实验设计](NEXT_EXPERIMENT.md)。

## 实际实验与边界

历史模型为 [Qwen/Qwen2.5-0.5B-Instruct，固定 revision](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/tree/7ae557604adf67be50417f59c2c2f167def9a775)。原实验使用 Apple M3 Pro / PyTorch MPS、普通 LoRA，而非 CUDA QLoRA。100 条训练、80 条 validation、120 条 benchmark；先完成 Base eval，再训练，再评估同一 benchmark。运行配置、时间、seed、数据哈希见 [experiment.json](evidence/experiment.json)。这次只复算已保存的预测。

本包复现的是**评分与分析**，不是端到端重训：没有权重、adapter、训练数据、loss curve 或训练运行时。它们仍保存在原始私有实验工作区，没有因打包而删改。

训练与 benchmark 共享类别生成器；不同 seed 和 `template_family` 前缀不能证明模板隔离。数值也并非都从同一批原始观测推导，ground truth 是生成器标签，尚非专家审核的统计金标准。训练 target 的 confidence 全为 1.0，LoRA 也全部输出 1.0。因此本结果既不证明稳定泛化，也不证明校准有效。

当前 120 题已经被逐题分析，应视为公开回归/诊断集。下一轮确认性评估必须另建、冻结且隔离模板的测试集，不能通过重标这 120 题提高分数。

## 代码阅读卡

入口是 [replay.py](replay.py)，评分内核是 [scoring.py](scoring.py) 的 `parse_output → align → score`。值得读的 6 行：

```python
if row.get("id") != identifier:
    raise ValueError("prediction IDs must match benchmark order exactly")
if (row.get("gold_category") != case["category"]
        or type(row.get("gold_valid")) is not bool
        or row["gold_valid"] != target["valid"]):
    raise ValueError("prediction gold fields disagree with benchmark")
```

目的不是“让评测顺利跑完”，而是在样本错位、gold 改写时停止。原始回答每次重新解析；文件里的缓存解析只用于交叉检查。延伸阅读 [tests/test_scoring.py](tests/test_scoring.py) 和 [tests/test_replay.py](tests/test_replay.py)。

## 发布状态

这是待确认发布范围与许可证的隔离候选包。没有创建公共仓库、推送或合并 PR；也没有改变任何私有仓库可见性。候选白名单和许可证建议见 [PUBLICATION.md](PUBLICATION.md)。
