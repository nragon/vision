import os
from os import listdir, remove
from os.path import getmtime, join
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger


def start():
    logger.info("starting watcher[pid=%s]" % common.PID)
    config = common.load_config()
    output = config["output"]
    threshold = config["filesystem.threshold"]
    loop_interval = 10
    camera_dirs = []
    for camera, config in config["cameras"].items():
        camera_dirs.append("%s/%s" % (output, camera))
        loop_interval = min(loop_interval, int(config["duration"]))

    del config
    try:
        while 1:
            if free_percentage(output) >= threshold:
                logger.warning("filesystem has reached max size threshold")
                logger.info("cleaning old segments")
                for segment_dir in camera_dirs:
                    try:
                        segments = []
                        for segment in listdir(segment_dir):
                            segments.append(join(segment_dir, segment))

                        if len(segments) > 1:
                            segment = sorted(segments, key=getmtime)[0]
                            logger.info("cleaning oldest segment[%s] to free space" % segment)
                            remove(segment)
                            logger.info("segment %s removed" % segment)

                            if free_percentage(output) < threshold:
                                break
                    except Exception as e:
                        logger.info("unable to remove segments from %s: %s" % (segment_dir, e))
            else:
                sleep(loop_interval)
    finally:
        logger.info("stopping watcher[pid=%s]" % common.PID)


if hasattr(os, "statvfs"):
    from os import statvfs


    def free_percentage(path):
        st = statvfs(path)
        f_b = st.f_blocks
        f_f = st.f_frsize

        return (((f_b - st.f_bfree) * f_f) * 100) / (f_b * f_f)
elif os.name == "nt":
    from nt import _getdiskusage


    def free_percentage(path):
        total, free = _getdiskusage(path)

        return free * 100 / total


def main():
    signal(SIGTERM, common.stop)
    signal(SIGINT, common.stop)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during watcher execution: %s" % e)
