from datetime import datetime, timedelta
from genericpath import exists
from os import getcwd, mkdir, utime, listdir, rmdir, remove
from os.path import join
from shutil import rmtree, disk_usage
from time import mktime
from unittest import TestCase

from runtime import watcher

DATA_DIR = "%s/watcherdata" % getcwd()


class WatcherTestCase(TestCase):
    def setUp(self):
        if not exists(DATA_DIR):
            mkdir(DATA_DIR)
        # create a file
        self.oldest_path = join(DATA_DIR, "oldest.mp4")
        with open(self.oldest_path, "wb"):
            pass
        # create a file
        self.newest_path = join(DATA_DIR, "newest.mp4")
        with open(self.newest_path, "w"):
            pass

        self.initial_free = watcher.free_percentage(DATA_DIR)

    def tearDown(self):
        rmtree(DATA_DIR)


class Watcher(WatcherTestCase):
    def test_threshold_not_reached(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)
        if watcher.free_percentage(DATA_DIR) < self.initial_free:
            watcher.clean(DATA_DIR)

        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)

    def test_threshold_reached(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)
        total, _, _ = disk_usage(DATA_DIR)
        oldest_path_size = int(total / 100)
        with open(self.oldest_path, "wb") as oldest:
            oldest.seek(oldest_path_size - 1)
            oldest.write(b"\0")

        minus_3_days = datetime.now() - timedelta(seconds=60)
        minus_3_days = mktime(minus_3_days.timetuple())
        utime(self.oldest_path, (minus_3_days, minus_3_days))
        if watcher.free_percentage(DATA_DIR) < self.initial_free:
            watcher.clean(DATA_DIR)

        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 1)
