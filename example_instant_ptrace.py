import perfetto_trace_pb2 as pftrace
import uuid
import time
from typing import Dict, Tuple, Optional, List
import datetime

def uuid64():
    return uuid.uuid4().int >> 64

class PerfettoTraceManager:
    def __init__(self):
        self.trace = pftrace.Trace()
        self.trusted_packet_sequence_id = uuid64() >> 32
        self.process_tracks: Dict[str, Tuple[pftrace.TracePacket, int, int]] = {}  # process_name -> (track, uuid, pid)
        self.instant_tracks: Dict[str, Tuple[pftrace.TracePacket, int]] = {}  # process_name -> (track, uuid)
        self.slice_tracks: Dict[str, Tuple[pftrace.TracePacket, int]] = {}  # process_name -> (track, uuid)
        self.counter_tracks: Dict[str, Tuple[pftrace.TracePacket, int]] = {}  # process_name -> (track, uuid)
        self.log_tracks: Dict[str, Tuple[pftrace.TracePacket, int]] = {}  # process_name -> (track, uuid)

    def ensure_process_track(self, process_name: str, pid: Optional[int] = None) -> Tuple[int, int]:
        if process_name not in self.process_tracks:
            if pid is None:
                pid = uuid64() & 0xFFFF
            track, uuid = create_process_track(pid, process_name)
            self.trace.packet.append(track)
            self.process_tracks[process_name] = (track, uuid, pid)
        return self.process_tracks[process_name][2], self.process_tracks[process_name][1]

    def ensure_track(self, process_name: str, track_type: str, track_name: str) -> int:
        tracks_map = {
            'instant': self.instant_tracks,
            'slice': self.slice_tracks,
            'counter': self.counter_tracks,
            'log': self.log_tracks
        }
        if process_name not in tracks_map[track_type]:
            _, process_uuid = self.ensure_process_track(process_name)
            track, uuid = create_track(process_uuid, track_name, track_type)
            self.trace.packet.append(track)
            tracks_map[track_type][process_name] = (track, uuid)
        return tracks_map[track_type][process_name][1]

    def add_instant_event(self, process_name: str, event_name: str, category: str = "default", 
                         timestamp: int = None, track_name: str = "default_instant_track"):
        if timestamp is None:
            timestamp = int((time.time() + 3600 * 8) * 1e9)
        track_uuid = self.ensure_track(process_name, 'instant', track_name)
        packet = add_event(timestamp, track_uuid, event_name, category, 
                          self.trusted_packet_sequence_id, 'instant')
        self.trace.packet.append(packet)

    def add_slice_event(self, process_name: str, event_name: str, duration_ns: int,
                       category: str = "default", timestamp: int = None, 
                       track_name: str = "default_slice_track"):
        if timestamp is None:
            timestamp = int((time.time() + 3600 * 8) * 1e9)
        track_uuid = self.ensure_track(process_name, 'slice', track_name)
        start_packet = add_event(timestamp, track_uuid, event_name, category,
                               self.trusted_packet_sequence_id, 'slice', duration_ns)
        self.trace.packet.append(start_packet)
        end_packet = pftrace.TracePacket()
        end_packet.timestamp = timestamp + duration_ns
        end_packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
        end_packet.track_event.type = pftrace.TrackEvent.Type.TYPE_SLICE_END
        end_packet.track_event.track_uuid = track_uuid
        end_packet.track_event.categories.append(category)
        self.trace.packet.append(end_packet)

    def add_counter_event(self, process_name: str, event_name: str, value: float,
                         category: str = "default", timestamp: int = None,
                         track_name: str = "default_counter_track"):
        if timestamp is None:
            timestamp = int((time.time() + 3600 * 8) * 1e9)
        track_uuid = self.ensure_track(process_name, 'counter', track_name)
        packet = pftrace.TracePacket()
        packet.timestamp = timestamp
        packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
        packet.track_event.type = pftrace.TrackEvent.Type.TYPE_COUNTER
        # 兼容 float/int
        if hasattr(packet.track_event, 'double_counter_value'):
            packet.track_event.double_counter_value = float(value)
        else:
            packet.track_event.counter_value = int(value)
        packet.track_event.track_uuid = track_uuid
        packet.track_event.name = event_name
        packet.track_event.categories.append(category)
        self.trace.packet.append(packet)

    def add_log_event(self, process_name: str, log_lines: List[str], track_name: str = "default_log_track"):
        # 参考 perf_data_merge.py 的 write_log_track
        # 只支持格式："2024-06-01 12:00:00.000 pid tid LEVEL TAG: message"
        track_uuid = self.ensure_track(process_name, 'log', track_name)
        for line in log_lines:
            try:
                msg_time = line[:23]
                dt = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
                stamp = datetime.datetime.timestamp(dt)
                rest = line[23:].strip()
                parts = rest.split()
                pid = int(parts[0])
                tid = int(parts[1])
                level = parts[2]
                tag_and_msg = " ".join(parts[3:])
                tag, msg = tag_and_msg.split(": ", 1)
                packet = pftrace.TracePacket()
                packet.timestamp = int((stamp + 3600 * 8) * 1e9)
                packet.trusted_packet_sequence_id = self.trusted_packet_sequence_id
                log_event = pftrace.AndroidLogPacket.LogEvent()
                log_event.timestamp = int((stamp + 3600 * 8) * 1e9)
                log_event.pid = pid
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

def create_process_track(pid: int, process_name: str) -> Tuple[pftrace.TracePacket, int]:
    process_track = pftrace.TracePacket()
    process_track_uuid = uuid64()
    process_track.track_descriptor.uuid = process_track_uuid
    process_track.track_descriptor.process.pid = pid
    process_track.track_descriptor.process.process_name = process_name
    return process_track, process_track_uuid

def create_track(parent_uuid: int, track_name: str, track_type: str) -> Tuple[pftrace.TracePacket, int]:
    track = pftrace.TracePacket()
    track_uuid = uuid64()
    track.track_descriptor.uuid = track_uuid
    track.track_descriptor.parent_uuid = parent_uuid
    track.track_descriptor.name = track_name
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

def main():
    manager = PerfettoTraceManager()
    manager.add_instant_event(process_name="my_process", event_name="event_1", category="categoryA")
    manager.add_instant_event(process_name="my_process", event_name="event_2", category="categoryB")
    manager.add_slice_event(process_name="my_process", event_name="slice_1", duration_ns=1000000000, category="categoryC")
    manager.add_counter_event(process_name="my_process1111", event_name="counter_1", value=42.0, category="categoryD")
    # 添加 log 示例
    log_lines = [
        "2024-06-01 12:00:00.000 1234 1234 I MyTag: hello world",
        "2024-06-01 12:00:01.000 1234 1234 W MyTag: warning message"
    ]
    manager.add_log_event(process_name="my_process", log_lines=log_lines)
    manager.add_clock_snapshot()
    manager.save_to_file("instant_only.perfetto")
    print("已生成 instant_only.perfetto 文件，可用 Perfetto UI 打开查看事件。")

if __name__ == "__main__":
    main() 