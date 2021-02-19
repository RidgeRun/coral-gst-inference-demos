# Gst-Inference Media Server Demo

## Demo Summary

The demo can switch between two origins (camera or RTSP stream) and produces 3 outputs (udp streaming, recording and display) as seen in the following image:

![Demo Pipeline Structure](rsrc/demo.png?raw=true "Demo Pipeline Structure")

## Dependencies
The demo uses two RidgeRun open source projects. Please make sure you install and setup the following dependencies before running the demo

* [GStreamer Daemon](https://developer.ridgerun.com/wiki/index.php?title=GStreamer_Daemon_-_Building_GStreamer_Daemon)
* [GStreamer Interpipes](https://developer.ridgerun.com/wiki/index.php?title=GstInterpipe_-_Building_and_Installation_Guide)


## Demo Execution

Make sure GStreamer Daemon (gstd) is up and running previous to running the media server demo on the media-server directory:
```bash
gstd
```

### Camera RTSP source video
The demo expects a RTSP link at RTSP_URI (defined at config.txt).
You can modify the default one to test with your own. RidgeRun also offers a product with an easy to use GStreamer plugin to create a RTSP stream. More information [here](https://developer.ridgerun.com/wiki/index.php?title=GstRtspSink).


After setting up the RTSP stream, run the script with:

```bash
./media_server.sh
```

You can change between sources by using the input 

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