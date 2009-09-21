'''Iax Client library wrapper'''

from ctypes import *
import time
import sys
import math
import os



IAXC_FORMAT_G723_1       = (1 << 0)        # G.723.1 compression 
IAXC_FORMAT_GSM          = (1 << 1)        # GSM compression 
IAXC_FORMAT_ULAW         = (1 << 2)        # Raw mu-law data (G.711) 
IAXC_FORMAT_ALAW         = (1 << 3)        # Raw A-law data (G.711) 
IAXC_FORMAT_G726         = (1 << 4)        # ADPCM, 32kbps  
IAXC_FORMAT_ADPCM        = (1 << 5)        # ADPCM IMA 
IAXC_FORMAT_SLINEAR      = (1 << 6)        # Raw 16-bit Signed Linear (8000 Hz) PCM 
IAXC_FORMAT_LPC10        = (1 << 7)        # LPC10, 180 samples/frame 
IAXC_FORMAT_G729A        = (1 << 8)        # G.729a Audio 
IAXC_FORMAT_SPEEX        = (1 << 9)        # Speex Audio 
IAXC_FORMAT_ILBC         = (1 << 10)       # iLBC Audio 

IAXC_CALL_STATE_FREE     = 0
IAXC_CALL_STATE_ACTIVE   = (1<<1)
IAXC_CALL_STATE_OUTGOING = (1<<2)
IAXC_CALL_STATE_RINGING  = (1<<3)
IAXC_CALL_STATE_COMPLETE = (1<<4)
IAXC_CALL_STATE_SELECTED = (1<<5)
IAXC_CALL_STATE_BUSY     = (1<<6)
IAXC_CALL_STATE_TRANSFER = (1<<7)

IAXC_EVENT_TEXT          = 1
IAXC_EVENT_LEVELS        = 2
IAXC_EVENT_STATE         = 3
IAXC_EVENT_NETSTAT       = 4
IAXC_EVENT_URL           = 5        # URL push via IAX(2)
IAXC_EVENT_VIDEO         = 6
IAXC_EVENT_REGISTRATION  = 8
IAXC_EVENT_DTMF          = 9
IAXC_EVENT_AUDIO         = 10
IAXC_EVENT_VIDEOSTATS    = 11

IAXC_EVENT_BUFSIZ = 256

# registration accepted
IAXC_REGISTRATION_REPLY_ACK     = 18
# registration rejected
IAXC_REGISTRATION_REPLY_REJ     = 30
# registraton timeout
IAXC_REGISTRATION_REPLY_TIMEOUT = 6


class Timeval(Structure):
  pass
Timeval._fields_ = [("tv_sec", c_int),
                    ("tv_usec", c_int)]

class EventLevels(Structure):
  pass
EventLevels._fields_ = [("input", c_float),
                        ("output", c_float)]

class EventText(Structure):
  pass
EventText._fields_ = [("type", c_int),
                      ("callNo", c_int),
                      ("message", c_char * IAXC_EVENT_BUFSIZ)]


class EventCallState(Structure):
  pass
EventCallState._fields_ = [("callNo", c_int),
                           ("state", c_int),
                           ("format", c_int),
                           ("vformat", c_int),
                           ("remote", c_char * IAXC_EVENT_BUFSIZ),
                           ("remote_name", c_char * IAXC_EVENT_BUFSIZ),
                           ("local", c_char * IAXC_EVENT_BUFSIZ),
                           ("local_context", c_char * IAXC_EVENT_BUFSIZ)]

class Netstat(Structure):
  pass
Netstat._fields_ = [("jitter", c_int),
                    ("losspct", c_int),
                    ("losscnt", c_int),
                    ("packets", c_int),
                    ("delay", c_int),
                    ("dropped", c_int),
                    ("ooo", c_int)]

class EventNetStats(Structure):
  pass
EventNetStats._fields_ = [("callNo", c_int),
                          ("rtt", c_int), 
                          ("local", Netstat), 
                          ("remote", Netstat)]

class VideoStat(Structure):
  pass
VideoStat._fields_ = [("received_slices", c_ulong),
                      ("acc_recv_size", c_ulong),
                      ("sent_slices", c_ulong),
                      ("acc_sent_size", c_ulong),
                      ("dropped_frames", c_ulong),
                      ("inbound_frames", c_ulong),
                      ("outbound_frames", c_ulong),
                      ("avg_inbound_fps", c_float),
                      ("avg_inbound_bps", c_ulong),
                      ("avg_outbound_fps", c_float),
                      ("avg_outbound_bps", c_ulong),
                      ("start_time", Timeval)]

class EventVideoStats(Structure):
  pass
EventVideoStats._fields_ = [("callNo", c_int),
                            ("stats", VideoStat)]

class EventUrl(Structure):
  pass
EventUrl._fields_ = [("callNo", c_int),
                     ("type", c_int),
                     ("url", c_char * IAXC_EVENT_BUFSIZ)]

class EventVideo(Structure):
  pass
EventVideo._fields_ = [("callNo", c_int),
                       ("ts", c_uint),
                       ("format", c_int),
                       ("width", c_int),
                       ("height", c_int),
                       ("encoded", c_int),
                       ("source", c_int),
                       ("size", c_int),
                       ("data", c_char_p)]

class EventAudio(Structure):
  pass
EventAudio._fields_ = [("callNo", c_int),
                       ("ts", c_uint),
                       ("format", c_int),
                       ("encoded", c_int),
                       ("source", c_int),
                       ("size", c_int),
                       ("data", c_char_p)]

class EventRegistration(Structure):
  pass
EventRegistration._fields_ = [("id", c_int),
                              ("reply", c_int),
                              ("msgcount", c_int)]

class Ev(Union):
  pass
Ev._fields_ = [("levels", EventLevels),
               ("text", EventText),
               ("call", EventCallState),
               ("netstats", EventNetStats),
               ("videostats", EventVideoStats),
               ("url", EventUrl),
               ("video", EventVideo),
               ("audio", EventAudio),
               ("reg", EventRegistration)]

class Event(Structure):
  pass
Event._fields_ = [("next", POINTER(Event)),
                  ("type", c_int),
                  ("ev", Ev)]




class Sound(Structure):
  pass
Sound._fields_ = [("data", POINTER(c_short)),
                  ("len", c_long),
                  ("malloced", c_int),
                  ("channel", c_int),
                  ("repeat", c_int),
                  ("pos", c_long),
                  ("id", c_int),
                  ("next", POINTER(Sound))]




DTMF_HZ = {'0':(1336, 941),
           '1':(1209, 697),
           '2':(1336, 697),
           '3':(1477, 697),
           '4':(1209, 770),
           '5':(1336, 770),
           '6':(1477, 770),
           '7':(1209, 852),
           '8':(1336, 852),
           '9':(1477, 852),
           '*':(1209, 941),
           '#':(1477, 941)}

class IAXWrapper:
  '''Wrapper class for iax client C library'''
  def __init__(self):
    if os.name == 'nt':
      self.iax = cdll.libiaxclient 
    else:
      try:
        self.iax = cdll.LoadLibrary("libiaxclient.so") 
      except OSError, err:
        self.iax = cdll.LoadLibrary("libiaxclient.so.1") 

    self._get_event = self.iax.iaxc_get_event_state
    self._get_event.restype = POINTER(EventCallState)
    self._get_event.argtypes = [POINTER(Event)]

    self._play_sound = self.iax.iaxc_play_sound
    self._play_sound.restype = c_int
    self._play_sound.argtypes = [POINTER(Sound), c_int]

    self._stop_sound = self.iax.iaxc_stop_sound
    self._stop_sound.restype = c_int
    self._stop_sound.argtypes = [c_int]

    self._send_dtmf = self.iax.iaxc_send_dtmf
    self._send_dtmf.argtypes = [c_char]

  def initialize(self, maxcalls=1):
    self.iax.iaxc_initialize(maxcalls)

  def set_preferred_source_udp_port(self, sourceport=-1):
    srcport = self.iax.iaxc_set_preferred_source_udp_port(sourceport)
    return srcport

  def set_audio_output(self, audiomode=0):
    self.iax.iaxc_set_audio_output(audiomode)

  def set_formats(self, preferred, allowed):
    self.iax.iaxc_set_formats(preferred, allowed)

  def set_callerid(self, name, number):
    self.iax.iaxc_set_callerid(name, number)

  def send_dtmf(self, digit):
    self._send_dtmf(c_char(digit))

  def play_sound(self, sound, ring):
    soundid = self._play_sound(byref(sound), c_int(ring))
    return soundid

  def stop_sound(self, soundid):
    self._stop_sound(c_int(soundid))

  def register(self, user, password, host):
    registerid = self.iax.iaxc_register(user, password, host)
    return registerid

  def register_ex(self, user, host, refresh):
    registerid = self.iax.iaxc_register_ex(user, password, host, refresh)
    return registerid

  def unregister(self, registerid):
    self.iax.iaxc_unregister(registerid)

  def call(self, num):
    return self.iax.iaxc_call(num)

  def start_processing_thread(self):
    self.iax.iaxc_start_processing_thread()

  def stop_processing_thread(self):
    self.iax.iaxc_stop_processing_thread()

  def set_silence_threshold(self, thr):
    self.iax.iaxc_set_silence_threshold(c_float(thr))

  def dump_call(self):
    self.iax.iaxc_dump_call()

  def dump_all_calls(self):
    self.iax.iaxc_dump_all_calls()

  def dump_call_number(callid):
    self.iax.iaxc_dump_call_number(callid)

  def millisleep(self, ms):
    self.iax.iaxc_millisleep(c_long(ms))

  def shutdown(self):
    self.iax.iaxc_shutdown()

  def get_event(self, p_event):
    return self._get_event(byref(p_event))

  def set_event_callback(self, cb):
    cb_func = CFUNCTYPE(c_int, Event)
    self.pcb = cb_func(cb)
    self.iax.iaxc_set_event_callback(self.pcb)


class IAXClient(IAXWrapper):

  valid_dtmfs = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '*', '#']

  def __init__(self, 
               prefered_codec=IAXC_FORMAT_ALAW, 
               other_codecs=[IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, IAXC_FORMAT_ILBC], 
               ringin=False,
               ringout=False,
               debug=False):

    IAXWrapper.__init__(self)
    self.debug = debug
    self.disconnected = False
    self.ringin = ringin
    self.ringout = ringout

    # init iaxclient
    self.set_preferred_source_udp_port(-1)
    self.initialize()

    # codec settings
    self.pref_codec = prefered_codec 
    self.others_codecs = 0
    self.others_codecs |= self.pref_codec
    for codec in other_codecs:
      if codec != self.pref_codec:
        self.others_codecs |= codec
    self.set_formats(self.pref_codec, self.others_codecs)

    # set ring tones
    if self.ringout:
      self.low_ring = self._build_tone(1500, 500, 5500)
    if self.ringin:
      self.high_ring = self._build_tone(2500, 1200, 3000)
    self.ringid = 0

    # load tones for dtmf
    self.tones = {}
    for x in self.valid_dtmfs:
      self.tones[x] = self._build_dtmf_tone(x)

    # set event callback
    self.set_event_callback(self.event_cb)

  def _build_dtmf_tone(self, dtmf):
    fq1 = DTMF_HZ[dtmf][0]
    fq2 = DTMF_HZ[dtmf][1] 
    return self._build_tone(fq1, fq2, 500)

  def _build_tone(self, fq1, fq2, length):
    tone = Sound()
    memset(byref(tone), c_int(0), sizeof(tone))
    tone.len = length
    ArrayData = c_short * tone.len
    data = ArrayData()
    data_l = []
    for x in xrange(0, tone.len):
      u1 = (0x7fff*0.4*math.sin(float(x)*fq1*math.pi/8000))
      u2 = (0x7fff*0.4*math.sin(float(x)*fq2*math.pi/8000))
      d = c_short(int(u1 + u2))
      data[x] = d
    tone.repeat = 0
    tone.data = data
    return tone

  def play_low_ring(self):
    if self.ringout:
      self.ringid = self.play_sound(self.low_ring, 1)
      self.millisleep(2500)
  
  def play_high_ring(self):
    if self.ringin:
      for x in xrange(3):
        self.ringid = self.play_sound(self.high_ring, 1)
        self.millisleep(500)
      self.millisleep(2500)

  def _log(self, msg):
      sys.stdout.write(msg+'\n')
      sys.stdout.flush()

  def log_debug(self, msg):
    if self.debug:
      msg = "iaxclient.py - DEBUG: "+str(msg)
      self._log(msg)

  def get_tone(self, dtmf):
    return self.tones[dtmf]

  def is_valid_dtmf(self, digit):
    return digit in self.valid_dtmfs

  def is_valid_dtmfs(self, dtmfs):
    for c in dtmfs:
      if c not in self.valid_dtmfs:
        return False
    return True
      
  def is_call_disconnected(self):
    return self.disconnected

  def play_dtmf(self, dtmf):
    tone = self.get_tone(dtmf)
    self.play_sound(tone, 1)

  def play_dtmfs(self, dtmfs, timerms=200):
    '''play_dtmfs(str, int)'''
    for x in dtmfs:
      if not x in self.valid_dtmfs:
        self.log_debug("Invalid dtmf : %s in '%s'" % (x, dtmfs))
        return False 
    for x in dtmfs:
      self.play_dtmf(x)
      self.millisleep(timerms)
    return True

  def send_dtmfs(self, dtmfs, timerms=200):
    '''send_dtmfs(str, int)'''
    for x in dtmfs:
      if not x in self.valid_dtmfs:
        self.log_debug("Invalid dtmf : %s in '%s'" % (x, dtmfs))
        return False 
    for x in dtmfs:
      self.send_dtmf(x)
      self.millisleep(timerms)
    return True

  def send_and_play_dtmfs(self, dtmfs, timerms=200):
    '''send_and_play_dtmfs(str, int)'''
    for x in dtmfs:
      if not x in self.valid_dtmfs:
        self.log_debug("Invalid dtmf : %s in '%s'" % (x, dtmfs))
        return False 
    for x in dtmfs:
      self.send_dtmf(x)
      self.play_dtmf(x)
      self.millisleep(timerms)
    return True

  def start(self, iaxuser, host, exten, iaxpw=None, context=None, port=4569, callername="Wphoniax", callernum="0000"):
    self.set_callerid(callername, callernum)
    self.set_silence_threshold(-99.0)
    peer = iaxuser
    if iaxpw:
      peer += ":%s" % iaxpw
    peer += "@%s" % host
    peer += ":%d" % port
    peer += "/%s" % exten
    if context:
      peer += "@%s" % context
    self.log_debug("Calling %s at %s:%d" % (exten, host, port))
    self.log_debug("Caller is %s <%s>" % (callernum, callername))
    self.call(peer)
    self.start_processing_thread()
    self.log_debug("Started")
    time.sleep(0.1)

  def setup(self, iaxuser, host, exten, iaxpw=None, context=None, port=4569, callername="Wphoniax", callernum="0000"):
    self.set_callerid(callername, callernum)
    self.set_silence_threshold(-99.0)
    peer = iaxuser
    if iaxpw:
      peer += ":%s" % iaxpw
    peer += "@%s" % host
    peer += ":%d" % port
    peer += "/%s" % exten
    if context:
      peer += "@%s" % context
    self.log_debug("Calling %s at %s:%d" % (exten, host, port))
    self.log_debug("Caller is %s <%s>" % (callernum, callername))
    self.call(peer)
    self.log_debug("Setup")

  def run(self):
    self.log_debug("Run")
    self.start_processing_thread()
    while not self.is_call_disconnected():
      self.millisleep(100)

  def event_cb(self, ev):
    if not ev:
      return 1
    if ev.type == IAXC_EVENT_DTMF:
      self.log_debug("Dtmf received")
      return 1
    elif ev.type == IAXC_EVENT_STATE:
      return self.handle_event_state(ev)
    elif ev.type == IAXC_EVENT_REGISTRATION:
      self.log_debug("Register event received")
      return 1
    return 1

  def handle_event_state(self, ev_state):
    self.log_debug("Disconnected=%s" % str(self.disconnected))
    st = self.get_event(ev_state)
    callno = st.contents.callNo
    if st:
      callstate =  st.contents.state
      self.log_debug("Callstate : %s" % str(callstate))
      if callstate == 0:
        if self.ringid:
	  self.stop_sound(self.ringid)
	self.disconnected = True
	self.log_debug("Call %d Hangup" % callno)
	return 1

    ringing = False
    complete = False
    outgoing = False
    self.disconnected = False

    if callstate & IAXC_CALL_STATE_RINGING:
      ringing = True
    if callstate & IAXC_CALL_STATE_ACTIVE:
      if callstate & IAXC_CALL_STATE_COMPLETE:
        complete = True
      if callstate & IAXC_CALL_STATE_OUTGOING:
        outgoing = True
    if outgoing:
      if ringing:
        self.log_debug("Call %d OUT Ringing" % callno)
        self.play_low_ring()
      elif complete:
        self.stop_sound(self.ringid)
        self.log_debug("Call %d OUT Complete" % callno)
      else:
        self.log_debug("Call %d OUT Not Yet Accepted" % callno)
    else:
      if ringing:
        self.log_debug("Call %d IN Ringing" % callno)
        self.play_high_ring()
      elif complete:
        self.stop_sound(self.ringid)
        self.log_debug("Call %d IN Complete" % callno)
      else:
        self.log_debug("Call %d IN Not Yet Accepted" % callno)
    return 1

  def hangup(self):
    self.dump_call()
    self.millisleep(600)
    self.stop_processing_thread()
    self.disconnected = True

  def stop(self):
    self.hangup()





