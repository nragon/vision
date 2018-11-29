import sys
from multiprocessing import current_process
from os import environ, getpid, listdir
from os.path import join

from yaml import load

PID = getpid()
PROCESS_NAME = current_process().name


def load_config():
    return load(open("%s/config/vision-config.yaml" % environ["VISION_HOME"]))


def stop(signum=None, frame=None):
    sys.exit(0)


def list_abs(base_dir):
    def to_absolute(filename):
        return join(base_dir, filename)

    return map(to_absolute, listdir(base_dir))
