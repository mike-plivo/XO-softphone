import time
from gettext import gettext as _
import logging
_logger = logging.getLogger('Voipclient')

import pygtk
pygtk.require('2.0')
import gtk
import gobject
from threading import Thread
from sugar.activity import activity
from iaxclient import *

# we need gtk threads
gtk.gdk.threads_init()

import sys
def log(msg):
  sys.stdout.write(msg)
  sys.stdout.flush()


class XOIAXClient(IAXClient):
    def __init__(self, 
               prefered_codec=IAXC_FORMAT_ALAW, 
               other_codecs=[IAXC_FORMAT_ULAW, IAXC_FORMAT_GSM, IAXC_FORMAT_SPEEX, IAXC_FORMAT_ILBC], 
               ringin=False,
               ringout=False,
               debug=False):
	IAXClient.__init__(self, prefered_codec, other_codecs, ringin, ringout, debug)

        # prototype for event handlers
        protofunc = CFUNCTYPE(c_int, POINTER(Event))
        self.handle_event_registration = protofunc(self._handle_event_registration)

	 

    def event_cb(self, ev):
	if not ev:
	    return 1
	if ev.type == IAXC_EVENT_DTMF:
	    self.log_debug("Dtmf Event")
	    return 1
	elif ev.type == IAXC_EVENT_STATE:
	    return self.handle_event_state(ev)
	elif ev.type == IAXC_EVENT_REGISTRATION:
	    self.log_debug("Registration Event")
	    return self.handle_event_registration(ev)
	return 1

    def _handle_event_registration(self, ev_state):
	self.log_debug("Registration Event")
	regev = ev_state.contents.ev.reg
        return 1

    def handle_event_state(self, ev_state):
	self.log_debug("Call state Event")
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


class Voipclient(activity.Activity):
    #### Method: __init__, initialize this Voipclient instance
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        tlbx = activity.ActivityToolbox(self)
        self.set_toolbox(tlbx)
        self.mainbox = gtk.HBox()
        self.make_callbox()
        self.make_rcallbox()
        self.make_dtmfbox()
        self.set_canvas(self.mainbox)
        self.show_all()
        self.dtmfbox.hide_all()
        self.rcallbox.hide_all()
	self.voip = None
	self.registerid = None
        self.use_register = False

    
    def on_dtmf_clicked(self, button):
	if not self.voip:
          return False
	elif self.voip.is_call_disconnected():
          return False
	self.voip.send_and_play_dtmfs(button.get_label())


    def on_call_clicked(self, button):
    	username = self.account_fields['username'].get_text()
    	password = self.account_fields['password'].get_text()
    	peer = self.account_fields['peer'].get_text()
    	number = self.account_fields['number'].get_text()
        print username, password, peer, number
    	if not username or not peer or not number:
            print "A field is empty !"
            return
        if not password:
            password = ''
        self.start_voip(username, password, peer, number)
        self.callbutton.set_label("Calling ...")
        self.callbutton.queue_draw()


    def on_reg_clicked(self, button):
    	username = self.raccount_fields['username'].get_text()
    	password = self.raccount_fields['password'].get_text()
    	peer = self.raccount_fields['peer'].get_text()
        print username, password, peer
    	if not username or not peer:
            print "Reg: A field is empty !"
            return
        if not password:
            password = ''
        self.registerid = self.register_voip(username, password, peer)
        print "Registerid is ", self.registerid
        if self.registerid:
            self.regbutton.disconnect(self.regbutton_handlerid)
            self.regbutton.set_label("Unregister")
            self.regbutton.connect("clicked", self.on_unreg_clicked)
            self.regbutton.queue_draw()


    def on_unreg_clicked(self, button):
        if self.registerid:
            self.voip.unregister(self.registerid)
            self.regbutton.disconnect(self.regbutton_handlerid)
            self.regbutton.set_label("Register")
            self.regbutton.connect("clicked", self.on_reg_clicked)
            self.regbutton.queue_draw()
            self.voip = None
            print "Unregistered"


    def on_reg_call_clicked(self, button):
    	num = self.raccount_fields['number'].get_text()
    	username = self.raccount_fields['username'].get_text()
    	password = self.raccount_fields['password'].get_text()
        password = password.strip()
    	host = self.raccount_fields['peer'].get_text()
        if password:
	    data = "%s:%s@%s/%s" % (username, password, host, num)
        else:
	    data = "%s@%s/%s" % (username, host, num)
        self.reg_call(num)


    def on_hangup_clicked(self, button):
        try:
            self.voip.hangup()
        except:
            pass
        print "Hangup"


    def on_switch_register(self, button):
        if not self.use_register:
	    self.use_register = True
        else:
	    self.use_register = False
        if self.use_register:
	    self.callbox.hide_all()
	    self.rcallbox.show_all()
        else:
	    self.rcallbox.hide_all()
	    self.callbox.show_all()


    def make_rcallbox(self):
	self.rcallbox = gtk.HBox(False, 10)
        self.rvcallbox = gtk.VBox(False, 0)

        switchbutton = gtk.Button("Don't use register")
        switchbutton.connect("clicked", self.on_switch_register)
        self.rvcallbox.pack_start(switchbutton, False, False, 0)

	self.raccount_fields = {}
	self.raccount_fields['username'] = gtk.Entry(max=25)
	self.raccount_fields['password'] = gtk.Entry(max=25)
	self.raccount_fields['password'].set_visibility(False)
	self.raccount_fields['peer'] = gtk.Entry(max=50)
	self.raccount_fields['number'] = gtk.Entry(max=50)
	self.rvcallbox.pack_start(gtk.Label("Username"), False, False, 0)
	self.rvcallbox.pack_start(self.raccount_fields['username'], False, False, 0)
	self.rvcallbox.pack_start(gtk.Label("Password"), False, False, 0)
	self.rvcallbox.pack_start(self.raccount_fields['password'], False, False, 0)
	self.rvcallbox.pack_start(gtk.Label("Peer"), False, False, 0)
	self.rvcallbox.pack_start(self.raccount_fields['peer'], False, False, 0)

        self.regbutton = gtk.Button(label="Register")
        self.regbutton_handlerid = self.regbutton.connect("clicked", self.on_reg_clicked)
        self.rvcallbox.pack_start(self.regbutton, False, False, 0)
      
        hsep = gtk.HSeparator()
        self.rvcallbox.pack_start(hsep, False, False, 0)

	self.rvcallbox.pack_start(gtk.Label("Number"), False, False, 0)
	self.rvcallbox.pack_start(self.raccount_fields['number'], False, False, 0)

        self.rcallbutton = gtk.Button(label="Call")
        self.rcallbutton_handlerid = self.rcallbutton.connect("clicked", self.on_reg_call_clicked)
        self.rvcallbox.pack_start(self.rcallbutton, False, False, 10)
	self.rcallbox.pack_start(self.rvcallbox, False, False, 0)

	self.mainbox.pack_start(self.rcallbox, False, False, 0)


    def make_callbox(self):
	self.callbox = gtk.HBox(False, 10)
        self.vcallbox = gtk.VBox(False, 0)

        switchbutton = gtk.Button("Use register")
        switchbutton.connect("clicked", self.on_switch_register)
        self.vcallbox.pack_start(switchbutton, False, False, 0)

	self.account_fields = {}
	self.account_fields['username'] = gtk.Entry(max=25)
	self.account_fields['password'] = gtk.Entry(max=25)
	self.account_fields['password'].set_visibility(False)
	self.account_fields['peer'] = gtk.Entry(max=50)
	self.account_fields['number'] = gtk.Entry(max=50)
	self.vcallbox.pack_start(gtk.Label("Username"), False, False, 0)
	self.vcallbox.pack_start(self.account_fields['username'], False, False, 0)
	self.vcallbox.pack_start(gtk.Label("Password"), False, False, 0)
	self.vcallbox.pack_start(self.account_fields['password'], False, False, 0)
	self.vcallbox.pack_start(gtk.Label("Peer"), False, False, 0)
	self.vcallbox.pack_start(self.account_fields['peer'], False, False, 0)
	self.vcallbox.pack_start(gtk.Label("Number"), False, False, 0)
	self.vcallbox.pack_start(self.account_fields['number'], False, False, 0)

        self.callbutton = gtk.Button(label="Call")
        self.callbutton_handlerid = self.callbutton.connect("clicked", self.on_call_clicked)
        self.vcallbox.pack_start(self.callbutton, False, False, 10)
	self.callbox.pack_start(self.vcallbox, False, False, 0)

	self.mainbox.pack_start(self.callbox, False, False, 0)


    def make_dtmfbox(self):
	self.dtmfbox = gtk.VBox(False, 10)
        dtmflabel = gtk.Label("DTMFS")
	self.dtmfbox.pack_start(dtmflabel, False, False, 0)

	self.dtmf_fields = {}
	for dtmf in ('0','1','2','3','4','5','6','7','8','9','#','*'):
	    self.dtmf_fields[dtmf] = gtk.Button(dtmf)
	    self.dtmf_fields[dtmf].set_border_width(2)
	    self.dtmf_fields[dtmf].connect("clicked", self.on_dtmf_clicked)
	    self.dtmf_fields[dtmf].set_sensitive(False)

        dtmfbox1 = gtk.HButtonBox()
        dtmfbox1.set_layout(gtk.BUTTONBOX_START)
        for dtmf in ('0','1','2','3'):
	    dtmfbox1.add(self.dtmf_fields[dtmf])

        dtmfbox2 = gtk.HButtonBox()
        dtmfbox2.set_layout(gtk.BUTTONBOX_START)
        for dtmf in ('4','5','6','7'):
	    dtmfbox2.add(self.dtmf_fields[dtmf])

        dtmfbox3 = gtk.HButtonBox()
        dtmfbox3.set_layout(gtk.BUTTONBOX_START)
        for dtmf in ('8','9','#','*'):
	    dtmfbox3.add(self.dtmf_fields[dtmf])

	self.dtmfbox.pack_start(dtmfbox1, False, False, 0)
	self.dtmfbox.pack_start(dtmfbox2, False, False, 0)
	self.dtmfbox.pack_start(dtmfbox3, False, False, 0)

	self.mainbox.pack_start(self.dtmfbox, False, False, 25)


    def reg_call(self, number):
        self.voip_th = Thread(target=self.__reg_call, args=(number,))


    def __reg_call(self, number):
        self.rcallbutton.disconnect(self.regbutton_handlerid)
        self.rcallbutton.set_label('Hangup call')
        self.rcallbutton.connect("clicked", self.on_hangup_clicked)
	self.raccount_fields['username'].set_editable(False)
	self.raccount_fields['password'].set_editable(False)
	self.raccount_fields['peer'].set_editable(False)
	self.raccount_fields['number'].set_editable(False)
	self.raccount_fields['username'].set_sensitive(False)
	self.raccount_fields['password'].set_sensitive(False)
	self.raccount_fields['peer'].set_sensitive(False)
	self.raccount_fields['number'].set_sensitive(False)
	for dtmf in self.dtmf_fields:
	    self.dtmf_fields[dtmf].set_sensitive(True)
        self.dtmfbox.show_all()
      
        self.voip.call(number)
        
        while True:
            disconnected = self.voip.is_call_disconnected()
            if disconnected:
                print "Hangup in Voipclient !"
                break
            else:
                self.voip.millisleep(100) 
        self.clean_call()
	_logger.debug("End Voipclient")


    def start_voip(self, username, password, peer, number):
        self.voip_th = Thread(target=self.__start_voip, args=(username, password, peer, number))
        self.voip_th.start()

    def __start_voip(self, username, password, peer, number):
	try:
	    self.voip = XOIAXClient(ringout=True, debug=True)
	    _logger.info("IAXClient init ok")
	except Exception, err:
	    _logger.error("Cannot initialize IAXClient : %s" % str(err))
	    self.voip = None
	try:
	    self.voip.setup(username , peer, number, iaxpw=password, port=4569, callername="Wphoniax", callernum="0000")
	except Exception, err:
	    _logger.error("IAXClient setup error : %s" % str(err))
	    _logger.debug("Init done")

        self.callbutton.disconnect(self.callbutton_handlerid)
        self.callbutton.set_label('Hangup call')
        self.callbutton.connect("clicked", self.on_hangup_clicked)
	self.account_fields['username'].set_editable(False)
	self.account_fields['password'].set_editable(False)
	self.account_fields['peer'].set_editable(False)
	self.account_fields['number'].set_editable(False)
	self.account_fields['username'].set_sensitive(False)
	self.account_fields['password'].set_sensitive(False)
	self.account_fields['peer'].set_sensitive(False)
	self.account_fields['number'].set_sensitive(False)
	for dtmf in self.dtmf_fields:
	    self.dtmf_fields[dtmf].set_sensitive(True)
        self.dtmfbox.show_all()

        self.voip.start_processing_thread()
        while True:
            disconnected = self.voip.is_call_disconnected()
            if disconnected:
                print "Hangup in Voipclient !"
                break
            self.voip.millisleep(100) 

        self.clean_call()
	_logger.debug("End Voipclient")


    def register_voip(self, username, password, peer):
	try:
	    self.voip = XOIAXClient(ringout=True, debug=True)
	    _logger.info("IAXClient init ok")
	except Exception, err:
	    _logger.error("Cannot initialize IAXClient : %s" % str(err))
	    self.voip = None
            return None
	try:
            self.voip.start_processing_thread()
            regid = self.voip.register(username, password, peer)
            return regid
	except Exception, err:
	    _logger.error("IAXClient setup error : %s" % str(err))
	    _logger.debug("Init done")
            return None


    def clean_call(self):
        print "clean_call"
        self.callbutton.disconnect(self.callbutton_handlerid)
        self.callbutton.set_label("Call")
        self.callbutton.connect("clicked", self.on_call_clicked)
	self.account_fields['username'].set_sensitive(True)
	self.account_fields['password'].set_sensitive(True)
	self.account_fields['peer'].set_sensitive(True)
	self.account_fields['number'].set_sensitive(True)
	self.account_fields['username'].set_editable(True)
	self.account_fields['password'].set_editable(True)
	self.account_fields['peer'].set_editable(True)
	self.account_fields['number'].set_editable(True)
	self.account_fields['password'].set_text('')

        self.rcallbutton.disconnect(self.rcallbutton_handlerid)
        self.rcallbutton.set_label("Call")
        self.rcallbutton.connect("clicked", self.on_reg_call_clicked)
	self.raccount_fields['username'].set_sensitive(True)
	self.raccount_fields['password'].set_sensitive(True)
	self.raccount_fields['peer'].set_sensitive(True)
	self.raccount_fields['number'].set_sensitive(True)
	self.raccount_fields['username'].set_editable(True)
	self.raccount_fields['password'].set_editable(True)
	self.raccount_fields['peer'].set_editable(True)
	self.raccount_fields['number'].set_editable(True)
	self.raccount_fields['password'].set_text('')

	for dtmf in self.dtmf_fields:
	    self.dtmf_fields[dtmf].set_sensitive(False)
        self.dtmfbox.hide_all()




def main():
    _logger.info("main")
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    v = Voipclient(win)
    gtk.main()
    return 0

if __name__ == "__main__":
    main()

