import os
from os import remove
from os.path import getmtime, join
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger, storage
from core.common import list_abs

WATCHER_DELETED_TOTAL = "watcherTotalDeleted"
WATCHER_DELETED_SINCE_START = "watcherDeletedSinceStart"
WATCHER_STATUS = "watcherStatus"

running = False


def start():
    logger.info("starting watcher[pid=%s]" % common.PID)
    config = common.load_config()
    output = config["output"]
    threshold = config["filesystem.threshold"]
    loop_interval = 10
    segment_dirs = []
    for camera, config in config["cameras"].items():
        segment_dirs.append(join(output, camera))
        loop_interval = min(loop_interval, int(config["duration"]))

    del config
    with storage.get_connection() as conn:
        storage.put(conn, WATCHER_STATUS, "Running")
        try:
            loop(conn, segment_dirs, loop_interval, output, threshold)
        finally:
            storage.put(conn, WATCHER_STATUS, "Not Running")
            logger.info("stopping watcher[pid=%s]" % common.PID)


def loop(conn, segment_dirs, loop_interval, output, threshold):
    inc = storage.inc
    delete_total = storage.get_int(conn, WATCHER_DELETED_TOTAL)
    if not delete_total:
        delete_total = 0

    delete_since_start = 0
    global running
    running = True
    while running:
        if usage_percentage(output) > threshold:
            logger.warning("filesystem has reached max size threshold")
            logger.info("cleaning old segments")
            for segment_dir in segment_dirs:
                if clean(segment_dir):
                    delete_total = inc(conn, WATCHER_DELETED_TOTAL, delete_total)
                    delete_since_start = inc(conn, WATCHER_DELETED_SINCE_START, delete_since_start)
                    if usage_percentage(output) < threshold:
                        break

        sleep(loop_interval)


def clean(segment_dir):
    try:
        segments = sorted(list_abs(segment_dir), key=getmtime)
        if segments:
            segment = segments[0]
            logger.info("cleaning oldest segment[%s] to free space" % segment)
            remove(segment)
            logger.info("segment %s removed" % segment)

            return True
    except Exception as e:
        logger.error("unable to remove segments from %s: %s" % (segment_dir, e))

        return False


if hasattr(os, "statvfs"):
    from os import statvfs


    def usage_percentage(path):
        st = statvfs(path)
        f_b = st.f_blocks
        f_f = st.f_frsize

        return (((f_b - st.f_bfree) * f_f) * 100) / (f_b * f_f)
elif os.name == "nt":
    from nt import _getdiskusage


    def usage_percentage(path):
        total, free = _getdiskusage(path)

        return (total - free) * 100 / total


def stop():
    global running
    running = False


def handle_signal(signum=None, frame=None):
    stop()
    common.stop()


def main():
    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during watcher execution: %s" % e)
