import json
import os
import datetime
from src.perfetto.perfetto_trace_manager import PerfettoTraceManager

OUTPUT_TRACE = "HLX33B121R1647380_trace.perfetto"

def load_json_data(path):
    with open(path, "r") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data

def main():
    
    manager = PerfettoTraceManager()
    # track_dict 配置，每个 track 单独定义
    cpu_short_data_list = load_json_data("/Users/liumoulu/logdoctor/data/HLX33B121R1647380/cpu/short/HLX33B121R1647380_short_2025-02-06-21-40-14_2025-02-06-22-10-14.json")
    cpu_short_track_config = {
        "cpu_usage_30s": [
            {"field": "soft_irq", "type": "counter", "tname": "soft_irq", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
            {"field": "total", "type": "counter", "tname": "total", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
            {"field": "kernel", "type": "counter", "tname": "kernel", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
            {"field": "irq", "type": "counter", "tname": "irq", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
            {"field": "nice", "type": "counter", "tname": "nice", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
            {"field": "user", "type": "counter", "tname": "user", "ts": "collect_time", "offset": "-30s", "timezone": "+0800"},
        ],
        "psi_avg10": [
            {"field": "psi_avg10.cpuSome", "type": "counter", "tname": "cpuSome", "ts": "collect_time", "timezone": "+0800"},
            {"field": "psi_avg10.ioFull", "type": "counter", "tname": "ioFull", "ts": "collect_time", "timezone": "+0800"},
            {"field": "psi_avg10.ioSome", "type": "counter", "tname": "ioSome", "ts": "collect_time", "timezone": "+0800"},
            {"field": "psi_avg10.memoryFull", "type": "counter", "tname": "memoryFull", "ts": "collect_time", "timezone": "+0800"},
            {"field": "psi_avg10.memorySome", "type": "counter", "tname": "memorySome", "ts": "collect_time", "timezone": "+0800"},
        ]
    }
    manager.json2perfetto(cpu_short_data_list, cpu_short_track_config)

    gfx_data_list = load_json_data("/Users/liumoulu/logdoctor/data/HLX33B121R1647380/gfx/HLX33B121R1647380_gfx_2025-02-06-21-40-14_2025-02-06-22-10-14.json")
    gfx_track_config = {
        "gfx": [
            {"field": "total_duration", "type": "slice", "tname": "total_duration", "ts": "current_time_millis", "offset": "-$(total_duration)s", "timezone": "+0800", "duration_ms": "$(total_duration)"},
        ]
    }
    manager.json2perfetto(gfx_data_list, gfx_track_config)

    manager.add_clock_snapshot()
    manager.save_to_file(OUTPUT_TRACE)
    print(f"已生成 {OUTPUT_TRACE}，可用 Perfetto UI 打开查看。")

if __name__ == "__main__":
    main()
