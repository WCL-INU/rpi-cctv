#!/bin/bash

DATE=$(date +"%Y%m%d_%H%M%S")
HOSTNAME=$(hostname)

rpicam-vid -t 0 --inline -n \
    --segment 120000 \
    --bitrate 10000000 \
    --profile high \
    --framerate 30 \
    --width 1640 \
    --height 1232 \
    -o /home/pi/cctv_buffer/${HOSTNAME}_${DATE}_%05d.h264
