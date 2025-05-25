import click
from trace_converter.api import run_trace_convert

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