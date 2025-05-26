import click
from trace_converter.api import run_trace_convert

DEFAULT_VIN = 'HLX33B121R1647380'
DEFAULT_START_TIME = '2025-02-06 21:40:14'
DEFAULT_END_TIME = '2025-02-06 22:10:14'
DEFAULT_TYPES = ['short', 'gfx']
DEFAULT_TIMEZONE = '+0800'

@click.command()
@click.option('-v', '--vin', default=DEFAULT_VIN, help='车辆VIN码')
@click.option('-s', '--start-time', default=DEFAULT_START_TIME, help='开始时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-e', '--end-time', default=DEFAULT_END_TIME, help='结束时间，格式YYYY-MM-DD HH:MM:SS')
@click.option('-t', '--type', 'types', multiple=True, default=DEFAULT_TYPES, help='数据类型，可多次指定，如 -t short -t gfx')
@click.option('--timezone', default=DEFAULT_TIMEZONE, help='时区，格式如+0800/-0600，影响所有trace事件的时间戳')
def cli(vin, start_time, end_time, types, timezone):
    """命令行入口"""
    run_trace_convert(vin, start_time, end_time, types, timezone=timezone)

if __name__ == "__main__":
    cli() 