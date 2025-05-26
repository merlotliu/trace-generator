import datetime
from trace_converter.utils import parse_offset_str, parse_datetime_to_ms
import json

def safe_float(val, default=0.0):
    """安全地将值转为float，失败时返回default。"""
    try:
        return float(val)
    except Exception:
        return default

def parse_collect_time_to_ms(val, offset_sec_str=None):
    """
    将字符串或数值时间转为毫秒时间戳，并应用业务偏移。
    :param val: 时间字符串或数值
    :param offset_sec_str: 业务偏移（如-30s）
    :return: 毫秒时间戳
    """
    ts = parse_datetime_to_ms(val)
    offset = parse_offset_str(offset_sec_str) if offset_sec_str else 0
    ts -= offset * 1000
    return ts

def build_counter_event(item, field, offset_sec_str=None):
    """
    构建标准格式的counter事件。
    :param item: 单条原始数据
    :param field: 字段名
    :param offset_sec_str: 业务偏移
    :return: dict 标准事件
    """
    return {
        "event_type": "counter",
        "process_name": "cpu_short_30s",
        "track_name": field,
        "event_name": field,
        "timestamp": parse_collect_time_to_ms(item.get("collect_time"), offset_sec_str=offset_sec_str),
        "value": safe_float(item.get(field, 0)),
        "category": "cpu_short",
        "arguments": {}  # 预留，便于后续扩展
    }

def build_psi_avg10_events(item):
    """
    解析psi_avg10字段，生成多个counter事件。
    process_name: psi_avg_10s
    track_name: psi_avg10的key
    timestamp: collect_time-10s
    value: float
    """
    events = []
    psi_str = item.get("psi_avg10", "")
    if not psi_str:
        return events
    try:
        psi_dict = json.loads(psi_str)
    except Exception:
        return events
    for key, val in psi_dict.items():
        event = {
            "event_type": "counter",
            "process_name": "psi_avg_10s",
            "track_name": key,
            "event_name": key,
            "timestamp": parse_collect_time_to_ms(item.get("collect_time"), offset_sec_str="10s"),
            "value": safe_float(val),
            "category": "cpu_short",
            "arguments": {}
        }
        events.append(event)
    return events

def cpu_short_to_standard(json_data):
    """
    将 cpu_short 数据转为标准 trace 格式。
    每个字段都生成一个 counter 事件。
    :param json_data: 原始数据列表
    :return: 标准格式事件列表
    """
    fields = ["soft_irq", "total", "kernel", "irq", "nice", "user"]
    standard_list = []
    for item in json_data:
        for field in fields:
            standard_list.append(build_counter_event(item, field, offset_sec_str='30s'))
        # 处理psi_avg10
        standard_list.extend(build_psi_avg10_events(item))
    return standard_list 