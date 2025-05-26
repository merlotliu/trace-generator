# -*- coding: utf-8 -*-
from collections import defaultdict
from trace_converter.utils import parse_datetime_to_ms

def gfx_to_standard(json_data):
    """
    将GFX原始数据转为标准trace格式：
    - 按jank_event分组
    - 每条数据生成一个slice事件，track_name为jank_event
    - process_name统一为'gfx_200ms'
    - event_name为window_name
    - timestamp为create_time毫秒时间戳减去total_duration
    - duration_ns为total_duration*1_000_000
    - arguments字段包含指定性能细节字段
    """
    # 需要放入arguments的字段
    argument_fields = [
        'mark_animation_time', 'ui_draw_time', 'sync_time', 'handle_input_time',
        'draw_command_time', 'perform_traversals_time', 'current_frame_index',
        'gpu_slow', 'ui_thread_dely', 'swap_buffers_and_gpu_draw_time'
    ]
    result = []
    # 按jank_event分组
    groups = defaultdict(list)
    for item in json_data:
        jank_event = item.get('jank_event', 'Unknown')
        groups[jank_event].append(item)
    for jank_event, items in groups.items():
        for item in items:
            window_name = item.get('window_name', '')
            # 统一用工具函数转毫秒时间戳
            create_time_ms = parse_datetime_to_ms(item.get('create_time', ''))
            total_duration = int(item.get('total_duration', 0))
            # slice开始时间 = create_time_ms - total_duration
            timestamp = create_time_ms - total_duration
            duration_ns = total_duration * 1_000_000
            # arguments字段收集
            arguments = {field: item.get(field) for field in argument_fields}
            event = {
                'event_type': 'slice',
                'process_name': 'gfx_200ms',
                'track_name': jank_event,
                'timestamp': timestamp,
                'duration_ns': duration_ns,
                'event_name': window_name,
                'category': 'gfx',
                'arguments': arguments
            }
            result.append(event)
    return result 