from os import devnull, kill
from signal import signal, SIGTERM, SIGINT
from socket import socket, SOCK_STREAM, AF_INET, SHUT_RDWR
from subprocess import Popen
from time import sleep

from core import common, logger


def start():
    logger.info("starting recorder[pid=%s]" % common.PID)
    config = common.load_config()
    segment_dir = "%s/%s" % (config["output"], common.PROCESS_NAME)
    config = config["cameras"][common.PROCESS_NAME]
    logger.info("saving segments of camera %s in directory %s" % (common.PROCESS_NAME, segment_dir))
    duration = int(config["duration"])
    command = ["ffmpeg", "-rtsp_transport", "tcp", "-i", config["rtsp.url"], "-an", "-sn", "-b:v", "132k", "-bufsize",
               "132k", "-c:v", "copy", "-r", str(config["fps"]), "-bsf:v", "h264_mp4toannexb", "-map", "0", "-shortest",
               "-strftime", "1", "-f", "segment", "-segment_time", str(duration), "-segment_format", "mp4",
               "%s/%s-%s.mp4" % (segment_dir, common.PROCESS_NAME, "%Y%m%d%H%M%S")]
    url = (config["rtsp.ip"], config["rtsp.port"])
    del config, segment_dir
    process = None
    try:
        while 1:
            if not is_reachable(url):
                logger.warning("destination %s:%s is not reachable" % (url[0], str(url[1])))
                logger.info("waiting for camera[%s:%s] to be available" % (url[0], str(url[1])))
                while not is_reachable(url):
                    sleep(1)

                close(process)
                process = None

            if not is_running(process):
                close(process)
                process = launch(command)
            else:
                sleep(duration)
    finally:
        logger.info("stopping recorder[pid=%s]" % common.PID)
        close(process)


def launch(command):
    attempts = 0
    logger.info("launching recorder[%s]" % command)
    while 1:
        try:
            with open(devnull, "wb") as dev_null:
                process = Popen(command, stdout=dev_null, stderr=dev_null)

            logger.info("process[%s] launched" % str(process.pid))

            return process
        except Exception as e:
            if attempts >= 3:
                logger.error("max of 3 launching attempts was reached when launching recorder process: %s" % e)
                raise

            logger.warning("error launching recorder process: %s" % e)
            attempts += 1
            logger.warning("reattempting launch (%s of 3)" % attempts)
            sleep(1)


def is_running(process):
    try:
        return process.returncode is None and process.poll() is None
    except:
        return 0


def is_reachable(url):
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(1)
        s.connect(url)
        s.shutdown(SHUT_RDWR)

        return 1
    except:
        return 0


def close(process):
    if not process:
        return

    try:
        process.terminate()
        process.wait(3)
        if process.returncode is None:
            kill(process.pid, 9)
    except:
        kill(process.pid, 9)


def main():
    signal(SIGTERM, common.stop)
    signal(SIGINT, common.stop)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during recorder execution: %s" % e)
