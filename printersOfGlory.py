#!/usr/local/bin/python2.7

import urllib2
from bs4 import BeautifulSoup
import simplejson as json
import threading
import time
from datetime import datetime
import calendar
from pymongo import MongoClient

client = MongoClient("mongodb://aegis:pn93WLnJI1@192.168.101.44/status", 27017)
db = client["status"]
col = db["machines"]

START = time.time()
TIMEOUT = 25
NUM_PRINTERS = 7
	
class Machine(object):
	'''Any type of library printer or copier'''
	def __init__(self, _ip, _id, _name):
		print "\tIt's alive!!!"
		self.machine = dict()
		self.machine["Timestamp"] = calendar.timegm(datetime.utcnow().utctimetuple())
		self.machine["Online"] = dict()
		self.machine["Info"] = dict()
		self.machine["Info"]["IP_Address"] = _ip
		self.machine["Info"]["TGIOA_ID"] = _id
		self.machine["Info"]["Name"] = _name
		self.source = dict()
		self.online = 1
		self.defineLinks()
		self.downloadLinks()
		if (True):
			while (self.thread.isAlive() or len(self.source) < self.numLinks):
				pass
			if (self.online == 1):		
				self.machine["Status"] = dict()
				self.machine["Supplies"] = dict()
				self.machine["Supplies"]["Paper"] = dict()
				self.machine["Supplies"]["Toner"] = dict()
				self.machine["Counter"] = dict()
				self.initializeContents()
				if (self.processSources()):
					self.processInfo()
					self.processStatus()
					self.processSupplies()
					self.processCounter()
				else:
					self.machine["Online"] = self.online
			else:
				self.machine["Online"] = self.online
		self.machine["Online"] = self.online
		
	def __del__(self):
		print "He was a good machine"
	
	def download(self, _url, _type):
		print "Downloading " + _url + " @ Type: " + _type
		try:
			response = urllib2.urlopen(_url, None, TIMEOUT)
			print "Adding " + _type + " to source"
			self.source[_type] = response
		except:
			print "Timeout: Failed to communicate with printer"
			print "Printer is offline or needs to be restarted"
			self.source[_type] = "ERROR"
			self.online = 0
			
	def processInfo(self):
		self.machine["Info"]["Machine_ID"] = self.info.find(text='Machine ID').parent.parent.contents[7].get_text()
		self.machine["Info"]["Device_Name"] = self.status.find(text='Device Name').parent.parent.contents[7].get_text()
		self.machine["Info"]["Host_Name"] = self.status.find(text='Host Name').parent.parent.contents[7].get_text()
		self.machine["Info"]["Model_Name"] = self.info.find(text='Model Name').parent.parent.contents[7].get_text()
			
	def processTray(self, _tray):
		for i in self.status.find_all('tr'):
			if (str(i.td.get_text()) == _tray):
				status = i.contents[3].td.img['alt']
				paperRemaining = self.processTrayInfo(i.contents[3].img['src'])
				paperSize = i.contents[7].td.get_text()
				if paperSize != "Unknown":
					paperOrientation = i.contents[7].find_all('td')[3].img['alt']
				else:
					paperOrientation = "Unknown"
		tray = dict()
		tray["Status"] = status
		tray["Paper_Size"] = paperSize
		tray["Paper_Orientation"] = paperOrientation
		tray["Paper_Remaining"] = paperRemaining
		return tray

	def processTrayInfo(self, _trayInfo):
		if (_trayInfo == "/images/deviceStPend16.gif"):
			return ""
		elif (_trayInfo == "/images/deviceStPNend16.gif"):
		  return ""
		elif (_trayInfo == "/images/deviceStP25_16.gif"):
			return "(25%)"
		elif (_trayInfo == "/images/deviceStP50_16.gif"):
			return "(50%)"
		elif (_trayInfo == "/images/deviceStP75_16.gif"):
			return "(75%)"
		elif (_trayInfo == "/images/deviceStP100_16.gif"):
			return "(100%)"
		else:
			return ""
			
	def returnMachine(self):
		return self.machine

class PrinterMeth(object):
	'''
	Base class for Derived that already inherits from Machine
	(BWPrinter, ColorPrinter)
	'''
			
	def defineLinks(self):
		self.numLinks = 4
		self.infoPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/status/configuration.cgi"
		self.statusPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/webArch/topPage.cgi"
		self.supplyPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/webprinter/supply.cgi"
		self.counterPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/status/getUnificationCounter.cgi"
	
	def downloadLinks(self):
		links = dict()
		links["info"] = self.infoPage
		links["status"] = self.statusPage
		links["supply"] = self.supplyPage
		links["counter"] = self.counterPage
		
		for key, link in links.items():
			self.thread = threading.Thread(target=self.download, args=(link, key))
			self.thread.start()
	
	def processSources(self):
		if (self.source["info"] != "ERROR"):
			self.info = BeautifulSoup(self.source["info"].read())
			self.status = BeautifulSoup(self.source["status"].read())
			self.supply = BeautifulSoup(self.source["supply"].read())
			self.counter = BeautifulSoup(self.source["counter"].read())
			return True
		else:
			return False
			
	def processToner(self, _toner):
		for i in self.status.find_all('tr'):
			if (str(i.td.get_text()) == _toner):
				status = i.contents[4].img['alt']
				if status == "":
					status = i.contents[8].get_text();	
				if status != "Cartridge Empty":
				  tonerRemaining = "%.2f" % round(float(i.contents[4].img['width'])/1.62, 2)
				else:
				  tonerRemaining = "0"
		toner = dict()
		toner["Status"] = status
		toner["Toner_Remaining"] = tonerRemaining
		return toner

class CopierMeth(object):
	'''
	Base class for Derived that already inherits from Machine
	In comparison to PrinterMeth, this class lacks "supply" and differs in toner processing
	(MFP, MFPFax, MFPStaff)
	'''
	
	def defineLinks(self):
		self.numLinks = 3
		self.infoPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/status/configuration.cgi"
		self.statusPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/webArch/topPage.cgi"
		self.counterPage = "http://" + self.machine["Info"]["IP_Address"] + "/web/guest/en/websys/status/getUnificationCounter.cgi"
		
	def downloadLinks(self):
		links = dict()
		links["info"] = self.infoPage
		links["status"] = self.statusPage
		links["counter"] = self.counterPage
		
		for key, link in links.items():
			self.thread = threading.Thread(target=self.download, args=(link, key))
			self.thread.start()
		
	def processSources(self):
		if (self.source["info"] != "ERROR"):
			self.info = BeautifulSoup(self.source["info"].read())
			self.status = BeautifulSoup(self.source["status"].read())
			self.counter = BeautifulSoup(self.source["counter"].read())
			return True
		else:
			return False
		
	def processToner(self, _toner):
		for i in self.status.find_all('tr'):
			if str(i.td.get_text()) == _toner:
				status = i.contents[4].get_text()
		toner = dict()
		toner["Status"] = status
		return toner
		
class BWPrinter(Machine, PrinterMeth):

	def __init__(self, _ip, _id, _name):
		print "BWPrinter,"
		super(BWPrinter, self).__init__(_ip, _id, _name)
		
	def initializeContents(self):
		self.machine["Supplies"]["Kits"] = dict()
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_A"] = dict()
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_B"] = dict()
		self.machine["Counter"]["Printer"] = dict()
		self.machine["Counter"]["Other"] = dict()
		self.machine["Status"]["Printer"] = dict()
			
	def processStatus(self):
		printer = self.status.find(text='Printer').parent.parent.parent.contents[5]
		self.machine["Status"]["Printer"]["Status"] = printer.font.get_text()
		self.machine["Status"]["Printer"]["Message"] = printer.img['alt']
		
	def processSupplies(self):
		trays = ["Tray 1", "Tray 2", "Tray 3 (LCT)", "Bypass Tray"]
		for tray in trays:
			self.machine["Supplies"]["Paper"][tray.replace(" ","_").replace("(","").replace(")","")] = self.processTray(tray)
		self.machine["Supplies"]["Toner"]["Black"] = self.processToner("Black")
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_A"]["Level"] = "%.2f" % round(float(self.supply.find(text='Maintenance Kit A').parent.parent.findAll('td')[9].img['width'])/1.62, 2)
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_A"]["Status"] = self.supply.find(text='Maintenance Kit A').parent.parent.findAll('img')[6]['alt']
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_B"]["Level"] = "%.2f" % round(float(self.supply.find(text='Maintenance Kit B').parent.parent.findAll('td')[9].img['width'])/1.62, 2)
		self.machine["Supplies"]["Kits"]["Maintenance_Kit_B"]["Status"] = self.supply.find(text='Maintenance Kit B').parent.parent.findAll('img')[6]['alt']
		
	def processCounter(self):
		self.machine["Counter"]["Printer"]["Black__White"] = self.counter.find(text='Black & White').parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Other"]["Duplex"] = self.counter.find(text='Duplex').parent.parent.findAll('td')[3].get_text()

class ColorPrinter(Machine, PrinterMeth):
	
	def __init__(self, _ip, _id, _name):
		print "ColorPrinter, "
		super(ColorPrinter, self).__init__(_ip, _id, _name)
		
	def initializeContents(self):
		self.machine["Supplies"]["Photoconductor_Unit"] = dict()
		self.machine["Supplies"]["Other"] = dict()
		self.machine["Supplies"]["Other"]["Intermediate_Transfer_Unit"] = dict()
		self.machine["Supplies"]["Other"]["Fusing_Unit_Transfer_Roller"] = dict()
		self.machine["Counter"]["Printer"] = dict()
		self.machine["Counter"]["Other"] = dict()
		self.machine["Status"]["Printer"] = dict()
			
	def processStatus(self):
		self.machine["Status"]["Printer"]["Status"] = self.status.find(text="Printer").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Printer"]["Message"] = self.status.find(text="Printer").parent.parent.parent.find("font").parent.find("img")['title']
		
	def processSupplies(self):
		trays = ["Tray 1", "Tray 2", "Tray 3 (LCT)", "Bypass Tray"]
		toners = ["Black", "Cyan", "Magenta", "Yellow"]
		for tray in trays:
			self.machine["Supplies"]["Paper"][tray.replace(" ","_").replace("(","").replace(")","")] = self.processTray(tray)
		for toner in toners:
			self.machine["Supplies"]["Toner"][toner] = self.processToner(toner)
		self.machine["Supplies"]["Photoconductor_Unit"]["Black"] = "%.2f" %round(float(self.supply.findAll(text="Black")[1].parent.parent.findAll('img')[5]['width'])/1.62, 2)
		self.machine["Supplies"]["Photoconductor_Unit"]["Color"] = "%.2f" %round(float(self.supply.find(text="Color").parent.parent.findAll('img')[5]['width'])/1.62, 2)
		if str(self.supply.find(text="Intermediate Transfer Unit").parent.parent.findAll('td')[11].find('img')) == "None":
			self.machine["Supplies"]["Other"]["Intermediate_Transfer_Unit"]["Status"] = self.supply.find(text="Intermediate Transfer Unit").parent.parent.findAll('td')[11].getText()
		else:
			self.machine["Supplies"]["Other"]["Intermediate_Transfer_Unit"]["Status"] = self.supply.find(text="Intermediate Transfer Unit").parent.parent.findAll('td')[11].find('img')['alt']
		self.machine["Supplies"]["Other"]["Intermediate_Transfer_Unit"]["Level"] = "%.2f" % round(float(self.supply.find(text="Intermediate Transfer Unit").parent.parent.findAll('img')[5]['width'])/1.62, 2)
		self.machine["Supplies"]["Other"]["Fusing_Unit_Transfer_Roller"]["Status"] = self.supply.find(text="Fusing Unit/Transfer Roller").parent.parent.findAll('img')[6]['alt']
		self.machine["Supplies"]["Other"]["Fusing_Unit_Transfer_Roller"]["Level"] = "%.2f" % round(float(self.supply.find(text="Fusing Unit/Transfer Roller").parent.parent.findAll('img')[5]['width'])/1.62, 2)
		self.machine["Supplies"]["Other"]["Waste_Toner_Bottle"] = self.supply.find(text="Waste Toner Bottle").parent.parent.findAll('td')[7].get_text()
		
	def processCounter(self):
		for i in ["Black & White", "Full Color", "Single Color", "Two-color"]:
			self.machine["Counter"]["Printer"][i.replace(" ","_").replace("&","").replace("-","_")] = self.counter.find(text=i).parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Other"]["Duplex"] = self.counter.find(text='Duplex').parent.parent.findAll('td')[3].get_text()
		
class MFP(Machine, CopierMeth):

	def __init__(self, _ip, _id, _name):
		print "MFP, "
		super(MFP, self).__init__(_ip, _id, _name)
		
	def initializeContents(self):
		self.machine["Counter"]["Printer"] = dict()
		self.machine["Counter"]["Copier"] = dict()
		self.machine["Counter"]["Scanner"] = dict()
		self.machine["Counter"]["Other"] = dict()
		self.machine["Status"]["Printer"] = dict()
		self.machine["Status"]["Copier"] = dict()
		self.machine["Status"]["Scanner"] = dict()
	
	def processStatus(self):
		self.machine["Status"]["Printer"]["Status"] = self.status.find(text="Printer").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Printer"]["Message"] = self.status.find(text="Printer").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Copier"]["Status"] = self.status.find(text="Copier").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Copier"]["Message"] = self.status.find(text="Copier").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Scanner"]["Status"] = self.status.find(text="Scanner").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Scanner"]["Message"] = self.status.find(text="Scanner").parent.parent.parent.find("font").parent.img['title']
		
	def processSupplies(self):
		trays = ["Tray 1", "Tray 2", "Tray 3", "Tray 4", "Bypass Tray"]
		for tray in trays:
			self.machine["Supplies"]["Paper"][tray.replace(" ","_").replace("(","").replace(")","")] = self.processTray(tray)
		self.machine["Supplies"]["Toner"]["Black"] = self.processToner("Black")
		
	def processCounter(self):
		self.machine["Counter"]["Copier"]["Black__White"] = self.counter.find(text="Black & White").parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Printer"]["Black__White"] = self.counter.findAll(text="Black & White")[1].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Black__White"] = self.counter.findAll(text="Black & White")[2].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Color"] = self.counter.find(text="Color").parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Other"]["Duplex"] = self.counter.find(text="Duplex").parent.parent.findAll('td')[3].get_text()

class MFPFax(Machine, CopierMeth):

	def __init__(self, _ip, _id, _name):
		print "MFPFax, "
		super(MFPFax, self).__init__(_ip, _id, _name)
	
	def initializeContents(self):
		self.machine["Counter"]["Printer"] = dict()
		self.machine["Counter"]["Copier"] = dict()
		self.machine["Counter"]["Fax"] = dict()
		self.machine["Counter"]["Scanner"] = dict()
		self.machine["Counter"]["Other"] = dict()
		self.machine["Status"]["Printer"] = dict()
		self.machine["Status"]["Copier"] = dict()
		self.machine["Status"]["Fax"] = dict()
		self.machine["Status"]["Scanner"] = dict()
	
	def processStatus(self):
		self.machine["Status"]["Printer"]["Status"] = self.status.find(text="Printer").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Printer"]["Message"] = self.status.find(text="Printer").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Copier"]["Status"] = self.status.find(text="Copier").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Copier"]["Message"] = self.status.find(text="Copier").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Fax"]["Status"] = self.status.find(text="Fax").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Fax"]["Message"] = self.status.find(text="Fax").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Scanner"]["Status"] = self.status.find(text="Scanner").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Scanner"]["Message"] = self.status.find(text="Scanner").parent.parent.parent.find("font").parent.img['title']
		
	def processSupplies(self):
		trays = ["Tray 1", "Tray 2", "Bypass Tray"]
		for tray in trays:
			self.machine["Supplies"]["Paper"][tray.replace(" ","_").replace("(","").replace(")","")] = self.processTray(tray)
		self.machine["Supplies"]["Toner"]["Black"] = self.processToner("Black")
		
	def processCounter(self):
		self.machine["Counter"]["Copier"]["Black__White"] = self.counter.find(text="Black & White").parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Printer"]["Black__White"] = self.counter.findAll(text="Black & White")[1].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Fax"]["Black__White"] = self.counter.findAll(text="Black & White")[2].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Black__White"] = self.counter.findAll(text="Black & White")[3].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Color"] = self.counter.find(text="Color").parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Other"]["Duplex"] = self.counter.find(text="Duplex").parent.parent.findAll('td')[3].get_text()

class MFPStaff(Machine, CopierMeth):
	
	def __init__(self, _ip, _id,_name):
		print "MFP Staff, "
		super(MFPStaff, self).__init__(_ip, _id, _name)
		
	def initializeContents(self):
		self.machine["Counter"]["Printer"] = dict()
		self.machine["Counter"]["Copier"] = dict()
		self.machine["Counter"]["Fax"] = dict()
		self.machine["Counter"]["Scanner"] = dict()
		self.machine["Counter"]["Other"] = dict()
		self.machine["Status"]["Printer"] = dict()
		self.machine["Status"]["Copier"] = dict()
		self.machine["Status"]["Fax"] = dict()
		self.machine["Counter"]["Send_TX_Total"] = dict()
		self.machine["Counter"]["Fax_Transmission"] = dict()
		self.machine["Status"]["Scanner"] = dict()
	
	def processStatus(self):
		self.machine["Status"]["Printer"]["Status"] = self.status.find(text="Printer").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Printer"]["Message"] = self.status.find(text="Printer").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Copier"]["Status"] = self.status.find(text="Copier").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Copier"]["Message"] = self.status.find(text="Copier").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Fax"]["Status"] = self.status.find(text="Fax").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Fax"]["Message"] = self.status.find(text="Fax").parent.parent.parent.find("font").parent.img['title']
		self.machine["Status"]["Scanner"]["Status"] = self.status.find(text="Scanner").parent.parent.parent.find("font").get_text()
		self.machine["Status"]["Scanner"]["Message"] = self.status.find(text="Scanner").parent.parent.parent.find("font").parent.img['title']
	
	def processToner(self, _toner):
		for i in self.status.find_all('tr'):
			if (str(i.td.get_text()) == _toner):
				status = i.contents[4].img['alt']
				if status == "":
					status = i.contents[8].get_text();	
				if status != "Cartridge Empty":
				  tonerRemaining = "%.2f" % round(float(i.contents[4].img['width'])/1.62, 2)
				else:
				  tonerRemaining = "0"
		toner = dict()
		toner["Status"] = status
		toner["Toner_Remaining"] = tonerRemaining
		return toner
	
	def processSupplies(self):
		trays = ["Tray 1", "Tray 2", "Tray 3", "Tray 4", "Bypass Tray"]
		toners = ["Black", "Cyan", "Magenta", "Yellow"]
		for tray in trays:
			self.machine["Supplies"]["Paper"][tray.replace(" ","_").replace("(","").replace(")","")] = self.processTray(tray)
		for toner in toners:
			self.machine["Supplies"]["Toner"][toner] = self.processToner(toner)
	
	def processCounter(self):
		for i in ["Black & White", "Full Color", "Single Color", "Two-color"]:
			self.machine["Counter"]["Copier"][i.replace(" ","_").replace("&","")] = self.counter.find(text=i).parent.parent.findAll('td')[3].get_text()
			self.machine["Counter"]["Printer"][i.replace(" ","_").replace("&","")] = self.counter.findAll(text=i)[1].parent.parent.findAll('td')[3].get_text()	
		self.machine["Counter"]["Fax"]["Black__White"] = self.counter.findAll(text="Black & White")[2].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Send_TX_Total"]["Black__White"] = self.counter.findAll(text="Black & White")[3].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Send_TX_Total"]["Color"] = self.counter.find(text="Color").parent.parent.findAll('td')[3].get_text()	
		self.machine["Counter"]["Fax_Transmission"]["Total"] = self.counter.find(text="Total").parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Black__White"] = self.counter.findAll(text="Black & White")[4].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Scanner"]["Color"] = self.counter.findAll(text="Color")[1].parent.parent.findAll('td')[3].get_text()
		self.machine["Counter"]["Other"]["Duplex"] = self.counter.find(text="Duplex").parent.parent.findAll('td')[3].get_text()

printers = dict()
printers[0] = dict()
printers[0]["ip"] = "128.238.69.23"
printers[0]["id"] = "58543"
printers[0]["name"] = "DBLIBBW1"
printers[0]["type"] = "BWPrinter"
printers[1] = dict()
printers[1]["ip"] = "128.238.69.19"
printers[1]["id"] = "71444"
printers[1]["name"] = "DBLIBBW2"
printers[1]["type"] = "BWPrinter"
printers[2] = dict()
printers[2]["ip"] = "128.238.69.24"
printers[2]["id"] = "58202"
printers[2]["name"] = "DBLIBBW3"
printers[2]["type"] = "MFP"
printers[3] = dict()
printers[3]["ip"] = "128.238.69.20"
printers[3]["id"] = "59234"
printers[3]["name"] = "DBLIBCOL1"
printers[3]["type"] = "ColorPrinter"
printers[4] = dict()
printers[4]["ip"] = "128.238.69.21"
printers[4]["id"] = "58193"
printers[4]["name"] = "DBLIBMFP1"
printers[4]["type"] = "MFP"
printers[5] = dict()
printers[5]["ip"] = "128.238.69.22"
printers[5]["id"] = "58188"
printers[5]["name"] = "DBLIBMFPF1"
printers[5]["type"] = "MFPFax"
printers[6] = dict()
printers[6]["ip"] = "128.238.142.40"
printers[6]["id"] = "58552"
printers[6]["name"] = "DBLIBMFPSTAFF"
printers[6]["type"] = "MFPStaff"

machines = dict()

def construct(_ip,_id,_name,_type):
	if _type == "BWPrinter":
		machines[_name] = BWPrinter(_ip,_id,_name).returnMachine()
	elif _type == "MFP":
		machines[_name] = MFP(_ip,_id,_name).returnMachine()
	elif _type == "ColorPrinter":
		machines[_name] = ColorPrinter(_ip,_id,_name).returnMachine()
	elif _type == "MFPFax":
		machines[_name] = MFPFax(_ip,_id,_name).returnMachine()
	elif _type == "MFPStaff":
		machines[_name] = MFPStaff(_ip,_id,_name).returnMachine()
	else:
		machines[_name] = "Unknown Type"

for i in range(0,NUM_PRINTERS):
	_ip = printers[i]["ip"]
	_id = printers[i]["id"]
	_name = printers[i]["name"] 
	_type = printers[i]["type"]
	thread = threading.Thread(target=construct, args=(_ip,_id,_name,_type))
	thread.start()

if (True):
	while (len(machines) < 7):
		pass
	print "Adding to database..."
	col.insert(machines)
	print "COMPLETED in " + str(time.time() - START) + " seconds."