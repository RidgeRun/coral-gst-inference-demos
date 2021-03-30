"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

from datetime import datetime
from threading import Timer

import ast
import configparser
import json
import time
import os

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, GLib


GObject.threads_init()
Gst.init(None)

class GstDisplay():
    """Class to hold the GStreamer logic"""

    def __init__(self, config_file_name, loop):
        self.loop = loop
        self.STATE_CHANGE_TIMEOUT = 1000000000

        # Create config object and load file
        self.config = configparser.ConfigParser()
        self.config.read(config_file_name)

        # Get demo settings
        try:
            video_dev = self.config['DEMO_SETTINGS']['CAMERA_DEVICE']
            model = self.config['DEMO_SETTINGS']['MODEL_LOCATION']
            labels = self.parseLabels(self.config['DEMO_SETTINGS']['LABELS_LOCATION'])
            self.arch = self.config['DEMO_SETTINGS']['ARCH']
            self.classes_id = ast.literal_eval(
                                self.config['DEMO_SETTINGS']['CLASSES_ID'])
            self.classes_probability = ast.literal_eval(
                                self.config['DEMO_SETTINGS']['CLASSES_MIN_PROBABILITY'])
            self.min_recording_time_seconds = int(self.config['DEMO_SETTINGS']\
                                ['MIN_RECORDING_TIME_IN_SECONDS'])
            videosink = self.config['DEMO_SETTINGS']['VIDEOSINK']
            self.rec_directory = self.config['DEMO_SETTINGS']['REC_DIRECTORY']

            if not os.path.isdir(self.rec_directory):
                print ("Given recording directory doesn't exist. Using current path...")
                self.rec_directory = os.getcwd()

            if(len(self.classes_id) != len(self.classes_probability)):
                print(("Classes_ID and Class_Min_Probability list must be of the same"
                       " lenght. Please review configuration file."), file = sys.stderr)
                exit(1)

        except KeyError:
            print("Config file does not have correct format", file = sys.stderr)
            exit(1)

        inference_pipe = "v4l2src device=%s ! videoscale ! videoconvert ! \
                          video/x-raw,width=640,height=480,format=I420 ! \
                          videoconvert ! inferencebin arch=%s backend=coral \
                          model-location=%s \
                          labels=\"%s\" overlay=true name=net ! videoconvert ! \
                          interpipesink forward-events=true forward-eos=true name=inference_src sync=false" % \
                          (video_dev,self.arch,model,labels)

        display_pipe = "interpipesrc name=display_sink listen-to=inference_src ! \
                        videoconvert ! %s name=videosink sync=false" % (videosink)

        # Create GStreamer pipelines
        self.inference_pipe = Gst.parse_launch(inference_pipe)
        self.display_pipe = Gst.parse_launch(display_pipe)

        if (not self.display_pipe or not self.inference_pipe):
            print("Unable to create pipeline", file = sys.stderr)
            exit(1)

        # Setup pipeline signals
        self.setupPipeline()
        self.playing = False
        self.recording = False
        self.togglePipelineState()
        self.net = self.inference_pipe.get_by_name("arch")
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
        # Load JSON meta from GstInference prediction signal
        data = json.loads(meta)

        classes = []
        probabilities = []

        # Each time a new prediction is done by GstInference it
        # generates a signal parsed as a JSON 
        # See: 
        # https://developer.ridgerun.com/wiki/index.php?title=GstInference/Metadatas/GstInferenceMeta

        # Detection models use predictions category from JSON meta
        predictions_list = data["predictions"]
        for item in predictions_list:
            # Parse class id from prediction
            classes.append(item["classes"][0]["Class"])
            # Parse probability from prediction. Handle ',' float notation.
            probabilities.append(float(item["classes"][0]["Probability"].replace(",",".")))

        # Classification models use classes category from JSON meta
        predictions_list_classes = data["classes"]
        for item in predictions_list_classes:
            # Parse class id from prediction
            class_id = item["Class"]
            # Parse probability from prediction. Handle ',' float notation.
            class_probability = float(item["Probability"].replace(",","."))

            classes.append(class_id)
            probabilities.append(class_probability)

        # Detect require class ID and min probability threshold
        for i in range(0,len(classes)):
            class_id = classes[i] # Model class ID required to start recording
            class_probability = probabilities[i] # Min probability needed to start recording

            if(class_id in self.classes_id):
                min_prob = self.classes_probability[self.classes_id.index(class_id)]

                if(class_probability >= min_prob):
                    if(self.recording == False):
                        print("Detected. Start recording.")
                        self.startRecordingPipeline()
                    else:
                        self.startTimer()

    def startTimer(self):
        if(self.recording):
            self.timer.cancel()

        # Add timer to handle stop recording
        self.timer = Timer(self.min_recording_time_seconds,
                           self.stopRecordingPipeline)
        self.timer.start()

    def startRecordingPipeline(self):
        if(self.recording == False):
            # Get current time for filename
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y_%H_%M_%S")

            # Build filename with date format
            filename = self.rec_directory + "/" + "intelligent_recording_" + dt_string + ".mp4"

            recording_pipe = "interpipesrc name=record_sink listen-to=inference_src \
                              format=3 ! videoconvert ! x264enc tune=zerolatency \
                              speed-preset=ultrafast ! h264parse ! \
                              qtmux ! filesink location=%s sync=false" % filename
            self.record_pipe = Gst.parse_launch(recording_pipe)

            self.record_pipe.set_state(Gst.State.PLAYING)
            self.record_pipe.get_state(self.STATE_CHANGE_TIMEOUT)

            self.startTimer()
            self.recording = True

    def stopRecordingPipeline(self):
        if(self.recording == True):
            print("No detection. Stop recording.")
            self.recording = False
            self.record_pipe.send_event(Gst.Event.new_eos())
            self.record_pipe.get_bus().timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
            self.record_pipe.set_state(Gst.State.NULL)
            print("Saved recording file.")
            self.record_pipe.get_state(self.STATE_CHANGE_TIMEOUT)

    def setupPipeline(self):
        """Install bus and connect to the interesting signals"""
        self.bus = self.display_pipe.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect("message", self.onMessage)

    def onMessage(self, bus, msg):
        """Callback for Bus messages"""
        if msg.type in {Gst.MessageType.EOS, Gst.MessageType.ERROR} :
            self.stopPipeline()

    def togglePipelineState(self):
        """Change the pipeline from play to null and from null to play"""
        if (not self.playing):
            self.inference_pipe.set_state(Gst.State.PLAYING)
            self.display_pipe.set_state(Gst.State.PLAYING)
        else:
            self.inference_pipe.set_state(Gst.State.NULL)
            self.display_pipe.set_state(Gst.State.NULL)
        
        self.inference_pipe.get_state(self.STATE_CHANGE_TIMEOUT)
        self.display_pipe.get_state(self.STATE_CHANGE_TIMEOUT)
        self.playing = not self.playing

    def stopPipeline(self):
        """Stop the pipeline by setting it to null state"""
        self.stopRecordingPipeline()
        self.togglePipelineState()
        self.bus.remove_signal_watch()
        self.loop.quit()
