import perfetto_trace_pb2 as pftrace
import uuid
import time

# 生成64位唯一ID
def uuid64():
    return uuid.uuid4().int >> 64

trusted_packet_sequence_id = uuid64() >> 32

# 1. 创建 Trace 根对象
trace = pftrace.Trace()

# 2. 创建进程 Track（可选，但建议加上，便于 UI 展示）
process_track = pftrace.TracePacket()
process_track_uuid = uuid64()
process_track.track_descriptor.uuid = process_track_uuid
process_track.track_descriptor.process.pid = 12345
process_track.track_descriptor.process.process_name = "instant_demo"
trace.packet.append(process_track)

process_track2 = pftrace.TracePacket()
process_track_uuid2 = uuid64()
process_track2.track_descriptor.uuid = process_track_uuid2
process_track2.track_descriptor.process.pid = 12345
process_track2.track_descriptor.process.process_name = "instant_demo2"
trace.packet.append(process_track2)

# 3. 创建 INSTANT Track
instant_track = pftrace.TracePacket()
instant_track_uuid = uuid64()
instant_track.track_descriptor.uuid = instant_track_uuid
instant_track.track_descriptor.parent_uuid = process_track_uuid
instant_track.track_descriptor.name = "my_instant_track"
trace.packet.append(instant_track)

# 4. 添加 INSTANT 事件1
packet1 = pftrace.TracePacket()
packet1.timestamp = int((time.time() + 3600 * 8) * 1e9)  # 当前时间，东八区
packet1.trusted_packet_sequence_id = trusted_packet_sequence_id
packet1.track_event.type = pftrace.TrackEvent.Type.TYPE_INSTANT
packet1.track_event.name = "event_1"
packet1.track_event.track_uuid = instant_track_uuid
packet1.track_event.categories.append("categoryA")
trace.packet.append(packet1)

# 5. 添加 INSTANT 事件2
packet2 = pftrace.TracePacket()
packet2.timestamp = int((time.time() + 3600 * 8 + 1) * 1e9)  # 比前一个晚1秒
packet2.trusted_packet_sequence_id = trusted_packet_sequence_id
packet2.track_event.type = pftrace.TrackEvent.Type.TYPE_INSTANT
packet2.track_event.name = "event_2"
packet2.track_event.track_uuid = instant_track_uuid
packet2.track_event.categories.append("categoryB")
trace.packet.append(packet2)

# 6. 添加时钟快照（可选，但建议加上，保证 UI 能正常显示时间轴）
start_stamp = int(time.time())
clock_packet = pftrace.TracePacket()
clock_packet.timestamp = int((start_stamp + 3600 * 8) * 1e9)
clock_packet.trusted_packet_sequence_id = trusted_packet_sequence_id
clock_packet.clock_snapshot.primary_trace_clock = pftrace.BuiltinClock.BUILTIN_CLOCK_BOOTTIME
for i in range(1, 7):
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = i
    clock.timestamp = int((start_stamp + 3600 * 8) * 1e9)
    clock_packet.clock_snapshot.clocks.append(clock)
trace.packet.append(clock_packet)

# 7. 保存为文件
with open("instant_only.perfetto", "wb") as f:
    f.write(trace.SerializeToString())

print("已生成 instant_only.perfetto 文件，可用 Perfetto UI 打开查看 INSTANT 事件。") 