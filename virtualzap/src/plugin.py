#
#  VirtualZap E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Coding idea and design by Vali
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from enigma import eServiceReference,  eTimer, getDesktop
from ServiceReference import ServiceReference
from Components.SystemInfo import SystemInfo
from enigma import eServiceCenter, getBestPlayableServiceReference
from Components.VideoWindow import VideoWindow
from enigma import ePoint, eEPGCache
from time import localtime, time
from Screens.InfoBarGenerics import InfoBarShowHide, NumberZap
from Screens.InfoBar import InfoBar

from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop

from Screens.EpgSelection import EPGSelection
from Screens.EventView import  EventViewEPGSelect

InfoBarShowHideINIT = None

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, getConfigListEntry, configfile
from Components.ConfigList import ConfigList, ConfigListScreen

# for localized messages
from . import _

config.plugins.virtualzap = ConfigSubsection()
config.plugins.virtualzap.mode = ConfigSelection(default="0", choices = [("0", _("as plugin in extended bar")),("1", _("with long OK press")), ("2", _("with exit button"))])
config.plugins.virtualzap.usepip = ConfigYesNo(default = True)

def autostart(reason, **kwargs):
	if config.plugins.virtualzap.mode.value != "0":
		# overide InfoBarShowHide
		global InfoBarShowHideINIT
		if InfoBarShowHideINIT is None:
			InfoBarShowHideINIT = InfoBarShowHide.__init__
		InfoBarShowHide.__init__ = InfoBarShowHide__init__
		# new method
		InfoBarShowHide.showVZ = showVZ
		if config.plugins.virtualzap.mode.value == "2":
			InfoBarShowHide.newHide = newHide

def InfoBarShowHide__init__(self):
	# initialize InfoBarShowHide with original __init__
	InfoBarShowHideINIT(self)
	# delete current key map --> we have to use "ok" with b-flag
	if config.plugins.virtualzap.mode.value == "1":
		del self["ShowHideActions"]
		# initialize own actionmap with ok = b and longOK = l
		self["myactions"] = ActionMap( ["myShowHideActions"] ,
		{
			"toggleShow": self.toggleShow,
			"longOK": self.showVZ,
			"hide": self.hide,
		}, 1)
	elif config.plugins.virtualzap.mode.value == "2":
		self["ShowHideActions"] = ActionMap( ["InfobarShowHideActions"] ,
		{
			"toggleShow": self.toggleShow,
			"hide": self.newHide,
		}, 1)


def showVZ(self):
	from  Screens.InfoBarGenerics import InfoBarEPG, InfoBarPiP
	# check for InfoBarEPG --> only start if true
	if isinstance(self, InfoBarEPG):
		# check for PiP
		if isinstance(self, InfoBarPiP):
			# check if PiP is already shown
			if self.pipShown():
				# it is... close it!
				self.showPiP()
		if isinstance(self, InfoBar):
			self.session.open(VirtualZap, self.servicelist)

def newHide(self):
	# remember if infobar is shown
	visible = self.shown
	self.hide()
	if not visible:
		# infobar was not shown, start VZ
		self.showVZ()

def Plugins(**kwargs):
 	plist =  [PluginDescriptor(name="Virtual Zap Setup", description=_("Virtual Zap Setup"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc = setup)]
	if config.plugins.virtualzap.mode.value == "0":
		plist.append(PluginDescriptor(name="Virtual Zap", description=_("Virtual (PiP) Zap"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU],icon = "plugin.png", fnc = main))
	elif config.plugins.virtualzap.mode.value == "1" or config.plugins.virtualzap.mode.value == "2":
		plist.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART],fnc = autostart))
	return plist

def setup(session,**kwargs):
	session.open(VirtualZapConfig)

def main(session,**kwargs):
		session.open(VirtualZap, kwargs["servicelist"])

class VirtualZap(Screen):
	sz_w = getDesktop(0).size().width()

	#
	# VirtualZap or VirtualZapNoPiP
	#

	if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value:
		if sz_w == 1280:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,505" size="1280,220" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,0" size="1280,220" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="60,50" size="214,120" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="left" name="NowChannel" position="305,60" size="887,32" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEPG" position="305,105" size="600,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEPG" position="305,140" size="600,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowTime" position="1070,105" size="124,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextTime" position="1070,140" size="124,28" transparent="1" zPosition="2"/>
				</screen>"""
		elif sz_w == 1024:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,420" size="1024,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="1024,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,20" size="164,92" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="230,25" size="741,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="230,55" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="230,80" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowTime" position="850,55" size="124,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextTime" position="850,80" size="124,25" transparent="1" zPosition="2"/>
				</screen>"""
		else:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,420" size="720,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="720,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,25" size="130,73" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="190,25" size="480,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="190,55" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="190,80" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowTime" position="550,55" size="120,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextTime" position="550,80" size="120,25" transparent="1" zPosition="2"/>
				</screen>"""
	else:
		if sz_w == 1280:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,505" size="1280,220" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,0" size="1280,220" zPosition="0"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowChannel" position="140,60" size="1000,32" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEPG" position="140,105" size="860,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEPG" position="140,140" size="860,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowTime" position="1015,105" size="124,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextTime" position="1015,140" size="124,28" transparent="1" zPosition="2"/>
				</screen>"""
		elif sz_w == 1024:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,420" size="1024,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="1024,176" zPosition="0"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="100,25" size="824,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="100,55" size="700,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="100,80" size="700,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowTime" position="800,55" size="124,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextTime" position="800,80" size="124,25" transparent="1" zPosition="2"/>
				</screen>"""
		else:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,420" size="720,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="720,176" zPosition="0"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="50,25" size="620,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="50,55" size="500,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="50,80" size="500,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowTime" position="550,55" size="120,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextTime" position="550,80" size="120,25" transparent="1" zPosition="2"/>
				</screen>"""


	def __init__(self, session, servicelist = None):
		Screen.__init__(self, session)
		self.session = session
		self.pipAvailable = False
		if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value:
			self.skinName = "VirtualZap"
			self.pipAvailable = True
		else:
			self.skinName = "VirtualZapNoPiP"
		self.epgcache = eEPGCache.getInstance()
		self.CheckForEPG = eTimer()
		self.CheckForEPG.callback.append(self.CheckItNow)
		self["NowChannel"] = Label()
		self["NowEPG"] = Label()
		self["NextEPG"] = Label()
		self["NowTime"] = Label()
		self["NextTime"] = Label()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ChannelSelectBaseActions", "ChannelSelectEPGActions"], 
		{
			"ok": self.ok, 
			"cancel": self.closing,
			"right": self.nextService,
			"left": self.prevService,
			"nextBouquet": self.nextBouquet,
			"prevBouquet": self.prevBouquet,
			"showEPGList": self.openEventView,
		},-2)
		self["actions2"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutReady)
		# PiP
		if self.pipAvailable:
			# activate PiP support
			self["video"] = VideoWindow(fb_width = getDesktop(0).size().width(), fb_height = getDesktop(0).size().height())
			self.pip = None
			self.currentPiP = ""
		# this is the servicelist from ChannelSelectionBase
		self.servicelist = servicelist
		self.newServicePlayed  =  False
		# needed, because if we won't zap, we habe to go back to the current bouquet and service
		self.curRef = ServiceReference(self.servicelist.getCurrentSelection())
		self.curBouquet = self.servicelist.getRoot()

	def onLayoutReady(self):
		self.updateInfos()

	def nextService(self):
		# get next service
		if self.servicelist.inBouquet():
			prev = self.servicelist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
						self.servicelist.nextBouquet()
					else:
						self.servicelist.moveDown()
					cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			self.servicelist.moveDown()
		if self.isPlayable():
			self.updateInfos()
		else:
			self.nextService()

	def prevService(self):
		# get previous service
		if self.servicelist.inBouquet():
			prev = self.servicelist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value:
						if self.servicelist.atBegin():
							self.servicelist.prevBouquet()
					self.servicelist.moveUp()
					cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			self.servicelist.moveUp()
		if self.isPlayable():
			self.updateInfos()
		else:
			self.prevService()

	def isPlayable(self):
		# check if service is playable
		current = ServiceReference(self.servicelist.getCurrentSelection())
		return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))


	def nextBouquet(self):
		# next bouquet with first service
		if config.usage.multibouquet.value:
			self.servicelist.nextBouquet()
		self.updateInfos()

	def prevBouquet(self):
		# previous bouquet with first service
		if config.usage.multibouquet.value:
			self.servicelist.prevBouquet()
		self.updateInfos()


	def updateInfos(self):
		# update data
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self["NowChannel"].setText(current.getServiceName())
		nowepg, nowtimedisplay = self.getEPGNowNext(current.ref,0)
		nextepg, nexttimedisplay = self.getEPGNowNext(current.ref,1)
		self["NowEPG"].setText(nowepg)
		self["NextEPG"].setText(nextepg)
		self["NowTime"].setText(nowtimedisplay)
		self["NextTime"].setText(nexttimedisplay)
		if not nowepg:
			# no epg found --> let's try it again, but only if PiP is activated
			if self.pipAvailable:
				self.CheckForEPG.start(3000, True)
		if self.pipAvailable:
			# play in videowindow
			self.playService(current.ref)

	def getEPGNowNext(self,ref, modus):
		# get now || next event
		if self.epgcache is not None:
			event = self.epgcache.lookupEvent(['IBDCTSERNX', (ref.toString(), modus, -1)])
			if event:
				if event[0][4]:
					t = localtime(event[0][1])
					duration = event[0][2]
					if modus == 0:
						timedisplay = "+%d min" % (((event[0][1] + duration) - time()) / 60)
					elif modus == 1:
						timedisplay = "%d min" %  (duration / 60)
					return "%02d:%02d %s" % (t[3],t[4], event[0][4]), timedisplay
				else:
					return "", ""
		return "", ""

	def openSingleServiceEPG(self):
		# show EPGList
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self.session.open(EPGSelection, current.ref)

	def openEventView(self):
		# show EPG Event
		epglist = [ ]
		self.epglist = epglist
		service = ServiceReference(self.servicelist.getCurrentSelection())
		ref = service.ref
		evt = self.epgcache.lookupEventTime(ref, -1)
		if evt:
			epglist.append(evt)
		evt = self.epgcache.lookupEventTime(ref, -1, 1)
		if evt:
			epglist.append(evt)
		if epglist:
			self.session.open(EventViewEPGSelect, epglist[0], service, self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)

	def eventViewCallback(self, setEvent, setService, val):
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

	def openMultiServiceEPG(self):
		# not supported
		pass

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def closing(self):
		if self.pipAvailable:
			self.pipservice = None
		if not self.newServicePlayed:
			# we need to select the old service with bouquet
			if self.curBouquet != self.servicelist.getRoot():
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != self.curBouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(self.curBouquet)
			self.servicelist.setCurrentSelection(self.curRef.ref)
		self.close()
			
	def ok(self):
		# we have to close PiP first, otherwise the service-display is freezed
		if self.pipAvailable:
			self.pipservice = None
		# play selected service and close virtualzap
		self.newServicePlayed = True
		self.servicelist.zap()
		self.close()

	def CheckItNow(self):
		self.CheckForEPG.stop()
		self.updateInfos()

	# if available play service in PiP 
	def playService(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		if ref and ref.toString() != self.currentPiP:
			self.pipservice = eServiceCenter.getInstance().play(ref)
			if self.pipservice and not self.pipservice.setTarget(1):
				self.pipservice.start()
				self.currentPiP = ref.toString()
			else:
				self.pipservice = None
				self.currentPiP = ""


	# switch with numbers
	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number)

	def numberEntered(self, retval):
		if retval > 0:
			self.zapToNumber(retval)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if not servicelist is None:
			while num:
				serviceIterator = servicelist.getNext()
				if not serviceIterator.valid(): #check end of list
					break
				playable = not (serviceIterator.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
				if playable:
					num -= 1;
			if not num: #found service with searched number ?
				return serviceIterator, 0
		return None, num

	def zapToNumber(self, number):
		bouquet = self.servicelist.bouquet_root
		service = None
		serviceHandler = eServiceCenter.getInstance()
		bouquetlist = serviceHandler.list(bouquet)
		if not bouquetlist is None:
			while number:
				bouquet = bouquetlist.getNext()
				if not bouquet.valid(): #check end of list
					break
				if bouquet.flags & eServiceReference.isDirectory:
					service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if not service is None:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
		# update infos, no matter if service is none or not
		self.updateInfos()



class VirtualZapConfig(Screen, ConfigListScreen):

	skin = """
		<screen position="center,center" size="560,110" title="Virtual Zap Config" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="520,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.list = [ ]
		self.list.append(getConfigListEntry(_("Usage"), config.plugins.virtualzap.mode))
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			self.list.append(getConfigListEntry(_("Show with PiP"), config.plugins.virtualzap.usepip))
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply the new settings.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))
		

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()
