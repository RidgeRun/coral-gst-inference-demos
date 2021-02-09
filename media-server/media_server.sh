# Load settings
source config.txt

# Create pipelines
echo "Creating camera pipeline"
gstd-client pipeline_create cam_pipe v4l2src device=$CAMERA \
! "video/x-raw, width=1280, height=720" \
! interpipesink name=cam_pipe_src sync=false async=false

echo "Creating display pipeline"
gstd-client pipeline_create show_pipe interpipesrc name=show_sink listen-to=cam_pipe_src \
! videoconvert ! xvimagesink sync=false async=false

echo "Creating record pipeline"
gstd-client pipeline_create record_pipe interpipesrc name=record_sink listen-to=cam_pipe_src \
! videoconvert ! x264enc ! h264parse \
! qtmux ! filesink location=$OUTPUT_FILE

# Start all pipelines
echo "Starting pipelines"
gstd-client pipeline_play cam_pipe

echo "Play show"
gstd-client pipeline_play show_pipe
sleep 1 # Wait for pipeline initialization
echo "Play record"
gstd-client pipeline_play record_pipe


save_recording (){
    gstd-client event_eos record_pipe
    gstd-client bus_filter record_pipe eos
    gstd-client bus_read record_pipe
}

free_pipelines (){
    gstd-client pipeline_stop cam_pipe
    gstd-client pipeline_stop record_pipe
    gstd-client pipeline_stop show_pipe

    gstd-client pipeline_delete cam_pipe
    gstd-client pipeline_delete record_pipe
    gstd-client pipeline_delete show_pipe
}

while true; do
    read -p "> " usr_input

    if [[ $usr_input == *"exit"* ]] ; then
        save_recording
        free_pipelines
        exit
    fi
done