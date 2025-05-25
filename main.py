import json
import os
import datetime
from src.perfetto.perfetto_trace_manager import PerfettoTraceManager
from adapters.cpu_short_adapter import cpu_short_to_standard

INPUT_JSON = "/Users/liumoulu/logdoctor/data/HLX33B121R1647380/cpu/short/HLX33B121R1647380_short_2025-02-06-21-40-14_2025-02-06-22-10-14.json"
OUTPUT_TRACE = "cpu_usage_trace.perfetto"

def load_json_data(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    # 1. 加载原始数据
    raw_data = load_json_data(INPUT_JSON)
    # 2. 适配层转换为标准格式
    standard_data = cpu_short_to_standard(raw_data)
    # 3. 生成 trace
    manager = PerfettoTraceManager()
    manager.from_standard_format(standard_data)
    manager.add_clock_snapshot()
    manager.save_to_file(OUTPUT_TRACE)
    print(f"已生成 {OUTPUT_TRACE}，可用 Perfetto UI 打开查看。")

if __name__ == "__main__":
    main()