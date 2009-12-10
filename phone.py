import iaxclient
from iaxclient import *
import sys

prefered_codec = IAXC_FORMAT_ALAW
other_codecs = [IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, IAXC_FORMAT_ILBC]

class Call:
  def setup(self, iaxuser, host, exten, iaxpw=None, context=None, port=4569, callername="Wphoniax", callernum="0000"):
    self.iax = IAXWrapper()
    self.iax.set_preferred_source_udp_port(-1)
    self.iax.initialize()
    # codec settings
    pref_codec = prefered_codec 
    others_codecs = 0
    others_codecs |= pref_codec
    for codec in other_codecs:
      if codec != pref_codec:
        others_codecs |= codec
    self.iax.set_formats(pref_codec, others_codecs)
    self.iax.set_callerid(callername, callernum)
    self.iax.set_silence_threshold(-99.0)
    peer = iaxuser
    if iaxpw:
      peer += ":%s" % iaxpw
    peer += "@%s" % host
    peer += ":%d" % port
    peer += "/%s" % exten
    if context:
      peer += "@%s" % context

    self.pref = 0
    #prefs |= IAXC_AUDIO_PREF_RECV_DISABLE

    self.iax.set_audio_prefs(0)

    self.iax.call(peer)

  def is_in_muted(self):
    ret = (self.pref & IAXC_AUDIO_PREF_RECV_DISABLE)
    return ret != 0

  def in_mute(self):
    if self.is_in_muted():
      print "Already In muted"
    else:
      self.pref |= IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(self.pref)
      print "In Muted"

  def in_unmute(self):
    if self.is_in_muted():
      self.pref &= ~IAXC_AUDIO_PREF_RECV_DISABLE
      self.iax.set_audio_prefs(self.pref)
      print "In unmuted"
    else:
      print "Not In muted"

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
      

  def run(self):
    self.iax.start_processing_thread()
    while True:
      try:
        raw = raw_input()
        raw = raw.strip()
        if raw == '+':
          self.in_mute()
        elif raw == '-':
          self.in_unmute()
        elif raw == 'o':
          self.out_mute()
        elif raw == 'O':
          self.out_unmute()
        elif raw == 'q':
          break
        self.iax.millisleep(50)
      except KeyboardInterrupt:
        break
    self.iax.dump_call()
    self.iax.millisleep(600)
    self.iax.stop_processing_thread()


if __name__ == '__main__':
  try:
    arg = sys.argv[1]    
    userpw, hostext = arg.split('@', 1)
    if ':' in userpw:
      user, pw = userpw.split(':', 1)
    else:
      user = userpw
      pw = None
    host, ext = hostext.split('/', 1)
  except:
    print "phone.py user[:password]@host/exten"
    sys.exit(1)

  c = Call()
  c.setup(user, host, ext, pw)
  c.run()


