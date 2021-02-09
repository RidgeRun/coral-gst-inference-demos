# Load settings
source config.txt

# Create pipelines
echo "Creating camera pipeline"
gstd-client pipeline_create cam_pipe v4l2src device=$CAMERA \
! video/x-raw, width=$CAMERA_WIDTH, height=$CAMERA_HEIGHT, \
framerate=10/1, format=$CAMERA_FORMAT ! videoconvert \
! video/x-raw, format=Y42B \
! interpipesink name=cam_pipe_src sync=false async=false

echo "Creating input stream pipeline"
gstd-client pipeline_create in_stream_pipe rtspsrc \
location=$RTSP_URI ! rtph264depay ! h264parse ! avdec_h264 ! queue \
! interpipesink name=in_stream_pipe_src sync=false async=false

echo -e "Creating inference pipeline with model: $MODEL_LOCATION"
gstd-client pipeline_create inference_pipe interpipesrc name=inf_sink \
listen-to=cam_pipe_src ! videoconvert ! tee name=t t. ! videoscale ! \
queue ! net.sink_model t. ! queue ! net.sink_bypass \
tinyyolov3 name=net model-location=$MODEL_LOCATION backend=tensorflow \
backend::input-layer=$INPUT_LAYER backend::output-layer=$OUTPUT_LAYER \
net.src_bypass ! detectionoverlay labels="$(cat $LABELS)" font-scale=1 thickness=2 \
! videoconvert ! interpipesink name=inf_src sync=false async=false

echo "Creating display pipeline"
gstd-client pipeline_create show_pipe interpipesrc name=show_sink listen-to=inf_src \
! videoconvert ! xvimagesink sync=false async=false

echo "Creating record pipeline"
gstd-client pipeline_create record_pipe interpipesrc name=record_sink listen-to=inf_src \
! videoconvert ! x264enc ! h264parse \
! qtmux ! filesink location=$OUTPUT_FILE

echo "Creating streaming pipeline"
gstd-client pipeline_create stream_pipe interpipesrc name=stream_sink listen-to=inf_src \
! videoconvert ! x264enc tune=zerolatency ! h264parse \
! mpegtsmux ! udpsink host=$HOST port=$PORT sync=false async=false

# Start all pipelines
echo "Starting pipelines"
gstd-client pipeline_play cam_pipe
gstd-client pipeline_play in_stream_pipe
gstd-client pipeline_play inference_pipe

echo "Play show"
gstd-client pipeline_play show_pipe
sleep 1 # Wait for pipeline initialization
echo "Play record"
gstd-client pipeline_play record_pipe
echo "Play stream"
gstd-client pipeline_play stream_pipe

save_recording (){
    gstd-client event_eos record_pipe
    gstd-client bus_filter record_pipe eos
    gstd-client bus_read record_pipe
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

switch_source (){
    if [[ $1 == *"stream"* ]] ; then
        gstd-client element_set inference_pipe inf_sink listen-to in_stream_pipe_src
    elif [[ $1 == *"camera"* ]] ; then
        gstd-client element_set inference_pipe inf_sink listen-to cam_pipe_src
    fi
}

while true; do
    read -p "> " usr_input

    if [[ $usr_input == *"exit"* ]] ; then
        save_recording
        free_pipelines
        exit
    elif [[ $usr_input == *"stream"* || $usr_input == *"camera"* ]] ; then
        switch_source $usr_input
    fi
done