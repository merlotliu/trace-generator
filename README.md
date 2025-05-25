# Trace Converter 标准格式 Trace 生成工具

## 项目简介

本项目用于将多种原始性能数据（如 CPU、GFX、PSI 等）统一转换为 Perfetto trace 文件，便于性能分析和可视化。核心思想是：**所有 trace 生成流程只处理标准格式数据，各类原始数据通过适配层（adapter）转换为标准格式**，极大提升了可维护性、扩展性和团队协作效率。

---

## 目录结构

```
trace-converter/
├── main.py                    # 主流程入口
├── adapters/                  # 各类原始数据到标准格式的适配层模板
│   ├── cpu_short_adapter.py
│   ├── cpu_long_adapter.py
│   └── gfx_adapter.py
├── configs/                   # 标准格式 schema、配置等
│   └── standard_trace_schema.json
├── src/
│   └── perfetto/
│       └── perfetto_trace_manager.py  # 核心 trace 生成类
└── ...
```

---

## 标准格式说明

所有 trace 生成流程只处理如下标准格式（详见 [configs/standard_trace_schema.json](configs/standard_trace_schema.json)）：

```json
{
  "event_type": "counter",      // "counter" | "slice" | "instant" | "log"
  "process_name": "进程/分组名",
  "track_name": "track名",
  "timestamp": 1710000000000,    // 毫秒时间戳 (ms)
  "value": 10.0,                 // counter值，可选
  "duration_ns": 3000000000,     // slice持续时间，纳秒，可选
  "category": "cpu",            // 可选
  "pid": 1234,                   // 可选
  "message": "日志内容",         // log/instant可选
  "extra": { ... }               // 其它自定义字段，可选
}
```
- **所有字段类型和必选性见 schema 文件**。
- **timestamp 必须为毫秒（ms）数值**，内部自动转为纳秒。

---

## 流程梳理

1. **原始数据准备**
   - 支持多种原始 JSON 格式（如 cpu_short、cpu_long、gfx 等）。
2. **适配层转换**
   - 每种原始格式有独立的适配层（如 adapters/cpu_short_adapter.py），负责将原始数据转换为标准格式列表。
3. **主流程处理**
   - main.py 负责加载原始数据，调用适配层转换为标准格式，然后调用 PerfettoTraceManager 生成 trace 文件。
4. **trace 生成**
   - PerfettoTraceManager.from_standard_format(data_list) 负责对标准格式数据做严格校验，并生成最终的 trace 文件。
5. **可视化分析**
   - 生成的 .perfetto 文件可直接用 Perfetto UI 打开分析。

---

## 适配层开发规范

- 每种原始数据类型都应有独立的适配层脚本，输出标准格式数据。
- 适配层只负责"原始数据 → 标准格式"，主流程和 trace 生成代码无需修改。
- 新增数据类型时，只需添加适配层脚本，无需动主流程。

**示例：adapters/cpu_short_adapter.py**
```python
def cpu_short_to_standard(json_data):
    fields = ["soft_irq", "total", "kernel", "irq", "nice", "user"]
    standard_list = []
    for item in json_data:
        for field in fields:
            standard_list.append({
                "event_type": "counter",
                "process_name": "cpu_short",
                "track_name": field,
                "timestamp": item.get("collect_time"),
                "value": float(item.get(field, 0)),
                "category": "cpu_short"
            })
    return standard_list
```

---

## 主流程用法

```python
from adapters.cpu_short_adapter import cpu_short_to_standard
from src.perfetto.perfetto_trace_manager import PerfettoTraceManager
import json

raw_data = load_json_data("your_cpu_short.json")
standard_data = cpu_short_to_standard(raw_data)
manager = PerfettoTraceManager()
manager.from_standard_format(standard_data)
manager.add_clock_snapshot()
manager.save_to_file("output_trace.perfetto")
```

---

## 校验与健壮性
- PerfettoTraceManager.from_standard_format 会对所有标准格式字段做严格校验，遇到不合法数据会详细警告并跳过。
- 推荐用 [configs/standard_trace_schema.json](configs/standard_trace_schema.json) 做自动化校验，保证数据质量。

---

## 团队协作建议
- 统一标准格式和适配层开发规范，便于多人协作和新成员快速上手。
- 所有配置、schema、适配层模板集中管理，便于维护和自动化。

---

## 联系与贡献
如有问题或建议，欢迎 issue 或 PR！ 