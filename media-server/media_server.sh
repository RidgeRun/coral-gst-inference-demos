#!/usr/bin/env bash

# Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Fabian Solano <fabian.solano@ridgerun.com>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.


# Load settings
CONFIG_FILE=${1?"Usage: ./media_server.sh [CONFIG_FILE]"}
source $CONFIG_FILE

gstd_not_found_msg="Could not connect to localhost: Connection refused"
check_gstd=$(gstd-client list_pipelines  2>&1)

# Verify if gstd is reachable
if [[ $check_gstd == $gstd_not_found_msg ]] ; then
    echo "Could not connect to gstd. Please check gstd is up and running."
    exit 1
fi

need_save_recording="no"

# Create pipelines
echo "Initializing camera capture"
gstd-client pipeline_create cam_pipe v4l2src device=$CAMERA_DEVICE \
! video/x-raw, width=$CAMERA_DEVICE_WIDTH, height=$CAMERA_DEVICE_HEIGHT \
! videoscale ! videoconvert ! video/x-raw,width=640,height=480,format=I420 \
! interpipesink name=cam_pipe_src sync=false

echo "Initializing RTSP streaming capture"
gstd-client pipeline_create in_stream_pipe rtspsrc \
location=$INPUT_RTSP_URI ! decodebin ! queue \
! videoscale ! videoconvert ! video/x-raw,width=640,height=480,format=I420 \
! interpipesink name=in_stream_pipe_src sync=false

echo "Initializing inference capture with model: $MODEL_LOCATION"
gstd-client pipeline_create inference_pipe interpipesrc name=inf_input \
listen-to=cam_pipe_src ! inferencebin arch=$ARCH backend=coral \
model-location=$MODEL_LOCATION input-layer=$INPUT_LAYER output-layer=$OUTPUT_LAYER \
labels="\"$(awk '{$1=""; printf "\%s\;",$0}' $LABELS)\"" overlay=true ! \
videoconvert ! interpipesink name=inf_src sync=false

echo "Creating display pipeline"
gstd-client pipeline_create show_pipe interpipesrc name=show_sink listen-to=inf_src \
! videoconvert ! autovideosink sync=false

echo "Creating record pipeline"
gstd-client pipeline_create record_pipe interpipesrc name=record_sink listen-to=inf_src \
! videoconvert ! x264enc tune=zerolatency speed-preset=ultrafast ! h264parse \
! qtmux ! filesink location=$OUTPUT_FILE

echo "Creating streaming pipeline"
gstd-client pipeline_create stream_pipe interpipesrc name=stream_sink listen-to=inf_src \
! videoconvert ! x264enc tune=zerolatency key-int-max=30 speed-preset=ultrafast \
! h264parse ! mpegtsmux ! udpsink host=$OUTPUT_HOST port=$OUTPUT_PORT sync=false

# Start all capture instances
gstd-client pipeline_play cam_pipe
gstd-client pipeline_play in_stream_pipe
gstd-client pipeline_play inference_pipe

echo "Start live preview"
gstd-client pipeline_play show_pipe
sleep 1 # Wait for pipeline initialization

save_recording (){
    if [[ $need_save_recording == "yes" ]] ; then
        gstd-client event_eos record_pipe
        gstd-client bus_filter record_pipe eos
        gstd-client bus_read record_pipe
        gstd-client bus_timeout record_pipe 5000000000
        need_save_recording="no"
    fi
}

free_pipelines (){
    gstd-client pipeline_stop cam_pipe
    gstd-client pipeline_stop in_stream_pipe
    gstd-client pipeline_stop inference_pipe
    gstd-client pipeline_stop record_pipe
    gstd-client pipeline_stop show_pipe
    gstd-client pipeline_stop stream_pipe

    gstd-client pipeline_delete cam_pipe
    gstd-client pipeline_delete in_stream_pipe
    gstd-client pipeline_delete inference_pipe
    gstd-client pipeline_delete record_pipe
    gstd-client pipeline_delete show_pipe
    gstd-client pipeline_delete stream_pipe
}

trap_sigint() {
    save_recording
    free_pipelines
    echo "Closing media server"
    exit
}

trap trap_sigint SIGINT

while true; do
    read -p "> " usr_input

    if [[ $usr_input == *"exit"* ]] ; then
        save_recording
        free_pipelines
        exit
    elif [[ $usr_input == *"help"* ]] ; then
cat << EOF
exit: exit the media server and save recording
help: shows this message
stream: changes current output to stream source
camera: changes current output to camera source
start_streaming: start the output RTSP streaming
start_recording: start the mp4 file recording
stop_streaming: stops the output RTSP streaming
stop_recording: stops the mp4 file recording
EOF
    elif [[ $usr_input == "stream" ]] ; then
        gstd-client element_set inference_pipe inf_input listen-to in_stream_pipe_src
    elif [[ $usr_input == "camera" ]] ; then
        gstd-client element_set inference_pipe inf_input listen-to cam_pipe_src
    elif [[ $usr_input == "start_streaming" ]] ; then
        gstd-client pipeline_play stream_pipe
    elif [[ $usr_input == "start_recording" ]] ; then
        gstd-client pipeline_play record_pipe
        need_save_recording="yes"
    elif [[ $usr_input == "stop_streaming" ]] ; then
        gstd-client pipeline_stop stream_pipe
    elif [[ $usr_input == "stop_recording" ]] ; then
        save_recording
    fi
done
