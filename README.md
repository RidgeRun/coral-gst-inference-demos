# Coral by Google GstInference Demos

RidgeRun provides support for embedded Linux development for Coral platform, specializing in the use of hardware accelerators in multimedia applications. RidgeRun's products take full advantage of the hardware that Coral exposes to perform transformations on the video streams achieving great performance on complex processes. GstInference maintains the modularity, flexibility, and scalability of the GStreamer pipeline architecture by encapsulating the inference logic in another processing element. 

This repo includes several demos with different approaches to evaluate the use of GstInference on Coral platform.

By using GstInference as the interface between Coral and GStreamer, users can:

* Easily prototype GStreamer pipelines with common and basic GStreamer tools such as gst-launch and GStreamer Daemon.
* Easily test and benchmark TFLite models using GStreamer with Coral.
* Enable a world of possibilities to use Coral with video feeds from cameras, video files, and network streams, and process the prediction information (detection, classification, estimation, segmentation) to monitor events and trigger actions.
* Develop intelligent media servers with recording, streaming, capture, playback, and display features.
* Abstract GStreamer complexity in terms of buffers and events handling.
* Abstract TensorFlow Lite complexity and configuration.
* Make use of GstInference helper elements and API to visualize and easily extract readable prediction information.

GstInference               |  Coral from Google
:-------------------------:|:-------------------------:
[<img src="https://developer.ridgerun.com/wiki/images/thumb/9/92/GstInference_Logo_with_name.jpeg/600px-GstInference_Logo_with_name.jpeg" height="400" width="400">](https://developer.ridgerun.com/wiki/index.php?title=GstInference)  |  [<img src="https://developer.ridgerun.com/wiki/images/6/62/Works_with_coral_svg.svg" height="400" width="400">](https://coral.ai/products/#prototyping-products)
[GstInference Repository](https://github.com/RidgeRun/gst-inference) | [Coral RidgeRun Developer's Wiki](https://developer.ridgerun.com/wiki/index.php?title=Coral_from_Google)
[GstInference Developer's Wiki](https://developer.ridgerun.com/wiki/index.php?title=GstInference/Introduction) |