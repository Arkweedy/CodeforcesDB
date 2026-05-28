# Tagging 规则

本文件记录 tag 层级、importance、evidence、新 tag 标准和前端翻译同步。

## 层级 tag

tag 是动态层级路径，不是封闭集合。

示例：

```text
algorithm/string/acam
algorithm/dp/automaton-dp
algorithm/transform/fwt
algorithm/transform/fwt/and-fwt
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
trick/maintain-contribution
```

父 tag 查询应包含子 tag。例如查询 `algorithm/transform/fwt` 应命中 `algorithm/transform/fwt/and-fwt`。

## Importance

`problem_tags.importance`：

```text
primary
secondary
incidental
```

语义：

- `primary`：主解法核心。如果移除该技术，解法基本不成立。
- `secondary`：重要辅助技术、替代解法中的核心技术，或实现中明显有价值的结构。
- `incidental`：题面风格、弱相关背景、只在官方 tag 中出现但不是高质量检索点。

每个 `primary` tag 必须有 evidence。

默认查询匹配 `primary + secondary`，不匹配 `incidental`。

## 新 tag 标准

新增 tag 必须满足：

- 能显著改善未来检索。
- 不是一次性题面描述。
- 和已有 tag 不重复。
- 同义词应加入 alias，而不是创建重复 tag。
- 有清楚的父 tag、定义和使用边界。
- 预期可复用于多题，或属于经典算法、技巧、证明模式、题型范式。

新增 tag 默认状态：

```text
candidate
```

reviewed JSON 中应提供：

```json
{
  "tag": "algorithm/transform/fwt/and-fwt",
  "importance": "primary",
  "evidence": "使用 AND FWT 聚合 mask 超集贡献。",
  "solution_variant": "and-fwt-batched-greedy",
  "description": "Fast Walsh-Hadamard Transform specialized for subset/superset convolution over bitwise AND masks.",
  "parent": "algorithm/transform/fwt",
  "created_reason": "AND-FWT is a concrete FWT subtype useful for high-rating bitmask aggregation queries.",
  "status": "candidate"
}
```

## Evidence

Evidence 应说明 tag 与解法的关系，而不是重复 tag 名。

好 evidence：

```text
The optimized solution uses AND Fast Walsh-Hadamard Transform to aggregate costs over masks containing required bits.
```

差 evidence：

```text
This is FWT.
```

## Alias

同义词、常见缩写或中英文混用应走 alias。

示例：

```text
AC automaton -> algorithm/string/acam
digit dp -> algorithm/dp/digit-dp
FWHT -> algorithm/transform/fwt
```

## WebUI 翻译同步

创建新 tag 后，应同步维护：

```text
web/src/i18n.ts
```

然后运行：

```powershell
python scripts/check_tag_translations.py
```

若暂不补翻译，需要确认 WebUI fallback 英文路径显示可接受。

## Tag 颜色

WebUI 中 tag 颜色按最长前缀匹配。

大类示例：

- `algorithm/dp`：蓝色。
- `math`：浅绿。
- `data-structure`：黄色。
- `algorithm/graph`：靛紫。
- `algorithm/string`：青绿。
- `algorithm/transform`：玫紫。
- `paradigm`：橙色。
- `trick`：粉色。
- `implementation`：灰色。

颜色只是显示层，不影响查询语义。
