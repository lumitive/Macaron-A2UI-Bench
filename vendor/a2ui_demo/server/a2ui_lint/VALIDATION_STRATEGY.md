# A2UI Lint — Validation Strategy

本文档描述 A2UI Lint 的 4 级验证策略：每一级检查什么、为什么要检查、判断逻辑和严重程度。

---

## 设计原则

1. **分层递进（概念）** — Level 1 → 4 在语义上递进；实现上默认会运行所选的所有 level 并汇总诊断，不会因前一级失败而自动中断。
2. **Schema 驱动** — 组件类型、必填字段、枚举值、容器类型等元数据全部从 `schema.json` 动态提取（`ComponentSchema`），不硬编码。
3. **预处理索引** — `ValidationContext` 在验证前构建 O(1) 查找索引（component map、children graph、parent graph、data paths），避免每级重复遍历。
4. **ERROR vs WARNING** — ERROR 表示"Renderer 无法正确渲染或会产生未定义行为"；WARNING 表示"可以渲染但可能不是预期效果"。

---

## Level 1: 结构验证 (Structural)

**目标**: 确保每条 A2UI 消息具有合法的 JSON 结构，字段类型正确，必填项存在。

**严重程度**: 全部 ERROR

| 检查项 | DiagnosticCode | 判断逻辑 |
|--------|---------------|----------|
| 消息必须是 dict | `STRUCT_MESSAGE_NOT_DICT` | `not isinstance(msg, dict)` |
| 必须包含且仅包含一个 action key | `STRUCT_INVALID_ACTION_KEY` / `STRUCT_MULTIPLE_ACTION_KEYS` | 检查 msg keys 与 `{beginRendering, surfaceUpdate, dataModelUpdate, deleteSurface}` 的交集 |
| beginRendering 必须有 `root` 和 `surfaceId`（string） | `STRUCT_MISSING_REQUIRED` / `STRUCT_WRONG_TYPE` | 字段存在性 + `isinstance(v, str)` |
| surfaceUpdate 必须有 `surfaceId`（string）和 `components`（array） | 同上 | 同上 |
| 每个 component 必须有 `id`（string） | `STRUCT_MISSING_REQUIRED` / `STRUCT_WRONG_TYPE` | `"id" not in comp` |
| 每个 component 必须有 `component` wrapper（dict，恰好一个 key） | `STRUCT_MISSING_COMPONENT_WRAPPER` / `STRUCT_MULTIPLE_COMPONENT_TYPES` | `len(wrapper.keys()) == 1` |
| component type 必须是已知类型 | `STRUCT_UNKNOWN_COMPONENT_TYPE` | `comp_type not in schema.known_component_types` |
| schema 定义的 required fields 必须存在 | `STRUCT_MISSING_REQUIRED` | 从 `schema.component_required_fields` 查 |
| schema 定义的 `type` 必须匹配（补充校验） | `STRUCT_WRONG_TYPE` | 使用 JSON Schema validator 补充检测 type mismatch |
| 枚举字段值必须合法 | `STRUCT_INVALID_ENUM` | 从 `schema.component_enums` 查 |
| Icon.name.literalString 必须是已知 icon | `STRUCT_INVALID_ENUM` | `lit not in schema.icon_names` |
| 容器 `children` 必须是 object | `STRUCT_WRONG_TYPE` | `not isinstance(children, dict)` |
| 容器的 children.explicitList 必须是 array | `STRUCT_WRONG_TYPE` | `isinstance(el, list)` |
| `template` 必须是 object | `STRUCT_WRONG_TYPE` | `not isinstance(template, dict)` |
| template 必须有 `componentId` 和 `dataBinding` | `STRUCT_MISSING_REQUIRED` | 字段存在性 |
| `template.componentId` / `template.dataBinding` 必须是 string | `STRUCT_WRONG_TYPE` | `isinstance(v, str)` |
| Tabs.tabItems[] 每项必须有 `title` 和 `child` | `STRUCT_MISSING_REQUIRED` | 字段存在性 |
| Button.action 必须有 `name` | `STRUCT_MISSING_REQUIRED` | 字段存在性 |
| dataModelUpdate 必须有 `surfaceId` 和 `contents`（array） | `STRUCT_MISSING_REQUIRED` / `STRUCT_WRONG_TYPE` | 同上 |
| `dataModelUpdate.path` 必须是 string（若存在） | `STRUCT_WRONG_TYPE` | `isinstance(path, str)` |
| 每个 data entry 必须有 `key` | `STRUCT_MISSING_REQUIRED` | `"key" not in entry` |
| 每个 data entry 的 `key` 必须是 string | `STRUCT_WRONG_TYPE` | `isinstance(entry["key"], str)` |
| 每个 data entry 恰好一个 value* 属性 | `STRUCT_NO_VALUE_TYPE` / `STRUCT_MULTIPLE_VALUE_TYPES` | 计算 `{valueString, valueNumber, valueBoolean, valueMap}` 交集数量 |
| deleteSurface 必须有 `surfaceId` | `STRUCT_MISSING_REQUIRED` | 字段存在性 |

---

## Level 2: 引用完整性 (Reference Integrity)

**目标**: 验证组件之间的 ID 引用能解析、没有悬空指针、没有重复和循环。

**严重程度**: 引用断裂 = ERROR，一致性问题 = WARNING

| 检查项 | DiagnosticCode | 严重程度 | 判断逻辑 |
|--------|---------------|---------|----------|
| beginRendering.root 指向存在的 component | `REF_MISSING_ROOT` | ERROR | `root not in ctx.components` |
| 单子组件字段（Card.child, Button.child, Modal.*Child）指向存在的 component | `REF_MISSING_COMPONENT` | ERROR | `child not in ctx.components` |
| explicitList 中每个 ID 指向存在的 component | `REF_MISSING_COMPONENT` | ERROR | 遍历 list，逐个检查 |
| template.componentId 指向存在的 component | `REF_MISSING_COMPONENT` | ERROR | `tid not in ctx.components` |
| Tabs.tabItems[].child 指向存在的 component | `REF_MISSING_COMPONENT` | ERROR | 同上 |
| 不存在重复的 component ID | `REF_DUPLICATE_ID` | ERROR | `ctx.duplicate_ids` 非空 |
| 不存在孤儿组件（从 root BFS 不可达） | `REF_ORPHAN_COMPONENT` | WARNING | BFS 遍历后检查差集（排除 template 组件） |
| 不存在循环引用 | `REF_CYCLE` | ERROR | DFS 三色标记法检测回边 |

> 说明：A2UI 协议支持多个 surface 并行更新；不同 surface 的消息序列彼此独立，因此不再对“多个 surfaceId”本身告警。

### 孤儿检测算法

```
reachable = BFS(root_ids, children_graph)
orphans = all_components - reachable - template_component_ids
```

Template 组件不算孤儿，因为它们通过 `template.componentId` 间接引用，在数据驱动下动态实例化。

### 循环检测算法

标准 DFS 三色法（WHITE → GRAY → BLACK）。发现 GRAY→GRAY 的回边即报告循环，并输出完整的 cycle path。

---

## Level 3: 数据模型一致性 (Data Model Consistency)

**目标**: 验证组件与 dataModelUpdate 之间的数据绑定是否正确。

**严重程度**: 以 WARNING 为主；`DATA_BINDING_INVALID` 为 ERROR

| 检查项 | DiagnosticCode | 判断逻辑 |
|--------|---------------|----------|
| template.dataBinding 必须是绝对路径（`/` 开头） | `DATA_BINDING_INVALID` | `not binding.startswith("/")` |
| template.dataBinding 路径在 dataModelUpdate 中存在 | `DATA_PATH_NOT_FOUND` | `binding not in ctx.data_paths` |
| 非 template 组件的绝对 path 引用在 data model 中存在 | `DATA_PATH_NOT_FOUND` | 收集所有 `{"path": "/..."}` 并与 `ctx.data_paths` 比对 |
| 组件期望的数据类型与实际数据类型匹配 | `DATA_TYPE_MISMATCH` | Text→valueString, Slider→valueNumber, CheckBox→valueBoolean |

### Template 路径规则

- **template.dataBinding**: 必须是绝对路径（如 `/items`），指向 data model 中一个 valueMap 列表
- **template 子树内的组件 path**: 属于上下文作用域路径，静态 lint 不做“绝对/相对”风格告警，仅做可静态判断的绑定检查

### 类型兼容性推断

类型映射从 schema 自动推导：如果组件的 `text` / `value` 字段 schema 中只有一种 `literal*` key，则推断对应的 `value*` 类型：

- `literalString` → 期望 `valueString`
- `literalNumber` → 期望 `valueNumber`
- `literalBoolean` → 期望 `valueBoolean`

---

## Level 4: 语义 / 最佳实践 (Semantic Lint)

**目标**: 检查不会导致崩溃但可能导致意外行为的模式。

**严重程度**: 全部 WARNING

| 检查项 | DiagnosticCode | 判断逻辑 |
|--------|---------------|----------|
| 三种消息类型齐全 | `LINT_MISSING_MESSAGE_TYPE` | `beginRendering`/`surfaceUpdate` 缺失即告警；`dataModelUpdate` 仅在存在数据绑定需求时告警 |
| 消息顺序正确（按 surface 独立） | `LINT_MESSAGE_ORDER` | 对每个 surface 检查 `beginRendering` 是否出现在该 surface 的首个 `surfaceUpdate` 之后 |
| weight 只用在 Row/Column 的直接子组件上 | `LINT_WEIGHT_OUTSIDE_FLEX` | 收集所有 Row/Column 的 children，检查有 weight 的组件是否在其中 |
| 组件嵌套深度不超过 10 | `LINT_DEEP_NESTING` | 从 root 递归计算 depth |
| 容器组件不应有空的 children | `LINT_EMPTY_CHILDREN` | explicitList 为空 array，或既无 explicitList 也无 template |

### 消息顺序建议

A2UI 协议的推荐顺序：

```
surfaceUpdate → (dataModelUpdate 可前可后) → beginRendering
```

关键点：

- 顺序约束按 **surface 维度** 独立判断；
- `surfaceUpdate` 与 `dataModelUpdate` 没有强制先后；
- `beginRendering` 应在该 surface 的初始 `surfaceUpdate` 之后到达，作为首次渲染信号。

---

## 诊断输出

每条诊断包含：

| 字段 | 说明 |
|------|------|
| `severity` | `error` / `warning` / `info` |
| `code` | 枚举码，如 `STRUCT_MISSING_REQUIRED` |
| `message` | 人类可读的描述 |
| `path` | JSON Pointer 定位，如 `/messages/0/surfaceUpdate/components/2/component/Text` |
| `suggestion` | 可操作的修复建议 |

### 输出格式

- **`format_for_llm()`** — 面向 LLM 的精简格式，用于 retry loop 中反馈给模型修正
- **`format_for_cli()`** — 面向开发者的终端彩色输出
- **`to_dict()`** — 结构化 JSON，用于 Web UI 和 API

---

## API 入口

```python
# 验证已解析的 A2UI messages
result = validate(messages, levels={1,2,3,4})

# 从 LLM 原始输出中提取 + 验证
text, messages, result = validate_raw(raw_response)

# 检查结果
result.is_valid      # True = 无 ERROR
result.errors        # ERROR 列表
result.warnings      # WARNING 列表
```

可通过 `levels` 参数选择性运行某几级，例如 `levels={1,2}` 只运行结构 + 引用检查。
