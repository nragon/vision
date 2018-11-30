from json import dumps

import paho.mqtt.client as mqtt
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger, storage

REPORTER_CONFIG_TOPIC = "homeassistant/sensor/visionReporter-%s/config"
REPORTER_CONFIG_PAYLOAD = "{\"name\": \"visionReport-%(s)s\", \"state_topic\": \"homeassistant/sensor/visionReporter/state\", \"value_template\": \"{{ value_json.%(s)s }}\"}"
REPORTER_TOPIC = "homeassistant/sensor/visionReporter/state"
REPORTER_STATUS = "reporterStatus"
running = False


def start():
    logger.info("starting reported[pid=%s]" % common.PID)
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config.get("mqtt.user")
    pwd = config.get("mqtt.pass")
    del config
    with storage.get_connection() as conn:
        storage.put(conn, REPORTER_STATUS, "Running")
        try:
            loop(conn, broker, port, user, pwd)
        finally:
            storage.put(conn, REPORTER_STATUS, "Not Running")
            logger.info("stopping watcher[pid=%s]" % common.PID)


def loop(conn, broker, port, user, pwd):
    global running
    running = True
    client = connect(broker, port, user, pwd)
    register(client, conn)
    while running:
        if client.loop() > 0 and running:
            client = connect(broker, port, user, pwd)
        else:
            try:
                send_report(client, conn)
                sleep(30)
            except Exception as e:
                logger.error("failed to send report: %s" % e)


def register(client, conn):
    try:
        keys = storage.get_keys(conn)
        if not keys:
            return

        for key in keys:
            client.publish(REPORTER_CONFIG_TOPIC % key, REPORTER_CONFIG_PAYLOAD % {"s": key}, 1, True)
    except Exception as e:
        logger.error("failed to register auto discover: %s" % e)


def send_report(client, conn):
    result = storage.get_all(conn)
    if not result:
        return

    report = {}
    for record in result:
        report[record[0]] = record[1]

    client.publish(REPORTER_TOPIC, dumps(report), 1, True)


def connect(broker, port, user, pwd):
    while running:
        try:
            logger.info("connecting to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="visionreporter")
            if user and pwd:
                client.username_pw_set(user, pwd)

            client.connect(broker, port, 60)

            return client
        except Exception as e:
            logger.warning("unable to connect %s:%s: %s" % (broker, port, e))
            logger.warning("retrying in 10 seconds")
            sleep(10)


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
        logger.error("An error occurred during watcher execution: %s" % e)
