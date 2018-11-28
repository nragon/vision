from datetime import datetime, timedelta
from os import listdir, remove
from os.path import getctime, getmtime, join
from signal import signal, SIGTERM, SIGINT
from sys import maxsize
from time import sleep

from core import common, logger


def start():
    logger.info("starting cleaner[pid=%s]" % common.PID)
    config = common.load_config()
    output = config["output"]
    cameras = config["cameras"]
    loop_interval = maxsize
    for camera, config in cameras.items():
        config["segment_dir"] = "%s/%s" % (output, camera)
        loop_interval = min(loop_interval, int(config["keep"]))

    loop_interval >>= 2
    del config, output
    now = datetime.now
    try:
        while 1:
            for camera, config in cameras.items():
                segment_dir = config["segment_dir"]
                threshold = (now() - timedelta(seconds=config["keep"] + config["duration"])).timestamp()
                try:
                    segments = []
                    for segment in listdir(segment_dir):
                        segments.append(join(segment_dir, segment))

                    if len(segments) > 1:
                        for segment in sorted(segments, key=getmtime):
                            if getctime(segment) >= threshold:
                                break

                            try:
                                logger.info("segment %s reached retention period" % segment)
                                remove(segment)
                                logger.info("segment %s was removed" % segment)
                            except Exception as e:
                                logger.info("unable to clean segment %s: %s" % (segment, e))
                except Exception as e:
                    logger.info("unable to clean segments from %s: %s" % (segment_dir, e))

            sleep(loop_interval)
    finally:
        logger.info("stopping cleaner[pid=%s]" % common.PID)


def main():
    signal(SIGTERM, common.stop)
    signal(SIGINT, common.stop)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during cleaner execution: %s" % e)
