"""
Copyright (C) 2021 RidgeRun, LLC (http://www.ridgerun.com)
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

import getopt
import os
import sys

from main_window import *


if __name__ == "__main__":

    # Parse options
    def help():
        """Print demo usage information"""
        print("Usage: python3 main.py -c <path-to-config>.cfg", file=sys.stderr)
        exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "input="])
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        help()

    config_file_name = ""

    for opt, arg in opts:
        if (opt in ("-h", "--help")):
            help()
        elif (opt in ("-c", "--config")):
            if (os.path.exists(arg)):
                config_file_name = arg
            else:
                print("No such file or directory: %s" % arg, file=sys.stderr)

    if (config_file_name == ""):
        help()

    MainEvntHndlr = QApplication([])
    MainApp = MainWindow(config_file_name)
    MainApp.show()
    MainEvntHndlr.exec()
