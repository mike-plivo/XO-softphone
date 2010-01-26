from iaxclient import (IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, 
                       IAXC_FORMAT_ILBC, IAXC_FORMAT_ALAW, 
                       IAXC_CALL_STATE_FREE, IAXC_CALL_STATE_ACTIVE, 
                       IAXC_CALL_STATE_OUTGOING, IAXC_CALL_STATE_RINGING, IAXC_CALL_STATE_COMPLETE, 
                       IAXC_CALL_STATE_SELECTED, IAXC_CALL_STATE_BUSY, IAXC_CALL_STATE_TRANSFER,
                       IAXC_AUDIO_PREF_SEND_DISABLE, IAXC_AUDIO_PREF_RECV_DISABLE)
from iaxclient import (DTMF_HZ)
from iaxclient import IAXWrapper


class Voip(object):
  def __init__(self):
    self.prefered_codec = IAXC_FORMAT_ALAW
    self.other_codecs = [IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, IAXC_FORMAT_ILBC]
    self.iax = IAXWrapper()
    self.iax.set_preferred_source_udp_port(-1)
    self.iax.initialize()
    self.iax.set_formats(self.prefered_codec, self.other_codecs)
    self.iax.set_silence_threshold(-99.0)
    self.iax.set_audio_prefs(0)
    self.iax.set_event_callback(self.event_cb)

