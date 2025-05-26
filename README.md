# Trace Converter 标准格式 Trace 生成工具

## 项目简介

本项目用于将多种原始性能数据（如 CPU、GFX、PSI 等）统一转换为 Perfetto trace 文件，便于性能分析和可视化。核心思想是：**所有 trace 生成流程只处理标准格式数据，各类原始数据通过适配层（adapter）转换为标准格式**，极大提升了可维护性、扩展性和团队协作效率。

---

## 目录结构

```
trace-converter/
├── trace_converter/                # 主包目录，所有核心代码和API
│   ├── __init__.py
│   ├── api.py                      # 主要API和实现逻辑（run_trace_convert等）
│   ├── data_fetcher.py             # 数据获取
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── cpu_short_adapter.py
│   │   └── gfx_adapter.py          # GFX数据适配器
│   ├── perfetto/
│   │   ├── __init__.py
│   │   └── perfetto_trace_manager.py
├── cli.py                          # 命令行入口，只负责参数解析和调用API
├── configs/
│   └── standard_trace_schema.json
├── requirements.txt
├── README.md
└── ...  # 其它文件
```

---

## 一键数据获取与 Trace 生成

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 命令行一键生成 Trace

支持通过 VIN、时间区间、数据类型一键获取数据并生成 trace 文件。

```bash
python cli.py -v HLX33B121R1647380 -s "2025-02-06 21:40:14" -e "2025-02-06 22:10:14" -t short -t gfx
```

- `-v/--vin`：车辆VIN码
- `-s/--start-time`：开始时间（格式 `YYYY-MM-DD HH:MM:SS`）
- `-e/--end-time`：结束时间（格式 `YYYY-MM-DD HH:MM:SS`）
- `-t/--type`：数据类型，可多次指定，如 `-t short -t gfx`

**输出文件名格式**：
```
{VIN}_{开始时间}_{结束时间}_trace.perfetto
# 例：HLX33B121R1647380_2025-02-06-21-40-14_2025-02-06-22-10-14_trace.perfetto
```

### 3. 作为 API 调用

可在 Python 代码中直接调用主流程：

```python
from trace_converter.api import run_trace_convert
run_trace_convert(
    vin="HLX33B121R1647380",
    start_time="2025-02-06 21:40:14",
    end_time="2025-02-06 22:10:14",
    types=["short", "gfx"]
)
```

---

## GFX 适配器说明

### 输入数据要求
- 输入为包含多个字典的列表，每个字典需包含如下字段：
  - `jank_event`、`total_duration`、`create_time`、`window_name` 及其它性能细节字段

### 处理逻辑
1. 按 `jank_event` 分组，遍历每组。
2. 每条数据生成一个 `slice` 事件：
   - `process_name`：统一为 `gfx_200ms`
   - `track_name`：为该条的 `jank_event`
   - `event_name`/`name`：为该条的 `window_name`
   - `timestamp`：`create_time`（转为毫秒时间戳）减去 `total_duration`（单位毫秒）
   - `duration_ns`：`total_duration` * 1_000_000
   - `category`：`gfx`
   - `arguments`：包含以下字段（会自动映射到 Perfetto UI 的 Arguments 面板）：
     - `mark_animation_time`, `ui_draw_time`, `sync_time`, `handle_input_time`,
       `draw_command_time`, `perform_traversals_time`, `current_frame_index`,
       `gpu_slow`, `ui_thread_dely`, `swap_buffers_and_gpu_draw_time`

### 示例标准格式输出
```json
{
  "event_type": "slice",
  "process_name": "gfx_200ms",
  "track_name": "FirstFrame",
  "timestamp": 1738850126257,
  "duration_ns": 269000000,
  "event_name": "com.liauto.onemap.mapeidcard.MapEidCardActivity",
  "category": "gfx",
  "arguments": {
    "mark_animation_time": 0,
    "ui_draw_time": 3,
    ...
  },
  "name": "com.liauto.onemap.mapeidcard.MapEidCardActivity"
}
```

---

## 工作流程（原理说明）

1. **数据获取**  
   通过 HTTP POST 请求自动拉取原始性能数据（如 CPU/GFX 等），无需手动下载。
2. **适配层转换**  
   每种原始格式有独立的适配层（如 adapters/cpu_short_adapter.py、adapters/gfx_adapter.py），负责将原始数据转换为标准格式列表。
3. **主流程处理**  
   cli.py/api.py 负责自动获取数据、调用适配层转换为标准格式，然后调用 PerfettoTraceManager 生成 trace 文件。
4. **trace 生成**  
   PerfettoTraceManager.from_standard_format(data_list) 负责对标准格式数据做严格校验，并生成最终的 trace 文件。
5. **可视化分析**  
   生成的 .perfetto 文件可直接用 Perfetto UI 打开分析。

---

## 标准格式说明（与 schema 保持一致）

- event_type: 必须为 "counter"、"slice"、"instant"、"log" 之一
- process_name, track_name: 必须为字符串
- timestamp: 必须为毫秒（ms）数值，内部自动转为纳秒
- value, duration_ns, message, arguments 等字段类型见 [configs/standard_trace_schema.json](configs/standard_trace_schema.json)
- arguments 字段会自动映射到 Perfetto UI 的 Arguments 面板

---

## 适配层开发规范

- 每种原始数据类型都应有独立的适配层脚本，输出标准格式数据。
- 适配层只负责"原始数据 → 标准格式"，主流程和 trace 生成代码无需修改。
- 支持 offset、时区等灵活配置，推荐用字符串表达式（如 '+08h'、'-30s'）。

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