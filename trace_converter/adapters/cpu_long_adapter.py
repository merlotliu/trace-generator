from trace_converter.utils import parse_datetime_to_ms
import json

def cpu_long_to_standard(json_data):
    """
    将CPU长周期数据转为标准trace格式：
    - process_name统一为'proc_cpu_usage_200s'
    - track_name和event_name为进程名(pid)
    - 每个采样点每个进程都生成counter事件，缺失补0（对比上一个时间点）
    - arguments保留pid/cswch/nvcswch/system/user
    - value为total
    """
    timestamps = []
    time_proc_map = {}
    all_proc_names = set()
    for idx, item in enumerate(json_data):
        ts = parse_datetime_to_ms(item.get('collect_time', ''))
        timestamps.append(ts)
        proc_info_list = json.loads(item.get('proc_info', '[]'))
        proc_map = {}
        for proc in proc_info_list:
            proc_name = proc.get('procName', '')
            pid = proc.get('pid', '')
            track_key = f"{proc_name}({pid})"
            all_proc_names.add(track_key)
            proc_map[track_key] = proc
        time_proc_map[ts] = proc_map
    timestamps = sorted(set(timestamps))
    result = []
    prev_proc_set = set()
    for idx, ts in enumerate(timestamps):
        proc_map = time_proc_map.get(ts, {})
        curr_proc_set = set(proc_map.keys())
        # 1. 正常生成当前进程事件
        for track_name, proc in proc_map.items():
            value = float(proc.get('total', 0))
            arguments = {
                'pid': proc.get('pid', ''),
                'cswch': proc.get('cswch', ''),
                'nvcswch': proc.get('nvcswch', ''),
                'system': proc.get('system', ''),
                'user': proc.get('user', ''),
            }
            event = {
                'event_type': 'counter',
                'process_name': 'proc_cpu_usage_200s',
                'track_name': track_name,
                'event_name': track_name,
                'timestamp': ts,
                'value': value,
                'category': 'cpu_long',
                'arguments': arguments
            }
            result.append(event)
        # 2. 对比上一个时间点，缺失的进程补0
        if idx > 0:
            lost_procs = prev_proc_set - curr_proc_set
            for lost_track in lost_procs:
                # 尽量保留上一个时间点的pid
                pid = ''
                if lost_track in prev_proc_pid_map:
                    pid = prev_proc_pid_map[lost_track]
                event = {
                    'event_type': 'counter',
                    'process_name': 'proc_cpu_usage_200s',
                    'track_name': lost_track,
                    'event_name': lost_track,
                    'timestamp': ts,
                    'value': 0.0,
                    'category': 'cpu_long',
                    'arguments': {'pid': pid, 'cswch': '', 'nvcswch': '', 'system': '', 'user': ''}
                }
                result.append(event)
        # 记录本轮track_name和pid
        curr_proc_pid_map = {track: proc.get('pid', '') for track, proc in proc_map.items()}
        prev_proc_set = curr_proc_set
        prev_proc_pid_map = curr_proc_pid_map
    return result 