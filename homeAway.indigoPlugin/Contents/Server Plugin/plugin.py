#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# EVENTS Plugin
# Developed by Karl Wachs
# karlwachs@me.com

import datetime
import simplejson as json
import subprocess
import fcntl
import os
import sys
import pwd
import time
import Queue
import random
import plistlib

import threading
import copy
import json

import logging

## Static parameters, not changed in pgm
################################################################################
# noinspection PyUnresolvedReferences,PyPep8,PyPep8,PyPep8
class Plugin(indigo.PluginBase):
	####-----------------             ---------
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

		#pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
		#self.plugin_file_handler.setFormatter(pfmt)


		self.getInstallFolderPath			= indigo.server.getInstallFolderPath()+"/"
		self.indigoPath						= indigo.server.getInstallFolderPath()+"/"
		self.indigoRootPath 				= indigo.server.getInstallFolderPath().split("Indigo")[0]
		self.pathToPlugin 					= self.completePath(os.getcwd())

		self.indigoPath						= indigo.server.getInstallFolderPath()+"/"
		major, minor, release 				= map(int, indigo.server.version.split("."))
		self.indigoVersion					= major
		self.pluginVersion					= pluginVersion
		self.pluginId						= pluginId
		self.pluginName						= pluginId.split(".")[-1]
		self.myPID							= os.getpid()
		self.pluginState					= "init"
		self.pluginShortName 				= "homeAway"

		self.myPID 							= os.getpid()
		self.MACuserName					= pwd.getpwuid(os.getuid())[0]

		self.MAChome						= os.path.expanduser(u"~")
		self.userIndigoDir					= self.MAChome + "/indigo/"
		self.indigoPreferencesPluginDir 	= self.getInstallFolderPath+"Preferences/Plugins/"+self.pluginId+"/"
		self.indigoPluginDirOld				= self.userIndigoDir + self.pluginShortName+"/"
		self.PluginLogFile					= self.indigoPath.split("Plugins/")[0]+"Logs/"+self.pluginId+"/plugin.log"


	####-----------------             ---------
	def __del__(self):
		indigo.PluginBase.__del__(self)

######################################################################################
	# INIT    ## START
######################################################################################

	####----------------- @ startup set global parameters, create directories etc ---------
	def startup(self):
	
		self.checkPluginName()


		indigo.server.log("initializing	 ... ")

		indigo.server.log(u"path To files:      =================")
		indigo.server.log(u"indigo              "+self.indigoRootPath)
		indigo.server.log(u"installFolder       "+self.indigoPath)
		indigo.server.log(u"plugin.py           "+self.pathToPlugin)
		indigo.server.log(u"Plugin params       "+self.indigoPreferencesPluginDir)
		indigo.server.log(u"PluginLogFile       "+self.PluginLogFile )
		indigo.server.log(u"Plugin short Name   "+self.pluginShortName)
		indigo.server.log(u"my PID              "+str(self.myPID))	 


		formats=	{   logging.THREADDEBUG: "%(asctime)s %(msg)s",
						logging.DEBUG:       "%(asctime)s %(msg)s",
						logging.INFO:        "%(msg)s",
						logging.WARNING:     "%(asctime)s %(msg)s",
						logging.ERROR:       "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s",
						logging.CRITICAL:    "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s" }

		date_Format = { logging.THREADDEBUG: "%d %H:%M:%S",
						logging.DEBUG:       "%d %H:%M:%S",
						logging.INFO:        "%H:%M:%S",
						logging.WARNING:     "%H:%M:%S",
						logging.ERROR:       "%Y-%m-%d %H:%M:%S",
						logging.CRITICAL:    "%Y-%m-%d %H:%M:%S" }
		formatter = LevelFormatter(fmt="%(msg)s", datefmt="%Y-%m-%d %H:%M:%S", level_fmts=formats, level_date=date_Format)

		self.plugin_file_handler.setFormatter(formatter)
		self.indiLOG = logging.getLogger("Plugin")  
		self.indiLOG.setLevel(logging.THREADDEBUG)

		self.indigo_log_handler.setLevel(logging.INFO)

		self.indiLOG.log(20,"=========================   initializing   ==============================================")

		indigo.server.log(  u"path To files:          ==================")
		indigo.server.log(  u"indigo                  {}".format(self.indigoRootPath))
		indigo.server.log(  u"installFolder           {}".format(self.indigoPath))
		indigo.server.log(  u"plugin.py               {}".format(self.pathToPlugin))
		indigo.server.log(  u"Plugin params           {}".format(self.indigoPreferencesPluginDir))

		self.indiLOG.log( 0, "!!!!INFO ONLY!!!!  logger  enabled for   0             !!!!INFO ONLY!!!!")
		self.indiLOG.log( 5, "!!!!INFO ONLY!!!!  logger  enabled for   THREADDEBUG   !!!!INFO ONLY!!!!")
		self.indiLOG.log(10, "!!!!INFO ONLY!!!!  logger  enabled for   DEBUG         !!!!INFO ONLY!!!!")
		self.indiLOG.log(20, "!!!!INFO ONLY!!!!  logger  enabled for   INFO          !!!!INFO ONLY!!!!")
		self.indiLOG.log(30, "!!!!INFO ONLY!!!!  logger  enabled for   WARNING       !!!!INFO ONLY!!!!")
		self.indiLOG.log(40, "!!!!INFO ONLY!!!!  logger  enabled for   ERROR         !!!!INFO ONLY!!!!")
		self.indiLOG.log(50, "!!!!INFO ONLY!!!!  logger  enabled for   CRITICAL      !!!!INFO ONLY!!!!")

		indigo.server.log(  u"check                   {}  <<<<    for detailed logging".format(self.PluginLogFile))
		indigo.server.log(  u"Plugin short Name       {}".format(self.pluginShortName))
		indigo.server.log(  u"my PID                  {}".format(self.myPID))	 
		indigo.server.log(  u"set params for indigo V {}".format(self.indigoVersion))	 
	
		if not self.moveToIndigoPrefsDir(self.indigoPluginDirOld, self.indigoPreferencesPluginDir):
				exit()

		self.getBasicParams()


	
		return 

   ####----check THIS pluging name etc     ---------
	def checkPluginName(self):
		 if self.pathToPlugin.find("/" + self.pluginName + ".indigoPlugin/") == -1:
			self.errorLog(u"--------------------------------------------------------------------------------------------------------------")
			self.errorLog(u"The pluginName is not correct, please reinstall or rename")
			self.errorLog(u"It should be   /Libray/....../Plugins/" + self.pluginName + ".indigoPlugin")
			p = max(0, self.pathToPlugin.find("/Contents/Server"))
			self.errorLog(u"It is: " + self.pathToPlugin[:p])
			self.errorLog(u"please check your download folder, delete old *.indigoPlugin files or this will happen again during next update")
			self.errorLog(u"---------------------------------------------------------------------------------------------------------------")
			self.sleep(2000)
			exit(1)
		 
		
	###########################    read / save stuff   ############################
			
	####----basic params    ---------
	def getBasicParams(self):
		self.myPID = os.getpid()
		self.loopSleep              = 1
		self.quitNow                = ""        
		self.pluginState            = "start"
		self.updateEVENTS           = {}
		self.selectedEventFunction  = ""
		self.selectedEvent          = ""
		self.triggerList            = []
		self.SENSORSelected         = "0"
		self.DoorSelected           = "0"
		self.enableEventTracking    = False
		self.logFileActive          = ""
		self.logFile                = ""
		self.debugLevel             = []
		self.doorLoopWait           = 99
		self.selectDeviceManagement = ""
		self.qualifiedDevicesUpdated = 0
		self.qualifiedDevices       = {}
		self.qualifiedDoorsUpdated  = 0
		self.qualifiedDoors         = {}
		self.autoAddDevices         = "ON"
		self.eventUpdateWait        = 20
		self.waitAfterStartForFirstTrigger = 60  # secs
		self.eventVariablePrefix    =  "EVENT"
		self.acceptableStateValues  = ["up","down","expired","on","off","yes","no","true","false","t","f","1","0","ja","nein","an","aus","open","closed","auf","zu"]
		self.emptyDEVICE            = {"up":{"lastChange":0,"signalReceived":"","state":"","delayTime":0},"down":{"lastChange":0,"signalReceived":"","state":"","delayTime":0},"valueForON":"","pluginId":"","name":"","used":False}
		self.emptyDOOR              = {"lastChange":0,"lastChangeDT":"","signalReceived":"","state":"","name":"","used":False,"requireStatusChange":True,"pollingIntervall":10,"lastCheck":0}
		self.evPropsToPrint         = ["sensorsMembers","sensorsCountTRUE","sensorsTrigger","sensorsTriggerTime","doorsMembers","doorsTimeWindowBefore","doorsTimeWindowAfter",
									   "atleastOne","triggerTimeLast","minTimeTriggerBeforeRepeat","delayAfterSensorTrigger","resetEVENTwoDoors","lastsyncWithDevices",
									   "variableConditionID","deviceConditionID"]
		self.PLUGINS                ={"excluded":{},"acceptable":{},"used":{},"all":{}}
		for item in ["com.perceptiveautomation.indigoplugin.zwave","com.karlwachs.utilities","com.karlwachs.INDIGOplotD","com.ssi.indigoplugin.SONOS",\
					  "com.karlwachs.SATI","com.schollnick.indigoplugin.Survey","com.indigodomo.indigoserver", "com.karlwachs.shutdownAction", \
					  "com.perceptiveautomation.indigoplugin.ActionCollection", "com.perceptiveautomation.indigoplugin.InsteonCommands",\
					  "com.perceptiveautomation.indigoplugin.devicecollection", "com.perceptiveautomation.indigoplugin.itunes",\
					  "com.perceptiveautomation.indigoplugin.sql-logger", "com.perceptiveautomation.indigoplugin.timersandpesters"]:
			self.PLUGINS["excluded"][item] = False
			self.PLUGINS["all"][item] = False

		for item in ["com.karlwachs.uniFiAP","com.karlwachs.fingscan","com.karlwachs.piBeacon"]:
			self.PLUGINS["acceptable"][item] = True
			self.PLUGINS["all"][item] = True


		self.getDebugSettings(init=True)

		self.readDEVICES()
		self.readDOORS()
		self.readPLUGINS()
		self.getActivePlugins()
		self.getQualifiedDevices()
		self.updateFields()

		return
   ####----update fileds      ---------
	def updateFields(self): # cleanup if case tehre are some fileds missingo should not be tehre 
		
		return



######################################################################################
	# menues ...
######################################################################################

######################################################################################
	 # menues   ==> EVENTS
######################################################################################

	def getEventConfigUiValues(self,valuesDict, typeId, targetId):
		#indigo.server.log("getEventConfigUiValues:  typeId: "+ unicode(typeId)+"  targetId:"+ unicode(targetId)+"  valuesDict:"+unicode(valuesDict))

		typeIdSplit = typeId.split("-")
		if targetId ==0:
			valuesDict["oneAll"]                = typeIdSplit[0]
			valuesDict["homeAway"]              = typeIdSplit[1]
			valuesDict["noDoors"]               = typeIdSplit[2]
			
			valuesDict["doorsMembers"]                  = "{}"
			valuesDict["sensorsMembers"]                = "{}"
			valuesDict["triggerTimeLast"]               = 0 
			valuesDict["sensorsTrigger"]                = False
			valuesDict["sensorsTriggerTime"]            = 0
			valuesDict["sensorsCountTRUE"]              = 0
			valuesDict["newOrExistingSensor"]           = "new"
			valuesDict["newOrExistingDoor"]             = "new"
			valuesDict["doorsTimeWindowBefore"]         = "300"
			valuesDict["doorsTimeWindowAfter"]          = "300"
			valuesDict["atleastOne"]                    = "2-1/0-1"
			valuesDict["lastDoorChange"]                = 0
			self.SENSORSMembers ={}
			self.doorsMembers ={}
		else:
			if "lastDoorChange" not in valuesDict:        valuesDict["lastDoorChange"]            = 0
			if "sensorsMembers" not in valuesDict:        valuesDict["sensorsMembers"]            = "{}"
			if "doorsMembers" not in valuesDict:          valuesDict["doorsMembers"]              = "{}"
			if "sensorsTrigger" not in valuesDict:        valuesDict["sensorsTrigger"]            = False
			if "sensorsTriggerTime" not in valuesDict:    valuesDict["sensorsTriggerTime"]        = 0
			if "sensorsCountTRUE" not in valuesDict:      valuesDict["sensorsCountTRUE"]          = 0
			if "newOrExistingSensor" not in valuesDict:   valuesDict["newOrExistingSensor"]       = "new"
			if "newOrExistingDoor" not in valuesDict:     valuesDict["newOrExistingDoor"]         = "new"
			if "doorsTimeWindowBefore" not in valuesDict: valuesDict["doorsTimeWindowBefore"]     = "300"
			if "atleastOne" not in valuesDict:            valuesDict["atleastOne"]                = "2-1/10-1"
			if "lastDoorChange" not in valuesDict:        valuesDict["lastDoorChange"]            = 0
			valuesDict["oneAll"]                        = typeIdSplit[0]
			valuesDict["homeAway"]                      = typeIdSplit[1]
			valuesDict["noDoors"]                       = typeIdSplit[2]
			self.SENSORSMembers, valuesDict["sensorsMembers"] = self.fixDICTEmpty(json.loads(valuesDict["sensorsMembers"]))

			self.doorsMembers,   valuesDict["doorsMembers"]   = self.fixDICTEmpty(json.loads(valuesDict["doorsMembers"]))

		if typeIdSplit[2] == "no":
			valuesDict["newOrExistingDoor"]   = "no"

		#self.deviceConditionID =""                        
		
		return super(Plugin, self).getEventConfigUiValues(valuesDict, typeId, targetId)

 
	# event menus
	def fixDICTEmpty(self,  D1):
		if "" in D1:
			del D1[""]
		VD = json.dumps(D1)
		return D1, VD
 
 
  ####-----------------  ---------
	def filterVariables(self, filter, valuesDict, typeId, targetId):
		xList =[]
		for var in indigo.variables :
			xList.append(( unicode(var.id),var.name+"   ; currentV: "+ var.value))
		xList.append(("0","==== off, do not use ===="))
		return xList
 
  ####-----------------  ---------
	def filterDevices(self, filter, valuesDict, typeId, targetId):
		xList =[]
		for dev in indigo.devices:
			xList.append(( unicode(dev.id),dev.name))
		xList.append(("0","==== off, do not use ===="))
		return xList
	####-----------------  ---------
	def buttonConfirmDeviceStateCALLBACK(self, valuesDict, typeId, devId):
		#self.deviceConditionID = valuesDict["deviceConditionID"]
		return valuesDict

  ####-----------------  ---------
	def filterDevStates(self, filter, valuesDict, typeId, targetId):
		xList =[]
		if len(valuesDict) < 2:                         return [("0","")]
		if "deviceConditionID" not in valuesDict:       return [("0","")]
		if valuesDict["deviceConditionID"] in ["0",""]: return [("0","")]
		dev = indigo.devices[int(valuesDict["deviceConditionID"])]
		for state in dev.states:
			xList.append((state,state+"   ; currentV: "+unicode(dev.states[state]) ))
		xList.append(("0","==== off, do not use ===="))
		return xList


   ####-----------------  --------- DEVICES
   ####-----------------  ---------
	def filterSensorsEvent(self, filter, valuesDict, typeId, targetId):
		xList =[]
		#indigo.server.log("filterSensorsEvent:  typeId: "+ unicode(typeId)+"  targetId:"+ unicode(targetId)+"  valuesDict:"+unicode(valuesDict))
		if len(valuesDict) == 0: 
			#indigo.server.log("filterSensorsEvent:  vd empty returning")
			return xList

		if filter == "existing":
			for DEVICEid in self.SENSORSMembers:
				dd = self.splitDev(DEVICEid)
				xList.append(( DEVICEid, self.SENSORS[DEVICEid]["name"]+"-"+dd[1]))

		else:
			for DEVICEid in self.SENSORS:
				if DEVICEid not in self.SENSORSMembers: 
					dd = self.splitDev(DEVICEid)
					xList.append(( DEVICEid, self.SENSORS[DEVICEid]["name"]+"-"+dd[1] ))

		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "xList "+ str(xList), mType="filterSensorsEvent" )
		return xList


	####-----------------  ---------
	def buttonconfirmRemoveSensorMemberCALLBACK(self, valuesDict, typeId, devId):
		try:
			if valuesDict["newOrExistingSensor"] !="delete": return 
			if len(valuesDict["selectExistingSensor"]) > 5:
				if valuesDict["selectExistingSensor"] in self.SENSORSMembers:
					del self.SENSORSMembers[valuesDict["selectExistingSensor"]]
					self.SENSORSMembers, valuesDict["sensorsMembers"] = self.fixDICTEmpty(self.SENSORSMembers)
		except Exception, e:
			self.indiLOG.log(40,u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return valuesDict

	####-----------------  ---------
	def buttonConfirmSensorSettingsCALLBACK(self, valuesDict, typeId, devId):
		valuesDict["msg"]                       = "settings saved"
		if valuesDict["newOrExistingSensor"] in ["new","existing"]:   
			if valuesDict["selectNewSensor"] not in self.SENSORSMembers:
				self.SENSORSMembers[valuesDict["selectNewSensor"]] =""
				self.SENSORSMembers, valuesDict["sensorsMembers"] = self.fixDICTEmpty(self.SENSORSMembers)
		else:
			valuesDict["msg"]                       = "error"
		return valuesDict


   ####-----------------  --------- DOORS
   ####-----------------  ---------
	def filterDoorsEvent(self, filter, valuesDict, typeId, targetId):
		xList =[]
		try:
			if self.decideMyLog(u"SETUP"):
					self.myLog(text = "typeId: "+ unicode(typeId)+"  targetId:"+ unicode(targetId)+"  valuesDict:"+unicode(valuesDict), mType="filterDoorsEvent")
			if len(valuesDict) == 0: 
				#indigo.server.log("filterDoorsInEvent:  vd empty returning")
				return xList

			if filter == "existing":
				for DEVICEid in self.doorsMembers:
					dd = self.splitDev(DEVICEid)
					xList.append(( DEVICEid, self.DOORS[DEVICEid]["name"]+"-"+dd[1]))

			elif  filter == "new":
				for DEVICEid in self.DOORS:
					if DEVICEid not in self.doorsMembers: 
						dd = DEVICEid.split(":::")
						xList.append(( DEVICEid, self.DOORS[DEVICEid]["name"]+"-"+dd[1] ))

			if self.decideMyLog(u"SETUP"): 
				self.myLog(text = "filterDoorsEvent    xList "+ str(xList) )
		except Exception, e:
			self.indiLOG.log(40,u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
			self.indiLOG.log(40,u"doorsMembers: "+unicode(self.doorsMembers) )
		return xList

	####-----------------  ---------
	def buttonConfirmRemoveDoorMemberCALLBACK(self, valuesDict, typeId, devId):
		try:
			if valuesDict["newOrExistingDoor"] !="delete": return 
			if valuesDict["selectExistingDoor"] in self.doorsMembers:
				del self.doorsMembers[valuesDict["selectExistingDoor"]]
				self.doorsMembers, valuesDict["doorsMembers"] = self.fixDICTEmpty(self.doorsMembers)
		except Exception, e:
			self.indiLOG.log(40,u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return valuesDict

	####-----------------  ---------
	def buttonConfirmDoorsSettingsCALLBACK(self, valuesDict, typeId, devId):
		valuesDict["msg"]                       = "settings saved"

		if valuesDict["newOrExistingDoor"] =="new":
			if valuesDict["selectNewDoor"] not in self.doorsMembers:
				self.doorsMembers[valuesDict["selectNewDoor"]]=""
				self.doorsMembers, valuesDict["doorsMembers"] = self.fixDICTEmpty(self.doorsMembers)

		elif valuesDict["newOrExistingDoor"] =="existing":
			if valuesDict["selectNewDoor"] not in self.doorsMembers:
				self.doorsMembers[valuesDict["selectNewDoor"]]=""
				self.doorsMembers, valuesDict["doorsMembers"] = self.fixDICTEmpty(self.doorsMembers)
		else:
			valuesDict["msg"]                       = "error"

		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = unicode(valuesDict), mType="butConfirmDoorsSettings")

		return valuesDict

	def validateEventConfigUi(self, valuesDict, typeId, eventId):
		return True, valuesDict



######################################################################################
	# config  callbacks and filters
######################################################################################
	####-----------------  save  config parameters---------
	def validatePrefsConfigUi(self, valuesDict):

		self.getDebugSettings(init=False, theDict=valuesDict)
		self.checkPluginsForUpdates()
		
		self.saveSENSORS()

		return True, valuesDict

######################################################################################
	####-----------------  CONFIG item  PLUGINs 
######################################################################################
 
	def filterExistingPlugins(self,  filter="", valuesDict=None, typeId="", targetId=0):

		retList = []

		for id in self.PLUGINS["used"]:
			retList.append((id,id) )
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>> ADD new plugin"))
		return retList

	####-----------------  ---------
	def filterNewPlugins(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		retList = []
		for id in self.PLUGINS["all"]:
			if id not in self.PLUGINS["used"]:
				retList.append((id,id) )
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>>no new device"))
		return retList

	####-----------------  ---------
	def buttonConfirmExistingOrNewPluginCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		self.PluginSelected = valuesDict["selectedExistingOrNewPlugin"]
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ self.PluginSelected +"  "+unicode(valuesDict), mType="butConfirmExistingOrNewPlugin")
		valuesDict["text0-1"]              = "  and then confirm !"

		try:
			if self.PluginSelected == "0":
				valuesDict["DefinePluginsAndNew"]  = True
				valuesDict["DefinePluginsAndOld"]  = False
			else:
				valuesDict["DefinePluginsAndOld"]  = True
				valuesDict["DefinePluginsAndNew"]  = False

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict
		
	####-----------------  ---------
	def buttonConfirmDeletePluginCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "pluginid  "+ str(self.PluginSelected) +"  "+unicode(valuesDict), mType="butConfirmDeletePlugin")
		valuesDict["DefinePluginsAndNew"]  = False
		valuesDict["DefinePluginsAndOld"]  = False

		try:
			if self.PluginSelected !="0":
				deldev = {}
				if self.PluginSelected in self.PLUGINS["used"]:
					del self.PLUGINS["used"][self.PluginSelected]
				self.PLUGINS["excluded"][self.PluginSelected] = True
				if self.PluginSelected in self.PLUGINS["acceptable"]:
					del self.PLUGINS["acceptable"][self.PluginSelected]
				self.savePLUGINS()
			
		except  Exception, e:
				self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict

	####-----------------  ---------
	def buttonConfirmPluginNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
		   self.myLog(text = "IndigoID "+ self.PluginSelected +"  "+unicode(valuesDict), mType="butConfirmExistingPlugin")
		self.PluginSelected = valuesDict["selectedNewPluginID"]
		try:
			if self.PluginSelected !="0":
				valuesDict["DefinePluginsAndOld"]  = False
				valuesDict["DefinePluginsAndNew"]  = False
				self.PLUGINS["used"][self.PluginSelected] = True
				self.PLUGINS["acceptable"][self.PluginSelected] = True
				if self.PluginSelected in self.PLUGINS["excluded"]:
					del self.PLUGINS["excluded"][self.PluginSelected]
				self.savePLUGINS()
			else:
				valuesDict["selectStatesOK"]       = False
				valuesDict["DefinePluginsAndNew"]  = False
				valuesDict["DefinePluginsAndOld"]  = False
				valuesDict["msg"]                  = "Plugin NOT added"
			

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict



######################################################################################
	 # menues   ==> plugin Menu
######################################################################################

		
	####-----------------  ---------
	def printHELP(self,valuesDict,typeId):
		indigo.server.log("\n\
# HOME AWAY plugin for indigo\n\
\n\
## Purpose \n\
define **triggers** that allow a combination of information from different indigo devices (sensors) to be combined to set home / away events.\n\
It can be combined with a door time gate and other variable or device/state conditions to veto a trigger \n\
\n\
## What / how\n\
The plugin can currently use info from fingscan(any ip device), unifi(any ip device) and pibeacon devices(ibeacons, BLE devices ..) called sensors in the following. \n\
Any plugin that can send *indigo broadcasts* could participate.\n\
Thesensor are combined with an \"AND\" to indicate how many sensors have come home or went away . NOT how many are home or are away - a slight difference. \n\
A snapshot would poll all devices and add their states. \n\
This plugin will receive updates on changes and then determine if a sensor went away or came home. \n\
THEN it determines how many came home / went away.\n\
In addition the plugin can use information from any other on/off type device (called doors in the followoing) to set a time gate function:\n\
only accept a come home or go away sensor change if the door was opened/closed x seconds before or y seconds after the sensor device came home or went away.\n\
This will reduce the false positives / negatives. Only when the door opens/ closes it will accpt a change in a sensor state.\n\
\n\
## Event types\n\
the plugin supports:\n\
* **all home** all devices must have come home\n\
* **one home** at least one device just came home \n\
* **xx home with door gate** same as above, but the door must have opened or closed before / after the sensor(s) came home and the same for away\n\
* **all away** all devices must have went away\n\
* **one away** at least one device just went away\n\
* **xx away with door gate** same as above, but the door must have opened or closed before / after the sensor(s) went away\n\
\n\
## Parameters\n\
###in config you can set some timing parameters: how often should events be checked etc.\n\
\n\
### In Menue you can set:\n\
* **which plugin to listen to** select from all indigo plugins which it should listen to \n\
* **accept new sensors automatically**  collect all sensors that send broadcasts and add to internal list, or keep it static/manual \n\
* **define sensors** define plugin / device / state that make up the sensor list (pick from above collected list) \n\
* **define doors** define the indigo device /states that are used as door devices. You can also specify the polling interval.\n\
* **print** this help and a dump of events, sensors, and door definitions and current states.\n\
\n\
### In trigger edit\n\
you can set various timing parameters and select which of the doors and sensors you want to use for THIS event trigger\n\
first you select event type: all/one home;  all/oneaway \n\
* **min time between 2 triggers** to avoid multiple triggers for one comming home / going away event\n\
* **trigger delay** wait some seconds to make sure the sensor state does not change.. to avoid false positives\n\
* **reset sensor** for a home event a sensor will stay home until it leaves AND a door open/close happens\n\
This option allows to have the sensor reset its state to away (for home events and visa versa for away events) without the door event\n\
* **variable condition** you can add a test on any variable <,<=, ==, >=, > \"in\" a test value. If not true the event will not trigger\n\
* **device/state condition** you can add a test on any device/state <,<=, ==, >=, > \"in\" a test value. If not true the event will not trigger\n\
* **select/delete sensors** then manage the sensors (one or many) that are part of this event group.\n\
* **select/delete doors** then manage doors (eg front and back door) that define the door time gate. You can set a before and an after time window \n\
\n\
## First steps\n\
* install plugin\n\
* set config parameters\n\
* in menu define plugins, sensors, and doors\n\
* create an indigo trigger, select homeAway / and your event type eg all/one home // away\n\
* set parameters and select sensors that participate in THIS trigger \n\
* add door if desired\n\
* add device/state or variable condition veto/ enable if desired.")

	####-----------------  ---------
	def printEVENTS(self,valuesDict,typeId):
		self.myLog(text ="")
		self.myLog(text =" ==== EVENTs ============ ")
		for item in indigo.triggers.iter(self.pluginId):
			valuesDict = self.printEVENT(valuesDict,typeId,item)
		return valuesDict

	####-----------------  ---------
	def printEVENT(self,valuesDict,typeId,item):
		props = item.pluginProps
		self.myLog(text ="===== EVENT id: "+ unicode(item.id).ljust(12)+ ";  Type: "+item.pluginTypeId +" ==== EVENT",mType=item.name+"==")
		for prop in self.evPropsToPrint:
			if prop not in props: continue
			if prop == "variableConditionID" and len(props[prop]) > 2: 
				var = indigo.variables[int(props[prop])]
				out = "CONDITION Variable" .ljust(30)  + ": "+ var.name
				self.myLog(text = out,mType="EVENTS")
				out = "    value to compare" .ljust(30)+ ": \""+ props["variableConditionValue"]+"\"  "+ props["variableConditionComp"]+"  \""+var.value+"\" (currentValue)"
			elif prop == "deviceConditionID" and len(props[prop]) > 2: 
				dev = indigo.devices[int(props[prop])]
				out = "CONDITION Device" .ljust(30)  + ": "+ dev.name+";    state: "+ unicode(props["deviceConditionSTATE"])
				self.myLog(text = out,mType="EVENTS")
				out  = "    value to compare" .ljust(30)+ ": \""+ props["deviceConditionValue"]
				out += "\"  "+ props["deviceConditionComp"]
				if "deviceConditionSTATE" in props and props["deviceConditionSTATE"] in dev.states:
					out += "  \""+unicode(dev.states[props["deviceConditionSTATE"]])+"\""
					out +=" (currentValue)"
				else: out += "  no state defined "
			elif prop == "doorsTimeWindowBefore": 
				out  = "doors time window" .ljust(30)+ ": [-"+ props["doorsTimeWindowBefore"]+" , "+props["doorsTimeWindowAfter"] +"] seconds"
			elif prop == "doorsTimeWindowAfter":
				continue 
			elif prop in ["sensorsTriggerTime","triggerTimeLast","lastsyncWithDevices"]: 
				out  = prop.ljust(30)+ ": %.1f"%(float(props[prop])) +"[tt-sec];   .. before now: %.1f"%(time.time() - float(props[prop]))+"[sec]"
			elif prop == "atleastOne": 
				out  = prop.ljust(30)+ ": accepted transitions: "
				if props[prop].find("2-1") >-1: out+= " from 2 to 1 device;"
				if props[prop].find("0-1") >-1: out+= " from 0 to 1 device;"
			else:
				out = prop.ljust(30)+ ": "+ unicode(props[prop])
			self.myLog(text = out,mType="EVENTS")
		return valuesDict


	####-----------------  ---------
	def printSENSORS(self,valuesDict,typeId):
		propsToPrint =["up","down","valueForON","used"]
		self.myLog(text =" ==== SENSORs============ ")
		for DEVICEid in self.SENSORS:
			dd = self.splitDev(DEVICEid)
			self.myLog(text ="ID: "+dd[0].ljust(12)+";  state: "+dd[1].ljust(15)+" plugin "+unicode(self.SENSORS[DEVICEid]["pluginId"]).ljust(20) +" ==== DEVICE",mType=self.SENSORS[DEVICEid]["name"]+"==")
			for prop in propsToPrint:
					self.myLog(text = prop.ljust(30)+ ": "+ unicode(self.SENSORS[DEVICEid][prop]),mType="SENSOR")
		return valuesDict


	####-----------------  ---------
	def printDOORS(self,valuesDict,typeId):
		propsToPrint =["lastM1Change","lastChange","lastChangeDT","signalReceived","state","used","requireStatusChange","pollingIntervall","lastCheck"]
		self.myLog(text =" ==== DOORs ============ ")
		for DEVICEid in self.DOORS:
			dd = self.splitDev(DEVICEid)
			self.myLog(text ="ID: "+dd[0].ljust(12)+";  state: "+dd[1].ljust(15)+" ==== DOOR",mType=self.DOORS[DEVICEid]["name"]+"==")
			for prop in propsToPrint:
					self.myLog(text = prop.ljust(30)+ ": "+ unicode(self.DOORS[DEVICEid][prop]),mType="DOOR")
		return valuesDict

	####-----------------  ---------
	def startEventTracking(self):
		self.myLog(text =" enabled EventTracking")
		self.enableEventTracking = True
		return 


	####-----------------  ---------
	def stopEventTracking(self):
		self.myLog(text =" disabled EventTracking ")
		self.enableEventTracking = False
		return 


######################################################################################
	####--------menu item   sync EVENTS
######################################################################################

	####-----------------  ---------
	def syncEVENTSCALLBACK(self,valuesDict,typeId):
		ev = self.enableEventTracking
		self.enableEventTracking = True
		for EVENT in indigo.triggers.iter(self.pluginId):
			self.updateEventStatus(EVENT, source = "sync", doTrigger = False, sync = True)
		self.enableEventTracking = ev 
		return valuesDict

	####-----------------  ---------
	def filterExistingEvents(self,  filter="self", valuesDict=None, typeId=""):
		xList = []
		for EVENT in indigo.triggers.iter(self.pluginId):
			xList.append([EVENT.id, EVENT.name])
		xList = sorted( xList, key=lambda x:(x[1]) )
		return xList

	####-----------------  ---------
	def buttonsyncEVENTCALLBACK(self,valuesDict,typeId):
		ev = self.enableEventTracking
		self.enableEventTracking = True
		if "selectedEventToSync" in valuesDict and len(valuesDict["selectedEventToSync"]) > 2:
			EVENT  = indigo.triggers[int(valuesDict["selectedEventToSync"])]
			self.updateEventStatus(EVENT, source = "sync", doTrigger = False, sync = True)
		self.enableEventTracking = ev 
		return valuesDict

	####-----------------  ---------
	def printEnabledBCplugins(self,valuesDict,typeId):
		self.myLog(text ="Home Away plugins ===============", mType="type")
		for theType in self.PLUGINS:
			for name in self.PLUGINS[theType]:
				self.myLog(text =name, mType=theType )
		return valuesDict




######################################################################################
	####--------menu item   DEVICES 
######################################################################################
	####-----------------  ---------
	def filterExistingDevices(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		xList = []

		for DEVICEid in self.SENSORS:
			if len(DEVICEid) < 3: continue
			dd = self.splitDev(DEVICEid)
			indigoID = dd[0]
			dev = indigo.devices[int(indigoID)]
			xList.append([indigoID, dev.name])
		xList = sorted( xList, key=lambda x:(x[1]) )
		xList.append((0,">>>> Pick new Device/Variable"))
		return xList

	####-----------------  ---------
	def getQualifiedDevices(self):
		self.qualifiedDevicesUpdated  = time.time()
		self.qualifiedDevices = {}
		for dev in indigo.devices:
			if len(dev.pluginId) < 5: continue
			if dev.pluginId  in self.PLUGINS["excluded"]: continue
			if not dev.enabled: continue
			id = str(dev.id)
			for state in dev.states:
				if unicode(dev.states[state]).lower() in self.acceptableStateValues:
					self.qualifiedDevices[id] = [dev.name,dev.pluginId]
					break
		for DEVICEid in self.SENSORS:
			id = DEVICEid.split(":::")[0]
			if id in self.qualifiedDevices: continue
			try: 
				dev = indigo.devices[int(id)]
				self.qualifiedDevices[id] = [dev.name,dev.pluginId]
			except: pass
		return 
	####-----------------  ---------
	def filterNewDevices(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		if time.time() - self.qualifiedDevicesUpdated > 100:
			self.getQualifiedDevices()
			
		retList = []
		for id in self.qualifiedDevices:
			retList.append((id,self.qualifiedDevices[id][1]+"--"+self.qualifiedDevices[id][0]) )
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>>no new device"))
		return retList

	####-----------------  ---------
	def buttonConfirmExistingOrNewDeviceCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		self.SENSORSelected = valuesDict["selectedExistingOrNewDevice"]
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ self.SENSORSelected +"  "+unicode(valuesDict), mType="butConfirmExistingOrNewDevice")
		valuesDict["selectStatesOK"]       = False
		valuesDict["text1-1"]              = "  and then confirm !"
		valuesDict["text1-2"]              = "  and then confirm !"

		try:
			if self.SENSORSelected == "0":
				valuesDict["DefineDevicesAndNew"]  = True
				valuesDict["DefineDevicesAndOld"]  = False
				valuesDict["msg"]                  = "device NOT selected"
			else:
				valuesDict["DefineDevicesAndOld"]  = True
				valuesDict["DefineDevicesAndNew"]  = False
				valuesDict["selectStatesOK"]       = True
				valuesDict["msg"]                  = "device selected, enter state or delete"

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict
		
	####-----------------  ---------
	def buttonConfirmDeleteDeviceCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ str(self.SENSORSelected) +"  "+unicode(valuesDict), mType="butConfirmDeleteDevice")
		valuesDict["DefineDevicesAndNew"]  = False
		valuesDict["DefineDevicesAndOld"]  = False
		valuesDict["selectStatesOK"]       = False

		try:
			if self.SENSORSelected !="0":
				deldev = {}
				for DEVICEid in self.SENSORS:
					dd = self.splitDev(DEVICEid)
					if self.SENSORSelected == dd[0]:
						deldev[DEVICEid] = True
				for DEVICEid in deldev:
					del self.SENSORS[DEVICEid]
				self.saveSENSORS()
				valuesDict["msg"]                  = "device deleted"
			
		except  Exception, e:
				self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict

	####-----------------  ---------
	def buttonConfirmDeviceNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ self.SENSORSelected +"  "+unicode(valuesDict), mType="butConfirmExistingDevice")
		self.SENSORSelected = valuesDict["selectedNewDeviceID"]
		valuesDict["selectStatesOK"]       = False
		valuesDict["DefineDevicesAndNew"]  = False
		valuesDict["DefineDevicesAndOld"]  = False
	

		try:
			if self.SENSORSelected !="0":
				valuesDict["DefineDevicesAndOld"]  = False
				valuesDict["DefineDevicesAndNew"]  = False
				valuesDict["selectStatesOK"]       = True
				valuesDict["msg"]                  = "device selected"
			else:
				valuesDict["selectStatesOK"]       = False
				valuesDict["DefineDevicesAndNew"]  = False
				valuesDict["DefineDevicesAndOld"]  = False
				valuesDict["msg"]                  = "device NOT selected"
			

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict


	####-----------------  ---------
	def filterStates(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		retList = []
		if self.SENSORSelected =="0": return retList

		selectedState =""

		for DEVICEid in self.SENSORS:
			if len(DEVICEid) < 3: continue
			dd = self.splitDev(DEVICEid)
			if self.SENSORSelected  == dd[0]:
				selectedState = dd[1]
				break

		dev = indigo.devices[int(self.SENSORSelected)]
		for state  in dev.states:
			stValue = unicode(dev.states[state])
			if stValue.lower() not in self.acceptableStateValues: continue
			text = state + ":"+stValue
			if state == selectedState:
			   text +=" << selected"
			retList.append([state, text])
		if len(retList) ==0: 
			retList.append(["0", ">>no state acceptable<<"])
			return retList
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>> select state"))

		return retList

	####-----------------  ---------
	def buttonConfirmStateCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ str(self.SENSORSelected) +"  "+unicode(valuesDict), mType="butConfirmState")
		valuesDict["selectStatesOK"]       = False
		valuesDict["DefineDevicesAndNew"]  = False
		valuesDict["DefineDevicesAndOld"]  = False

		try:
			if self.SENSORSelected !="0":
				DEVICEid = self.SENSORSelected+":::"+valuesDict["selectedState"]

				if DEVICEid not in self.SENSORS:
					self.SENSORS[DEVICEid] = copy.copy(self.emptyDEVICE)
				dev = indigo.devices[int(self.SENSORSelected)]
				self.SENSORS[DEVICEid]["pluginId"]          = dev.pluginId
				self.SENSORS[DEVICEid]["name"]              = dev.name
				self.SENSORS[DEVICEid]["state"]             = valuesDict["selectedState"]
				try: self.SENSORS[DEVICEid]["up"]["delayTime"]   = float(valuesDict["homeDelay"])
				except: pass
				try:self.SENSORS[DEVICEid]["down"]["delayTime"] = float(valuesDict["awayDelay"]) 
				except: pass

				valuesDict["msg"]                  = "device / state selected and saved"
			self.saveSENSORS()
			
		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict


######################################################################################
	####-----------------  MENU item DOORS 
######################################################################################
	def filterExistingDoors(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		retList = []

		for DEVICEid in self.DOORS:
			if len(DEVICEid) < 3: continue
			exDevState = DEVICEid.split(":::")
			indigoID = exDevState[0]
			dev = indigo.devices[int(indigoID)]
			retList.append([indigoID, dev.name])
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>> Pick new Door/Variable"))
		return retList

	####-----------------  ---------
	def getQualifiedDoors(self):
		self.qualifiedDoorsUpdated  = time.time()
		self.qualifiedDoors = {}
		for dev in indigo.devices:
			if not dev.enabled: continue
			id = str(dev.id)
			for state in dev.states:
				if unicode(dev.states[state]).lower() in self.acceptableStateValues:
					self.qualifiedDoors[id] = dev.name
					break
		for DEVICEid in self.DOORS:
			dd = self.splitDev(DEVICEid)
			id = dd[0]
			if id in self.qualifiedDoors: continue
			try: 
				dev = indigo.devices[int(id)]
				self.qualifiedDoors[id] = dev.name
			except: pass
		return 
	####-----------------  ---------
	def filterNewDoors(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		if time.time() - self.qualifiedDoorsUpdated > 100:
			self.getQualifiedDoors()
			
		retList = []
		for id in self.qualifiedDoors:
			retList.append( (id,self.qualifiedDoors[id]) )
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>>no new device"))
		return retList

	####-----------------  ---------
	def buttonConfirmExistingOrNewDoorCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		self.DoorSelected = valuesDict["selectedExistingOrNewDoor"]
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ self.DoorSelected +"  "+unicode(valuesDict), mType ="butConfirmExistingOrNewDoor")
		valuesDict["selectStatesOK"]       = False
		valuesDict["text1-1"]              = "  and then confirm !"
		valuesDict["text1-2"]              = "  and then confirm !"

		try:
			if self.DoorSelected == "0":
				valuesDict["DefineDoorsAndNew"]  = True
				valuesDict["DefineDoorsAndOld"]  = False
				valuesDict["msg"]                  = "device NOT selected"
			else:
				valuesDict["DefineDoorsAndOld"]  = True
				valuesDict["DefineDoorsAndNew"]  = False
				valuesDict["selectDoorsStatesOK"] = True
				valuesDict["msg"]                  = "device selected, enter state or delete"

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict
		
	####-----------------  ---------
	def buttonConfirmDeleteDoorCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ str(self.DoorSelected) +"  "+unicode(valuesDict), mType ="butConfirmDeleteDoor")
		valuesDict["DefineDoorsAndNew"]   = False
		valuesDict["DefineDoorsAndOld"]   = False
		valuesDict["selectDoorsStatesOK"] = False

		try:
			if self.DoorSelected !="0":
				deldev = {}
				for DEVICEid in self.DOORS:
					dd = self.splitDev(DEVICEid)
					if self.DoorSelected == dd[0]:
						deldev[DEVICEid] = True
				for DEVICEid in deldev:
					del self.DOORS[DEVICEid]
				self.saveDOORS()
				valuesDict["msg"]                  = "device deleted"
			
		except  Exception, e:
				self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict

	####-----------------  ---------
	def buttonConfirmDoorNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ self.DoorSelected +"  "+unicode(valuesDict), mType ="butConfirmExistingDoor")
		self.DoorSelected = valuesDict["selectedNewDoorID"]
		valuesDict["selectDoorsStatesOK"] = False
		valuesDict["DefineDoorsAndNew"]   = False
		valuesDict["DefineDoorsAndOld"]   = False
	

		try:
			if self.DoorSelected !="0":
				valuesDict["DefineDoorsAndOld"]   = False
				valuesDict["DefineDoorsAndNew"]   = False
				valuesDict["selectDoorsStatesOK"] = True
				valuesDict["msg"]                 = "door selected"
			else:
				valuesDict["selectDoorsStatesOK"] = False
				valuesDict["DefineDoorsAndNew"]   = False
				valuesDict["DefineDoorsAndOld"]   = False
				valuesDict["msg"]                 = "door NOT selected"
			

		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict


	####-----------------  ---------
	def filterDoorStates(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		retList = []
		if self.DoorSelected =="0": return retList

		selectedState =""

		for DEVICEid in self.DOORS:
			if len(DEVICEid) < 3: continue
			dd = self.splitDev(DEVICEid)
			if self.DoorSelected  == dd[0]:
				selectedState = dd[1]
				break

		dev = indigo.devices[int(self.DoorSelected)]
		for state  in dev.states:
			stValue = unicode(dev.states[state])
			if stValue.lower() not in self.acceptableStateValues: continue
			text = state + ":"+stValue
			if state == selectedState:
			   text +=" << selected"
			retList.append([state, text])
		if len(retList) ==0: 
			retList.append(["0", ">>no state acceptable<<"])
			return retList
		retList = sorted( retList, key=lambda x: (x[1]) )
		retList.append((0,">>>> select state"))

		return retList

	####-----------------  ---------
	def buttonConfirmDoorStateCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
		if self.decideMyLog(u"SETUP"): 
			self.myLog(text = "IndigoID "+ str(self.DoorSelected) +"  "+unicode(valuesDict), mType="butConfirmDoorState"    )
		valuesDict["selectDoorsStatesOK"]  = False
		valuesDict["DefineDoorAndNew"]     = False
		valuesDict["DefineDoorAndOld"]     = False

		try:
			if self.DoorSelected !="0":
				DEVICEid = self.DoorSelected+":::"+valuesDict["selectedDoorState"]

				if DEVICEid not in self.DOORS:
					self.DOORS[DEVICEid] = copy.copy(self.emptyDOOR)
				dev = indigo.devices[int(self.DoorSelected)]
				self.DOORS[DEVICEid]["name"]                        = dev.name
				self.DOORS[DEVICEid]["state"]                       = valuesDict["selectedDoorState"]
				self.DOORS[DEVICEid]["pollingIntervall"]            = float(valuesDict["pollingIntervall"])
				self.DOORS[DEVICEid]["requireStatusChange"]         = valuesDict["requireStatusChange"] == "yes"
	
				valuesDict["msg"]                  = "device / state selected and saved"
			self.saveDOORS()
			
		except  Exception, e:
			self.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return valuesDict


######################################################################################
	# MAIN LOOP
######################################################################################
		
	####----------------- main loop ---------
	def runConcurrentThread(self):
		nowDT = datetime.datetime.now()
		self.lastMinute     = nowDT.minute
		self.lastHour       = nowDT.hour

		indigo.server.log( u"initialized")
		try:    indigo.server.savePluginPrefs()
		except: pass
		lastHourCheck        = datetime.datetime.now().hour
		lastMinuteCheck      = datetime.datetime.now().minute
		lastMinute10Check    = datetime.datetime.now().minute/10
		self.pluginStartTime = time.time()
		self.countLoop       = 1
		self.pluginState     = "loop"
		self.lastEventUpdate = 0
		self.lastDoorCheck   = 0.
		self.loopSleep = max(1., min(self.doorLoopWait, self.eventUpdateWait) )
		self.lastPluginCheckUpdate  = time.time()
		self.subscribeToPlugins(self.PLUGINS["used"])

		## update devices in case state have changed while we were down 
		self.getDEVICEstates()
		self.fixEVprops()
		
		#for ev in indigo.triggers.iter(self.pluginId):
		#        indigo.server.log(unicode(ev))
		################   ------- here the loop starts    --------------
		try:
			self.quitNow = ""
			while self.quitNow == "":
				self.loopSleep = max(1., min(self.doorLoopWait, self.eventUpdateWait) )
				self.sleep(self.loopSleep)
				self.countLoop += 1

				if (time.time() - self.lastDoorCheck > self.doorLoopWait):
					self.getDOORstates()# read indigo devices for door states 

				if len(self.updateEVENTS) > 0 or (time.time() - self.lastEventUpdate > self.eventUpdateWait):
					self.periodCheckDEVICES() # check if trigeredDOWN --> AWAY etc 
					self.updateEventsStatus(source="period")  # check if events are triggerd from delayed changes in devices

				if (time.time() - self.lastPluginCheckUpdate > 300):
					self.checkPluginsForUpdates() # check if plugins defs are stiil ok 

		except  Exception, e:
				if len(unicode(e)) > 5:
					indigo.server.log(u"Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		################   ------- here the loop  ends    --------------

		self.pluginState   = "stop"
		if self.quitNow == "": self.quitNow = u" restart / self.stop requested "
		indigo.server.log( u" stopping plugin due to:  ::::: " + unicode(self.quitNow) + u" :::::")
   
		self.sleep(1)
		serverPlugin = indigo.server.getPlugin(self.pluginId)
		serverPlugin.restart(waitUntilDone=False)

		return




######################################################################################
	# DEVICE status , by polling 
######################################################################################
	####-----------------check DEVICES if they chnaged while not up, update if needed ---------
	def getDEVICEstates(self):
		update= False
		
		try:
			for DEVICEid in self.SENSORS:
				dd = self.splitDev(DEVICEid)
				try: dev = indigo.devices[int(dd[0])]
				except  Exception, e:
					indigo.server.log(u"Line {} has error={} please remove device from SENSORS\nSENSORS defined: {}".format(sys.exc_traceback.tb_lineno, e, self.SENSORS) )
					continue
				lastChangedDT = dev.lastChanged
				lastChanged = time.mktime(lastChangedDT.timetuple())
				newST = dev.states[dd[1]]
				UP = (unicode(newST) == self.SENSORS[DEVICEid]["valueForON"])
				
				if self.enableEventTracking or self.decideMyLog(u"SETUP"): 
					self.myLog(text = "getDEVICEstates    DEVICEid "+DEVICEid.ljust(20)+"  lastDT:"+unicode(lastChangedDT) +"   "+
					unicode(int(lastChanged)) +" == last  "+unicode(int(self.SENSORS[DEVICEid]["up"]["lastChange"]))+"  "+
					" delta  "+unicode(int(lastChanged - self.SENSORS[DEVICEid]["up"]["lastChange"])).rjust(10)+"  "+
					"; ex-Tf: "+ unicode(self.SENSORS[DEVICEid]["up"]["signalReceived"]) +
					"; upd?: "+unicode(self.SENSORS[DEVICEid]["up"]["signalReceived"] != UP ) +
					"", mType = "getDEVICEstates" )

				if self.SENSORS[DEVICEid]["up"]["signalReceived"] != UP:  
					self.SENSORS[DEVICEid]["up"]["lastChange"]          = lastChanged
					self.SENSORS[DEVICEid]["up"]["signalReceived"]      = UP
					self.SENSORS[DEVICEid]["up"]["state"]               = ""
					self.SENSORS[DEVICEid]["down"]["lastChange"]        = lastChanged
					self.SENSORS[DEVICEid]["down"]["signalReceived"]    = not UP
					self.SENSORS[DEVICEid]["down"]["state"]             = ""
					update= True
					
			if update: self.saveSENSORS()
		except  Exception, e:
				if len(unicode(e)) > 5:
					indigo.server.log(u"Line {} has error={}\nSENSORS defined: {}".format(sys.exc_traceback.tb_lineno, e, self.SENSORS) )
		return 


######################################################################################
	# DOOR status , by polling 
######################################################################################

	####-----------------check door s ---------
	def getDOORstates(self):
		update= False
		
		try:
			for DEVICEid in self.DOORS:
				dd = self.splitDev(DEVICEid)
				if  time.time() - self.DOORS[DEVICEid]["lastCheck"]  < self.DOORS[DEVICEid]["pollingIntervall"] : continue
				dev = indigo.devices[int(dd[0])]
				newST = dev.states[dd[1]]
				lastChangedDT = dev.lastChanged
				lastChanged = time.mktime(lastChangedDT.timetuple())

				if  (   
						(lastChanged != self.DOORS[DEVICEid]["lastChange"] ) 
						and 
						(
							(      self.DOORS[DEVICEid]["requireStatusChange"] and  unicode(newST) != self.DOORS[DEVICEid]["signalReceived"] ) 
							or
							(  not self.DOORS[DEVICEid]["requireStatusChange"] )                                                 
																				  
						)
					):
					if self.enableEventTracking or self.decideMyLog(u"DOORS") : 
						self.myLog(text = "getDOORstates    DEVICEid: "+DEVICEid.ljust(20)+ str(lastChangedDT) +" == lastDT  "+unicode(self.DOORS[DEVICEid]["lastChangeDT"])+"  "+
						unicode(int(lastChanged)) +" == last  "+unicode(int(self.DOORS[DEVICEid]["lastChange"]))+"  "+
						"; delta: "+unicode(int(lastChanged - self.DOORS[DEVICEid]["lastChange"])).rjust(10)+
						";  st curr "+ unicode(self.DOORS[DEVICEid]["signalReceived"]) +" == new: "+unicode(newST) +
						"", mType = "getDOORstates" )
					self.DOORS[DEVICEid]["lastM1Change"]   = self.DOORS[DEVICEid]["lastChange"]
					self.DOORS[DEVICEid]["lastChange"]     = lastChanged
					self.DOORS[DEVICEid]["lastChangeDT"]   = lastChangedDT.strftime(u"%Y-%m-%d %H:%M:%S")
					self.DOORS[DEVICEid]["signalReceived"] = unicode(dev.states[self.DOORS[DEVICEid]["state"]])
					update= True
				self.DOORS[DEVICEid]["lastCheck"] = time.time()
					
			if update: self.saveDOORS()
		except  Exception, e:
				if len(unicode(e)) > 5:
					indigo.server.log(u"Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


######################################################################################
	# handle messages 
######################################################################################

	####-----------------  receive changes from device changes  ---------
	def receiveDeviceChangedAction(self,MSG):
		self.receiveDeviceChanged(MSG.props)
	def receiveDeviceChangedSubscription(self,MSG):
		self.receiveDeviceChanged(json.loads(MSG))

	def receiveDeviceChanged(self, MSG):

		try:
			if self.decideMyLog(u"RECEIVE") and False: 
				self.myLog(text =  unicode(MSG), mType="receiveDeviceChanged" )
			if "data" not in MSG: 
				if self.decideMyLog(u"RECEIVE") : 
					self.myLog(text = "bad data received, not data element in dict "+ unicode(MSG), mType="receiveDeviceChanged" )
				return
				
			data = MSG["data"]
			if "pluginId" in MSG:
				receivedPluginId = MSG["pluginId"]
			else:
				receivedPluginId = ""
			for msg in data:
				upd = 0
					
				if not self.checkParams(msg):continue

				if msg["action"] == "event":
					DEVICEid= str(msg["id"]) +":::"+ msg["state"]

					if DEVICEid not in self.SENSORS: # check if device was ignored, add to the devices dict
						self.addNewSensor(DEVICEid, msg)
						continue
					if self.decideMyLog(u"RECEIVE"): 
						self.indiLOG.log(40, "msg:"+ str(msg) , mType="receiveDeviceChanged")
					
					self.SENSORS[DEVICEid]["valueForON"] = msg["valueForON"]
					UP      = msg["newValue"] == msg["valueForON"]
					UPnew   = self.SENSORS[DEVICEid]["up"]["signalReceived"]    != UP
					DOWNnew = self.SENSORS[DEVICEid]["down"]["signalReceived"]  == UP
					save = ["","","","","","","","",""]

					if self.enableEventTracking  or  self.decideMyLog(u"RECEIVE"):
							self.myLog(text = "DEVICEid:accepted.. UP " +unicode(UP) +"  UPnew "+unicode(UPnew) +"  DOWNnew "+unicode(DOWNnew), mType="receiveDeviceChanged")

					if UP:
						if UPnew:
							if self.SENSORS[DEVICEid]["up"]["state"] != "home": 
								self.SENSORS[DEVICEid]["up"]["state"] = "home"
								self.SENSORS[DEVICEid]["up"]["lastChange"] = time.time()
							save[0]="UU"
						if DOWNnew:
							save[1]="UD"
							if self.SENSORS[DEVICEid]["down"]["state"] != "": 
								self.SENSORS[DEVICEid]["down"]["state"] = ""
								self.SENSORS[DEVICEid]["down"]["lastChange"] = time.time()
								if self.SENSORS[DEVICEid]["up"]["delayTime"] == 0 or self.SENSORS[DEVICEid]["down"]["delayTime"] == 0: save[2]="NOW"
					
					if not UP: 
						if  UPnew:
							if self.SENSORS[DEVICEid]["up"]["state"] == "home": 
								save[3]="DU"
								self.SENSORS[DEVICEid]["up"]["state"] = "triggeredDOWN"
								self.SENSORS[DEVICEid]["up"]["lastChange"] = time.time()
								if self.SENSORS[DEVICEid]["up"]["delayTime"] == 0 or self.SENSORS[DEVICEid]["down"]["delayTime"] == 0: save[2]="NOW"
					
						if  DOWNnew: 
							if self.SENSORS[DEVICEid]["down"]["state"] != "triggeredDOWN": 
								save[4]="DD"
								self.SENSORS[DEVICEid]["down"]["state"] = "triggeredDOWN"
								self.SENSORS[DEVICEid]["down"]["lastChange"] = time.time()
								if self.SENSORS[DEVICEid]["up"]["delayTime"] == 0 or self.SENSORS[DEVICEid]["down"]["delayTime"] == 0: save[2]="NOW"

					if self.SENSORS[DEVICEid]["up"]["signalReceived"]   != UP:  save[5]="US"
					if self.SENSORS[DEVICEid]["down"]["signalReceived"] == UP:  save[6]="DS"
					self.SENSORS[DEVICEid]["up"]["signalReceived"]    = UP
					self.SENSORS[DEVICEid]["down"]["signalReceived"]  = not UP

					if save != ["","","","","","","","",""]: self.saveSENSORS()
					if self.enableEventTracking or  (self.decideMyLog(u"RECEIVE") and save != ["","","","","","","","",""] ):
						dd = self.splitDev(DEVICEid)
						self.myLog(text =  (dd[0]+":"+dd[1]).ljust(17)+
					"; stateUP:"+self.SENSORS[DEVICEid]["up"]["state"].ljust(13)+
					"; signRecUP:"+unicode(self.SENSORS[DEVICEid]["up"]["signalReceived"]).ljust(6)+
					"; lChgUP:%6.1f"%(min(time.time()-self.SENSORS[DEVICEid]["up"]["lastChange"], 9999))+
					"; stateDN:"+self.SENSORS[DEVICEid]["down"]["state"].ljust(13)+
					"; signRecDN:"+unicode(self.SENSORS[DEVICEid]["down"]["signalReceived"]).ljust(6)+
					"; lChgDN:%6.1f"%(min(time.time()-self.SENSORS[DEVICEid]["down"]["lastChange"], 9999))+
					"; save:%s"%unicode(save)+
					"",     mType="rcvBC:"+msg["name"])
					self.updateDeviceStatus(DEVICEid,periodCheck="devChg", callEvent=(upd==2)) # set new status now 
		except Exception, e:
			self.indiLOG.log(40," Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		
	####-----------------  update device status  ---------
	def periodCheckDEVICES(self):
		for DEVICEid in self.SENSORS:
			self.updateDeviceStatus(DEVICEid, periodCheck="period")
		return 
		
	####-----------------  update individual device status  ---------
	def updateDeviceStatus(self, DEVICEid, periodCheck="",callEvent=False):
		try:
			if DEVICEid not in self.SENSORS: return 
			save = ["","",""]
			if self.SENSORS[DEVICEid]["up"]["state"] == "triggeredDOWN": 
				if time.time() - self.SENSORS[DEVICEid]["up"]["lastChange"] > self.SENSORS[DEVICEid]["up"]["delayTime"]: 
					self.SENSORS[DEVICEid]["up"]["lastChange"] = time.time() 
					self.SENSORS[DEVICEid]["up"]["state"] = ""
				save[0] = "UTD-x"        

			if self.SENSORS[DEVICEid]["down"]["state"] == "triggeredDOWN": 
				if time.time() - self.SENSORS[DEVICEid]["down"]["lastChange"] > self.SENSORS[DEVICEid]["down"]["delayTime"]:
					self.SENSORS[DEVICEid]["down"]["lastChange"] = time.time() 
					self.SENSORS[DEVICEid]["down"]["state"] = "away"
				save[1] = "DTD-x"        
			if save != ["","","","","","","","",""] or callEvent: 
				self.saveSENSORS()
				self.updateEventsStatus(source=periodCheck)
			if self.enableEventTracking  or  ( self.decideMyLog(u"RECEIVE") and save != ["","",""]  ): 
				dd = self.splitDev(DEVICEid)
				self.indiLOG.log(40, (dd[0]+":"+dd[1]).ljust(17)+
					";  stateUP:"+self.SENSORS[DEVICEid]["up"]["state"].ljust(13)+
					";  signRecUP:"+unicode(self.SENSORS[DEVICEid]["up"]["signalReceived"])[0]+
					";  lChgUP:%5.1f"%(min(time.time()-self.SENSORS[DEVICEid]["up"]["lastChange"],999))+
					";  stateDN:"+self.SENSORS[DEVICEid]["down"]["state"].ljust(13)+
					";  signRecDN:"+unicode(self.SENSORS[DEVICEid]["down"]["signalReceived"])[0]+
					";  lChgDN:%5.1f"%(min(time.time()-self.SENSORS[DEVICEid]["down"]["lastChange"],999))+
					";  save:%s"%unicode(save)+
					"",     mType="rcvBC:"+periodCheck)

		except  Exception, e:
			if len(unicode(e)) > 5:
				indigo.server.log(u"Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 

	def splitDev(self,DEVICEid):
		dd = DEVICEid.split(":::")
		if len(dd) == 2: return dd
		if len(dd) == 1: return  dd.append("")
		return ["",""]
	####-----------------  update EVENTS status  ---------
	def updateEventsStatus(self,source = ""):
		try:
			self.lastEventUpdate  = time.time()
			self.updateEVENTS     = {} #reset any pending update , wil be done after this 
			for EVENT in indigo.triggers.iter(self.pluginId):
				self.updateEventStatus(EVENT,source=source)
		except  Exception, e:
			if len(unicode(e)) > 5:
				indigo.server.log(u"updateEventsStatus in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))



	####-----------------  update EVENT status  ---------
	def updateEventStatus(self, EVENT, source = "", doTrigger = True, sync = False):
		try:

				save = ["","","","","",""]
				if not EVENT.enabled: return
				
				props = EVENT.pluginProps
				oneAll   = props["oneAll"] 
				homeAway = props["homeAway"] 
				noDoors  = props["noDoors"] 
				resetEVENTwoDoors = False
				if "resetEVENTwoDoors" in props and props["resetEVENTwoDoors"] == "woDoors":
					resetEVENTwoDoors = True
				triggerType = oneAll+"-"+homeAway+"-"+noDoors
				doorsTimeWindowAfter  = 30
				doorsTimeWindowBefore = -300
				if  homeAway =="away":  
					doorsTimeWindowAfter  = 300
					doorsTimeWindowBefore = 0
				else:
					doorsTimeWindowAfter  = 30
					doorsTimeWindowBefore = -300
				if "doorsTimeWindowAfter"  in props: 
					try:    doorsTimeWindowAfter  =  float(props["doorsTimeWindowAfter"])
					except: pass
				if "doorsTimeWindowBefore" in props: 
					try:    doorsTimeWindowBefore = -float(props["doorsTimeWindowBefore"])
					except: pass

				devicesM        = json.loads(props["sensorsMembers"])

				try:    lastDoorChange = props["lastDoorChange"]
				except: lastDoorChange = 0

				dChanged, doorsLastChange, doorsM = self.getLastDoorChange(json.loads(props["doorsMembers"]), lastDoorChange)
				if dChanged: 
					props["doorsMembers"]   = json.dumps(doorsM)
					props["lastDoorChange"] = doorsLastChange
					save[0]= "Dc"
						
				try:    oldsensorsCountTRUE = int(props["sensorsCountTRUE"])
				except: oldsensorsCountTRUE = 0

				devLastChanged  = [self.getLastSensorChange(devicesM,"up"),self.getLastSensorChange(devicesM,"down")]


				if sync:
					for DEVICEid in devicesM:
						if DEVICEid in self.SENSORS: # safety check
							if "lastsyncWithDevices" not in props:
								  props["lastsyncWithDevices"] = 0
							if time.time() - props["lastsyncWithDevices"] >100:  
								devicesM, update = self.syncEventStatesToDeviceStates(DEVICEid,devicesM)
								props["lastsyncWithDevices"] = time.time()
								save[5]           = "sync"
								props["sensorsMembers"] = json.dumps(devicesM)




				### count # of devices home/ away 
				for DEVICEid in devicesM:
					if DEVICEid in self.SENSORS: # safety check
						for ud,ha in (("up","home"),("down","away")):
								
							dTT_dLC         = self.SENSORS[DEVICEid][ud]["lastChange"] - doorsLastChange
							#dTT_dLC         = devLastChanged[ud] - doorsLastChange
							if self.SENSORS[DEVICEid][ud]["state"]   == ha and devicesM[DEVICEid] != ha: 
								if ( 
											( noDoors != "doors"     or ( resetEVENTwoDoors and noDoors == "doors")                   ) # either no door or door but un-trigger eg for oneHome, allow to go away w/o door 
										or                              # eg         -30          -5            -5     <    300
											( noDoors == "doors"  and   doorsTimeWindowBefore < dTT_dLC  and  dTT_dLC < doorsTimeWindowAfter ) # in time window before / after door event ?
									): 
										devicesM[DEVICEid] = ha
										props["sensorsMembers"] = json.dumps(devicesM)
										save[1]= "DW"
							if self.enableEventTracking  or  ( self.decideMyLog(u"EVENTS") and save != ["","","","","",""] ): 
								self.myLog(text = ""+
									"DEVid:%s" %( DEVICEid.replace(":::","/").ljust(18) ) +
									";  noDoors:%s" %(noDoors.ljust(5) ) +
									";  ud:%s" %( ud[0:2] ) +
									";  ha:%s" %( ha[0:2] ) +
									";  devTrgT-tDoor:%7.1f" %(  min(dTT_dLC, 9999)  ) +
									";  dTWB:%7.1f" %(  min(doorsTimeWindowBefore, 9999)  )     +
									";  dTWA:%7.1f" %(  min(doorsTimeWindowAfter, 9999)  )     +
									";  devM:%s" %(  devicesM[DEVICEid].ljust(5)  )    +
									";  devUPs:%s" %(self.SENSORS[DEVICEid][ud]["state"])+
									";  save:%s" %unicode(save)+
									"",mType= "EV-"+source+":"+EVENT.name )

				counter = {"home":0,"away":0}
				countr2 = {"home":0,"away":0}
				for DEVICEid in devicesM:
					if DEVICEid in self.SENSORS: # 
						if devicesM[DEVICEid] == "home":
							counter["home"] +=1
						if devicesM[DEVICEid] == "away":
							counter["away"] +=1

						if devicesM[DEVICEid] == "shouldBe-home":
							countr2["home"] +=1
						if devicesM[DEVICEid] == "shouldBe-away":
							countr2["away"] +=1

								
				if self.eventVariablePrefix !="":
					for vn in ["home","away"]:
						varName = (self.eventVariablePrefix+"_"+EVENT.name+"_"+vn).replace(" ","_")
						try:
							var = indigo.variables[varName].value
						except:
							indigo.variable.create(varName,"0")
							var = "0"
						if unicode(counter[vn]) != var:
							indigo.variable.updateValue(varName, unicode(counter[vn]))


				### make  the device summary input
				if  oldsensorsCountTRUE != counter[homeAway]:
					if (  
							( oneAll == "all" and counter[homeAway] == len(devicesM) ) 
							 or 
							( oneAll == "one" and counter[homeAway] == 1   and "atleastOne" in props and 
								(   
									( props["atleastOne"].find("2-1") >-1  and oldsensorsCountTRUE > 1 )  # from 2-->1
								or
									( props["atleastOne"].find("0-1") >-1  and oldsensorsCountTRUE == 0 ) # from 0-->1
								)
							)
						):  # one : if 0-->1; or 2-->1 ?
						props["sensorsTrigger"]      = True 
						props["sensorsTriggerTime"]  = time.time()  # start the timer 
					else:
						props["sensorsTrigger"]      = False 
					props["sensorsCountTRUE"]        = counter[homeAway]
					save[2] = "T"
	  
				## ready to trigger?

				testVarCondition  = True
				varValue          = ""
				if "variableConditionID" in props and len(props["variableConditionID"]) > 2 and "variableConditionValue" in props:
					testVarCondition, varValue = self.compareCurentToProp(testVarCondition, props["variableConditionComp"],  indigo.variables[int(props["variableConditionID"])].value, props["variableConditionValue"])
					
				testDevCondition  = True
				devValue          = ""
				if "deviceConditionID"   in props and len(props["deviceConditionID"]) > 2   and "deviceConditionValue"   in props and "deviceConditionSTATE" in props:
					try: 
						dev = indigo.devices[int(props["deviceConditionID"])]
						if  props["deviceConditionSTATE"] in dev.states:
							testDevCondition, devValue = self.compareCurentToProp(testDevCondition, props["deviceConditionComp"],  dev.states[props["deviceConditionSTATE"]], props["deviceConditionValue"])
					except: pass

				triggered = props["sensorsTrigger"]
				if triggered:
					
					if (  time.time() - props["triggerTimeLast"] < float(props["minTimeTriggerBeforeRepeat"])  ): ## first test if we should ignore , to fast after last trigger  use eg 5 mninutes 
							props["sensorsTrigger"]  = False
							save[3] = "T-repeat"
					elif  ( time.time() - props["sensorsTriggerTime"] < float(props["delayAfterSensorTrigger"]) ): # delay after trigger enable before exeute to allow a quick reset
							pass
					else:
						if testVarCondition and testDevCondition:
							props["triggerTimeLast"] = time.time()
							if doTrigger:
								self.triggerEvent(EVENT.id,triggerType)
						else:
							if self.enableEventTracking  or  ( self.decideMyLog(u"EVENTS") and save != ["","","","","",""] ) : 
								if not testVarCondition:
									self.myLog( text= "trig  vetoed by variable condition: "+varValue+" NE "+props["variableConditionValue"]+
									"",mType= "EV-"+source+":"+EVENT.name )
								if not testDevCondition:
									self.myLog( text= "trig  vetoed by dev/state condition: "+devValue+" NE "+props["deviceConditionValue"]+
									"",mType= "EV-"+source+":"+EVENT.name )
						save[4] = "Trig"
						props["sensorsTrigger"]  = False
						
				if self.enableEventTracking  or  ( self.decideMyLog(u"EVENTS") and save != ["","","","","",""] ): 
					self.myLog(text = 
					"trigTyp: "              +unicode( triggerType ).ljust(14)+
					";  devTrig: "           +unicode( triggered )[0]+" -> "+unicode( props["sensorsTrigger"] )[0]+
					";  allT:"               +unicode( oneAll == "all" and counter[homeAway] == len(devicesM) )[0]+
					";  1T:"                 +unicode( oneAll == "one" and counter[homeAway] >= 1 and  oldsensorsCountTRUE == 0  )[0]+
					";  olddevCtTRUE:"       +unicode( oldsensorsCountTRUE ).ljust(2)+
					";  countTRUE:"          +unicode(counter).replace(" ","")+
					";  Ndevs:%d"            %( len(devicesM) )+
					";  devM:%s"             %(props["sensorsMembers"].replace(" ","").replace(":::","/")) +
					";  dorM:%s"             %(props["doorsMembers"].replace(" ","").replace(":::","/")) +
					";  t-tTrg:%6.1f"        %(  min(time.time() - props["sensorsTriggerTime"]   , 9999)  )+
					";  t-tDoor:%6.1f"       %(  min(time.time() - doorsLastChange   , 9999)  )+
					";  dTWB:%4d"            %(  min(doorsTimeWindowBefore, 9999)  )     +
					";  dTWA:%4d"            %(  min(doorsTimeWindowAfter, 9999)  )     +
					";  varCond:%s"          %unicode(testVarCondition)[0]  +
					";  devCond:%s"          %unicode(testDevCondition)[0]  +
					";  save:%s"             %unicode(save)+
					"",mType= "EV-"+source+":"+EVENT.name )

				if not doTrigger:  
					props["sensorsTrigger"]  = False

				if save != ["","","","","",""]: EVENT.replacePluginPropsOnServer(props)
	 
		except Exception, e:
			self.indiLOG.log(40, u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return 

	####-----------------  manage trigger list---------
	def triggerStartProcessing(self, trigger):
		self.triggerList.append(trigger.id)

	def triggerStopProcessing(self, trigger):
		if trigger.id in self.triggerList:
			self.triggerList.remove(trigger.id)


######################################################################################
	# Indigo Trigger Firing

	####-----------------  
	def triggerEvent(self, eventId, triggerType):
		try:
			#if (time.time() - self.pluginStartTime) < self.waitAfterStartForFirstTrigger: return 
			for trigId in self.triggerList:
				trigger = indigo.triggers[trigId]
				
				if trigger.pluginTypeId == triggerType and trigId == eventId:
					if self.decideMyLog(u"EVENTS") or self.enableEventTracking:
						self.indiLOG.log(40,u"trigger/eventId id: "+ str(trigId).rjust(12)+" == "+ str(eventId).rjust(12)+" and trigTypes "+ unicode(triggerType)+" == "+ unicode(trigger.pluginTypeId))
					indigo.trigger.execute(trigger)
					break
		except Exception, e:
			self.indiLOG.log(40, u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return


######################################################################################


######################################################################################
	# manage the other plugins 
######################################################################################
	####----check ?     ---------
	def checkPluginsForUpdates(self):
		action = self.comparePluginsToListenToCheckForRestart( self.PLUGINS["used"],self.pluginSubscribedTo)
		if    action == "reload":   self.subscribeToPlugins(self.PLUGINS["used"])
		elif  action == "restart":  self.quitNow = " need to restart due to reduced plugin list"
		return 
	####----restart ?     ---------
	def comparePluginsToListenToCheckForRestart(self, NEW, active):
		self.lastPluginCheckUpdate = time.time()
		for pl in active:
			if pl not in NEW:
				return "restart"
		for pl in NEW:
			if pl not in active:
				return "reload"
		return ""
	####----subscribe     ---------
	def subscribeToPlugins(self, plList):
		self.pluginSubscribedTo ={}
		for pl in  plList:
			if len(pl) < 5: continue
			self.pluginSubscribedTo [pl] = True
			indigo.server.subscribeToBroadcast(pl, u"deviceStatusChanged", u"receiveDeviceChangedSubscription")
			if self.decideMyLog(u"SETUP"): 
				self.indiLOG.log(40, "subscribeToPlugins: "+pl  )
		return 

	####-----------------  ---------
	def getActivePlugins(self):
		for id in self.PLUGINS["used"]:
			self.PLUGINS["all"][id] = True
			
		ret = subprocess.Popen("export LANG=en_US.UTF-8; /bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].decode("UTF-8")
		lines = ret.strip("\n").split("\n")
		for line in lines:
			if len(line) < 40: continue
			items = line.split()
			if len(items) < 7: continue
			if line.find("indigoPlugin") ==-1: continue
			#self.myLog(-1,unicode(items))
			items = line.split(" -f")
			pName = items[1].split(".indigoPlugin")[0]
			try:
				plugId  = plistlib.readPlist(self.indigoPath+"Plugins/"+pName+".indigoPlugin/Contents/Info.plist")["CFBundleIdentifier"]
				###self.indiLOG.log(40, "reading: "+ self.indigoPath+"Plugins/"+pName+".indigoPlugin/Contents/Info.plist" +"  plid: "+ plugId)
				accept = True
				if plugId == self.pluginId:              accept = False
				elif plugId in self.PLUGINS["acceptable"]:   
					self.PLUGINS["all"][plugId] = True
					accept = True
				else:
					self.PLUGINS["all"][plugId] = True
					if plugId in self.PLUGINS["excluded"]:
						accept = False
				  
				if accept: self.PLUGINS["used"][plugId] = True
			except  Exception, e:
					self.indiLOG.log(40," getActivePlugins   Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
					version = " "
		self.savePLUGINS()
		return 




######################################################################################
	#utilities
######################################################################################
	####-----------------  ---------
	def filterDelayValues(self, filter, valuesDict, typeId="", targetId=""):
		xList =[]
		if filter in ["all","triggerRepeat"]: 
			xList.append(("0"  ,"immediate"))
		if filter  in ["all","short","doorPoll","events"]:
			xList.append(("1"  ,"1 sec"))
			xList.append(("2"  ,"2 sec"))
			xList.append(("3"  ,"3 sec"))
		if filter  in ["all","short","long","doorPoll","events"]:
			xList.append(("4"  ,"4 sec"))
			xList.append(("5"  ,"5 sec"))
			xList.append(("7"  ,"7 sec"))
			xList.append(("8"  ,"8 sec"))
			xList.append(("10" ,"10 sec"))
			xList.append(("12" ,"12 sec"))
		if filter  in ["all","short","long"]:
			xList.append(("15" ,"15 sec"))
			xList.append(("20" ,"20 sec"))
			xList.append(("30" ,"30 sec"))
			xList.append(("40" ,"40 sec"))
		if filter  in ["all","short","long","triggerRepeat"]:
			xList.append(("50" ,"50 sec"))
			xList.append(("60" ,"60 sec"))
			xList.append(("70" ,"70 sec"))
			xList.append(("90" ,"90 sec"))
		if filter in ["all","long","triggerRepeat"]:
			xList.append(("120" ,"2 minutes"))
			xList.append(("150" ,"2.5 minutes"))
			xList.append(("180" ,"3 minutes"))
			xList.append(("210" ,"3.5 minutes"))
			xList.append(("240" ,"4 minutes"))
			xList.append(("300" ,"5 minutes"))
			xList.append(("360" ,"6 minutes"))
			xList.append(("480" ,"8 minutes"))
			xList.append(("600" ,"10 minutes"))
			xList.append(("900" ,"15 minutes"))
		return xList

	####----directories ...     ---------
	def makeDirectories(self):
		if not os.path.exists(self.indigoDir):
			os.mkdir(self.indigoDir)

		if not os.path.exists(self.indigoPreferencesPluginDir):
			os.mkdir(self.indigoPreferencesPluginDir)

			if not os.path.exists(self.indigoPreferencesPluginDir):
				self.errorLog("error creating the plugin data dir did not work, can not create: "+ self.indigoPreferencesPluginDir)
				self.sleep(1000)
				exit()

	####----DEVICES/EVENTS READ / SAVE     ---------
	def readDEVICES(self):
		self.SENSORS  = {}
		try:
			f=open(self.indigoPreferencesPluginDir+"SENSORS","r")
			self.SENSORS= json.loads(f.read())
			f.close()
		except: pass
		self.saveSENSORS()
		return 
	####-----------------    ---------
	def saveSENSORS(self):
		try:
			xxx = copy.copy(self.SENSORS)
			self.SENSORS  = {}
			for sens in xxx:
				if len(sens) < 10: continue
				if len(sens.split(":::")) !=2: continue
				self.SENSORS[sens]= xxx[sens]

			for sens in self.SENSORS:
				for DEVICEid in self.SENSORS:
					self.SENSORS[DEVICEid]["used"] = False
					for EVENT in indigo.triggers.iter(self.pluginId):
						props = EVENT.pluginProps
						if "sensorsMembers" not in props: continue
						if DEVICEid in json.loads(props["sensorsMembers"]):
							self.SENSORS[DEVICEid]["used"] = True
							break
				out = "{"
				for id in self.SENSORS:
					out+='"'+id+'":'+json.dumps(self.SENSORS[id])+",\n"
				f=open(self.indigoPreferencesPluginDir+"SENSORS","w")
				f.write(out.strip(",\n")+"}")
				f.close()
		except  Exception, e:
					self.indiLOG.log(40,"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return 
	####-----------------    ---------
	def fixEVprops(self):
		return 

	####----Doors READ / SAVE     ---------
	def readDOORS(self):
		self.DOORS  = {}
		try:
			f=open(self.indigoPreferencesPluginDir+"DOORS","r")
			self.DOORS= json.loads(f.read())
			f.close()
		except: pass
		for DEVICEid in self.DOORS:
			for item in self.emptyDOOR:
				if item not in self.DOORS[DEVICEid]:
					self.DOORS[DEVICEid][item] = self.emptyDOOR[item]
		self.saveDOORS()
		return 
	####-----------------    ---------
	def saveDOORS(self):
		try:
			for DEVICEid in self.DOORS:
				self.DOORS[DEVICEid]["used"] = False
				for EVENT in indigo.triggers.iter(self.pluginId):
					props = EVENT.pluginProps
					if "doorsMembers" not in props: continue
					if DEVICEid in json.loads(props["doorsMembers"]):
						self.DOORS[DEVICEid]["used"] = True
						self.doorLoopWait = min(self.doorLoopWait,self.DOORS[DEVICEid]["pollingIntervall"])
						break

			out = "{"
			for id in self.DOORS:
				out+='"'+id+'":'+json.dumps(self.DOORS[id])+",\n"
			f=open(self.indigoPreferencesPluginDir+"DOORS","w")
			f.write(out.strip(",\n")+"}")
			f.close()
		except  Exception, e:
					self.indiLOG.log(40," Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return 
	####-----------------    ---------
	def readPLUGINS(self):
		try:
			f=open(self.indigoPreferencesPluginDir+"PLUGINS","r")
			self.PLUGINS = json.loads(f.read())
			f.close()
			self.savePLUGINS()
		except: pass
		return 
	####-----------------    ---------
	def savePLUGINS(self):
		try:
			for item in self.PLUGINS["excluded"]:
				self.PLUGINS["all"][item] = True
			for item in self.PLUGINS["acceptable"]:
				self.PLUGINS["all"][item] = True
			for item in self.PLUGINS["used"]:
				self.PLUGINS["all"][item] = True
			f=open(self.indigoPreferencesPluginDir+"PLUGINS","w")
			f.write(json.dumps(self.PLUGINS, sort_keys=True, indent=2))
			f.close()
		except  Exception, e:
					self.indiLOG.log(40,"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return 
	####-----------------    ---------
	####-----------------    --------- END


	####-----------------  
	def compareCurentToProp(self,testCondition, COMP, value, prop):
		try:
			if   COMP == "LT":
			   if  float(value)    >= float(prop):  testCondition  = False
			elif COMP == "LE":
			   if  float(value)    >  float(prop):  testCondition  = False
			elif COMP == "EQ":
			   if  unicode(value)  != (prop):       testCondition  = False
			elif COMP == "NE":
			   if  unicode(value)  == (prop):       testCondition  = False
			elif COMP == "GE":
			   if  float(value)    <  float(prop):  testCondition  = False
			elif COMP == "GT":
			   if  float(value)    <= float(prop):  testCondition  = False
			elif COMP == "in":
			   if  unicode(value)  not in (prop):   testCondition  = False
			elif COMP == "not in":
			   if  unicode(value)  in (prop):       testCondition  = False
		except Exception, e:
			self.indiLOG.log(40, u"Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return testCondition, value


	####----debug levels    ---------
	def getDebugSettings(self, init=False, theDict={}):
		self.debugLevel         = []
		if init:
			if self.pluginPrefs.get(u"debugDOORS", False):           self.debugLevel.append("DOORS")
			if self.pluginPrefs.get(u"debugSETUP", False):           self.debugLevel.append("SETUP")
			if self.pluginPrefs.get(u"debugRECEIVE", False):         self.debugLevel.append("RECEIVE")
			if self.pluginPrefs.get(u"debugEVENTS", False):          self.debugLevel.append("EVENTS")
			if self.pluginPrefs.get(u"debugall", False):             self.debugLevel.append("all")
  
			self.setLogfile(self.pluginPrefs.get("logFileActive2", "standard"))
			self.autoAddDevices      = self.pluginPrefs.get(u"autoAddDevices","ON")
			self.eventUpdateWait     = float(self.pluginPrefs.get(u"eventUpdateWait",10))
			self.eventVariablePrefix = self.pluginPrefs.get(u"eventVariablePrefix","EVENT")
			
		else:
			if theDict[u"debugDOORS"]:           self.debugLevel.append("DOORS")
			if theDict[u"debugSETUP"]:           self.debugLevel.append("SETUP")
			if theDict[u"debugRECEIVE"]:         self.debugLevel.append("RECEIVE")
			if theDict[u"debugEVENTS"]:          self.debugLevel.append("EVENTS")
			if theDict[u"debugall"]:             self.debugLevel.append("all")
			self.autoAddDevices =       theDict["autoAddDevices"]
			self.eventUpdateWait =      float(theDict["eventUpdateWait"])
			self.eventVariablePrefix =  theDict["eventVariablePrefix"]
			self.setLogfile(theDict[u"logFileActive2"])


		
		 ####----------------- add new device to list from bc message  ---------
	def checkParams(self, msg):
		try:
			if "newValue"   not in msg: 
				if self.decideMyLog(u"RECEIVE"): 
					self.indiLOG.log(40, "msg no  newValue", mType="receiveDeviceChanged" )
				return False
			if "valueForON" not in msg: 
				if self.decideMyLog(u"RECEIVE"): 
					self.indiLOG.log(40, "msg no  valueForON", mType="receiveDeviceChanged" )
				return False
			if "action"     not in msg: 
				if self.decideMyLog(u"RECEIVE"): 
					self.indiLOG.log(40, "msg no  action", mType="receiveDeviceChanged" )
				return False
			if "state"     not in msg: 
				if self.decideMyLog(u"RECEIVE"): 
					self.indiLOG.log(40, "msg no  state", mType="receiveDeviceChanged" )
				return False
			return True
		except Exception, e:
			self.indiLOG.log(40," Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return False
		
	####----------------- add new device to list from bc message  ---------
	def addNewSensor(self, DEVICEid, msg):
		try:
			if self.decideMyLog(u"RECEIVE") and False: 
				self.indiLOG.log(40, "DEVICEid not in SENSORS, skip", mType="receiveDeviceChanged" )
			if  self.autoAddDevices == "ON":
				self.SENSORS[DEVICEid] = copy.copy(self.emptyDEVICE)
				if ("name" not in msg) :
					dev = indigo.devices[int(msg["id"])]
					msg["name"] = dev.name
				if ("receivedPluginId" not in msg):
					dev = indigo.devices[int(msg["id"])]
					receivedPluginId = dev.pluginId
					msg["receivedPluginId"] = receivedPluginId

				self.SENSORS[DEVICEid]["pluginId"]   = msg["receivedPluginId"]
				self.SENSORS[DEVICEid]["valueForON"] = msg["valueForON"]
				self.SENSORS[DEVICEid]["name"]       = msg["name"]
				self.PLUGINS["used"][msg["receivedPluginId"]] = True
				self.saveSENSORS()
				self.savePLUGINS()
		except Exception, e:
			self.indiLOG.log(40," Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))

		return

	####-----------------  door gate ---------
	def getLastDoorChange(self, doorsM,lastDoorChange):
		lastChange    = 0
		changed = False
		for DEVICEid in doorsM:
			if DEVICEid in self.DOORS: # safety check
				if self.DOORS[DEVICEid]["lastChange"] > lastChange: 
					lastChange       = self.DOORS[DEVICEid]["lastChange"]  
					doorsM[DEVICEid] = self.DOORS[DEVICEid]["signalReceived"]
					
		if  lastChange != lastDoorChange:
			changed = True
		return changed, lastChange, doorsM


	####-----------------   overall last dev change for this event---------
	def getLastSensorChange(self, deviceM,haType):
		lastChange    = 0
		changed = False
		for DEVICEid in deviceM:
			if DEVICEid in self.SENSORS: # safety check
				if self.SENSORS[DEVICEid][haType]["lastChange"] > lastChange: 
					lastChange = self.SENSORS[DEVICEid][haType]["lastChange"]  
					
		return lastChange

		
	####-----------------  update individual device status  ---------
	def syncEventStatesToDeviceStates(self, DEVICEid,devicesM):
		update = False
		try:
			dd = self.splitDev(DEVICEid)
			if DEVICEid not in self.SENSORS: 
				if self.enableEventTracking  or  ( self.decideMyLog(u"EVENT") and update ) : 
					self.myLog(text = "  devId: %s"  %(dd[0]+"/"+dd[1]).ljust(27)+
						"  not in DEVICES "+
						"",     mType = "syncEventStatesToDeviceStates")
				return devicesM, update
			minTime = 10
			if   self.SENSORS[DEVICEid]["up"]["state"]     == "home":
				if devicesM[DEVICEid] !="home" and time.time() - self.SENSORS[DEVICEid]["up"]["lastChange"]   > minTime :
					 devicesM[DEVICEid] ="home"
					 update = True
			elif self.SENSORS[DEVICEid]["up"]["state"]     == "":
				if devicesM[DEVICEid] !="away" and time.time() - self.SENSORS[DEVICEid]["up"]["lastChange"]   > minTime :
					 devicesM[DEVICEid] ="away"
					 update = True

			if   self.SENSORS[DEVICEid]["down"]["state"]    == "away":
				if devicesM[DEVICEid] !="away" and time.time() - self.SENSORS[DEVICEid]["down"]["lastChange"]   > minTime :
					 devicesM[DEVICEid] ="away"
					 update = True
			elif self.SENSORS[DEVICEid]["down"]["state"]    == "":
				if devicesM[DEVICEid] !="home" and time.time() - self.SENSORS[DEVICEid]["down"]["lastChange"]   > minTime :
					 devicesM[DEVICEid] ="home"
					 update = True

			if self.enableEventTracking  or  ( self.decideMyLog(u"EVENT") and update ) :
				self.myLog(text = ""+
					"  devId: %s"  %(dd[0]+"/"+dd[1]).ljust(27)+
					";  up-state: %s" %unicode(self.SENSORS[DEVICEid]["up"]["state"])+
					";  do-state: %s" %unicode(self.SENSORS[DEVICEid]["down"]["state"])+
					"",     mType = "syncEventStatesToDeviceStates")

		except  Exception, e:
			if len(unicode(e)) > 5:
				indigo.server.log(u"Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return devicesM, update



	####-----------------	 ---------
	def completePath(self,inPath):
		if len(inPath) == 0: return ""
		if inPath == " ":	 return ""
		if inPath[-1] !="/": inPath +="/"
		return inPath

########################################
########################################
####----checkPluginPath----
########################################
########################################
	####------ --------
	def checkPluginPath(self, pluginName, pathToPlugin):

		if pathToPlugin.find("/" + self.pluginName + ".indigoPlugin/") == -1:
			self.indiLOG.critical(u"--------------------------------------------------------------------------------------------------------------")
			self.indiLOG.critical(u"The pluginName is not correct, please reinstall or rename")
			self.indiLOG.critical(u"It should be   /Libray/....../Plugins/" + pluginName + ".indigoPlugin")
			p = max(0, pathToPlugin.find("/Contents/Server"))
			self.indiLOG.critical(u"It is: " + pathToPlugin[:p])
			self.indiLOG.critical(u"please check your download folder, delete old *.indigoPlugin files or this will happen again during next update")
			self.indiLOG.critical(u"---------------------------------------------------------------------------------------------------------------")
			self.sleep(100)
			return False
		return True

########################################
########################################
####----move files to ...indigo x.y/Preferences/Plugins/< pluginID >.----
########################################
########################################
	####------ --------
	def moveToIndigoPrefsDir(self, fromPath, toPath):
		if os.path.isdir(toPath): 		
			return True
		indigo.server.log(u"--------------------------------------------------------------------------------------------------------------")
		indigo.server.log("creating plugin prefs directory ")
		os.mkdir(toPath)
		if not os.path.isdir(toPath): 	
			self.indiLOG.critical("| preference directory can not be created. stopping plugin:  "+ toPath)
			self.indiLOG.critical(u"--------------------------------------------------------------------------------------------------------------")
			self.sleep(100)
			return False
		indigo.server.log("| preference directory created;  all config.. files will be here: "+ toPath)
			
		if not os.path.isdir(fromPath): 
			indigo.server.log(u"--------------------------------------------------------------------------------------------------------------")
			return True
		cmd = "cp -R '"+ fromPath+"'  '"+ toPath+"'"
		os.system(cmd )
		self.sleep(1)
		indigo.server.log("| plugin files moved:  "+ cmd)
		indigo.server.log("| please delete old files")
		indigo.server.log(u"--------------------------------------------------------------------------------------------------------------")
		return True

########################################
########################################
####-----------------  logging ---------
########################################
########################################

	####----------------- ---------
	def setLogfile(self, lgFile):
		self.logFileActive =lgFile
		if   self.logFileActive =="standard":	self.logFile = ""
		elif self.logFileActive =="indigo":		self.logFile = self.indigoPath.split("Plugins/")[0]+"Logs/"+self.pluginId+"/plugin.log"
		else:									self.logFile = self.indigoPreferencesPluginDir +"plugin.log"
		self.myLog( text="myLogSet setting parameters -- logFileActive= "+ unicode(self.logFileActive) + "; logFile= "+ unicode(self.logFile)+ ";  debugLevel= "+ unicode(self.debugLevel) , destination="standard")


			
	####-----------------	 ---------
	def decideMyLog(self, msgLevel):
		try:
			if msgLevel	 == u"all" or u"all" in self.debugLevel:	 return True
			if msgLevel	 == ""	 and u"all" not in self.debugLevel:	 return False
			if msgLevel in self.debugLevel:							 return True
			return False
		except	Exception, e:
			if len(unicode(e)) > 5:
				indigo.server.log( u"decideMyLog in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
		return False

	####-----------------  print to logfile or indigo log  ---------
	def myLog(self,	 text="", mType="", errorType="", showDate=True, destination=""):
		   

		try:
			if	self.logFileActive =="standard" or destination.find("standard") >-1:
				if errorType == u"smallErr":
					self.indiLOG.error(u"------------------------------------------------------------------------------")
					self.indiLOG.error(text)
					self.indiLOG.error(u"------------------------------------------------------------------------------")

				elif errorType == u"bigErr":
					self.indiLOG.error(u"==================================================================================")
					self.indiLOG.error(text)
					self.indiLOG.error(u"==================================================================================")

				elif mType == "":
					indigo.server.log(text)
				else:
					indigo.server.log(text, type=mType)


			if	self.logFileActive !="standard":

				ts =""
				try:
					if len(self.logFile) < 3: return # not properly defined
					f =	 open(self.logFile,"a")
				except	Exception, e:
					indigo.server.log(u"in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
					try:
						f.close()
					except:
						pass
					return

				if errorType == u"smallErr":
					if showDate: ts = datetime.datetime.now().strftime(u"%H:%M:%S")
					f.write(u"----------------------------------------------------------------------------------\n")
					f.write((ts+u" ".ljust(12)+u"-"+text+u"\n").encode(u"utf8"))
					f.write(u"----------------------------------------------------------------------------------\n")
					f.close()
					return

				if errorType == u"bigErr":
					if showDate: ts = datetime.datetime.now().strftime(u"%H:%M:%S")
					ts = datetime.datetime.now().strftime(u"%H:%M:%S")
					f.write(u"==================================================================================\n")
					f.write((ts+u" "+u" ".ljust(12)+u"-"+text+u"\n").encode(u"utf8"))
					f.write(u"==================================================================================\n")
					f.close()
					return

				if showDate: ts = datetime.datetime.now().strftime(u"%H:%M:%S")
				if mType == u"":
					f.write((ts+u" " +u" ".ljust(25)  +u"-" + text + u"\n").encode("utf8"))
				else:
					f.write((ts+u" " +mType.ljust(25) +u"-" + text + u"\n").encode("utf8"))
				### print calling function 
				#f.write(u"_getframe:   1:" +sys._getframe(1).f_code.co_name+"   called from:"+sys._getframe(2).f_code.co_name+" @ line# %d"%(sys._getframe(1).f_lineno) ) # +"    trace# "+unicode(sys._getframe(1).f_trace)+"\n" )
				f.close()
				return


		except	Exception, e:
			if len(unicode(e)) > 5:
				self.indiLOG.critical(u"myLog in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
				indigo.server.log(text)
				try: f.close()
				except: pass



##################################################################################################################
####-----------------  valiable formatter for differnt log levels ---------
# call with: 
# formatter = LevelFormatter(fmt='<default log format>', level_fmts={logging.INFO: '<format string for info>'})
# handler.setFormatter(formatter)
class LevelFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None, level_fmts={}, level_date={}):
		self._level_formatters = {}
		self._level_date_format = {}
		for level, format in level_fmts.items():
			# Could optionally support level names too
			self._level_formatters[level] = logging.Formatter(fmt=format, datefmt=level_date[level])
		# self._fmt will be the default format
		super(LevelFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

	def format(self, record):
		if record.levelno in self._level_formatters:
			return self._level_formatters[record.levelno].format(record)

		return super(LevelFormatter, self).format(record)




