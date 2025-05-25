import os
from datetime import datetime
import click
from src.perfetto.perfetto_trace_manager import PerfettoTraceManager
from adapters.cpu_short_adapter import cpu_short_to_standard
from data_fetcher import fetch_data

# 适配器映射表，后续可扩展其它类型
ADAPTER_MAP = {
    'short': cpu_short_to_standard,
    # 'gfx': gfx_to_standard, # 预留
}

def run_trace_convert(vin, start_time, end_time, types):
    """
    主流程API，可直接调用。
    vin: 车辆VIN
    start_time: 开始时间 'YYYY-MM-DD HH:MM:SS'
    end_time: 结束时间 'YYYY-MM-DD HH:MM:SS'
    types: list[str]，如['short', 'gfx']
    """
    results = []
    for data_type in types:
        if data_type not in ADAPTER_MAP:
            print(f"暂不支持的数据类型: {data_type}")
            continue
        print(f"正在获取 {data_type} 数据...")
        raw_data = fetch_data(vin, start_time, end_time, data_type)
        print(f"原始数据条数: {len(raw_data)}")
        standard_data = ADAPTER_MAP[data_type](raw_data)
        print(f"标准格式数据条数: {len(standard_data)}")
        manager = PerfettoTraceManager()
        manager.from_standard_format(standard_data)
        manager.add_clock_snapshot()
        # 输出文件名: VIN_开始时间_结束时间_trace.perfetto
        start_str = start_time.replace(':', '-').replace(' ', '-')
        end_str = end_time.replace(':', '-').replace(' ', '-')
        out_name = f"{vin}_{start_str}_{end_str}_trace.perfetto"
        manager.save_to_file(out_name)
        print(f"已生成 {out_name}，可用 Perfetto UI 打开查看。\n")
        results.append(out_name)
    return results

@click.command()
@click.option('-v', '--vin', default='HLX33B121R1647380', help='车辆VIN码')
@click.option('-s', '--start-time', default='2025-02-06 21:40:14', help='开始时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-e', '--end-time', default='2025-02-06 22:10:14', help='结束时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-t', '--type', 'types', multiple=True, default=['short'], help='数据类型，可多次指定，如 -t short -t gfx')
def cli(vin, start_time, end_time, types):
    """命令行入口"""
    run_trace_convert(vin, start_time, end_time, types)

if __name__ == "__main__":
    cli()