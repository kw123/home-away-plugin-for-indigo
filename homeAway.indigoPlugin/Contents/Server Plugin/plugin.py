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
import versionCheck.versionCheck as VS
import plistlib

import threading
import copy
import json
import myLogPgms.myLogPgms 


## Static parameters, not changed in pgm
################################################################################
# noinspection PyUnresolvedReferences
class Plugin(indigo.PluginBase):
    ####-----------------             ---------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        #pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
        #self.plugin_file_handler.setFormatter(pfmt)

        self.pathToPlugin = self.completePath(os.getcwd())
        ## = /Library/Application Support/Perceptive Automation/Indigo 6/Plugins/piBeacon.indigoPlugin/Contents/Server Plugin
        p = max(0, self.pathToPlugin.lower().find("/plugins/")) + 1
        self.indigoPath = self.pathToPlugin[:p]
        #self.errorLog(self.indigoPath)
        #self.errorLog(self.pathToPlugin)
        #self.errorLog(self.pathToPlugin)
        self.indigoVersion = int(self.indigoPath.strip("/")[-1:])
        indigo.server.log(u"setting parameters for indigo version: >>"+unicode(self.indigoVersion)+u"<<")   
        self.pluginState                = "init"
        self.pluginVersion      = pluginVersion
        self.pluginId           = pluginId
        self.pluginName         = pluginId.split(".")[-1]

    ####-----------------             ---------
    def __del__(self):
        indigo.PluginBase.__del__(self)

######################################################################################
    # INIT    ## START
######################################################################################

    ####----------------- @ startup set global parameters, create directories etc ---------
    def startup(self):
    
        self.checkPluginName()
        indigo.server.log("initializing  ... variables, directories, ...")
        indigo.server.log("startup  my pluginid:  "+ self.pluginId) 
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
        self.MACuserName            = pwd.getpwuid(os.getuid())[0]
        self.MAChome                = os.path.expanduser("~")
        self.indigoDir              = self.MAChome+"/indigo/" #  this is the data directory
        self.homeAwayPath             = self.indigoDir + "homeAway/"
        self.loopSleep              = 1
        self.quitNow                = ""        
        self.pluginState            = "start"
        self.updateEVENTS           = {}
        self.selectedEventFunction  = ""
        self.selectedEvent          = ""
        self.triggerList            = []
        self.DeviceSelected         = "0"
        self.DoorSelected           = "0"
        self.enableEventTracking    = False
        self.logFileActive          = ""
        self.logFile                = ""
        self.debugLevel             = []
        self.doorLoopWait           = 99
        self.selectDeviceManagement = ""
        self.qualifiedDevicesUpdated= 0
        self.qualifiedDevices       = {}
        self.qualifiedDoorsUpdated  = 0
        self.qualifiedDoors         = {}
        self.autoAddDevices         = "ON"
        self.eventUpdateWait        = 20
        self.waitAfterStartForFirstTrigger= 60 # secs
        self.eventVariablePrefix    =  "EVENT"
        self.acceptableStateValues  = ["up","down","expired","on","off","yes","no","true","false","t","f","1","0","ja","nein","an","aus","open","closed","auf","zu"]
        self.emptyDEVICE            = {"up":{"lastChange":0,"signalReceived":"","state":"","delayTime":0},"down":{"lastChange":0,"signalReceived":"","state":"","delayTime":0},"valueForON":"","pluginId":"","name":"","used":False}
        self.emptyDOOR              = {"lastChange":0,"lastChangeDT":"","signalReceived":"","state":"","name":"","used":False,"requireStatusChange":True,"pollingIntervall":10,"lastCheck":0}
        self.evPropsToPrint         = ["devicesMembers","devicesCountTRUE","devicesTrigger","devicesTriggerTime","doorsMembers","doorsTimeWindow",
                                       "atleastOne","triggerTimeLast","minTimeTriggerBeforeRepeat","delayAfterDeviceTrigger","doorsTimeWindowBeforeOrAfter",
                                       "variableConditionID"]
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

        self.makeDirectories()

        self.ML = myLogPgms.myLogPgms.MLX()
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
            
            valuesDict["doorsMembers"]                  = ""
            valuesDict["devicesMembers"]                = ""
            valuesDict["triggerTimeLast"]               = 0 
            valuesDict["devicesTrigger"]                = False
            valuesDict["devicesTriggerTime"]            = 0
            valuesDict["devicesCountTRUE"]              = 0
            valuesDict["newOrExistingDevice"]           = "new"
            valuesDict["newOrExistingDoor"]             = "new"
            valuesDict["doorsTimeWindow"]               = "300"
            valuesDict["doorsTimeWindowBeforeOrAfter"]  = "After"
            valuesDict["atleastOne"]                    = "2-1/0-1"
            valuesDict["lastDoorChange"]                = 0
                        
            self.devicesMembers ={}
            self.doorsMembers ={}
        else:
            if "lastDoorChange" not in valuesDict:
                valuesDict["lastDoorChange"]            = 0
            valuesDict["oneAll"]                        = typeIdSplit[0]
            valuesDict["homeAway"]                      = typeIdSplit[1]
            valuesDict["noDoors"]                       = typeIdSplit[2]
            self.devicesMembers, valuesDict["devicesMembers"] = self.fixDICTEmpty(json.loads(valuesDict["devicesMembers"]))

            self.doorsMembers,   valuesDict["doorsMembers"]   = self.fixDICTEmpty(json.loads(valuesDict["doorsMembers"]))

        if typeIdSplit[2] == "no":
            valuesDict["newOrExistingDoor"]   = "no"
        
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


   ####-----------------  --------- DEVICES
   ####-----------------  ---------
    def filterDevicesEvent(self, filter, valuesDict, typeId, targetId):
        xList =[]
        #indigo.server.log("filterDevicesEvent:  typeId: "+ unicode(typeId)+"  targetId:"+ unicode(targetId)+"  valuesDict:"+unicode(valuesDict))
        if len(valuesDict) == 0: 
            #indigo.server.log("filterDevicesEvent:  vd empty returning")
            return xList

        if filter == "existing":
            for DEVICEid in self.devicesMembers:
                xList.append(( DEVICEid, self.DEVICES[DEVICEid]["name"]+"-"+DEVICEid.split(":::")[1]))

        else:
            for DEVICEid in self.DEVICES:
                if DEVICEid not in self.devicesMembers: 
                    dd = DEVICEid.split(":::")
                    xList.append(( DEVICEid, self.DEVICES[DEVICEid]["name"]+"-"+DEVICEid.split(":::")[1] ))

        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "xList "+ str(xList), mType="filterDevicesEvent" )
        return xList


    ####-----------------  ---------
    def buttonConfirmRemoveDeviceMemberCALLBACK(self, valuesDict, typeId, devId):
        try:
            if valuesDict["newOrExistingDevice"] !="delete": return 
            if len(valuesDict["selectExistingDevice"]) > 5:
                if valuesDict["selectExistingDevice"] in self.devicesMembers:
                    del self.devicesMembers[valuesDict["selectExistingDevice"]]
                    self.devicesMembers, valuesDict["devicesMembers"] = self.fixDICTEmpty(self.devicesMembers)
        except Exception, e:
            self.ML.myLog( text =u"error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return valuesDict

    ####-----------------  ---------
    def buttonConfirmDeviceSettingsCALLBACK(self, valuesDict, typeId, devId):
        valuesDict["msg"]                       = "settings saved"
        if valuesDict["newOrExistingDevice"] in ["new","existing"]:   
            if valuesDict["selectNewDevice"] not in self.devicesMembers:
                self.devicesMembers[valuesDict["selectNewDevice"]] =""
                self.devicesMembers, valuesDict["devicesMembers"] = self.fixDICTEmpty(self.devicesMembers)
        else:
            valuesDict["msg"]                       = "error"
        return valuesDict


   ####-----------------  --------- DOORS
   ####-----------------  ---------
    def filterDoorsEvent(self, filter, valuesDict, typeId, targetId):
        try:
            xList =[]
            if self.ML.decideMyLog(u"SETUP"): 
                self.ML.myLog(text = "typeId: "+ unicode(typeId)+"  targetId:"+ unicode(targetId)+"  valuesDict:"+unicode(valuesDict), mType="filterDoorsEvent")
            if len(valuesDict) == 0: 
                #indigo.server.log("filterDoorsInEvent:  vd empty returning")
                return xList
            xList =[]
                
            if filter == "existing":
                for DEVICEid in self.doorsMembers:
                    xList.append(( DEVICEid, self.DOORS[DEVICEid]["name"]+"-"+DEVICEid.split(":::")[1]))

            elif  filter == "new":
                for DEVICEid in self.DOORS:
                    if DEVICEid not in self.doorsMembers: 
                        dd = DEVICEid.split(":::")
                        xList.append(( DEVICEid, self.DOORS[DEVICEid]["name"]+"-"+DEVICEid.split(":::")[1] ))

            if self.ML.decideMyLog(u"SETUP"): 
                self.ML.myLog(text = "filterDoorsEvent    xList "+ str(xList) )
        except Exception, e:
            self.ML.myLog( text =u"filterDoorsEvent error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
            self.ML.myLog( text =u"filterDoorsEvent doorsMembers: "+unicode(self.doorsMembers) )
        return xList

    ####-----------------  ---------
    def buttonConfirmRemoveDoorMemberCALLBACK(self, valuesDict, typeId, devId):
        try:
            if valuesDict["newOrExistingDoor"] !="delete": return 
            if valuesDict["selectExistingDoor"] in self.doorsMembers:
                del self.doorsMembers[valuesDict["selectExistingDoor"]]
                self.doorsMembers, valuesDict["doorsMembers"] = self.fixDICTEmpty(self.doorsMembers)
        except Exception, e:
            self.ML.myLog( text =u"error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
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

        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = unicode(valuesDict), mType="butConfirmDoorsSettings")

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
        
        self.saveDEVICES()

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
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ self.PluginSelected +"  "+unicode(valuesDict), mType="butConfirmExistingOrNewPlugin")
        valuesDict["text0-1"]              = "  and then confirm !"

        try:
            if self.PluginSelected == "0":
                valuesDict["DefinePluginsAndNew"]  = True
                valuesDict["DefinePluginsAndOld"]  = False
            else:
                valuesDict["DefinePluginsAndOld"]  = True
                valuesDict["DefinePluginsAndNew"]  = False

        except  Exception, e:
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict
        
    ####-----------------  ---------
    def buttonConfirmDeletePluginCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "pluginid  "+ str(self.PluginSelected) +"  "+unicode(valuesDict), mType="butConfirmDeletePlugin")
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
                self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict

    ####-----------------  ---------
    def buttonConfirmPluginNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
           self.ML.myLog(text = "IndigoID "+ self.PluginSelected +"  "+unicode(valuesDict), mType="butConfirmExistingPlugin")
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
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict



######################################################################################
     # menues   ==> plugin Menu
######################################################################################


######################################################################################
    ####--------menu items  
######################################################################################
        
    def printHELP(self,valuesDict,typeId):
        indigo.server.log("\n\
Purpose of the plugin:\n\
create reliable info for home away status by using regular on/of devices and DOOR info to time gate the status changes\n\
It combines the info of several sensors with an AND (all must be up / down) and applies a time gate of the DOOR info to trigger \n\
home / away events\n\
Details\n\
==1. collect info from other ON/off(UP/down..) devices that broadcast their states eg piBeacon, fingscan, UniFi.\n\
That info can be combined into groups to define away / home status (oneHome, allHome, oneAway, allAway) for the group of devices (individual, family, guests)\n\
Together with expiration/delay times that can be set to allow a state going from UP/down/UP on a per device and or a per EVENT basis.\n\
The ON/off devices must be from a plugin that braodcasts their states = support indigo internal BC-API. THIS pugin will subscribe to their broadcasts.\n\
The plugin can set variables with the number of devices ON/off (set in config)\n\
==2. THEN you can add devices like a DOOR open/close type (from alarm plugins or zwave/ insteon sensors) to set a time window for changes of the ON/off devices to be considered.\n\
eg if a pibeacon goes ON to off and no door was opened in eg  +- 2 minutes the away trigger would not fire.\n\
The Door devices can be any device with an On/off .. 1/0 state. They are polled on a regular basis(set in config)\n\
Examples:\n\
Use your door sensor as DOOR device, set Time Window to 2 minutes\n\
Use 1 or n iBeacons and or iphone Unifi / fingscan devices as 'DEVICEs'\n\
Set delay before trigger to 5 seconds - to avoid on/off/on scenarious\n\
1. Then, when you physically exit the door device starts its time window (x minutes before and after)\n\
if the eg ibeacons/iPhone goes off within  2 minutes One/all Away condition is True and the event gets triggered\n\
2. When coming back iBeacon/iPhone goes on, but does not set Home condition, only after the door opens (within 2 minutes) the One/All home condition is met.\n\
You define the EVENTS in Indigo add new Trigger where you select \n\
Type = homeAway\n\
Event = All/One Device(s) must be ... home /Away\n\
you can use OneAway/Home or allAway/Home triggers for you or your family iBeacons/ iPhones\n\
======= initial setup =======\n\
--0. in config set basic parameters like repeat times, variables names, debug levels\n\
--1. define the plugins that participate(Broadcast)  (menu)\n\
--2. define the ON/off devices (menu) from these plugins you want to use\n\
--3. define the DOOR type devices (menu) from any ON/off device\n\
--4. Create a Trigger using the plugin configured EVENTS/events and subtypes (one/all/ home/away door/noDoor.. ) that can use one or many of the above defined devices to trigger actions\n\
")

    def printEVENTS(self,valuesDict,typeId):
        self.ML.myLog(text =" ==== EVENTs ============ ")
        for item in indigo.triggers.iter(self.pluginId):
            valuesDict = self.printEVENT(valuesDict,typeId,item)
        return valuesDict

    def printEVENT(self,valuesDict,typeId,item):
        props = item.pluginProps
        self.ML.myLog(text ="ev id: "+ unicode(item.id).ljust(12)+ "; ev Type: "+item.pluginTypeId +" ==== EVENT",mType=item.name+"==")
        for prop in self.evPropsToPrint:
            if prop not in props: continue
            if prop == "variableConditionID" and props[prop] not in ["0",""]: 
                var = indigo.variables[int(props[prop])]
                out = "Variable condition name" .ljust(30)  + ": "+ var.name
                self.ML.myLog(text = out,mType="EVENTS")
                out = "Variable value to trigger" .ljust(30)+ ": "+ props["variableConditionValue"]+" =-= currentValue: "+var.value
            else:
                out = prop.ljust(30)+ ": "+ unicode(props[prop])
            self.ML.myLog(text = out,mType="EVENTS")
        return valuesDict


    def printDEVICES(self,valuesDict,typeId):
        propsToPrint =["up","down","valueForON","used"]
        self.ML.myLog(text =" ==== DEVICEs============ ")
        for DEVICEid in self.DEVICES:
            self.ML.myLog(text ="ID: "+DEVICEid.split(":::")[0].ljust(12)+";  state: "+DEVICEid.split(":::")[1].ljust(15)+" plugin "+unicode(self.DEVICES[DEVICEid]["pluginId"]).ljust(20) +" ==== DEVICE",mType=self.DEVICES[DEVICEid]["name"]+"==")
            for prop in propsToPrint:
                    self.ML.myLog(text = prop.ljust(30)+ ": "+ unicode(self.DEVICES[DEVICEid][prop]),mType="DEVICE")
        return valuesDict


    def printDOORS(self,valuesDict,typeId):
        propsToPrint =["lastM1Change","lastChange","lastChangeDT","signalReceived","state","used","requireStatusChange","pollingIntervall","lastCheck"]
        self.ML.myLog(text =" ==== DOORs ============ ")
        for DEVICEid in self.DOORS:
            self.ML.myLog(text ="ID: "+DEVICEid.split(":::")[0].ljust(12)+";  state: "+DEVICEid.split(":::")[1].ljust(15)+" ==== DOOR",mType=self.DOORS[DEVICEid]["name"]+"==")
            for prop in propsToPrint:
                    self.ML.myLog(text = prop.ljust(30)+ ": "+ unicode(self.DOORS[DEVICEid][prop]),mType="DOOR")
        return valuesDict

    def startEventTracking(self):
        self.ML.myLog(text =" enabled EventTracking")
        self.enableEventTracking = True
        return 


    def stopEventTracking(self):
        self.ML.myLog(text =" disabled EventTracking ")
        self.enableEventTracking = False
        return 



######################################################################################
    ####--------menu item   DEVICES 
######################################################################################
    def filterExistingDevices(self,  filter="self", valuesDict=None, typeId="", targetId=0):

        retList = []

        for DEVICEid in self.DEVICES:
            if len(DEVICEid) < 3: continue
            exDevState = DEVICEid.split(":::")
            indigoID = exDevState[0]
            dev = indigo.devices[int(indigoID)]
            retList.append([indigoID, dev.name])
        retList = sorted( retList, key=lambda x:(x[1]) )
        retList.append((0,">>>> Pick new Device/Variable"))
        return retList

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
        for DEVICEid in self.DEVICES:
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
 
        self.DeviceSelected = valuesDict["selectedExistingOrNewDevice"]
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ self.DeviceSelected +"  "+unicode(valuesDict), mType="butConfirmExistingOrNewDevice")
        valuesDict["selectStatesOK"]       = False
        valuesDict["text1-1"]              = "  and then confirm !"
        valuesDict["text1-2"]              = "  and then confirm !"

        try:
            if self.DeviceSelected == "0":
                valuesDict["DefineDevicesAndNew"]  = True
                valuesDict["DefineDevicesAndOld"]  = False
                valuesDict["msg"]                  = "device NOT selected"
            else:
                valuesDict["DefineDevicesAndOld"]  = True
                valuesDict["DefineDevicesAndNew"]  = False
                valuesDict["selectStatesOK"]       = True
                valuesDict["msg"]                  = "device selected, enter state or delete"

        except  Exception, e:
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict
        
    ####-----------------  ---------
    def buttonConfirmDeleteDeviceCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ str(self.DeviceSelected) +"  "+unicode(valuesDict), mType="butConfirmDeleteDevice")
        valuesDict["DefineDevicesAndNew"]  = False
        valuesDict["DefineDevicesAndOld"]  = False
        valuesDict["selectStatesOK"]       = False

        try:
            if self.DeviceSelected !="0":
                deldev = {}
                for DEVICEid in self.DEVICES:
                    if self.DeviceSelected == DEVICEid.split(":::")[0]:
                        deldev[DEVICEid] = True
                for DEVICEid in self.DEVICES:
                    del self.DEVICES[DEVICEid]
                self.saveDEVICES()
                valuesDict["msg"]                  = "device deleted"
            
        except  Exception, e:
                self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict

    ####-----------------  ---------
    def buttonConfirmDeviceNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ self.DeviceSelected +"  "+unicode(valuesDict), mType="butConfirmExistingDevice")
        self.DeviceSelected = valuesDict["selectedNewDeviceID"]
        valuesDict["selectStatesOK"]       = False
        valuesDict["DefineDevicesAndNew"]  = False
        valuesDict["DefineDevicesAndOld"]  = False
    

        try:
            if self.DeviceSelected !="0":
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
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict


    ####-----------------  ---------
    def filterStates(self,  filter="self", valuesDict=None, typeId="", targetId=0):

        retList = []
        if self.DeviceSelected =="0": return retList

        selectedState =""

        for DEVICEid in self.DEVICES:
            if len(DEVICEid) < 3: continue
            exDevState = DEVICEid.split(":::")
            if self.DeviceSelected  == exDevState[0]:
                selectedState = exDevState[1]
                break

        dev = indigo.devices[int(self.DeviceSelected)]
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
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ str(self.DeviceSelected) +"  "+unicode(valuesDict), mType="butConfirmState")
        valuesDict["selectStatesOK"]       = False
        valuesDict["DefineDevicesAndNew"]  = False
        valuesDict["DefineDevicesAndOld"]  = False

        try:
            if self.DeviceSelected !="0":
                DEVICEid = self.DeviceSelected+":::"+valuesDict["selectedState"]

                if DEVICEid not in self.DEVICES:
                    self.DEVICES[DEVICEid] = copy.copy(self.emptyDEVICE)
                dev = indigo.devices[int(self.DeviceSelected)]
                self.DEVICES[DEVICEid]["pluginId"]          = dev.pluginId
                self.DEVICES[DEVICEid]["name"]              = dev.name
                self.DEVICES[DEVICEid]["state"]             = valuesDict["selectedState"]
                try: self.DEVICES[DEVICEid]["up"]["delayTime"]   = float(valuesDict["homeDelay"])
                except: pass
                try:self.DEVICES[DEVICEid]["down"]["delayTime"] = float(valuesDict["awayDelay"]) 
                except: pass

                valuesDict["msg"]                  = "device / state selected and saved"
            self.saveDEVICES()
            
        except  Exception, e:
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

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
            id = DEVICEid.split(":::")[0]
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
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ self.DoorSelected +"  "+unicode(valuesDict), mType ="butConfirmExistingOrNewDoor")
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
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict
        
    ####-----------------  ---------
    def buttonConfirmDeleteDoorCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ str(self.DoorSelected) +"  "+unicode(valuesDict), mType ="butConfirmDeleteDoor")
        valuesDict["DefineDoorsAndNew"]   = False
        valuesDict["DefineDoorsAndOld"]   = False
        valuesDict["selectDoorsStatesOK"] = False

        try:
            if self.DoorSelected !="0":
                deldev = {}
                for DEVICEid in self.DOORS:
                    if self.DoorSelected == DEVICEid.split(":::")[0]:
                        deldev[DEVICEid] = True
                for DEVICEid in deldev:
                    del self.DEVICES[DEVICEid]
                self.saveDOORS()
                valuesDict["msg"]                  = "device deleted"
            
        except  Exception, e:
                self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict

    ####-----------------  ---------
    def buttonConfirmDoorNewCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ self.DoorSelected +"  "+unicode(valuesDict), mType ="butConfirmExistingDoor")
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
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

        return valuesDict


    ####-----------------  ---------
    def filterDoorStates(self,  filter="self", valuesDict=None, typeId="", targetId=0):

        retList = []
        if self.DoorSelected =="0": return retList

        selectedState =""

        for DEVICEid in self.DOORS:
            if len(DEVICEid) < 3: continue
            exDevState = DEVICEid.split(":::")
            if self.DoorSelected  == exDevState[0]:
                selectedState = exDevState[1]
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
        retList = sorted( retList, key=lambda x:(x[1]) )
        retList.append((0,">>>> select state"))

        return retList

    ####-----------------  ---------
    def buttonConfirmDoorStateCALLBACK(self, valuesDict=None, typeId="", targetId=0):
 
        if self.ML.decideMyLog(u"SETUP"): 
            self.ML.myLog(text = "IndigoID "+ str(self.DoorSelected) +"  "+unicode(valuesDict), mtype="butConfirmDoorState"    )
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
            self.ML.myLog(text = "Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))

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
                    self.updateEVENTStatus(source="period")  # check if events are triggerd from delayed changes in devices

                if (time.time() - self.lastPluginCheckUpdate > 300):
                    self.checkPluginsForUpdates() # check if plugins defs are stiil ok 

        except  Exception, e:
                if len(unicode(e)) > 5:
                    indigo.server.log(u"in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
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
    ####-----------------check DEVICES if they chnaged whil not up, update if needed ---------
    def getDEVICEstates(self):
        update= False
        
        try:
            for DEVICEid in self.DEVICES:
                devState = DEVICEid.split(":::")
                dev = indigo.devices[int(devState[0])]
                lastChangedDT = dev.lastChanged
                lastChanged = time.mktime(lastChangedDT.timetuple())
                newST = dev.states[devState[1]]
                UP = (unicode(newST) == self.DEVICES[DEVICEid]["valueForON"])
                
                if self.enableEventTracking or self.ML.decideMyLog(u"SETUP"): 
                    self.ML.myLog(text = "getDEVICEstates    DEVICEid "+DEVICEid.ljust(20)+"  lastDT:"+unicode(lastChangedDT) +"   "+
                    unicode(int(lastChanged)) +" == last  "+unicode(int(self.DEVICES[DEVICEid]["up"]["lastChange"]))+"  "+
                    " delta  "+unicode(int(lastChanged - self.DEVICES[DEVICEid]["up"]["lastChange"])).rjust(10)+"  "+
                    "; ex-Tf: "+ unicode(self.DEVICES[DEVICEid]["up"]["signalReceived"]) +
                    "; upd?: "+unicode(self.DEVICES[DEVICEid]["up"]["signalReceived"] != UP ) +
                    "", mType = "getDEVICEstates" )

                if  (  self.DEVICES[DEVICEid]["up"]["signalReceived"]   != UP):  
                    self.DEVICES[DEVICEid]["up"]["lastChange"]          = lastChanged
                    self.DEVICES[DEVICEid]["up"]["signalReceived"]      = UP
                    self.DEVICES[DEVICEid]["up"]["state"]               = ""
                    self.DEVICES[DEVICEid]["down"]["lastChange"]        = lastChanged
                    self.DEVICES[DEVICEid]["down"]["signalReceived"]    = not UP
                    self.DEVICES[DEVICEid]["down"]["state"]             = ""
                    update= True
                    
            if update: self.saveDEVICES()
        except  Exception, e:
                if len(unicode(e)) > 5:
                    indigo.server.log(u"getDEVICEstates in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e)+"\n" +unicode(self.DEVICES) )
        return 


######################################################################################
    # DOOR status , by polling 
######################################################################################

    ####-----------------check door s ---------
    def getDOORstates(self):
        update= False
        
        try:
            for DEVICEid in self.DOORS:
                devState = DEVICEid.split(":::")
                if  time.time() - self.DOORS[DEVICEid]["lastCheck"]  < self.DOORS[DEVICEid]["pollingIntervall"] : continue
                dev = indigo.devices[int(devState[0])]
                newST = dev.states[devState[1]]
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
                    if self.enableEventTracking or self.ML.decideMyLog(u"DOORS") : 
                        self.ML.myLog(text = "getDOORstates    DEVICEid: "+DEVICEid.ljust(20)+ str(lastChangedDT) +" == lastDT  "+unicode(self.DOORS[DEVICEid]["lastChangeDT"])+"  "+
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
                    indigo.server.log(u"getDOORstates in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
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
            if self.ML.decideMyLog(u"RECEIVE") and False: 
                self.ML.myLog( text = unicode(MSG), mType="receiveDeviceChanged" )
            if "data" not in MSG: 
                if self.ML.decideMyLog(u"RECEIVE") : 
                    self.ML.myLog( text = "bad data received, not data element in dict "+ unicode(MSG), mType="receiveDeviceChanged" )
                return
                
            data = MSG["data"]
            if "pluginId" in MSG:
                receivedPluginId = MSG["pluginId"]
            else:
                receivedPluginId = ""
            for msg in data:
                upd = 0
                    
                if "newValue"   not in msg: 
                    if self.ML.decideMyLog(u"RECEIVE"): 
                        self.ML.myLog( text = "msg no  newValue", mType="receiveDeviceChanged" )
                    continue
                if "valueForON" not in msg: 
                    if self.ML.decideMyLog(u"RECEIVE"): 
                        self.ML.myLog( text = "msg no  valueForON", mType="receiveDeviceChanged" )
                    continue
                if "action"     not in msg: 
                    if self.ML.decideMyLog(u"RECEIVE"): 
                        self.ML.myLog( text = "msg no  action", mType="receiveDeviceChanged" )
                    continue
                if "state"     not in msg: 
                    if self.ML.decideMyLog(u"RECEIVE"): 
                        self.ML.myLog( text = "msg no  state", mType="receiveDeviceChanged" )
                    continue

                if msg["action"] == "event":
                    DEVICEid= str(msg["id"]) +":::"+ msg["state"]

                    if DEVICEid not in self.DEVICES: # check if device was ignored, add to the devices dict
                        if self.ML.decideMyLog(u"RECEIVE") and False: 
                            self.ML.myLog( text = "DEVICEid not in DEVICES, skip", mType="receiveDeviceChanged" )
                        if  self.autoAddDevices == "ON":
                            self.DEVICES[DEVICEid] = copy.copy(self.emptyDEVICE)
                            if ("name" not in msg or receivedPluginId =="" ) :
                                dev = indigo.devices[int(msg["id"])]
                                msg["name"] = dev.name
                                receivedPluginId = dev.pluginId
                            
                            self.DEVICES[DEVICEid]["pluginId"]   = receivedPluginId
                            self.DEVICES[DEVICEid]["valueForON"] = msg["valueForON"]
                            self.DEVICES[DEVICEid]["name"]       = msg["name"]
                            self.PLUGINS["used"][receivedPluginId] = True
                            self.saveDEVICES()
                            self.savePLUGINS()
                        continue
                    if self.ML.decideMyLog(u"RECEIVE"): 
                        self.ML.myLog( text = "msg:"+ str(msg) , mType="receiveDeviceChanged")
                    
                    self.DEVICES[DEVICEid]["valueForON"] = msg["valueForON"]
                    UP   = msg["newValue"] == msg["valueForON"]
                    UPnew   = self.DEVICES[DEVICEid]["up"]["signalReceived"]    != UP
                    DOWNnew = self.DEVICES[DEVICEid]["down"]["signalReceived"]  == UP
                    save = 0
                    if self.enableEventTracking  or  self.ML.decideMyLog(u"RECEIVE") : 
                            self.ML.myLog( text = "DEVICEid:accepted.. UP " +unicode(UP) +"  UPnew "+unicode(UPnew) +"  DOWNnew "+unicode(DOWNnew), mType="receiveDeviceChanged")
                    if UP:
                        if UPnew : 
                            if self.DEVICES[DEVICEid]["up"]["state"] != "home": 
                                self.DEVICES[DEVICEid]["up"]["state"] = "home"
                                self.DEVICES[DEVICEid]["up"]["lastChange"] = time.time()
                                upd = 2
                        if DOWNnew:
                            save = 1
                            if self.DEVICES[DEVICEid]["down"]["state"] != "": 
                                upd = max(1,upd)
                                self.DEVICES[DEVICEid]["down"]["state"] = ""
                                self.DEVICES[DEVICEid]["down"]["lastChange"] = time.time()
                                if self.DEVICES[DEVICEid]["up"]["delayTime"] == 0 or self.DEVICES[DEVICEid]["down"]["delayTime"] == 0 : upd = 2
                    
                    if not UP: 
                        if  UPnew : 
                            if self.DEVICES[DEVICEid]["up"]["state"] == "home": 
                                save +=2
                                upd = max(1,upd)
                                self.DEVICES[DEVICEid]["up"]["state"] = "triggeredDOWN"
                                self.DEVICES[DEVICEid]["up"]["lastChange"] = time.time()
                                if self.DEVICES[DEVICEid]["up"]["delayTime"] == 0 or self.DEVICES[DEVICEid]["down"]["delayTime"] == 0 : upd = 2
                    
                        if  DOWNnew: 
                            if self.DEVICES[DEVICEid]["down"]["state"] != "triggeredDOWN": 
                                save +=4
                                upd = max(1,upd)
                                self.DEVICES[DEVICEid]["down"]["state"] = "triggeredDOWN"
                                self.DEVICES[DEVICEid]["down"]["lastChange"] = time.time()
                                if self.DEVICES[DEVICEid]["up"]["delayTime"] == 0 or self.DEVICES[DEVICEid]["down"]["delayTime"] == 0 : upd = 2

                    if self.DEVICES[DEVICEid]["up"]["signalReceived"]   != UP:  save +=8
                    if self.DEVICES[DEVICEid]["down"]["signalReceived"] == UP:  save +=16
                    self.DEVICES[DEVICEid]["up"]["signalReceived"]    = UP
                    self.DEVICES[DEVICEid]["down"]["signalReceived"]  = not UP

                    if save>0 or upd >0: self.saveDEVICES()
                    if (self.enableEventTracking and save>0 ) or  self.ML.decideMyLog(u"RECEIVE") : 
                        dd = DEVICEid.split(":::")
                        self.ML.myLog( text = (dd[0]+":"+dd[1]).ljust(17)+
                    "; stateUP:"+self.DEVICES[DEVICEid]["up"]["state"].ljust(13)+
                    "; signRecUP:"+unicode(self.DEVICES[DEVICEid]["up"]["signalReceived"]).ljust(6)+
                    "; lChgUP:%6.1f"%(min(time.time()-self.DEVICES[DEVICEid]["up"]["lastChange"],9999))+
                    "; stateDN:"+self.DEVICES[DEVICEid]["down"]["state"].ljust(13)+
                    "; signRecDN:"+unicode(self.DEVICES[DEVICEid]["down"]["signalReceived"]).ljust(6)+
                    "; lChgDN:%6.1f"%(min(time.time()-self.DEVICES[DEVICEid]["down"]["lastChange"],9999))+
                    "; save:%d"%(save)+
                    "",     mType="rcvBC:"+msg["name"])
                    self.updateDeviceStatus(DEVICEid,periodCheck="devChg", callEvent=(upd==2)) # set new status now 
        except Exception, e:
            indigo.server.log(u"error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))

    ####-----------------  update device status  ---------
    def periodCheckDEVICES(self):
        for DEVICEid in self.DEVICES:
            self.updateDeviceStatus(DEVICEid, periodCheck="period")
        return 
        
    ####-----------------  update individual device status  ---------
    def updateDeviceStatus(self, DEVICEid, periodCheck="",callEvent=False):
        try:
            if DEVICEid not in self.DEVICES: return 
            save = 0
            if self.DEVICES[DEVICEid]["up"]["state"] == "triggeredDOWN": 
                if time.time() - self.DEVICES[DEVICEid]["up"]["lastChange"] > self.DEVICES[DEVICEid]["up"]["delayTime"]: 
                    self.DEVICES[DEVICEid]["up"]["lastChange"] = time.time() 
                    self.DEVICES[DEVICEid]["up"]["state"] = ""
                save = 1        

            if self.DEVICES[DEVICEid]["down"]["state"] == "triggeredDOWN": 
                if time.time() - self.DEVICES[DEVICEid]["down"]["lastChange"] > self.DEVICES[DEVICEid]["down"]["delayTime"]:
                    self.DEVICES[DEVICEid]["down"]["lastChange"] = time.time() 
                    self.DEVICES[DEVICEid]["down"]["state"] = "away"
                save +=2        
            if save or callEvent: 
                self.saveDEVICES()
                self.updateEVENTStatus(source=periodCheck)
            if (self.enableEventTracking and save>0 ) or  self.ML.decideMyLog(u"RECEIVE") : 
                dd = DEVICEid.split(":::")
                self.ML.myLog( text = (dd[0]+":"+dd[1]).ljust(17)+
                    ";  stateUP:"+self.DEVICES[DEVICEid]["up"]["state"].ljust(13)+
                    ";  signRecUP:"+unicode(self.DEVICES[DEVICEid]["up"]["signalReceived"])[0]+
                    ";  lChgUP:%5.1f"%(min(time.time()-self.DEVICES[DEVICEid]["up"]["lastChange"],999))+
                    ";  stateDN:"+self.DEVICES[DEVICEid]["down"]["state"].ljust(13)+
                    ";  signRecDN:"+unicode(self.DEVICES[DEVICEid]["down"]["signalReceived"])[0]+
                    ";  lChgDN:%5.1f"%(min(time.time()-self.DEVICES[DEVICEid]["down"]["lastChange"],999))+
                    ";  save:%d"%(save)+
                    "",     mType="rcvBC:"+periodCheck)

        except  Exception, e:
            if len(unicode(e)) > 5:
                indigo.server.log(u"updateDeviceStatus in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return 

    ####-----------------  update EVENTS status  ---------
    def updateEVENTStatus(self,source=""):
        try:
            self.lastEventUpdate  = time.time()
            self.updateEVENTS     = {} #reset any pending update , wil be done after this 
            save = False

            for EVENT in indigo.triggers.iter(self.pluginId):
                if not EVENT.enabled : continue
                save = 0
                props = EVENT.pluginProps
                oneAll   = props["oneAll"] 
                homeAway = props["homeAway"] 
                noDoors  = props["noDoors"] 
                triggerType = oneAll+"-"+homeAway+"-"+noDoors
                if  homeAway =="away":  doorsTimeWindowSymetric = "After"
                else:                   doorsTimeWindowSymetric = "BeforeOrAfter"
                if "doorsTimeWindowBeforeOrAfter" in props: doorsTimeWindowBeforeOrAfter = props["doorsTimeWindowBeforeOrAfter"]
                devicesM        = json.loads(props["devicesMembers"])
                try:    lastDoorChange = props["lastDoorChange"]
                except: lastDoorChange = 0
                dChanged, doorsLastChange, doorsM ,newChanged= self.getLastDoorChange(json.loads(props["doorsMembers"]), lastDoorChange)
                if dChanged: 
                    props["doorsMembers"]   = json.dumps(doorsM)
                    props["lastDoorChange"] = newChanged
                    save = 1
                        
                dTW             = float(props["doorsTimeWindow"])

                try:    olddevicesCountTRUE = int(props["devicesCountTRUE"])
                except: olddevicesCountTRUE = 0

                counter = {"home":0,"away":0}
                for DEVICEid in devicesM:
                    if DEVICEid in self.DEVICES: # safety check
                        for ud,ha in (("up","home"),("down","away")):
                            dTT_dLC         = self.DEVICES[DEVICEid]["down"]["lastChange"] - doorsLastChange
                            if self.DEVICES[DEVICEid][ud]["state"]   == ha and devicesM[DEVICEid] != ha: 
                                if ( 
                                        (
                                            noDoors != "doors" or noDoors == "doors" 
                                        )
                                        and  
                                        ( 
                                            (  doorsTimeWindowBeforeOrAfter =="BeforeOrAfter"   and  abs(dTT_dLC) < dTW                   )  # for home use symetric window
                                            or      
                                            (  doorsTimeWindowBeforeOrAfter =="Before"          and  abs(dTT_dLC) < dTW  and dTT_dLC < 0  )  # device event must be fore door, eg coming home device present, then open door
                                            or     
                                            (  doorsTimeWindowBeforeOrAfter =="After"           and  abs(dTT_dLC) < dTW  and dTT_dLC > 0  )   # dvice event must be after door event: open door then leave    
                                        )
                                    ): # for away use trailing window
                                        devicesM[DEVICEid] = ha
                                        props["devicesMembers"] = json.dumps(devicesM)
                                        save +=2
                            if (self.enableEventTracking and save>0 ) or self.ML.decideMyLog(u"EVENTS"): 
                                self.ML.myLog( text =""+
                                    "DEVid:%s" %( DEVICEid.replace(":::","/").ljust(18) ) +
                                    ";  noDoors:%s" %(noDoors.ljust(5) ) +
                                    ";  ud:%s" %( ud[0:2] ) +
                                    ";  ha:%s" %( ha[0:2] ) +
                                    ";  devTrgT-tDoor:%7.1f" %(  min(dTT_dLC, 9999)  ) +
                                    ";  dTW:%7.1f" %(  min(dTW, 9999)  )     +
                                    ";  devM:%s" %(  devicesM[DEVICEid].ljust(5)  )    +
                                    ";  devUPs:%s" %(self.DEVICES[DEVICEid][ud]["state"])+
                                    "",mType= "EV-"+source+":"+EVENT.name )

                for DEVICEid in devicesM:
                    if DEVICEid in self.DEVICES: # safety check
                        if devicesM[DEVICEid] == "home":
                            counter["home"] +=1
                        if devicesM[DEVICEid] == "away":
                            counter["away"] +=1

                                
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
                if  olddevicesCountTRUE != counter[homeAway]:
                    if (  
                            ( oneAll == "all" and counter[homeAway] == len(devicesM) ) 
                             or 
                            ( oneAll == "one" and counter[homeAway] == 1   and "atleastOne" in props and 
                                (   
                                    ( props["atleastOne"].find("2-1") >-1  and olddevicesCountTRUE > 1 )  # from 2-->1
                                or
                                    ( props["atleastOne"].find("0-1") >-1  and olddevicesCountTRUE == 0 ) # from 0-->1
                                )
                            )
                        ):  # one : if 0-->1; or 2-->1 ?
                        props["devicesTrigger"]      = True 
                        props["devicesTriggerTime"]  = time.time()  # start the timer 
                    else:
                        props["devicesTrigger"]      = False 
                    props["devicesCountTRUE"]        = counter[homeAway]
                    save +=4
      
                ## ready to trigger?

                testVarCondition  = True
                varValue          =""
                if "variableConditionID" in props and props["variableConditionID"] not in ["0",""] and "variableConditionValue" in props:
                     var = indigo.variables[int(props["variableConditionID"])]
                     varValue = var.value
                     if  varValue != props["variableConditionValue"]: testVarCondition  = False

                triggered = props["devicesTrigger"]
                if triggered:
                    ## first test if we should ignore , to often? 
                    if (  time.time() - props["triggerTimeLast"] < float(props["minTimeTriggerBeforeRepeat"])  ):
                            props["devicesTrigger"]  = False
                            save +=8
                    ##  do a delay 
                    elif  ( time.time() - props["devicesTriggerTime"] < float(props["delayAfterDeviceTrigger"]) ): # requested a delay after trigger to allow a quick reset
                            pass
                    else:
                        if testVarCondition:
                            props["triggerTimeLast"] = time.time()
                            self.triggerEvent(EVENT.id,triggerType)
                        else:
                            if (self.enableEventTracking and save >0 )  or  self.ML.decideMyLog(u"EVENTS"): 
                                self.ML.myLog( text= "trig  vetoed by variable condition: "+varValue+" NE "+props["variableConditionValue"]+
                                "",mType= "EV-"+source+":"+EVENT.name )
                        save +=16
                        props["devicesTrigger"]  = False
                        
                if save: EVENT.replacePluginPropsOnServer(props)
                if (self.enableEventTracking and save >0 )  or  self.ML.decideMyLog(u"EVENTS") : 
                    self.ML.myLog( text =""+
                    "trigTyp: "              +unicode( triggerType ).ljust(14)+
                    ";  devTrig: "           +unicode( triggered )[0]+" -> "+unicode( props["devicesTrigger"] )[0]+
                    ";  allT:"               +unicode( oneAll == "all" and counter[homeAway] == len(devicesM) )[0]+
                    ";  1T:"                 +unicode( oneAll == "one" and counter[homeAway] >= 1 and  olddevicesCountTRUE == 0  )[0]+
                    ";  olddevCtTRUE:"       +unicode( olddevicesCountTRUE ).ljust(2)+
                    ";  countTRUE:"          +unicode(counter).replace(" ","")+
                    ";  Ndevs:%d"            %( len(devicesM) )+
                    ";  devM:%s"             %(props["devicesMembers"].replace(" ","").replace(":::","/")) +
                    ";  dorM:%s"             %(props["doorsMembers"].replace(" ","").replace(":::","/")) +
                    ";  t-tTrg:%6.1f"        %(  min(time.time() - props["devicesTriggerTime"]   , 9999)  )+
                    ";  t-tDoor:%6.1f"       %(  min(time.time() - doorsLastChange   , 9999)  )+
                    ";  doorTWdow:%4d"       %( dTW )  +
                    ";  varCond:%s"          %unicode(testVarCondition)[0]  +
                    ";  save:%d"%(save)+
                    "",mType= "EV-"+source+":"+EVENT.name )
     
        except Exception, e:
            self.ML.myLog( text = u"updateEVENTStatus error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return 

    ####-----------------  manage trigger list---------
    def triggerStartProcessing(self, trigger):
        self.triggerList.append(trigger.id)

    def triggerStopProcessing(self, trigger):
        if trigger.id in self.triggerList:
            self.triggerList.remove(trigger.id)


    ####-----------------  door gate ---------
    def getLastDoorChange(self, doorsM,lastDoorChange):
        doorsLastChange    = 0
        changed = False
        for DEVICEid in doorsM:
            if DEVICEid in self.DOORS: # safety check
                if self.DOORS[DEVICEid]["lastChange"] > doorsLastChange: 
                    doorsLastChange = self.DOORS[DEVICEid]["lastChange"]  
                    doorsM[DEVICEid] = self.DOORS[DEVICEid]["signalReceived"]
                    
        if  doorsLastChange != lastDoorChange:
            changed = True
        return changed, doorsLastChange, doorsM, doorsLastChange

######################################################################################
    # Indigo Trigger Firing

    ####-----------------  
    def triggerEvent(self, eventId, triggerType):
        try:
            if (time.time() - self.pluginStartTime) < self.waitAfterStartForFirstTrigger: return 
            for trigId in self.triggerList:
                trigger = indigo.triggers[trigId]
                
                if trigger.pluginTypeId == triggerType and trigId == eventId:
                    if self.ML.decideMyLog(u"EVENTS"):
                        self.ML.myLog( text =u"trigger/eventId id: "+ str(trigId).rjust(12)+" == "+ str(eventId).rjust(12)+" and trigTypes "+ unicode(triggerType)+" == "+ unicode(trigger.pluginTypeId))
                    indigo.trigger.execute(trigger)
                    break
        except Exception, e:
            self.ML.myLog( text = u"error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
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
            if self.ML.decideMyLog(u"SETUP"): 
                self.ML.myLog( text = "subscribeToPlugins: "+pl  )
        return 

    ####-----------------  ---------
    def getActivePlugins(self):
        for id in self.PLUGINS["used"]:
            self.PLUGINS["all"][id] = True
            
        ret = subprocess.Popen("/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0]
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
                    self.ML.myLog( text =" getActivePlugins   error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
                    version = " "
        self.savePLUGINS()
        return 




######################################################################################
    #utilities
######################################################################################
    ####-----------------  ---------
    def filterDelayValues(self, filter, valuesDict, typeId="", targetId=""):
        xList =[]
        if filter in ["all"]: 
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
            xList.append(("50" ,"50 sec"))
            xList.append(("60" ,"60 sec"))
            xList.append(("70" ,"70 sec"))
            xList.append(("90" ,"90 sec"))
        if filter in ["all","long"]:
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

        if not os.path.exists(self.homeAwayPath):
            os.mkdir(self.homeAwayPath)

            if not os.path.exists(self.homeAwayPath):
                self.errorLog("error creating the plugin data dir did not work, can not create: "+ self.homeAwayPath)
                self.sleep(1000)
                exit()

    ####----DEVICES/EVENTS READ / SAVE     ---------
    def readDEVICES(self):
        self.DEVICES  = {}
        try:
            f=open(self.homeAwayPath+"DEVICES","r")
            self.DEVICES= json.loads(f.read())
            f.close()
        except: pass
        self.saveDEVICES()
        return 
    ####-----------------    ---------
    def saveDEVICES(self):
        try:
            for DEVICEid in self.DEVICES:
                self.DEVICES[DEVICEid]["used"] = False
                for EVENT in indigo.triggers.iter(self.pluginId):
                    props = EVENT.pluginProps
                    if "devicesMembers" not in props: continue
                    if DEVICEid in json.loads(props["devicesMembers"]):
                        self.DEVICES[DEVICEid]["used"] = True
                        break
            out = "{"
            for id in self.DEVICES:
                out+='"'+id+'":'+json.dumps(self.DEVICES[id])+",\n"
            f=open(self.homeAwayPath+"DEVICES","w")
            f.write(out.strip(",\n")+"}")
            f.close()
        except  Exception, e:
                    self.ML.myLog( text =" saveDOORS   error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return 
    ####-----------------    ---------
    def fixEVprops(self):
        return 

    ####----Doors READ / SAVE     ---------
    def readDOORS(self):
        self.DOORS  = {}
        try:
            f=open(self.homeAwayPath+"DOORS","r")
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
                        break
                        self.doorLoopWait = min(self.doorLoopWait,self.DOORS[DEVICEid]["pollingIntervall"])
                        
            out = "{"
            for id in self.DOORS:
                out+='"'+id+'":'+json.dumps(self.DOORS[id])+",\n"
            f=open(self.homeAwayPath+"DOORS","w")
            f.write(out.strip(",\n")+"}")
            f.close()
        except  Exception, e:
                    self.ML.myLog( text =" saveDOORS   error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return 
    ####-----------------    ---------
    def readPLUGINS(self):
        try:
            f=open(self.homeAwayPath+"PLUGINS","r")
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
            f=open(self.homeAwayPath+"PLUGINS","w")
            f.write(json.dumps(self.PLUGINS, sort_keys=True, indent=2))
            f.close()
        except  Exception, e:
                    self.ML.myLog( text =" savePLUGINS   error in  Line '%s' ;  error='%s'" % (sys.exc_traceback.tb_lineno, e))
        return 
    ####-----------------    ---------
    ####-----------------    --------- END

    ####-----------------    ---------
    def completePath(self,inPath):
        if len(inPath) == 0: return ""
        if inPath == " ":    return ""
        if inPath[-1] !="/": inPath +="/"
        return inPath
    ####----debug levels    ---------
    def getDebugSettings(self, init=False, theDict={}):
        self.debugLevel         = []
        if init:
            if self.pluginPrefs.get(u"debugDOORS", False):           self.debugLevel.append("DOORS")
            if self.pluginPrefs.get(u"debugSETUP", False):           self.debugLevel.append("SETUP")
            if self.pluginPrefs.get(u"debugRECEIVE", False):         self.debugLevel.append("RECEIVE")
            if self.pluginPrefs.get(u"debugEVENTS", False):          self.debugLevel.append("EVENTS")
            if self.pluginPrefs.get(u"debugall", False):             self.debugLevel.append("all")
  
            newLogFile               = self.pluginPrefs.get("logFilePath", "no")
            self.autoAddDevices      = self.pluginPrefs.get(u"autoAddDevices","ON")
            self.eventUpdateWait     = float(self.pluginPrefs.get(u"eventUpdateWait",10))
            self.eventVariablePrefix = self.pluginPrefs.get(u"eventVariablePrefix","EVENT")
            
        else:
            if theDict[u"debugDOORS"]:           self.debugLevel.append("DOORS")
            if theDict[u"debugSETUP"]:           self.debugLevel.append("SETUP")
            if theDict[u"debugRECEIVE"]:         self.debugLevel.append("RECEIVE")
            if theDict[u"debugEVENTS"]:          self.debugLevel.append("EVENTS")
            if theDict[u"debugall"]:             self.debugLevel.append("all")
            newLogFile =                theDict["logFilePath"]
            self.autoAddDevices =       theDict["autoAddDevices"]
            self.eventUpdateWait =      float(theDict["eventUpdateWait"])
            self.eventVariablePrefix =  theDict["eventVariablePrefix"]

        if newLogFile != self.logFileActive:
            if newLogFile =="no":
                self.logFile =""
                indigo.server.log("logfile handling: regular indigo logfile")
            elif newLogFile =="indigo":
                self.logFile = self.indigoPath.split("Plugins/")[0]+"logs/"+self.pluginId+"/homeAway.log"
                indigo.server.log("logfile output to : "+self.logFile)
            else:
                self.logFile    = self.homeAwayPath + "homeAway.log"
                indigo.server.log("logfile output to : "+self.logFile)
        self.logFileActive = newLogFile
        self.ML.myLogSet(debugLevel = self.debugLevel ,logFileActive=self.logFileActive, logFile = self.logFile)
        self.ML.myLog( text = "getDebugSettings: "+unicode(self.debugLevel) )


