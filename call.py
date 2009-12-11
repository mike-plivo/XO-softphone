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
    self.disconnected = False
    self.iax.call(peer)
    self.iax.start_processing_thread()

  def in_mute(self):
    prefs = self.iax.get_audio_prefs()
    if prefs & IAXC_AUDIO_PREF_RECV_DISABLE:
      return False
    else:
      prefs |= IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(prefs)
      return True

  def in_unmute(self):
    prefs = self.iax.get_audio_prefs()
    if prefs & IAXC_AUDIO_PREF_RECV_DISABLE:
      prefs &= ~IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(prefs)
      return True
    else:
      return False

  def out_mute(self):
    prefs = self.iax.get_audio_prefs()
    if prefs & IAXC_AUDIO_PREF_SEND_DISABLE:
      return False
    else:
      prefs |= IAXC_AUDIO_PREF_SEND_DISABLE
      self.iax.set_audio_prefs(prefs)
      return True

  def out_unmute(self):
    prefs = self.iax.get_audio_prefs()
    if prefs & IAXC_AUDIO_PREF_SEND_DISABLE:
      prefs &= ~IAXC_AUDIO_PREF_SEND_DISABLE
      self.iax.set_audio_prefs(prefs)
      return True
    else:
      return False

  def all_mute(self):
    self.out_mute()
    self.in_mute()

  def all_unmute(self):
    self.out_unmute()
    self.in_unmute()

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
      if callstate & IAXC_CALL_STATE_RINGING:
        print "Call %d Ringing" % callno
      if callstate & IAXC_CALL_STATE_COMPLETE:
        print "Call %d Complete" % callno
      if callstate & IAXC_CALL_STATE_ACTIVE:
        print "Call %d Active" % callno
      if callstate & IAXC_CALL_STATE_OUTGOING:
        print "Call %d Outgoing" % callno
      if callstate & IAXC_CALL_STATE_SELECTED:
        print "Call %d Selected" % callno
      if callstate & IAXC_CALL_STATE_BUSY:
        print "Call %d Busy" % callno
      if callstate & IAXC_CALL_STATE_FREE:
        print "Call %d Free" % callno
      if callstate == 0:
        self.disconnected = True
        print "Call %d Hangup" % callno
        return 1
    return 1

  def is_call_disconnected(self):
    return self.disconnected
        


