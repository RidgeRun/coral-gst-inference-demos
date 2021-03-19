"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

import ast
import configparser
from datetime import datetime
import json
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
import time

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GObject, GstVideo


GObject.threads_init()
Gst.init(None)

class GstDisplay(QWidget):
    """Widget to hold the gstreamer pipeline output"""

    def __init__(self, config_file_name):
        super(GstDisplay, self).__init__()
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Recording")
        self.layout.addWidget(self.label)

        self.STATE_CHANGE_TIMEOUT = 1000000000

        # Create config object and load file
        self.config = configparser.ConfigParser()
        self.config.read(config_file_name)
        self.parent = None

        # Get demo settings
        try:
            video_dev = self.config['DEMO_SETTINGS']['CAMERA_DEVICE']
            model = self.config['DEMO_SETTINGS']['MODEL_LOCATION']
            input_layer = self.config['DEMO_SETTINGS']['INPUT_LAYER']
            output_layer = self.config['DEMO_SETTINGS']['OUTPUT_LAYER']
            labels = self.parseLabels(self.config['DEMO_SETTINGS']['LABELS'])
            self.classes_id = ast.literal_eval(
                                self.config['DEMO_SETTINGS']['CLASSES_ID'])
            self.classes_probability = ast.literal_eval(
                                self.config['DEMO_SETTINGS']['CLASSES_MIN_PROBABILITY'])
            self.min_recording_time_seconds = int(self.config['DEMO_SETTINGS']\
                                ['MIN_RECORDING_TIME_IN_SECONDS'])
        except KeyError:
            print("Config file does not have correct format")
            exit(1)

        inference_pipe = "v4l2src device=%s ! videoscale ! videoconvert ! \
                          video/x-raw,width=640,height=480,format=I420 ! \
                          videoconvert ! tee name=t t. ! videoscale ! \
                          queue ! net.sink_model t. ! queue ! net.sink_bypass \
                          mobilenetv2 name=net labels=\"%s\" model-location=%s backend=coral \
                          backend::input-layer=%s backend::output-layer=%s \
                          net.src_bypass ! inferenceoverlay ! videoconvert ! \
                          clockoverlay valignment=bottom halignment=right \
                          shaded-background=true shading-value=255 ! \
                          interpipesink name=inference_src sync=false" % \
                          (video_dev,labels,model,input_layer,output_layer)

        display_pipe = "interpipesrc name=display_sink listen-to=inference_src ! \
                        videoconvert ! autovideosink name=videosink sync=false"

        # Create GStreamer pipelines
        self.inference_pipe = Gst.parse_launch(inference_pipe)
        self.display_pipe = Gst.parse_launch(display_pipe)

        if (not self.display_pipe or not self.inference_pipe):
            print("Unable to create pipeline", file=sys.stderr)
            sys.exit(1)

        # Setup pipeline signals and output window
        self.window_id = self.winId()
        self.setupPipeline()
        # Get imagesink Tracker element to further box appending
        self.videosink = self.display_pipe.get_by_name("videosink")
        self.playing = False
        self.recording = False
        self.togglePipelineState()
        self.net = self.inference_pipe.get_by_name("net")
        # Handle new prediction signal
        self.net.connect("new-inference-string", self.newPrediction)

    def parseLabels(self, file):
        """Parse labels to format supported by GstInference"""
        labels = ""

        with open(file) as fp:
            lines = fp.readlines()
            for line in lines:
                tmp = line.split("  ")[1].split("\n")[0]
                labels += tmp + ";"

        return labels

    def newPrediction(self, element, meta):
        data = json.loads(meta)

        # Parse class id from prediction
        class_id = data["classes"][0]["Class"]
        # Parse probability from prediction. Handle ',' float notation.
        class_probability = float(data["classes"][0]["Probability"].replace(",","."))

        # Detect require class ID and min probability threshold
        if(class_id in self.classes_id):
            min_prob = self.classes_probability[self.classes_id.index(class_id)]

            if(class_probability >= min_prob):
                if(self.recording == False):
                    print("Detected. Start recording.")
                    self.startRecordingPipeline()
                else:
                    self.start_recording_time = time.time()
        else:
            if(self.recording):
                self.stop_recording_time = time.time()
                diff = self.stop_recording_time - self.start_recording_time

                if(diff >= self.min_recording_time_seconds):
                    print("No detection. Stop recording.")
                    self.stopRecordingPipeline()

    def startRecordingPipeline(self):
        if(self.recording == False):
            self.parent.toggleRecording()
            self.recording = True

            # Get current time for filename
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y_%H_%M_%S")

            # Build filename with date format
            output_file = self.config['DEMO_SETTINGS']['OUTPUT_FILE']
            of = output_file.split(".")
            filename = of[0] + "_" + dt_string + "." + of[1]

            # Recording pipeline
            recording_pipe = "interpipesrc name=record_sink listen-to=inference_src \
                              format=3 ! videoconvert ! avenc_mpeg2video ! mpegtsmux ! \
                              filesink location=%s sync=false" % filename
            self.record_pipe = Gst.parse_launch(recording_pipe)

            self.record_pipe.set_state(Gst.State.PLAYING)
            self.record_pipe.get_state(self.STATE_CHANGE_TIMEOUT)

            # Record start time
            self.start_recording_time = time.time()

    def stopRecordingPipeline(self):
        if(self.recording == True):
            self.parent.toggleRecording()
            self.recording = False
            self.record_pipe.send_event(Gst.Event.new_eos())
            self.record_pipe.get_bus().timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
            self.record_pipe.set_state(Gst.State.NULL)
            print("Saved recording file.")
            self.record_pipe.get_state(self.STATE_CHANGE_TIMEOUT)

    def setupPipeline(self):
        """Install bus and connect to the interesting signals"""
        bus = self.display_pipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        # Callback for setting output window
        bus.connect("sync-message::element", self.onSyncMessage)

    def onSyncMessage(self, bus, msg):
        """Set pipeline output to qt window"""
        if msg.get_structure().get_name() == "prepare-window-handle":
            msg.src.set_window_handle(self.window_id)

    def togglePipelineState(self):
        """Change the pipeline from play to pause and from pause to play"""
        if (not self.playing):
            self.inference_pipe.set_state(Gst.State.PLAYING)
            self.display_pipe.set_state(Gst.State.PLAYING)
        else:
            self.inference_pipe.set_state(Gst.State.PAUSED)
            self.display_pipe.set_state(Gst.State.PAUSED)
        
        self.inference_pipe.get_state(self.STATE_CHANGE_TIMEOUT)
        self.display_pipe.get_state(self.STATE_CHANGE_TIMEOUT)
        self.playing = not self.playing

    def getVideoResolution(self):
        """Obtain the resolution of the input video"""
        sink_pad = self.videosink.get_static_pad("sink")
        caps = sink_pad.get_current_caps()
        # Extract the width and height
        if (caps):
            _, width = caps.get_structure(0).get_int("width")
            _, height = caps.get_structure(0).get_int("height")
        else:
            print("Unable to get video resolution", file=sys.stderr)
            self.stopPipeline()
            sys.exit(1)
        return width, height

    def stopPipeline(self):
        """Stop the pipeline by setting it to null state"""
        self.stopRecordingPipeline()
        self.display_pipe.set_state(Gst.State.NULL)
        self.display_pipe.get_state(self.STATE_CHANGE_TIMEOUT)
