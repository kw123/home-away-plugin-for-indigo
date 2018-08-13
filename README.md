# home away plugin for indigo

## Purpose 
define **triggers** that allow a combination of information from different indigo devices (sensors) to be combined to set home / away events . 
It can be combined with a door time gate and other variable or device/state conditions to veto a trigger 

## What / how
The plugin can currently use info from fingscan(any ip device), unifi(any ip device) and pibeacon devices(ibeacons, BLE devices ..) called sensors in the following.   
Any plugin that can send *indigo broadcasts* could participate.  
Thesensor are combined with an "AND" to indicate how many sensors have come home or went away . NOT how many are home or are away - a slight difference.   
A snapshot would poll all devices and add their states.   
This plugin will receive updates on changes and then determine if a sensor went away or came home.   
THEN it determines how many came home / went away.  
In addition the plugin can use information from any other on/off type device (called doors in the followoing) to set a time gate function:  
only accept a come home or go away sensor change if the door was opened/closed x seconds before or y seconds after the sensor device came home or went away.  
This will reduce the false positives / negatives. Only when the door opens/ closes it will accpt a change in a sensor state.  

## Event types
the plugin supports:  
* **all home** all devices must have come home  
* **one home** at least one device just came home   
* **xx home with door gate** same as above, but the door must have opened or closed before / after the sensor(s) came home  
and the same for away  
* **all away** all devices must have went away  
* **one away** at least one device just went away  
* **xx away with door gate** same as above, but the door must have opened or closed before / after the sensor(s) went away  

##Parameters  
###in config you can set some timing parameters: how often should events be checked etc.  

### In Menue you can set:  
* **which plugin to listen to** select from all indigo plugins which it should listen to   
* **accept new sensors automatically**  collect all sensors that send broadcasts and add to internal list, or keep it static/manual 
* **define sensors** define plugin / device / state that make up the sensor list (pick from above collected list)   
* **define doors** define the indigo device /states that are used as door devices. You can also specify the polling interval.  
* **print** this help and a dump of events, sensors, and door definitions and current states.  

### In trigger edit
you can set various timing parameters and select which of the doors and sensors you want to use for THIS event trigger  
first you select event type: all/one home;  all/oneaway   
* **min time between 2 triggers** to avoid multiple triggers for one comming home / going away event  
* **trigger delay** wait some seconds to make sure the sensor state does not change.. to avoid false positives  
* **reset sensor** for a home event a sensor will stay home until it leaves AND a door open/close happens  
This option allows to have the sensor reset its state to away (for home events and visa versa for away events) without the door event  
* **variable condition** you can add a test on any variable <,<=, ==, >=, > "in" a test value. If not true the event will not trigger  
* **device/state condition** you can add a test on any device/state <,<=, ==, >=, > "in" a test value. If not true the event will not trigger  
* **select/delete sensors** then manage the sensors (one or many) that are part of this event group.  
* **select/delete doors** then manage doors (eg front and back door) that define the door time gate. You can set a before and an after time window   

## First steps
* install plugin
* set config parameters
* in menu define plugins, sensors, and doors
* create an indigo trigger, select homeAway / and your event type eg all/one home // away
* set parameters and select sensors that participate in THIS trigger 
* add door if desired
* add device/state or variable condition veto/ enable if desired.

 
