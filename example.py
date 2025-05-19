import json
from perf_data_merge import merge

# 构造丰富的示例数据
example_data = [
    # COUNTER track
    {
        "type": "COUNTER",
        "name": "cpu_usage",
        "value": [10, 20, 30],
        "timestamp": [1718000000, 1718000001, 1718000002]
    },
    {
        "type": "COUNTER",
        "name": "memory_usage",
        "group": "system",
        "value": [100, 120, 140],
        "timestamp": [1718000000, 1718000001, 1718000002]
    },
    # EVENT track
    {
        "type": "EVENT",
        "name": "button_click",
        "event": ["click", "click", "click"],
        "value": [1, 2, 3],
        "timestamp": [1718000000, 1718000001, 1718000002]
    },
    {
        "type": "EVENT",
        "name": "page_load",
        "group": "ui",
        "event": ["start", "end"],
        "value": [0, 1],
        "timestamp": [1718000003, 1718000004]
    },
    # SLICE track
    {
        "type": "SLICE",
        "name": "function_exec",
        "event": ["funcA", "funcB"],
        "value": [0.1, 0.2],
        "timestamp": [1718000005, 1718000007],
        "timestamp_end": [1718000006, 1718000008]
    },
    {
        "type": "SLICE",
        "name": "render_frame",
        "group": "ui",
        "event": ["frame1", "frame2"],
        "value": [16, 17],
        "timestamp": [1718000009, 1718000011],
        "timestamp_end": [1718000010, 1718000012]
    },
    # LOG track
    {
        "type": "LOG",
        "name": "system_log",
        "value": [
            "2024-06-10 10:00:00.000 123 456 I tag1: log message 1",
            "2024-06-10 10:00:01.000 123 456 W tag2: log message 2"
        ],
        "timestamp": []
    },
    {
        "type": "LOG",
        "name": "",
        "value": [
            "2024-06-10 10:00:02.000 789 101 I tag3: log message 3"
        ],
        "timestamp": []
    }
]

# 合并为trace对象
trace = merge(json.dumps(example_data))

# 保存为二进制文件
with open("output_rich_example.perfetto", "wb") as f:
    f.write(trace.SerializeToString())

print("生成的 Perfetto trace 文件为 output_rich_example.perfetto")