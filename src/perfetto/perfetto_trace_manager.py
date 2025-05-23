# -*- coding: utf-8 -*-
from src.perfetto import perfetto_trace_pb2 as pftrace
import uuid
import time
from typing import Dict, Tuple, Optional, List
import datetime
import re

def uuid64():
    return uuid.uuid4().int >> 64

class PerfettoTraceManager:
    def __init__(self):
        self.trace = pftrace.Trace()
        self.trusted_packet_sequence_id = uuid64() >> 32
        self.process_tracks: Dict[str, Tuple[pftrace.TracePacket, int, int]] = {}  # process_name -> (track, uuid, pid)
        self.instant_tracks: Dict[Tuple[str, str], Tuple[pftrace.TracePacket, int]] = {}
        self.slice_tracks: Dict[Tuple[str, str], Tuple[pftrace.TracePacket, int]] = {}
        self.counter_tracks: Dict[Tuple[str, str], Tuple[pftrace.TracePacket, int]] = {}
        self.log_tracks: Dict[Tuple[str, str], Tuple[pftrace.TracePacket, int]] = {}
        self._auto_pid = 10000  # 起始自动分配pid

    def ensure_process_track(self, process_name: str, pid: Optional[int] = None) -> Tuple[int, int]:
        if process_name not in self.process_tracks:
            process_track = pftrace.TracePacket()
            process_track_uuid = uuid64()
            process_track.track_descriptor.uuid = process_track_uuid
            process_track.track_descriptor.process.process_name = process_name
            # 自动分配pid
            if pid is None or pid == 0:
                pid = self._auto_pid
                self._auto_pid += 1
            process_track.track_descriptor.process.pid = pid
            self.trace.packet.append(process_track)
            self.process_tracks[process_name] = (process_track, process_track_uuid, pid)
        return self.process_tracks[process_name][2], self.process_tracks[process_name][1]

    def ensure_track(self, process_name: str, track_type: str, track_name: str, pid: Optional[int] = None) -> int:
        if track_type == 'counter':
            key = (process_name, track_name)
            tracks_map = self.counter_tracks
        elif track_type == 'instant':
            key = (process_name, track_name)
            tracks_map = self.instant_tracks
        elif track_type == 'slice':
            key = (process_name, track_name)
            tracks_map = self.slice_tracks
        elif track_type == 'log':
            key = (process_name, track_name)
            tracks_map = self.log_tracks
        else:
            raise ValueError(f"Unknown track_type: {track_type}")
        if key not in tracks_map:
            _, process_uuid = self.ensure_process_track(process_name, pid=pid)
            track, uuid = create_track(process_uuid, track_name, track_type)
            self.trace.packet.append(track)
            tracks_map[key] = (track, uuid)
        return tracks_map[key][1]

    def add_instant_event(self, process_name: str, track_name: str, event_name: str, timestamp: int, *, category: str = "default", pid: Optional[int] = None):
        track_uuid = self.ensure_track(process_name, 'instant', track_name, pid=pid)
        packet = add_event(timestamp, track_uuid, event_name, category, self.trusted_packet_sequence_id, 'instant')
        self.trace.packet.append(packet)

    def add_slice_event(self, process_name: str, track_name: str, event_name: str, timestamp: int, duration_ns: int, *, category: str = "default", pid: Optional[int] = None):
        track_uuid = self.ensure_track(process_name, 'slice', track_name, pid=pid)
        start_packet = add_event(timestamp, track_uuid, event_name, category, self.trusted_packet_sequence_id, 'slice', duration_ns)
        self.trace.packet.append(start_packet)
        end_packet = pftrace.TracePacket()
        end_packet.timestamp = timestamp + duration_ns
        end_packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
        end_packet.track_event.type = pftrace.TrackEvent.Type.TYPE_SLICE_END
        end_packet.track_event.track_uuid = track_uuid
        end_packet.track_event.categories.append(category)
        self.trace.packet.append(end_packet)

    def add_counter_event(self, process_name: str, track_name: str, event_name: str, timestamp: int, value: float, *, category: str = "default", pid: Optional[int] = None):
        track_uuid = self.ensure_track(process_name, 'counter', track_name, pid=pid)
        packet = pftrace.TracePacket()
        packet.timestamp = timestamp
        packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
        packet.track_event.type = pftrace.TrackEvent.Type.TYPE_COUNTER
        packet.track_event.track_uuid = track_uuid
        packet.track_event.name = event_name
        packet.track_event.categories.append(category)
        packet.track_event.double_counter_value = float(value)
        self.trace.packet.append(packet)

    def add_log_event(self, process_name: str, track_name: str, log_lines: List[str], category: str = "default", pid: Optional[int] = None):
        track_uuid = self.ensure_track(process_name, 'log', track_name, pid=pid)
        for line in log_lines:
            try:
                msg_time = line[:23]
                dt = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
                stamp = datetime.datetime.timestamp(dt)
                rest = line[23:].strip()
                parts = rest.split()
                pid_val = int(parts[0])
                tid = int(parts[1])
                level = parts[2]
                tag_and_msg = " ".join(parts[3:])
                tag, msg = tag_and_msg.split(": ", 1)
                packet = pftrace.TracePacket()
                packet.timestamp = int((stamp + 3600 * 8) * 1e9)
                packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
                log_event = pftrace.AndroidLogPacket.LogEvent()
                log_event.timestamp = int((stamp + 3600 * 8) * 1e9)
                log_event.pid = pid_val
                log_event.tid = tid
                log_event.tag = tag
                log_event.message = msg
                # level 映射
                if level == "V":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_VERBOSE
                elif level == "D":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_DEBUG
                elif level == "I":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_INFO
                elif level == "W":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_WARN
                elif level == "E":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_ERROR
                elif level == "F":
                    log_event.prio = pftrace.AndroidLogPriority.PRIO_FATAL
                packet.android_log.events.append(log_event)
                self.trace.packet.append(packet)
            except Exception as e:
                print(f"log parse error: {line}", e)

    def add_clock_snapshot(self, timestamp: int = None):
        if timestamp is None:
            timestamp = int((time.time() + 3600 * 8) * 1e9)
        clock_packet = add_clock_snapshot(timestamp, self.trusted_packet_sequence_id)
        self.trace.packet.append(clock_packet)

    def save_to_file(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.trace.SerializeToString())

    def json2perfetto(self, json_data_list, track_dict):
        processor = TrackProcessor(self)
        for pname, track_list in track_dict.items():
            for cfg in track_list:
                track_config = TrackConfig(cfg)
                processor.process(pname, json_data_list, track_config)

def create_process_track(pid: int, process_name: str) -> Tuple[pftrace.TracePacket, int]:
    process_track = pftrace.TracePacket()
    process_track_uuid = uuid64()
    process_track.track_descriptor.uuid = process_track_uuid
    process_track.track_descriptor.process.process_name = process_name
    if pid is not None and pid != 0:
        process_track.track_descriptor.process.pid = pid
    return process_track, process_track_uuid

def create_track(parent_uuid: int, track_name: str, track_type: str) -> Tuple[pftrace.TracePacket, int]:
    track = pftrace.TracePacket()
    track_uuid = uuid64()
    track.track_descriptor.uuid = track_uuid
    track.track_descriptor.parent_uuid = parent_uuid
    track.track_descriptor.name = track_name
    if track_type == 'counter':
        counter = pftrace.CounterDescriptor()
        counter.unit = pftrace.CounterDescriptor.Unit.UNIT_COUNT
        track.track_descriptor.counter.CopyFrom(counter)
    return track, track_uuid

def add_event(timestamp: int, track_uuid: int, event_name: str, category: str,
              trusted_packet_sequence_id: int, event_type: str,
              duration_ns: Optional[int] = None, value: Optional[float] = None) -> pftrace.TracePacket:
    packet = pftrace.TracePacket()
    packet.timestamp = timestamp
    packet.trusted_packet_sequence_id = trusted_packet_sequence_id
    if event_type == 'instant':
        packet.track_event.type = pftrace.TrackEvent.Type.TYPE_INSTANT
    elif event_type == 'slice':
        packet.track_event.type = pftrace.TrackEvent.Type.TYPE_SLICE_BEGIN
    packet.track_event.name = event_name
    packet.track_event.track_uuid = track_uuid
    packet.track_event.categories.append(category)
    return packet

def add_clock_snapshot(timestamp: int, trusted_packet_sequence_id: int) -> pftrace.TracePacket:
    clock_packet = pftrace.TracePacket()
    clock_packet.timestamp = timestamp
    clock_packet.trusted_packet_sequence_id = trusted_packet_sequence_id
    clock_packet.clock_snapshot.primary_trace_clock = pftrace.BuiltinClock.BUILTIN_CLOCK_BOOTTIME
    for i in range(1, 7):
        clock = pftrace.ClockSnapshot.Clock()
        clock.clock_id = i
        clock.timestamp = timestamp
        clock_packet.clock_snapshot.clocks.append(clock)
    return clock_packet

class TrackConfig:
    def __init__(self, config: dict):
        self.field = config["field"]
        self.tname = config.get("tname", self.field)
        self.track_type = config.get("type", "unknown")
        self.ts_field = config.get("ts", "collect_time")
        self.timezone = config.get("timezone", "+0800")
        self.offset = config.get("offset", None)
        self.category = config.get("category", "default")
        self.duration_ms = config.get("duration_ms", None)

def parse_template_value(val, item):
    import re
    if isinstance(val, str):
        pattern = re.compile(r"\$\(([^)]+)\)")
        def replacer(match):
            key = match.group(1)
            v = get_nested_value(item, key)
            if v is None:
                print(f"[WARN] parse_template_value: {key} not found in item {item}")
                return ""
            return str(v)
        return pattern.sub(replacer, val)
    return val

class TrackProcessor:
    def __init__(self, manager):
        self.manager = manager

    def process(self, pname, json_data_list, track_config: TrackConfig):
        for item in json_data_list:
            # 动态解析所有配置字段
            resolved = {}
            for key in vars(track_config):
                val = getattr(track_config, key)
                resolved[key] = parse_template_value(val, item) if isinstance(val, str) else val

            ts = parse_time_with_offset(item, resolved.get("ts_field", "collect_time"), resolved.get("offset"), resolved.get("timezone", "+0800"))
            value = float(get_nested_value(item, resolved.get("field")))
            duration_ms_val = resolved.get("duration_ms", None)
            if duration_ms_val not in (None, ""):
                try:
                    duration_ms_val = float(duration_ms_val)
                except Exception:
                    print(f"[WARN] duration_ms_val '{duration_ms_val}' cannot be converted to float")
                    duration_ms_val = 0
            else:
                duration_ms_val = 0

            if resolved.get("track_type") == "counter":
                self.manager.add_counter_event(
                    process_name=pname,
                    track_name=resolved.get("tname"),
                    event_name=resolved.get("field"),
                    timestamp=ts,
                    value=value,
                    category=resolved.get("category", "default")
                )
            if resolved.get("track_type") == "slice":
                self.manager.add_slice_event(
                    process_name=pname,
                    track_name=resolved.get("tname"),
                    event_name=resolved.get("field"),
                    timestamp=ts,
                    duration_ns=int(duration_ms_val) * 1_000_000 if duration_ms_val is not None else 0,
                    category=resolved.get("category", "default")
                )
            # 可扩展更多类型

def parse_time_with_offset(item, ts_field, offset=None, timezone="+0000"):
    import datetime
    ts_val = item.get(ts_field)
    if ts_val is None:
        return 0
    # 1. 直接是 int/float 时间戳
    if isinstance(ts_val, (int, float)):
        # 判断单位：大于1e12视为纳秒，1e9~1e12视为微秒，1e6~1e9视为秒
        if ts_val > 1e15:  # 假定为皮秒
            ts = int(ts_val / 1_000)
        elif ts_val > 1e12:  # 纳秒
            ts = int(ts_val)
        elif ts_val > 1e9:  # 微秒
            ts = int(ts_val * 1_000)
        elif ts_val > 1e6:  # 毫秒
            ts = int(ts_val * 1_000_000)
        else:  # 秒
            ts = int(ts_val * 1_000_000_000)
        # 处理 offset
        if offset:
            sign = -1 if offset.startswith("-") else 1
            offset_val = offset[1:] if offset[0] in "+-" else offset
            if offset_val.endswith("s"):
                ts += sign * int(float(offset_val[:-1]) * 1_000_000_000)
            elif offset_val.endswith("ms"):
                ts += sign * int(float(offset_val[:-2]) * 1_000_000)
        return ts
    # 2. 字符串格式
    ts_str = str(ts_val)
    # 解析时区
    if timezone.startswith("+") or timezone.startswith("-"):
        sign = 1 if timezone[0] == "+" else -1
        try:
            hours = int(timezone[1:3])
            mins = int(timezone[3:5])
        except Exception:
            hours = 0
            mins = 0
        tz_delta = datetime.timedelta(hours=sign * hours, minutes=sign * mins)
        tzinfo = datetime.timezone(tz_delta)
    else:
        tzinfo = datetime.timezone.utc
    # 支持多种字符串格式
    dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.datetime.strptime(ts_str, fmt)
            dt = dt.replace(tzinfo=tzinfo)
            break
        except Exception:
            continue
    if dt is None:
        print(f"[WARN] Unrecognized timestamp format: {ts_str}")
        return 0
    ts = int(dt.timestamp() * 1_000_000_000)
    # 处理 offset
    if offset:
        sign = -1 if offset.startswith("-") else 1
        offset_val = offset[1:] if offset[0] in "+-" else offset
        if offset_val.endswith("s"):
            ts += sign * int(float(offset_val[:-1]) * 1_000_000_000)
        elif offset_val.endswith("ms"):
            ts += sign * int(float(offset_val[:-2]) * 1_000_000)
    return ts

def get_nested_value(item, field):
    parts = field.split('.')
    val = item
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, None)
        else:
            return 0
    return val if val is not None else 0

def main():
    import datetime
    manager = PerfettoTraceManager()
    # 统一时间基准
    base_time = int((time.time() + 3600 * 8) * 1e9)
    ts_0 = base_time
    ts_1 = base_time + 10_000_000   # +10ms
    ts_2 = base_time + 20_000_000   # +20ms
    ts_3 = base_time + 30_000_000   # +30ms
    ts_4 = base_time + 40_000_000   # +40ms
    ts_5 = base_time + 50_000_000   # +50ms

    # 普通进程分组（有pid）
    manager.add_counter_event("my_process", "cpu", "counter_1", ts_0, 42.0, category="categoryD", pid=1234)
    manager.add_instant_event("my_process", "event_track", "event_1", ts_1, category="categoryA", pid=1234)
    manager.add_slice_event("my_process", "slice_track", "slice_1", ts_2, 20_000_000, category="categoryC", pid=1234)
    # 其它分组（自动分配pid）
    manager.add_counter_event("MyCustomGroup", "cpu", "custom_counter", ts_3, 123.0, category="custom_metrics")
    manager.add_instant_event("MyCustomGroup", "event_track", "custom_event", ts_4, category="custom_category")
    manager.add_slice_event("MyCustomGroup", "slice_track", "custom_slice", ts_5, 20_000_000, category="custom_slice_category")

    # # log 示例（原有格式，时间戳由字符串解析）
    # log_lines = [
    #     "2024-06-01 14:42:00.000 99999 1 I MyTag: hello world",
    #     "2024-06-01 14:42:00.010 99999 1 W MyTag: warning message"
    # ]
    # manager.add_log_event("MyCustomGroup", "log_track", log_lines, category="logcat")

    # 添加时钟快照
    manager.add_clock_snapshot(timestamp=ts_0)
    # 保存为文件
    manager.save_to_file("instant_only.perfetto")
    print("已生成 instant_only.perfetto 文件，可用 Perfetto UI 打开查看事件。")

if __name__ == "__main__":
    main()