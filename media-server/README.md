# Gst-Inference Media Server Demo

## Demo Summary

The demo can switch between two origins (camera or RTSP stream) and produces 3 outputs (udp streaming, recording and display) as seen in the following image:

![Demo Pipeline Structure](rsrc/demo.png?raw=true "Demo Pipeline Structure")

The demo currently supports both classification with MobileNetV2 and detection
with MobileNetV2 + SSD.

## Dependencies
The demo uses two RidgeRun open source projects. Please make sure you install and setup the following dependencies before running the demo

* [GStreamer Daemon](https://developer.ridgerun.com/wiki/index.php?title=GStreamer_Daemon_-_Building_GStreamer_Daemon)
* [GStreamer Interpipes](https://developer.ridgerun.com/wiki/index.php?title=GstInterpipe_-_Building_and_Installation_Guide)

The demo requires the models and labels files which can be downloaded from:

* MobileNetV2 (classification): [labels and model](https://coral.ai/models/)
* MobileNetV2 + SSD (detection): [labels](https://developer.ridgerun.com/wiki/index.php?title=Coral_MobilenetV2SSD_COCO_labels) and [models](https://coral.ai/models/).
In this case, you need to save the labels content into a file named ``coco_labels.txt``.

Choose a model architecture (``mobilenetv2`` or ``mobilenetv2ssd``) and update the paths to the model and labels file on the respective  ``config_classifier.txt`` or ``config_detector.txt`` configuration
file. You can provide your own configuration file but keep in mind that it must have the same variables of the template configuration files we provide.

## Demo Execution

Make sure GStreamer Daemon (gstd) is up and running previous to running the media server demo on the media-server directory:
```bash
gstd
```

### Camera RTSP source video
The demo expects a RTSP link at RTSP_URI (defined at the configuration file).
You can modify the default one to test with your own. RidgeRun also offers a product with an easy to use GStreamer plugin to create a RTSP stream. More information [here](https://developer.ridgerun.com/wiki/index.php?title=GstRtspSink).


After setting up the RTSP stream, run the script with:

```bash
./media_server.sh [CONFIG_FILE]
```

For example, to test the detection example run:

```bash
./media_server.sh config_detector.txt
```

Once the stream appears on the display you can change between sources by using the input 

To change to the RTSP stream:
```bash
> stream
```

To change to the camera stream:
```bash
> camera
```

To save the recording and exit the demo
```bash
> exit
```

### UDP destination video
The demo produces a UDP output stream. To receive the output video the media server generates, the following pipeline can be used as a reference. Please adjust port as needed.

```bash
gst-launch-1.0 udpsrc port=5060 ! queue  ! tsdemux ! h264parse ! avdec_h264 ! queue ! videoconvert ! autovideosink
```

It is also possible to access the streaming using VLC:
```bash
vlc udp://@127.0.0.1:5060
```