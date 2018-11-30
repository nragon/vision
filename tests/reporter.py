from os import environ, getcwd, mkdir
from os.path import join
from shutil import rmtree, copy
from unittest import TestCase

environ["VISION_HOME"] = join(getcwd(), "reporter")
from runtime import reporter
from core import storage, common


class Reporter(TestCase):
    def setUp(self):
        storage.setup()
        config_path = join(environ["VISION_HOME"], "config")
        mkdir(config_path)
        copy(join(environ["VISION_HOME"], "..", "..", "config", "vision-config.yaml"), config_path)

    def tearDown(self):
        rmtree(environ["VISION_HOME"])

    def test_register(self):
        config = common.load_config()
        with storage.get_connection() as conn:
            storage.put(conn, "reporterStatus", "Running")
            reporter.running = True
            client = reporter.connect(config["mqtt.broker"], config["mqtt.port"], config["mqtt.user"],
                                      config["mqtt.pass"])
            reporter.register(client, conn)

    def test_send(self):
        config = common.load_config()
        with storage.get_connection() as conn:
            storage.put(conn, "reporterStatus", "Running")
            reporter.running = True
            client = reporter.connect(config["mqtt.broker"], config["mqtt.port"], config["mqtt.user"],
                                      config["mqtt.pass"])
            reporter.send_report(client, conn)
