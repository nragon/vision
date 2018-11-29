from datetime import datetime, timedelta
from os import remove
from os.path import getmtime, join
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger
from core.common import list_abs


def start():
    logger.info("starting cleaner[pid=%s]" % common.PID)
    config = common.load_config()
    output = config["output"]
    cameras = config["cameras"]
    loop_interval = 3600
    for camera, config in cameras.items():
        config["segment_dir"] = join(output, camera)
        loop_interval = min(loop_interval, int(config["keep"]))

    del config, output
    now = datetime.now
    try:
        while 1:
            for camera, config in cameras.items():
                segment_dir = config["segment_dir"]
                try:
                    clean(segment_dir, (now() - timedelta(seconds=config["keep"] + config["duration"])).timestamp())
                except Exception as e:
                    logger.error("unable to clean segments from %s: %s" % (segment_dir, e))

            sleep(loop_interval)
    finally:
        logger.info("stopping cleaner[pid=%s]" % common.PID)


def clean(segment_dir, threshold):
    for segment in sorted(list_abs(segment_dir), key=getmtime):
        if getmtime(segment) >= threshold:
            break

        try:
            logger.warning("segment %s reached retention period" % segment)
            remove(segment)
            logger.info("segment %s was removed" % segment)
        except Exception as e:
            logger.error("unable to clean segment %s: %s" % (segment, e))


def main():
    signal(SIGTERM, common.stop)
    signal(SIGINT, common.stop)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during cleaner execution: %s" % e)
