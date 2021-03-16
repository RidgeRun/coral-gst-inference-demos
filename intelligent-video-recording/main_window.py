"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gst_display import *


class MainWidget(QWidget):
    """Central widget to place every other widget on"""

    def __init__(self, config_file_name):
        super(MainWidget, self).__init__()
        # Create gstreamer pipeline output
        self.gstDisplay = GstDisplay(config_file_name)
        # Remove any border keep video coordinates
        vBox = QVBoxLayout()
        vBox.setContentsMargins(0, 0, 0, 0)
        vBox.addWidget(self.gstDisplay)
        self.setLayout(vBox)

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config_file_name):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Intelligent Video Recording Demo")
        # Set main widget to add layouts on top of it
        self.mainWidget = MainWidget(config_file_name)
        self.setCentralWidget(self.mainWidget)

        # Move window to center and resize according to input video size
        width, height = self.mainWidget.gstDisplay.getVideoResolution()
        screenCenter = QDesktopWidget().screenGeometry().center()
        top = screenCenter.y() - height // 2 # Use /2 to center in y axis
        left = screenCenter.x() - width // 2 # Use /2 to center in x     axis
        self.setGeometry(left, top, width, height)
    
    def closeEvent(self, event):
        """Callback function for X window exit button to close app properly"""
        print("Closing application...")
        self.mainWidget.gstDisplay.stopPipeline()
        exit(0)
