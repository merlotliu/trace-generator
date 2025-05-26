# -*- coding: utf-8 -*-
from .adapters.cpu_short_adapter import cpu_short_to_standard
from .adapters.gfx_adapter import gfx_to_standard
from .data_fetcher import fetch_data
from .perfetto.perfetto_trace_manager import PerfettoTraceManager

# 适配器映射表，后续可扩展其它类型
ADAPTER_MAP = {
    'short': cpu_short_to_standard,
    'gfx': gfx_to_standard,
}

def run_trace_convert(vin, start_time, end_time, types, timezone):
    """
    主流程API，可直接调用。
    vin: 车辆VIN
    start_time: 开始时间 'YYYY-MM-DD HH:MM:SS'
    end_time: 结束时间 'YYYY-MM-DD HH:MM:SS'
    types: list[str]，如['short', 'gfx']
    timezone: 时区字符串，如'+0800'，影响所有trace事件的时间戳
    """
    manager = PerfettoTraceManager(timezone=timezone)
    for data_type in types:
        if data_type not in ADAPTER_MAP:
            print(f"暂不支持的数据类型: {data_type}")
            continue
        print(f"正在获取 {data_type} 数据...")
        raw_data = fetch_data(vin, start_time, end_time, data_type)
        print(f"原始数据条数: {len(raw_data)}")
        standard_data = ADAPTER_MAP[data_type](raw_data)
        print(f"标准格式数据条数: {len(standard_data)}")
        manager.from_standard_format(standard_data)
    manager.add_clock_snapshot()
    # 输出文件名: VIN_开始时间_结束时间_trace.perfetto
    start_str = start_time.replace(':', '-').replace(' ', '-')
    end_str = end_time.replace(':', '-').replace(' ', '-')
    out_name = f"{vin}_{start_str}_{end_str}_trace.perfetto"
    manager.save_to_file(out_name)
    print(f"已生成 {out_name}，可用 Perfetto UI 打开查看。\n")
    return out_name 