"""Perfetto data merge"""

import datetime
import json
import os
import sys
import traceback
import uuid

import perfetto_trace_pb2 as pftrace

TYPE_UNSPECIFIED = pftrace.TrackEvent.Type.TYPE_UNSPECIFIED
TYPE_SLICE_BEGIN = pftrace.TrackEvent.Type.TYPE_SLICE_BEGIN
TYPE_SLICE_END = pftrace.TrackEvent.Type.TYPE_SLICE_END
TYPE_INSTANT = pftrace.TrackEvent.Type.TYPE_INSTANT
TYPE_COUNTER = pftrace.TrackEvent.Type.TYPE_COUNTER

flow_name_to_id = {}


def uuid64() -> int:
    return uuid.uuid4().int >> 64


trusted_packet_sequence_id = uuid64() >> 32


def write_counter_track(
    trace: pftrace.Trace, track_name: str, values: list, ts: list, group_uuid: int
):
    # print(track_name)

    # Create a new track
    track = pftrace.TracePacket()
    counter_track_uuid = uuid64()
    track.track_descriptor.uuid = counter_track_uuid
    track.track_descriptor.parent_uuid = group_uuid
    track.track_descriptor.name = track_name
    counter = pftrace.CounterDescriptor()
    track.track_descriptor.counter.CopyFrom(counter)
    trace.packet.append(track)

    for index, value in enumerate(values):
        packet = pftrace.TracePacket()

        packet.timestamp = int((ts[index] + 3600 * 8) * 1000000000)
        packet.trusted_packet_sequence_id = trusted_packet_sequence_id

        packet.track_event.type = TYPE_COUNTER
        packet.track_event.double_counter_value = value
        packet.track_event.track_uuid = counter_track_uuid

        trace.packet.append(packet)


# {
#    "type": "EVENT",
#    "name": "looper sample",
#    "group": "time consuming",
#    "event": [
#      "android.app.ActivityThread$H",
#      "android.app.ActivityThread$H",
#      "android.view.Choreographer$FrameHandler",
#      "android.view.ViewRootImpl$ViewRootHandler",
#      "android.view.Choreographer$FrameHandler"
#    ],
#    "flow": ["", "", "", "flow1", ""],
#    "value": [ ... ],
#    "timestamp": [ ... ]
# }
def write_instant_track(
    trace: pftrace.Trace,
    track_name: str,
    event_names: list,
    ts: list,
    group_uuid: int,
    flow_ids: list = None,
    **kwargs,
):
    # print(track_name)

    # Create a new track
    track = pftrace.TracePacket()
    instant_track_uuid = uuid64()
    print(instant_track_uuid)
    track.track_descriptor.uuid = instant_track_uuid
    track.track_descriptor.parent_uuid = group_uuid
    track.track_descriptor.name = track_name
    trace.packet.append(track)

    for index, event_name in enumerate(event_names):
        packet = pftrace.TracePacket()

        packet.timestamp = int((ts[index] + 3600 * 8) * 1000000000)
        packet.trusted_packet_sequence_id = trusted_packet_sequence_id

        if flow_ids is not None and flow_ids[index] != "":
            if flow_ids[index] not in flow_name_to_id:
                flow_name_to_id[flow_ids[index]] = uuid64()
            packet.track_event.flow_ids.append(flow_name_to_id[flow_ids[index]])

        packet.track_event.type = TYPE_INSTANT
        packet.track_event.name = event_name
        packet.track_event.track_uuid = instant_track_uuid
        packet.track_event.categories.append(track_name)

        # da_log = pftrace.DebugAnnotation()
        # da_log.name = "log"
        # da_log.string_value = args[values.index(value)]

        da_args = pftrace.DebugAnnotation()
        da_args.name = "args"  # Dict style args
        # da_args.dict_entries.append(da_log)

        for k, v in kwargs.items():
            da = pftrace.DebugAnnotation()
            da.name = k
            if v == None:
                continue
            da_value = v[index]
            if type(da_value) == str:
                da.string_value = da_value
            elif type(da_value) == int:
                da.int_value = da_value
            elif type(da_value) == float:
                da.double_value = da_value
            elif type(da_value) == bool:
                da.bool_value = da_value
            else:
                da.string_value = str(da_value)

            da_args.dict_entries.append(da)

        packet.track_event.debug_annotations.append(da_args)

        trace.packet.append(packet)


def write_slice_track(
    trace: pftrace.Trace,
    track_name: str,
    event_names: list,
    ts_start: list,
    ts_end: list,
    group_uuid: int,
    flow_ids: list = None,
    **kwargs,
):
    # print(track_name)

    # Create a new track
    track = pftrace.TracePacket()
    instant_track_uuid = uuid64()
    track.track_descriptor.uuid = instant_track_uuid
    track.track_descriptor.parent_uuid = group_uuid
    track.track_descriptor.name = track_name
    trace.packet.append(track)

    for index, event_name in enumerate(event_names):
        # END packet
        if ts_end[index] != 0:
            packet = pftrace.TracePacket()

            packet.timestamp = int((ts_end[index] + 3600 * 8) * 1000000000)
            packet.trusted_packet_sequence_id = trusted_packet_sequence_id
            packet.track_event.type = TYPE_SLICE_END
            packet.track_event.name = event_name
            packet.track_event.track_uuid = instant_track_uuid
            packet.track_event.categories.append(track_name)
            trace.packet.append(packet)

        # BEGIN packet
        packet = pftrace.TracePacket()

        packet.timestamp = int((ts_start[index] + 3600 * 8) * 1000000000)
        packet.trusted_packet_sequence_id = trusted_packet_sequence_id

        if flow_ids is not None and flow_ids[index] != "":
            if flow_ids[index] not in flow_name_to_id:
                flow_name_to_id[flow_ids[index]] = uuid64()
            packet.track_event.flow_ids.append(flow_name_to_id[flow_ids[index]])

        packet.track_event.type = TYPE_SLICE_BEGIN
        packet.track_event.name = event_name
        packet.track_event.track_uuid = instant_track_uuid
        packet.track_event.categories.append(track_name)

        # da_log = pftrace.DebugAnnotation()
        # da_log.name = "log"
        # da_log.string_value = args[values.index(value)]

        da_args = pftrace.DebugAnnotation()
        da_args.name = "args"  # Dict style args
        # da_args.dict_entries.append(da_log)

        for k, v in kwargs.items():
            da = pftrace.DebugAnnotation()
            da.name = k
            if v == None:
                continue
            da_value = v[index]
            if type(da_value) == str:
                da.string_value = da_value
            elif type(da_value) == int:
                da.int_value = da_value
            elif type(da_value) == float:
                da.double_value = da_value
            elif type(da_value) == bool:
                da.bool_value = da_value
            else:
                da.string_value = str(da_value)

            da_args.dict_entries.append(da)

        packet.track_event.debug_annotations.append(da_args)

        trace.packet.append(packet)


def write_log_track(trace: pftrace.Trace, track_name: str, values: list):
    # print('>>>>>>>>>>>> %s' % values[0])
    dt_start = datetime.datetime.strptime(values[0][:23], "%Y-%m-%d %H:%M:%S.%f")
    start_stamp = datetime.datetime.timestamp(dt_start)
    dt_end = datetime.datetime.strptime(values[-1][:23], "%Y-%m-%d %H:%M:%S.%f")
    end_stamp = datetime.datetime.timestamp(dt_end)

    packet = pftrace.TracePacket()
    packet.timestamp = int((end_stamp + 3600 * 8) * 1000000000)
    packet.trusted_packet_sequence_id = trusted_packet_sequence_id
    packet.android_log.stats.num_total = len(values)
    packet.android_log.stats.num_failed = 0
    packet.android_log.stats.num_skipped = 0
    trace.packet.append(packet)

    packet = pftrace.TracePacket()
    packet.timestamp = int((end_stamp + 3600 * 8) * 1000000000)
    packet.trusted_packet_sequence_id = trusted_packet_sequence_id

    for index, line in enumerate(values):
        # print(line)

        msg = pftrace.AndroidLogPacket.LogEvent()
        msg_time = line[:23]
        dt = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        stamp = datetime.datetime.timestamp(dt)
        msg.timestamp = int((stamp + 3600 * 8) * 1000000000)
        line = line[23:]

        msg.log_id = pftrace.AndroidLogId.LID_DEFAULT
        msg.uid = 0

        list1 = line.split(" ")
        list2 = []
        for item in list1:
            if item != "":
                list2.append(item)

        try:
            msg.pid = int(list2[0])
            msg.tid = int(list2[1])

            level = list2[2]
            if level == "V":
                msg.prio = pftrace.AndroidLogPriority.PRIO_VERBOSE
            elif level == "D":
                msg.prio = pftrace.AndroidLogPriority.PRIO_DEBUG
            elif level == "I":
                msg.prio = pftrace.AndroidLogPriority.PRIO_INFO
            elif level == "W":
                msg.prio = pftrace.AndroidLogPriority.PRIO_WARN
            elif level == "E":
                msg.prio = pftrace.AndroidLogPriority.PRIO_ERROR
            elif level == "F":
                msg.prio = pftrace.AndroidLogPriority.PRIO_FATAL

            line = " ".join(list2[3:])
            list3 = line.split(": ")

            msg.tag = list3[0]

            if track_name != "":
                msg.message = "%s %d %d %s: %s" % (
                    msg_time[5:],
                    msg.pid,
                    msg.tid,
                    track_name,
                    ": ".join(list3[1:]),
                )
            else:
                msg.message = "%s %d %d %s" % (
                    msg_time[5:],
                    msg.pid,
                    msg.tid,
                    ": ".join(list3[1:]),
                )

            packet.android_log.events.append(msg)
        except:
            print(line)
            traceback.print_exc()
            pass

    packet.previous_packet_dropped = True

    trace.packet.append(packet)

    return start_stamp


def merge(json_str: str) -> pftrace.Trace:
    # Create a new trace
    root = pftrace.Trace()

    default_process_track = pftrace.TracePacket()
    default_process_track_uuid = uuid64()
    default_process_track.track_descriptor.uuid = default_process_track_uuid
    default_process_track.track_descriptor.process.pid = os.getpid()
    default_process_track.track_descriptor.process.process_name = "perf_data_merge"
    root.packet.append(default_process_track)

    # Using a thread track can make sub tracks ahead of others
    thread_track = pftrace.TracePacket()
    default_thread_track_uuid = uuid64()
    thread_track.track_descriptor.uuid = default_thread_track_uuid
    thread_track.track_descriptor.parent_uuid = default_process_track_uuid
    thread_track.track_descriptor.thread.pid = os.getpid()
    thread_track.track_descriptor.thread.tid = os.getpid()
    thread_track.track_descriptor.thread.thread_name = "perf_data_merge_main"
    root.packet.append(thread_track)

    # Deserialize the json
    data = json.loads(json_str)

    group_uuids = {}
    start_stamp = -1

    for track_data in data:
        track_name = track_data["name"]
        track_type = track_data["type"]
        track_values = track_data["value"]
        track_timestamps = track_data["timestamp"]
        # track_group_uuid = track_data["group_uuid"]

        if len(track_timestamps) != 0:
            if start_stamp == -1 or start_stamp > track_timestamps[0]:
                start_stamp = track_timestamps[0]

        if track_type == "COUNTER":
            if track_data.get("group", None) is None:
                # write_counter_track(root, track_name, track_values, track_timestamps, default_thread_track_uuid)
                write_counter_track(root, track_name, track_values, track_timestamps, 0)
            else:
                group_name = track_data["group"]
                if group_name not in group_uuids:
                    group_track = pftrace.TracePacket()
                    group_track_uuid = uuid64()
                    group_track.track_descriptor.uuid = group_track_uuid
                    group_track.track_descriptor.process.pid = group_track_uuid >> 48
                    group_track.track_descriptor.process.process_name = group_name
                    root.packet.append(group_track)
                    group_uuids[group_name] = group_track_uuid
                write_counter_track(
                    root,
                    track_name,
                    track_values,
                    track_timestamps,
                    group_uuids[group_name],
                )

        elif track_type == "EVENT":
            track_events = track_data["event"]
            track_log = track_data.get("log", None)
            flows = track_data.get("flow", None)
            if track_data.get("group", None) is None:
                # write_instant_track(root, track_name, track_events, track_timestamps, default_thread_track_uuid, log=track_values)
                write_instant_track(
                    root,
                    track_name,
                    track_events,
                    track_timestamps,
                    0,
                    flows,
                    values=track_values,
                    logs=track_log,
                )
            else:
                group_name = track_data["group"]
                if group_name not in group_uuids:
                    group_track = pftrace.TracePacket()
                    group_track_uuid = uuid64()
                    group_track.track_descriptor.uuid = group_track_uuid
                    group_track.track_descriptor.process.pid = group_track_uuid >> 48
                    group_track.track_descriptor.process.process_name = group_name
                    root.packet.append(group_track)
                    group_uuids[group_name] = group_track_uuid
                write_instant_track(
                    root,
                    track_name,
                    track_events,
                    track_timestamps,
                    group_uuids[group_name],
                    flows,
                    values=track_values,
                    logs=track_log,
                )
        elif track_type == "SLICE":
            track_end_timestamps = track_data["timestamp_end"]
            track_events = track_data["event"]
            track_log = track_data.get("log", None)
            flows = track_data.get("flow", None)
            if track_data.get("group", None) is None:
                write_slice_track(
                    root,
                    track_name,
                    track_events,
                    track_timestamps,
                    track_end_timestamps,
                    0,
                    flows,
                    values=track_values,
                    logs=track_log,
                )
            else:
                group_name = track_data["group"]
                if group_name not in group_uuids:
                    group_track = pftrace.TracePacket()
                    group_track_uuid = uuid64()
                    group_track.track_descriptor.uuid = group_track_uuid
                    group_track.track_descriptor.process.pid = group_track_uuid >> 48
                    group_track.track_descriptor.process.process_name = group_name
                    root.packet.append(group_track)
                    group_uuids[group_name] = group_track_uuid
                write_slice_track(
                    root,
                    track_name,
                    track_events,
                    track_timestamps,
                    track_end_timestamps,
                    group_uuids[group_name],
                    flows,
                    values=track_values,
                    logs=track_log,
                )
        elif track_type == "LOG":
            tmp_stamp = write_log_track(root, track_name, track_values)
            if start_stamp == -1 or start_stamp > tmp_stamp:
                start_stamp = tmp_stamp

    packet = pftrace.TracePacket()
    packet.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.trusted_packet_sequence_id = trusted_packet_sequence_id
    packet.clock_snapshot.primary_trace_clock = (
        pftrace.BuiltinClock.BUILTIN_CLOCK_BOOTTIME
    )
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 1
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 2
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 3
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 4
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 5
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    clock = pftrace.ClockSnapshot.Clock()
    clock.clock_id = 6
    clock.timestamp = int((start_stamp + 3600 * 8) * 1000000000)
    packet.clock_snapshot.clocks.append(clock)
    root.packet.append(packet)

    return root


def main(args=None):
    if len(args) != 2:
        sys.stderr.write("Usage: perf_data_merge.py <output_file>\n")
        sys.stderr.write("       or python -m perf_data_merge <output_file>\n")
        sys.exit(1)

    # Read input from stdin
    json_data = ""
    for line in sys.stdin:
        json_data += line
    # print(json_data)
    perfetto_trace = merge(json_data)
    print(perfetto_trace)

    with open(args[1], "wb") as f:
        f.write(perfetto_trace.SerializeToString())

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
