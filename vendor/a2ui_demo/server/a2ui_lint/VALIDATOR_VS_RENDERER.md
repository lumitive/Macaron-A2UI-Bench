# A2UI Lint Validator vs Flutter Renderer 对比

本文档对比 **A2UI Lint Validator**（Python, server 端静态检查）与 **Flutter Renderer**（Dart, client 端运行时渲染）在处理 A2UI JSON 时的行为差异。

---

## 定位差异

| | Lint Validator | Flutter Renderer |
|---|---|---|
| **运行时机** | LLM 输出后、发送给客户端前（server 端） | 客户端接收到消息后（client 端） |
| **目的** | 拦截错误，反馈给 LLM 重试修正 | 尽最大努力渲染，graceful degradation |
| **策略** | 严格检查，宁可误报 | 宽容接受，容错兜底 |
| **输出** | 结构化 Diagnostic 列表 | Widget 树（出错时 Placeholder / SizedBox.shrink） |

---

## 逐项对比

### 1. JSON 解析

| 场景 | Validator | Renderer |
|------|-----------|----------|
| JSON 语法错误 | ERROR `STRUCT_INVALID_ACTION_KEY` + 拒绝 | `jsonDecode` 抛异常，try-catch 捕获，log error，不渲染 |
| payload 不是 array/dict | ERROR `STRUCT_WRONG_TYPE` | 未处理，可能静默忽略 |

**差异**: Validator 给出精确的错误码和修复建议；Renderer 只记日志。

### 2. Action Key 识别

| 场景 | Validator | Renderer |
|------|-----------|----------|
| 无合法 action key | ERROR `STRUCT_INVALID_ACTION_KEY` | 静默跳过该消息 |
| 多个 action key | ERROR `STRUCT_MULTIPLE_ACTION_KEYS` | 按代码顺序处理第一个匹配的，忽略其余 |

**差异**: Validator 不允许多 key；Renderer 不在意，按 if-else 链匹配第一个。

### 3. beginRendering

| 场景 | Validator | Renderer |
|------|-----------|----------|
| 缺少 `root` | ERROR | 创建 surface 但无法渲染根组件 |
| 缺少 `surfaceId` | ERROR | 使用 null/空 ID，行为未定义 |
| root 指向不存在的 component | ERROR `REF_MISSING_ROOT`（Level 2） | 渲染 Placeholder + log SEVERE |

### 4. surfaceUpdate — 组件结构

| 场景 | Validator | Renderer |
|------|-----------|----------|
| component 缺少 `id` | ERROR `STRUCT_MISSING_REQUIRED` | fromJson 可能抛异常或生成空 ID |
| component 缺少 `component` wrapper | ERROR `STRUCT_MISSING_COMPONENT_WRAPPER` | 无法识别组件类型，跳过或异常 |
| wrapper 有多个 type key | ERROR `STRUCT_MULTIPLE_COMPONENT_TYPES` | 取第一个匹配的 key |
| 未知 component type | ERROR `STRUCT_UNKNOWN_COMPONENT_TYPE` | `Container()` 兜底 + log SEVERE |
| 缺少 required field（如 Text.text） | ERROR `STRUCT_MISSING_REQUIRED` | 使用 null 默认值，可能显示空白 |
| enum 值非法（如 alignment="center"） | ERROR `STRUCT_INVALID_ENUM` | 无检查，使用默认值或忽略 |

**关键差异**: Renderer 对未知组件用 `Container()` 兜底，对缺失字段用 null。虽然不崩溃，但用户看到的是意外的空白或默认行为。Validator 在此前拦截，让 LLM 有机会修正。

### 5. 组件引用 (Child References)

| 场景 | Validator | Renderer |
|------|-----------|----------|
| Card.child 引用不存在的 ID | ERROR `REF_MISSING_COMPONENT` | `Placeholder(child: Text('Widget with id: xxx not found.'))` |
| explicitList 中有不存在的 ID | ERROR `REF_MISSING_COMPONENT` | 同上，该位置显示 Placeholder |
| template.componentId 不存在 | ERROR `REF_MISSING_COMPONENT` | 同上 |
| Tabs.tabItems[].child 不存在 | ERROR `REF_MISSING_COMPONENT` | 同上 |

**差异**: Renderer 用 Placeholder 优雅降级，用户能看到哪里出了问题但体验不佳。Validator 在 server 端拦截，避免发送有问题的 UI。

### 6. 重复 ID

| 场景 | Validator | Renderer |
|------|-----------|----------|
| 两个 component 有相同 id | ERROR `REF_DUPLICATE_ID` | 后定义的覆盖前者（Map put），先前的引用可能指向错误的组件 |

**差异**: 这是 Validator 最关键的价值之一。Renderer 的 "last-write-wins" 行为会导致难以调试的 UI 错误。

### 7. 循环引用

| 场景 | Validator | Renderer |
|------|-----------|----------|
| A.child → B, B.child → A | ERROR `REF_CYCLE` | 无限递归 → StackOverflow 崩溃 |

**差异**: **Renderer 会崩溃**。这是 Validator 必须拦截的致命错误。

### 8. 孤儿组件

| 场景 | Validator | Renderer |
|------|-----------|----------|
| 定义了组件但从 root 不可达 | WARNING `REF_ORPHAN_COMPONENT` | 组件存在于 component map 但永远不被渲染 |

**差异**: 对 Renderer 无害（不渲染即可），但浪费 LLM token 且说明组件树结构可能有误。

### 9. 数据绑定 (Data Binding)

| 场景 | Validator | Renderer |
|------|-----------|----------|
| template.dataBinding 不以 `/` 开头 | ERROR `DATA_BINDING_INVALID` | 可能解析为错误的路径 |
| dataBinding 路径在 data model 中不存在 | WARNING `DATA_PATH_NOT_FOUND` | `ValueNotifier` 得到 null → `SizedBox.shrink()` |
| template 子树内使用绝对路径 | WARNING `DATA_ABSOLUTE_PATH_IN_TEMPLATE` | 路径不会自动加前缀，可能指向错误数据 |
| 组件 path 引用不存在的数据路径 | WARNING `DATA_PATH_NOT_FOUND` | 同上，值为 null |
| 类型不匹配（Text 绑到 valueNumber） | WARNING `DATA_TYPE_MISMATCH` | 运行时类型转换或显示 `null.toString()` |

**差异**: Renderer 对数据缺失全部静默处理（null → 空白）。Validator 主动检查以帮助 LLM 修正数据结构。

### 10. 语义 / 最佳实践

| 场景 | Validator | Renderer |
|------|-----------|----------|
| 缺少 beginRendering | WARNING `LINT_MISSING_MESSAGE_TYPE` | 无 surface 创建，后续消息无处渲染 |
| `beginRendering` 早于该 surface 的初始 `surfaceUpdate` | WARNING `LINT_MESSAGE_ORDER` | 会先触发渲染信号，后续再补组件，可能出现空白/迟到更新 |
| weight 用在非 Row/Column 子组件 | WARNING `LINT_WEIGHT_OUTSIDE_FLEX` | weight 被忽略，无视觉效果 |
| 嵌套深度 > 10 | WARNING `LINT_DEEP_NESTING` | 可以渲染，但性能可能下降 |
| 容器 children 为空 | WARNING `LINT_EMPTY_CHILDREN` | 渲染一个空容器 |

---

## 总结：互补关系

```
  LLM 输出
     │
     ▼
┌──────────────┐    ✗ errors    ┌──────────────┐
│  A2UI Lint    │──────────────▶│  LLM Retry   │
│  Validator    │               │  (with hints) │
│  (server)     │◀──────────────┘
└──────┬���──────┘
       │ ✓ valid
       ▼
┌──────────────┐
│  Flutter      │    graceful   ┌──────────────┐
│  Renderer     │──────────────▶│  Placeholder  │
│  (client)     │  degradation  │  SizedBox     │
└──────────────┘               └──────────────┘
```

- **Validator 是第一道防线**: 在 server 端拦截结构错误和引用断裂，触发 LLM 重试。
- **Renderer 是最后的兜底**: 即使有漏网之鱼，也能 graceful degradation 而不崩溃（循环引用除外）。
- **Validator 的 WARNING 是"可渲染但不理想"**: Renderer 能处理但会产生空白或意外行为。

### Validator 独有的价值

| 能力 | 为什么 Renderer 做不到 |
|------|----------------------|
| 循环检测 | Renderer 会无限递归崩溃 |
| 重复 ID 检测 | Renderer 静默覆盖，难以 debug |
| 数据类型匹配检查 | Renderer 不知道"应该"是什么类型 |
| 孤儿组件检测 | Renderer 不知道哪些组件"应该"被使用 |
| LLM 反馈 | Renderer 无法反馈给 LLM 修正 |
| 全局一致性 | Renderer 逐组件处理，无全局视图 |

### Renderer 独有的能力

| 能力 | 为什么 Validator 做不到 |
|------|----------------------|
| 运行时状态验证 | Validator 只看静态 JSON |
| 用户交互后的状态一致性 | 需要实际运行 |
| 实际渲染性能 | 需要 Flutter 引擎 |
| 平台特定问题（字体、布局溢出） | 需要设备上下文 |
