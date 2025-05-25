# Trace Converter 标准格式 Trace 生成工具

## 项目简介

本项目用于将多种原始性能数据（如 CPU、GFX、PSI 等）统一转换为 Perfetto trace 文件，便于性能分析和可视化。核心思想是：**所有 trace 生成流程只处理标准格式数据，各类原始数据通过适配层（adapter）转换为标准格式**，极大提升了可维护性、扩展性和团队协作效率。

---

## 目录结构

```
trace-converter/
├── main.py                        # 主流程入口，支持一键数据获取/转换/trace生成
├── adapters/                      # 各类原始数据到标准格式的适配层
│   ├── cpu_short_adapter.py       # CPU短周期数据适配层
│   ├── cpu_long_adapter.py        # CPU长周期数据适配层（可扩展）
│   └── gfx_adapter.py             # GFX数据适配层（可扩展）
├── configs/
│   └── standard_trace_schema.json # 标准格式schema
├── src/
│   └── perfetto/
│       └── perfetto_trace_manager.py # 核心trace生成类，只处理标准格式
├── data_fetcher.py                # 数据获取模块，自动拉取原始数据
├── requirements.txt               # 依赖说明
├── README.md                      # 项目说明文档
└── ...                            # 其它文件
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
python main.py -v HLX33B121R1647380 -s "2025-02-06 21:40:14" -e "2025-02-06 22:10:14" -t short
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
from main import run_trace_convert
run_trace_convert(
    vin="HLX33B121R1647380",
    start_time="2025-02-06 21:40:14",
    end_time="2025-02-06 22:10:14",
    types=["short"]
)
```

---

## 工作流程（原理说明）

1. **数据获取**  
   通过 HTTP POST 请求自动拉取原始性能数据（如 CPU 短周期等），无需手动下载。
2. **适配层转换**  
   每种原始格式有独立的适配层（如 adapters/cpu_short_adapter.py），负责将原始数据转换为标准格式列表。
3. **主流程处理**  
   main.py 负责自动获取数据、调用适配层转换为标准格式，然后调用 PerfettoTraceManager 生成 trace 文件。
4. **trace 生成**  
   PerfettoTraceManager.from_standard_format(data_list) 负责对标准格式数据做严格校验，并生成最终的 trace 文件。
5. **可视化分析**  
   生成的 .perfetto 文件可直接用 Perfetto UI 打开分析。

---

## 标准格式说明（与 schema 保持一致）

- event_type: 必须为 "counter"、"slice"、"instant"、"log" 之一
- process_name, track_name: 必须为字符串
- timestamp: 必须为毫秒（ms）数值，内部自动转为纳秒
- value, duration_ns, message, extra 等字段类型见 [configs/standard_trace_schema.json](configs/standard_trace_schema.json)

---

## 适配层开发规范

- 每种原始数据类型都应有独立的适配层脚本，输出标准格式数据。
- 适配层只负责"原始数据 → 标准格式"，主流程和 trace 生成代码无需修改。
- 支持 offset、时区等灵活配置，推荐用字符串表达式（如 '+08h'、'-30s'）。

**示例：adapters/cpu_short_adapter.py**
```python
import datetime
import re

def safe_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default

def parse_offset_str(offset_str):
    if not offset_str:
        return 0
    sign = 1
    s = offset_str.strip()
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
    total_sec = 0
    for part, mult in re.findall(r'(\d+)([hms])', s):
        if mult == 'h':
            total_sec += int(part) * 3600
        elif mult == 'm':
            total_sec += int(part) * 60
        elif mult == 's':
            total_sec += int(part)
    return sign * total_sec

def parse_collect_time_to_ms(val, offset_sec_str=None, tz_offset_sec_str=None):
    ts = 0
    if isinstance(val, (int, float)):
        ts = int(val)
    elif isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                ts = int(dt.timestamp() * 1000)
                break
            except Exception:
                continue
    tz_offset = parse_offset_str(tz_offset_sec_str) if tz_offset_sec_str else 0
    offset = parse_offset_str(offset_sec_str) if offset_sec_str else 0
    ts += tz_offset * 1000
    ts -= offset * 1000
    return ts

def build_counter_event(item, field, offset_sec_str=None, tz_offset_sec_str=None):
    return {
        "event_type": "counter",
        "process_name": "cpu_short_30s",
        "track_name": field,
        "timestamp": parse_collect_time_to_ms(item.get("collect_time"), offset_sec_str=offset_sec_str, tz_offset_sec_str=tz_offset_sec_str),
        "value": safe_float(item.get(field, 0)),
        "category": "cpu_short"
    }

def cpu_short_to_standard(json_data):
    fields = ["soft_irq", "total", "kernel", "irq", "nice", "user"]
    standard_list = []
    for item in json_data:
        for field in fields:
            standard_list.append(build_counter_event(item, field, offset_sec_str='30s', tz_offset_sec_str='+08h'))
    return standard_list
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