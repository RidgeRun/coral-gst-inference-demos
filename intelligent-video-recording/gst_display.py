"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

import configparser

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GObject, GstVideo
from PyQt5.QtWidgets import QWidget

from ctypes import Structure, POINTER, CDLL, addressof, sizeof, memmove, byref, cast
from ctypes import c_uint, c_int, c_float, c_ulong, c_void_p, c_bool

GObject.threads_init()
Gst.init(None)

class Prediction(Structure):
    _fields_ = [
        ("id", c_float)
    ]

class GstDisplay(QWidget):
    """Widget to hold the gstreamer pipeline output"""

    def __init__(self, config_file_name):
        super(GstDisplay, self).__init__()

        self.STATE_CHANGE_TIMEOUT = 1000000000

        # Create config object and load file
        config = configparser.ConfigParser()
        config.read(config_file_name)

        # Get demo settings
        try:
            video_dev = config['DEMO_SETTINGS']['CAMERA_DEVICE']
            model = config['DEMO_SETTINGS']['MODEL_LOCATION']
            input_layer = config['DEMO_SETTINGS']['INPUT_LAYER']
            output_layer = config['DEMO_SETTINGS']['OUTPUT_LAYER']
            labels= self.parseLabels(config['DEMO_SETTINGS']['LABELS'])
        except KeyError:
            print("Config file does not have correct format")
            exit(1)

        pipe = "v4l2src device=%s ! videoscale ! videoconvert ! \
                video/x-raw,width=640,height=480,format=I420 ! \
                videoconvert ! tee name=t t. ! videoscale ! \
                queue ! net.sink_model t. ! queue ! net.sink_bypass \
                mobilenetv2 name=net labels=\"%s\" model-location=%s backend=coral \
                backend::input-layer=%s backend::output-layer=%s \
                net.src_bypass ! inferenceoverlay ! videoconvert ! \
                autovideosink name=videosink sync=false " % \
                (video_dev,labels,model,input_layer,output_layer)

        # Create GStreamer pipeline
        self.pipeline = Gst.parse_launch(pipe)

        if (not self.pipeline):
            print("Unable to create pipeline", file=sys.stderr)
            sys.exit(1)

        # Setup pipeline signals and output window
        self.windowId = self.winId()
        self.setupPipeline()
        # Get imagesink Tracker element to further box appending
        self.videosink = self.pipeline.get_by_name("videosink")
        # Play pipeline
        self.playing = False
        self.togglePipelineState()
        self.net = self.pipeline.get_by_name("net")
        # Handle new prediction signal
        self.net.connect("new-prediction", self.newPrediction)

    def parseLabels(self, file):
        """Parse labels to format supported by GstInference"""
        labels = ""

        with open(file) as fp:
            lines = fp.readlines()
            for line in lines:
                tmp = line.split("  ")[1].split("\n")[0]
                labels += tmp + ";"

        return labels

    def newPrediction(self, prediction, pred_size, meta, info, valid):

        #pred = Prediction()
        #pred["id"] = pred_size
        pred = c_float()
        #pred = cast(valid, POINTER(c_float))
        memmove(pred, pred_size, 1)
        print(pred)

    def setupPipeline(self):
        """Install bus and connect to the interesting signals"""
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        # Callback for setting output window
        bus.connect("sync-message::element", self.onSyncMessage)
        # Callback for playing video on loop
        bus.connect("message::eos", self.onEOS)

    def onSyncMessage(self, bus, msg):
        """Set pipeline output to qt window"""
        if msg.get_structure().get_name() == "prepare-window-handle":
            msg.src.set_window_handle(self.windowId)
    
    def onEOS(self, bus, msg):
        """Send a seek event to the pipeline to go to start position"""
        print("Restarting video")
        self.pipeline.seek(
            1, Gst.Format.TIME, Gst.SeekFlags.FLUSH, Gst.SeekType.SET, 0,
            Gst.SeekType.SET, -1)

    def togglePipelineState(self):
        """Change the pipeline from play to pause and from pause to play"""
        if (not self.playing):
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.get_state(self.STATE_CHANGE_TIMEOUT)
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
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.get_state(self.STATE_CHANGE_TIMEOUT)
