import click
from .api import run_trace_convert

DEFAULT_VIN = 'HLX33B127R1035023'
DEFAULT_START_TIME = '2025-05-29 07:00:00'
DEFAULT_END_TIME = '2025-05-29 10:00:00'
DEFAULT_TYPES = ['gfx', 'short', 'long']
DEFAULT_TIMEZONE = '+0800'
DEFAULT_OUTPUT = '~/Downloads'

@click.command(name="tracegen", help="标准格式 Trace 生成工具，将原始数据一键转为 Perfetto trace 文件")
@click.option('-v', '--vin', default=DEFAULT_VIN, help='车辆VIN码')
@click.option('-s', '--start-time', default=DEFAULT_START_TIME, help='开始时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-e', '--end-time', default=DEFAULT_END_TIME, help='结束时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-t', '--type', 'types', multiple=True, default=DEFAULT_TYPES, help='数据类型，可多次指定，如 -t short -t gfx')
@click.option('--timezone', default=DEFAULT_TIMEZONE, help='时区，格式如+0800/-0600，影响所有trace事件的时间戳')
@click.option('-o', '--output', default=DEFAULT_OUTPUT, show_default=True, help='输出文件夹，默认~/Downloads')
def cli(vin, start_time, end_time, types, timezone, output):
    """命令行入口"""
    run_trace_convert(vin, start_time, end_time, types, timezone=timezone, output_dir=output)

if __name__ == "__main__":
    cli() 