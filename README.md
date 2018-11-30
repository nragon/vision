# Welcome to Vision
[Vision](https://github.com/nragon/vision) is an open source nvr system. It records rtsp stream and manages space from ip cameras. Currently no decoding and encoding is made.

# Table of Contents
- [Installation](#installation)
  - [Requirements](#requirements)
- [Configuration](#installation)
- [Contributing](#contributing)
- [Licensing](#licensing)
# Installation
Install the requirements
````
python3 -m pip install -r requirements.txt
```` 

Create a system service to initialize vision at boot
````
[Unit]
Description=vision service
After=network.target

[Service]
Type=simple
ExecStart=<pathtobin>/vision.sh
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
````
## Requirements
[FFmpeg](https://www.ffmpeg.org/) is required in order to execute vision

# Configuration
You can find a set of properties in a yaml file inside [config](config) directory that can be tuned and configured according with you own settings

## General configuration

Configuration | Definition
--------------| ----------
output | Directory where records will be stored
filesystem.threshold | Max Filesystem usage percentage before starting deleting old records
cameras | List of ip cameras

## Camera configuration
Camera configurations can be found under cameras tag

Configuration | Definition
--------------| ----------
rtsp.ip | RTSP ip address
rtsp.port |  RTSP port
rtsp.url | RTSP url
fps | FPS
keep | Number of seconds to keep before deleting old records
duration | Record duration, in seconds. Records are sliced according with this value

# Contributing
Pull requests and issues on [github](https://github.com/nragon/vision) are very grateful. Feel free to suggest any improvement.

# Licensing
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details