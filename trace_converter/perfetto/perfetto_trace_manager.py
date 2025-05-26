# -*- coding: utf-8 -*-
from trace_converter.perfetto import perfetto_trace_pb2 as pftrace
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

    def add_instant_event(self, 
        process_name: str, 
        track_name: str, 
        event_name: str, 
        timestamp: int, 
        category: str = "default", 
        pid: Optional[int] = None, 
        arguments: Optional[Dict[str, str]] = None):
        track_uuid = self.ensure_track(process_name, 'instant', track_name, pid=pid)
        packet = add_event(timestamp, track_uuid, event_name, category, self.trusted_packet_sequence_id, 'instant')
        # 支持Arguments（debug_annotations）
        if arguments:
            for k, v in arguments.items():
                ann = packet.track_event.debug_annotations.add()
                ann.name = str(k)
                ann.string_value = str(v)
        self.trace.packet.append(packet)

    def add_slice_event(self, 
        process_name: str, 
        track_name: str,
        event_name: str,
        timestamp: int,
        duration_ns: int,
        category: str = "default",
        pid: Optional[int] = None,
        arguments: Optional[Dict[str, str]] = None):
        track_uuid = self.ensure_track(process_name, 'slice', track_name, pid=pid)
        start_packet = add_event(timestamp, track_uuid, event_name, category, self.trusted_packet_sequence_id, 'slice', duration_ns)
        # 支持Arguments（debug_annotations）
        if arguments:
            for k, v in arguments.items():
                ann = start_packet.track_event.debug_annotations.add()
                ann.name = str(k)
                ann.string_value = str(v)
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

    def from_standard_format(self, data_list):
        for idx, item in enumerate(data_list):
            # 标准化校验
            etype = item.get("event_type")
            pname = item.get("process_name")
            tname = item.get("track_name")
            ename = item.get("event_name")
            ts = item.get("timestamp")
            # 必填字段校验
            if etype not in ("counter", "slice", "instant", "log"):
                print(f"[WARN] idx={idx} event_type非法: {etype}, 跳过该条")
                continue
            if not pname or not isinstance(pname, str):
                print(f"[WARN] idx={idx} process_name非法: {pname}, 跳过该条")
                continue
            if not tname or not isinstance(tname, str):
                print(f"[WARN] idx={idx} track_name非法: {tname}, 跳过该条")
                continue
            if ts is None or not isinstance(ts, (int, float)):
                print(f"[WARN] idx={idx} timestamp非法: {ts}, 跳过该条")
                continue
            # 其它字段类型校验
            category = item.get("category", "default")
            pid = item.get("pid")
            value = item.get("value", 0)
            duration_ns = item.get("duration_ns", 0)
            message = item.get("message", "")
            arguments = item.get("arguments", None)
            # 生成纳秒时间戳
            timestamp_ns = int(float(ts) * 1_000_000)
            if etype == "counter":
                try:
                    value_f = float(value)
                except Exception:
                    print(f"[WARN] idx={idx} value非法: {value}, 置为0")
                    value_f = 0
                self.add_counter_event(
                    process_name=pname,
                    track_name=tname,
                    event_name=ename,
                    timestamp=timestamp_ns,
                    value=value_f,
                    category=category,
                    pid=pid
                )
            elif etype == "slice":
                try:
                    duration_ns_f = int(duration_ns)
                except Exception:
                    print(f"[WARN] idx={idx} duration_ns非法: {duration_ns}, 置为0")
                    duration_ns_f = 0
                self.add_slice_event(
                    process_name=pname,
                    track_name=tname,
                    event_name=ename,
                    timestamp=timestamp_ns,
                    duration_ns=duration_ns_f,
                    category=category,
                    pid=pid,
                    arguments=arguments
                )
            elif etype == "instant":
                self.add_instant_event(
                    process_name=pname,
                    track_name=tname,
                    event_name=ename,
                    timestamp=timestamp_ns,
                    category=category,
                    pid=pid,
                    arguments=arguments
                )
            elif etype == "log":
                msg = str(message) if message is not None else ""
                self.add_log_event(
                    process_name=pname,
                    track_name=tname,
                    log_lines=[msg] if msg else [],
                    category=category,
                    pid=pid
                )
            # 可扩展更多类型

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
