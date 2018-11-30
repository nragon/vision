from datetime import datetime, timedelta
from genericpath import exists
from os import getcwd, mkdir, utime, listdir, rmdir, remove, environ
from os.path import join
from shutil import rmtree, disk_usage
from threading import Thread
from time import mktime, sleep
from unittest import TestCase

environ["VISION_HOME"] = join(getcwd(), "watcher")
from core import storage
from runtime import watcher

DATA_DIR = join(getcwd(), "watcherdata")


class WatcherTestCase(TestCase):
    def setUp(self):
        storage.setup()
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

        self.initial_free = watcher.usage_percentage(DATA_DIR)

    def tearDown(self):
        rmtree(DATA_DIR)
        rmtree(environ["VISION_HOME"])


class Watcher(WatcherTestCase):
    def test_threshold_not_reached(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)
        if watcher.usage_percentage(DATA_DIR) > self.initial_free:
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
        if watcher.usage_percentage(DATA_DIR) > self.initial_free:
            watcher.clean(DATA_DIR)

        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 1)

    def test_loop(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)

        def loop(segment_dirs, loop_interval, output, threshold):
            with storage.get_connection() as conn:
                watcher.loop(conn, segment_dirs, loop_interval, output, threshold)

        thread = Thread(target=loop, args=([DATA_DIR], 1, DATA_DIR, self.initial_free,))
        thread.daemon = True
        thread.start()
        sleep(3)
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)
        total, _, _ = disk_usage(DATA_DIR)
        oldest_path_size = int(total / 50)
        with open(self.newest_path, "wb") as oldest:
            oldest.seek(oldest_path_size - 1)
            oldest.write(b"\0")

        while 1:
            file_count = len(listdir(DATA_DIR))
            if file_count == 1:
                break

            sleep(1)

        self.assertEqual(file_count, 1)
        watcher.stop()
        thread.join()
        self.assertEqual(storage.get_int(storage.get_connection(), watcher.WATCHER_DELETED_TOTAL), 1)
        self.assertEqual(storage.get_int(storage.get_connection(), watcher.WATCHER_DELETED_SINCE_START), 1)
        thread = Thread(target=loop, args=([DATA_DIR], 1, DATA_DIR, self.initial_free,))
        thread.daemon = True
        thread.start()
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 1)
        with open(self.newest_path, "wb") as oldest:
            oldest.seek(oldest_path_size - 1)
            oldest.write(b"\0")

        while 1:
            file_count = len(listdir(DATA_DIR))
            if file_count == 0:
                break

            sleep(1)

        self.assertEqual(file_count, 0)
        watcher.stop()
        thread.join()
        self.assertEqual(storage.get_int(storage.get_connection(), watcher.WATCHER_DELETED_TOTAL), 2)
        self.assertEqual(storage.get_int(storage.get_connection(), watcher.WATCHER_DELETED_SINCE_START), 1)
