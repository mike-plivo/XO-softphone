from iaxclient import *

DTMFS = DTMF_HZ.keys()

class Call:
  def __init__(self, callername="Wphoniax", callernum="0000", dtmfsound=False):
    self.prefered_codec = IAXC_FORMAT_ALAW
    self.other_codecs = [IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, IAXC_FORMAT_ILBC]

    self.dtmfsound = dtmfsound

    self.disconnected = True

    self.iax = IAXWrapper()
    self.iax.set_preferred_source_udp_port(-1)
    self.iax.initialize()
    # codec settings
    pref_codec = self.prefered_codec 
    others_codecs = 0
    others_codecs |= pref_codec
    for codec in self.other_codecs:
      if codec != pref_codec:
        others_codecs |= codec
    self.iax.set_formats(pref_codec, others_codecs)
    self.iax.set_callerid(callername, callernum)
    self.iax.set_silence_threshold(-99.0)
    self.pref = 0
    self.iax.set_audio_prefs(0)
    self.iax.set_event_callback(self.event_cb)

  def send_dtmf(self, digit):
    self.iax.send_dtmf(digit, sound=self.dtmfsound)

  def get_iax(self):
    return self.iax

  def hangup(self):
    self.disconnected = True
    self.iax.dump_call()
    self.iax.millisleep(600)
    self.iax.stop_processing_thread()

  def sleep(self, ms):
    self.iax.millisleep(ms)

  def call(self, peer):
    self.pref = 0
    self.iax.set_audio_prefs(0)
    self.iax.call(peer)
    self.disconnected = False
    self.iax.start_processing_thread()

  def is_in_muted(self):
    ret = (self.pref & IAXC_AUDIO_PREF_RECV_DISABLE)
    return ret != 0

  def in_mute(self):
    if not self.is_in_muted():
      self.pref |= IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(self.pref)
      return True
    return False

  def in_unmute(self):
    if self.is_in_muted():
      self.pref &= ~IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(self.pref)
      return True
    return False

  def is_out_muted(self):
    ret = (self.pref & IAXC_AUDIO_PREF_SEND_DISABLE)
    return ret != 0

  def out_mute(self):
    if self.is_out_muted():
      print "Already Out muted"
    else:
      self.pref |= IAXC_AUDIO_PREF_SEND_DISABLE
      self.iax.set_audio_prefs(self.pref)
      print "Out Muted"

  def out_unmute(self):
    if self.is_out_muted():
      self.pref &= ~IAXC_AUDIO_PREF_SEND_DISABLE
      self.iax.set_audio_prefs(self.pref)
      print "Out unmuted"
    else:
      print "Not Out muted"

  def all_mute(self):
    self.pref = 0
    self.pref |= IAXC_AUDIO_PREF_SEND_DISABLE
    self.pref |= IAXC_AUDIO_PREF_RECV_DISABLE
    self.iax.set_audio_prefs(self.pref)
    print "Out/In muted"

  def all_unmute(self):
    self.pref = 0
    self.iax.set_audio_prefs(self.pref)
    print "Out/In unmuted"


  def event_cb(self, ev):
    if not ev:
      return 1
    if ev.type == IAXC_EVENT_DTMF:
      print "Dtmf received"
      return 1
    elif ev.type == IAXC_EVENT_STATE:
      return self.handle_event_state(ev)
    elif ev.type == IAXC_EVENT_REGISTRATION:
      print "Register event received"
      return 1
    return 1

  def handle_event_state(self, ev_state):
    print "Disconnected=%s" % str(self.disconnected)
    st = self.iax.get_event(ev_state)
    callno = st.contents.callNo
    if st:
      callstate =  st.contents.state
      print "Callstate : %s" % str(callstate)
      if callstate == 0:
        self.disconnected = True
        print "Call %d Hangup" % callno
        return 1
    return 1

  def is_call_disconnected(self):
    return self.disconnected
        


