"""
gst-launch-1.0 
udpsrc address=127.0.0.1 port=5000 caps="application/x-rtp,media=video,clock-rate=90000,payload=96" !
rtph264depay ! 
avdec_h264 ! 
autovideosink
"""
import sys
import pyds 
import gi 
import logging

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gst,GLib

address = "127.0.0.1"
port = 5000

Gst.init(None)
caps = Gst.Caps.from_string("application/x-rtp,media=video,clock-rate=90000,payload=96")

#Creating Logger 
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)

#Creating Pipeline 
pipeline = Gst.Pipeline()

#CapsFilter
capsfilter = Gst.ElementFactory.make("capsfilter","caps-filter")
if not capsfilter:
    sys.stderr.write("Unable to create capsfilter")
capsfilter.set_property("caps",caps)

#Source
udpsrc = Gst.ElementFactory.make("udpsrc","udp-src")
udpsrc.set_property("address","127.0.0.1")
udpsrc.set_property("port",port)
udpsrc.set_property("caps",caps)
#udpsrc.set_property("caps","application/x-rtp,media=video,clock-rate=90000,payload=96")

if not udpsrc:
    sys.stderr.write("Unable to create udpsrc")

#depay
rtph264depay = Gst.ElementFactory.make("rtph264depay","rtph264-depay")
if not rtph264depay:
    sys.stderr.write("Unable to create rtph264depay")

#Decoder
avdec_h264 = Gst.ElementFactory.make("avdec_h264","avdec-h264")
if not avdec_h264:
    sys.stderr.write("Unable to create avdec_h264")

#sink 
autovideosink = Gst.ElementFactory.make("autovideosink","autovideosink")
if not autovideosink:
    sys.stderr.make("Unable to create autovideosink")

pipeline.add(udpsrc)
pipeline.add(capsfilter)
pipeline.add(rtph264depay)
pipeline.add(avdec_h264)
pipeline.add(autovideosink)

if udpsrc.link(capsfilter):
    logger.info("udpsrc ---> capsfilter\n---\n")
if capsfilter.link(rtph264depay):
    logger.info("capsfilter ---> rtph264depay\n---\n")
if rtph264depay.link(avdec_h264):
    logger.info("rtph264depay\n---avdec_h264\n")
if avdec_h264.link(autovideosink):
    logger.info("avdec_h264 ---> autovideosink\n---\n")

ret = pipeline.set_state(Gst.State.PLAYING)

if ret==Gst.StateChangeReturn.FAILURE:
    logger.error("Pipeline çalışmıyor")
    sys.exit(1)

bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, 
    Gst.MessageType.ERROR | Gst.MessageType.EOS)

if msg:
    if msg.type == Gst.MessageType.ERROR:
        err, debug_info = msg.parse_error()
        logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
        logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")

    elif msg.type == Gst.MessageType.EOS:
        logger.info("End-Of-Stream reached.")

    else:
        # This should not happen as we only asked for ERRORs and EOS
        logger.error("Unexpected message received.")

pipeline.set_state(Gst.State.NULL)

