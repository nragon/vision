from datetime import datetime, timedelta
from genericpath import exists
from os import getcwd, mkdir, utime, listdir, rmdir, remove, environ
from os.path import join
from shutil import rmtree
from threading import Thread
from time import mktime, sleep
from unittest import TestCase

environ["VISION_HOME"] = join(getcwd(), "cleaner")
from core import storage
from runtime import cleaner

DATA_DIR = "%s/cleanerdata" % getcwd()


class CleanerTestCase(TestCase):
    def setUp(self):
        storage.setup()
        if not exists(DATA_DIR):
            mkdir(DATA_DIR)
        # create a file and change modified date to 3 days after current date
        self.oldest_path = join(DATA_DIR, "oldest.mp4")
        with open(self.oldest_path, "w"):
            pass
        minus_3_days = datetime.now() - timedelta(days=3)
        minus_3_days = mktime(minus_3_days.timetuple())
        utime(self.oldest_path, (minus_3_days, minus_3_days))
        # create a file
        self.newest_path = join(DATA_DIR, "newest.mp4")
        with open(self.newest_path, "w"):
            pass
        # create a file
        self.newest2_path = join(DATA_DIR, "newest2.mp4")
        with open(self.newest2_path, "w"):
            pass

    def tearDown(self):
        rmtree(DATA_DIR)
        rmtree(environ["VISION_HOME"])


class Cleaner(CleanerTestCase):
    def test_threshold_not_reached(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)
        cleaner.clean(DATA_DIR, (datetime.now() - timedelta(days=4)).timestamp())
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)

    def test_threshold_reached_oldest(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)
        cleaner.clean(DATA_DIR, (datetime.now() - timedelta(days=2)).timestamp())
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)

    def test_threshold_not_reached_oldest_multiple(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)
        # change newest_path and newest2_path time to -3 days
        minus_3_days = datetime.now() - timedelta(days=3)
        minus_3_days = mktime(minus_3_days.timetuple())
        utime(self.newest_path, (minus_3_days, minus_3_days))
        utime(self.newest2_path, (minus_3_days, minus_3_days))
        # wont delete
        cleaner.clean(DATA_DIR, (datetime.now() - timedelta(days=4)).timestamp())
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)

    def test_threshold_reached_oldest_multiple(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)
        # change newest_path and newest2_path time to -3 days
        minus_3_days = datetime.now() - timedelta(days=3)
        minus_3_days = mktime(minus_3_days.timetuple())
        utime(self.newest_path, (minus_3_days, minus_3_days))
        utime(self.newest2_path, (minus_3_days, minus_3_days))
        # wont delete
        cleaner.clean(DATA_DIR, (datetime.now() - timedelta(days=2)).timestamp())
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 0)

    def test_loop(self):
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 3)

        def loop(cameras, loop_interval):
            with storage.get_connection() as conn:
                cleaner.loop(conn, cameras, loop_interval)

        thread = Thread(target=loop, args=({"front": {"segment_dir": DATA_DIR, "keep": 172800, "duration": 30}},
                                           1,))
        thread.daemon = True
        thread.start()
        sleep(1)
        while 1:
            file_count = len(listdir(DATA_DIR))
            if file_count == 2:
                break

            sleep(1)

        self.assertEqual(file_count, 2)
        cleaner.stop()
        thread.join()
        self.assertEqual(storage.get_int(storage.get_connection(), cleaner.DELETED_TOTAL), 1)
        self.assertEqual(storage.get_int(storage.get_connection(), cleaner.DELETED_SINCE_START), 1)
        thread = Thread(target=loop, args=({"front": {"segment_dir": DATA_DIR, "keep": 172800, "duration": 30}},
                                           1,))
        thread.daemon = True
        thread.start()
        file_count = len(listdir(DATA_DIR))
        self.assertEqual(file_count, 2)
        minus_3_days = datetime.now() - timedelta(days=3)
        minus_3_days = mktime(minus_3_days.timetuple())
        utime(self.newest_path, (minus_3_days, minus_3_days))
        utime(self.newest2_path, (minus_3_days, minus_3_days))
        while 1:
            file_count = len(listdir(DATA_DIR))
            if file_count == 0:
                break

            sleep(1)

        self.assertEqual(file_count, 0)
        cleaner.stop()
        thread.join()
        self.assertEqual(storage.get_int(storage.get_connection(), cleaner.DELETED_TOTAL), 3)
        self.assertEqual(storage.get_int(storage.get_connection(), cleaner.DELETED_SINCE_START), 2)
