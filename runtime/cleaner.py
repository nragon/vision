from datetime import datetime, timedelta
from os import remove
from os.path import getmtime, join
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger, storage
from core.common import list_abs

DELETED_TOTAL = "cleaner.deleted.total"
DELETED_SINCE_START = "cleaner.deleted.sinceStart"
CLEANER_STATUS = "cleaner.status"
running = False


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
    with storage.get_connection() as conn:
        storage.put(conn, CLEANER_STATUS, "Running")
        try:
            loop(conn, cameras, loop_interval)
        finally:
            storage.put(conn, CLEANER_STATUS, "Not running")
            logger.info("stopping cleaner[pid=%s]" % common.PID)


def loop(conn, cameras, loop_interval):
    inc = storage.inc
    delete_total = storage.get_int(conn, DELETED_TOTAL)
    if not delete_total:
        delete_total = 0

    delete_since_start = 0
    global running
    running = True
    now = datetime.now
    while running:
        for camera, config in cameras.items():
            segment_dir = config["segment_dir"]
            try:
                cleaned = clean(segment_dir,
                                (now() - timedelta(seconds=config["keep"] + config["duration"])).timestamp())
                if cleaned > 0:
                    delete_total = inc(conn, DELETED_TOTAL, delete_total, cleaned)
                    delete_since_start = inc(conn, DELETED_SINCE_START, delete_since_start, cleaned)
            except Exception as e:
                logger.error("unable to clean segments from %s: %s" % (segment_dir, e))

        sleep(loop_interval)


def clean(segment_dir, threshold):
    cleaned = 0
    for segment in sorted(list_abs(segment_dir), key=getmtime):
        if getmtime(segment) >= threshold:
            break

        try:
            logger.warning("segment %s reached retention period" % segment)
            remove(segment)
            logger.info("segment %s was removed" % segment)
            cleaned += 1
        except Exception as e:
            logger.error("unable to clean segment %s: %s" % (segment, e))

    return cleaned


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
        logger.error("An error occurred during cleaner execution: %s" % e)
