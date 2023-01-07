"""
----SERVER PIPELINE----
pipeline gst-launch-1.0 
filesrc location=/home/nvidia/Mert/CatSleep.mp4 ! --
qtdemux ! --
h264parse ! --
nvv4l2decoder ! --
nvvideoconvert ! --
nvv4l2h264enc ! 
rtph264pay  ! 
udpsink host=127.0.0.1 port=5000

Always - Statik (linklenebilir direkt)
Sometimes - Dinamik (Direkt linklenemez)
"""
import gi
import sys
import pyds
import logging

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

host = "127.0.0.1"
port = "5000"
file_path = "/home/jaypear/Desktop/Genel/Gstreamer/video1.mp4"

from gi.repository import Gst,GLib

#Yöntem 1

def cb_newpad(demux, src, sink):
    print("In cb_newpad\n")
    caps=src.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    features=caps.get_features(0)

    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        print("features=",features)
        sink_pad=sink.get_static_pad("sink")
        if not src.link(sink_pad):
            sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")

logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)


#Initializing gst
Gst.init(None)

#Creating-pipeline
pipeline = Gst.Pipeline()

#Elemanların oluşturulması
#Source
filesrc = Gst.ElementFactory.make("filesrc","file-src")
filesrc.set_property("location",file_path)

#Demuxer
qtdemux = Gst.ElementFactory.make("qtdemux","qt-demux")

if not qtdemux:
    sys.stderr.write("Unable to create demuxer\n")
#Parser
h264parse = Gst.ElementFactory.make("h264parse","h264-parse")

if not h264parse:
    sys.stderr.write("Unable to create Parser\n")
#Converter
nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")

qtdemux.connect("pad-added", cb_newpad, h264parse)

if not nvvidconv:
    sys.stderr.write("Unable to create convertor\n")
#Decoder
decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
if not decoder:
    sys.stderr.write("")
#Sink
udpsink = Gst.ElementFactory.make("udpsink","sink")
udpsink.set_property("host",host)
udpsink.set_property("port",5000)
if not udpsink:
    sys.stderr.write("Unable to create udpsink")

#Encoder
nv264enc = Gst.ElementFactory.make("nvv4l2h264enc","nv264enc")
if not nv264enc:
    sys.stderr.write("Unable to create nv264enc")

#rtph264pay
rtph264pay = Gst.ElementFactory.make("rtph264pay","rtph264-pay")
if not rtph264pay:
    sys.stderr("Unable to create rtph264pay")

#Sink
if not udpsink or not decoder or not nvvidconv or not qtdemux or not pipeline:
    logger.error('There are problems on elements.')
    sys.exit(1)

pipeline.add(filesrc)
pipeline.add(qtdemux)
pipeline.add(h264parse)
pipeline.add(decoder)
pipeline.add(nvvidconv)
pipeline.add(nv264enc)
pipeline.add(rtph264pay)
pipeline.add(udpsink)


if filesrc.link(qtdemux):
    logger.info("filesrc ve qtdemux bağlandı")
if h264parse.link(decoder):
    logger.info("h264parser ve decoder bağlandı")
if decoder.link(nvvidconv):
    logger.info("decoder ve convertor bağlandı")    
if nvvidconv.link(nv264enc):
    logger.info("nvidconv ve nv264enc bağlandı")
if nv264enc.link(rtph264pay):
    logger.info("nv264enc ve rtph264pay bağlandı")
if rtph264pay.link(udpsink):
    logger.info("rtph264pay ve udpsink bağlandı\nHat tamamlandı!")

ret=pipeline.set_state(Gst.State.PLAYING)

if ret==Gst.StateChangeReturn.FAILURE:
    logger.error("pipeline'da sıkıntı var")
    sys.exit(1)

bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, 
    Gst.MessageType.ERROR | Gst.MessageType.EOS)