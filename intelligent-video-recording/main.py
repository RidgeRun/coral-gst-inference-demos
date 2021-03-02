"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of
RidgeRun, LLC.  The user is free to modify the source code after obtaining
a software license from RidgeRun.  All source code changes must be provided
back to RidgeRun without any encumbrance.
"""

import getopt
import os
import sys

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GObject, GstVideo
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

GObject.threads_init()
Gst.init(None)

# 1s
STATE_CHANGE_TIMEOUT = 1000000000

class GstDisplay(QWidget):
    """Widget to hold the gstreamer pipeline output"""

    def __init__(self, input_video):
        super(GstDisplay, self).__init__()
        # Create pipeline
        self.pipeline = Gst.parse_launch(
            "v4l2src device=%s ! videoscale ! videoconvert ! \
             video/x-raw,width=640,height=480,format=I420 ! \
             autovideosink name=videosink" % input_video)

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
        self.pipeline.get_state(STATE_CHANGE_TIMEOUT)
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
        self.pipeline.get_state(STATE_CHANGE_TIMEOUT)

class MainWidget(QWidget):
    """Central widget to place every other widget on"""

    def __init__(self, input_video):
        super(MainWidget, self).__init__()
        # Create gstreamer pipeline output
        self.gstDisplay = GstDisplay(input_video)
        # Remove any border keep video coordinates
        vBox = QVBoxLayout()
        vBox.setContentsMargins(0, 0, 0, 0)
        vBox.addWidget(self.gstDisplay)
        self.setLayout(vBox)

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, input_video):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Intelligent Video Recording Demo")
        # Set main widget to add layouts on top of it
        self.mainWidget = MainWidget(input_video)
        self.setCentralWidget(self.mainWidget)

        # Move window to center and resize according to input video size
        width, height = self.mainWidget.gstDisplay.getVideoResolution()
        screenCenter = QDesktopWidget().screenGeometry().center()
        top = screenCenter.y() - height // 2
        left = screenCenter.x() - width // 2
        self.setGeometry(left, top, width, height)
    
    def closeEvent(self, event):
        """Callback function for X window exit button to close app properly"""
        print("Closing application...")
        self.mainWidget.gstDisplay.stopPipeline()
        sys.exit(0)

if __name__ == "__main__":

    # Parse options
    def help():
        """Print demo usage information"""
        print("Usage: python3 main.py -i <video-device>",
              file=sys.stderr)
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "input="])
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        help()

    input_video = ""

    for opt, arg in opts:
        if (opt in ("-h", "--help")):
            help()
        elif (opt in ("-i", "--input")):
            if (os.path.exists(arg)):
                input_video = arg
            else:
                print("File %s does not exist" % arg, file=sys.stderr)

    if (input_video == ""):
        help()

    MainEvntHndlr = QApplication([])
    MainApp = MainWindow(input_video)
    MainApp.show()
    MainEvntHndlr.exec()
