# GstInference Intelligent Video Recording Demo

## Demo Summary

The demo aims to be a reference intelligent video recording security camera. The configuration file (''config.cfg'') allows to add a list of classes ID from the model being used.

As seen on the following image when a defined class ID is detected it will start recording. Default uses class ID 762 (Remote Control). If the class ID is still being detected it will continue recording, if the class ID does not match it will wait ``MIN_RECORDING_TIME_IN_SECONDS`` before saving the video. Multiple classes ID can be detected at once. If after saving the video a new valid detection appears a new video file will be created.

![Demo Pipeline Structure](rsrc/demo.png?raw=true "Demo Pipeline Structure")

## Dependencies
The demo uses RidgeRun open source project GstInterpipes. Please make sure you install and setup the following dependencies before running the demo

* [GStreamer Interpipes](https://developer.ridgerun.com/wiki/index.php?title=GstInterpipe_-_Building_and_Installation_Guide)

The demo requires the model and labels file from Coral which can be downloaded from:

[https://coral.ai/models/](https://coral.ai/models/)

Update the paths to model and labels file on ``config.cfg`` file. It uses by default ``mobilenet_v2_1.0_224_quant_edgetpu.tflite`` and ``imagenet_labels.txt``.

## Demo Settings

Please review labels file being used to find the class ID needed to be used. Default settings use ID 762 (Remote Control).

Several parameters can be configured using ``config.cfg`` file:

* CAMERA_DEVICE: Camera device to be used as input video. (Example: /dev/video0)
* CAMERA_DEVICE_WIDTH = Camera device width. (Example: 1280)
* CAMERA_DEVICE_HEIGHT = Camera device height. (Example: 720)
* MODEL_LOCATION = Absolute path to the model location.
* INPUT_LAYER = Layer to be used as input for the model.
* OUTPUT_LAYER = Layer to be used as output for the model.
* LABELS = Path to the labels file.
* OUTPUT_FILE = Path to save the recording. Demo only support mp4 files.
* CLASSES_ID = List of classes IDs to trigger recording. (Example: [762,468])
* CLASSES_MIN_PROBABILITY = List of min probability to trigger recording for each ID (Example: [0.75,0.80])
* MIN_RECORDING_TIME_IN_SECONDS = Min recording seconds to wait for ID to be detected before saving video.

## Demo Execution

Run the following command to start the demo:
```bash
python3 main.py -c config.cfg
```