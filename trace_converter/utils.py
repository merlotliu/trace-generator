import re
import datetime

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

def parse_datetime_to_ms(val):
    """
    支持字符串格式如 '2025-02-06 21:40:14'，返回毫秒时间戳。
    """
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                return int(dt.timestamp() * 1000)
            except Exception:
                continue
    return 0 