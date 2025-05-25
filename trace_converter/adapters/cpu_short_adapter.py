import datetime
import re

def safe_float(val, default=0.0):
    """安全地将值转为float，失败时返回default。"""
    try:
        return float(val)
    except Exception:
        return default

def parse_offset_str(offset_str):
    """
    解析 '+08h00m00s'、'-30s'、'+1h30m' 等字符串为秒数（int）。
    支持正负号，支持 h/m/s 任意组合。
    """
    if not offset_str:
        return 0
    sign = 1
    s = offset_str.strip()
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
    total_sec = 0
    for part, mult in re.findall(r'(\d+)([hms])', s):
        if mult == 'h':
            total_sec += int(part) * 3600
        elif mult == 'm':
            total_sec += int(part) * 60
        elif mult == 's':
            total_sec += int(part)
    return sign * total_sec

def parse_collect_time_to_ms(val, offset_sec_str=None, tz_offset_sec_str=None):
    """
    支持字符串格式如 '2025-02-06 21:40:14'，返回毫秒时间戳。
    offset_sec_str: 业务偏移（如-30s），tz_offset_sec_str: 时区偏移（如+8小时=28800秒）。
    """
    ts = 0
    if isinstance(val, (int, float)):
        ts = int(val)
    elif isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                ts = int(dt.timestamp() * 1000)
                break
            except Exception:
                continue
    # 先加时区偏移，再加业务偏移
    tz_offset = parse_offset_str(tz_offset_sec_str) if tz_offset_sec_str else 0
    offset = parse_offset_str(offset_sec_str) if offset_sec_str else 0
    ts += tz_offset * 1000
    ts -= offset * 1000
    return ts

def build_counter_event(item, field, offset_sec_str=None, tz_offset_sec_str=None):
    """构建标准格式的counter事件。"""
    return {
        "event_type": "counter",
        "process_name": "cpu_short_30s",
        "track_name": field,
        "timestamp": parse_collect_time_to_ms(item.get("collect_time"), offset_sec_str=offset_sec_str, tz_offset_sec_str=tz_offset_sec_str),
        "value": safe_float(item.get(field, 0)),
        "category": "cpu_short"
    }

def cpu_short_to_standard(json_data):
    """
    将 cpu_short 数据转为标准 trace 格式。
    每个字段都生成一个 counter 事件。
    """
    fields = ["soft_irq", "total", "kernel", "irq", "nice", "user"]
    standard_list = []
    for item in json_data:
        for field in fields:
            standard_list.append(build_counter_event(item, field, offset_sec_str='30s', tz_offset_sec_str='+08h'))
    return standard_list 