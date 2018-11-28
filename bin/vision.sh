#!/usr/bin/env bash

set -o posix

if [[ -z "$VISION_HOME" ]]; then
  export VISION_HOME="$(cd "`dirname "$0"`"/..; pwd)"
fi

finish() {
  pkill -9 -P $$
}

trap finish EXIT

if [[ ! -e "${VISION_HOME}/log/vision.log" ]]; then
    mkdir "${VISION_HOME}/log"
    touch "${VISION_HOME}/log/vision.log"
fi

sudo -E "${VISION_HOME}/bin/python3" -u "${VISION_HOME}/vision.py" >> "${VISION_HOME}/log/vision.log" 2>&1
wait $!