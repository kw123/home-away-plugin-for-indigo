# home-away-plugin-for-indigo
Purpose of the plugin:  
create reliable info for home away status by using regular on/of devices and DOOR info to time gate the status changes
It combines the info of several sensors with an AND (all must be up / down) and applies a time gate of the DOOR info to trigger 
home / away events    
Details  
==1. collect info from other ON/off(UP/down..) devices that broadcast their states eg piBeacon, fingscan, UniFi.
That info can be combined into groups to define away / home status (oneHome, allHome, oneAway, allAway) for the group of devices (individual, family, guests)
Together with expiration/delay times that can be set to allow a state going from UP/down/UP on a per device and or a per EVENT basis.
The ON/off devices must be from a plugin that braodcasts their states = support indigo internal BC-API. THIS pugin will subscribe to their broadcasts.
The plugin can set variables with the number of devices ON/off (set in config)
==2. THEN you can add devices like a DOOR open/close type (from alarm plugins or zwave/ insteon sensors) to set a time window for changes of the ON/off devices to be considered.
eg if a pibeacon goes ON to off and no door was opened in eg  +- 2 minutes the away trigger would not fire.
The Door devices can be any device with an On/off .. 1/0 state. They are polled on a regular basis(set in config)
Examples:  
Use your door sensor as DOOR device, set Time Window to 2 minutes
Use 1 or n iBeacons and or iphone Unifi / fingscan devices as 'DEVICEs'
Set delay before trigger to 5 seconds - to avoid on/off/on scenarious
1. Then, when you physically exit the door device starts its time window (x minutes before and after)
if the eg ibeacons/iPhone goes off within  2 minutes One/all Away condition is True and the event gets triggered
2. When coming back iBeacon/iPhone goes on, but does not set Home condition, only after the door opens (within 2 minutes) the One/All home condition is met.
You define the EVENTS in Indigo add new Trigger where you select 
Type = homeAway  
Event = All/One Device(s) must be ... home /Away  
you can use OneAway/Home or allAway/Home triggers for you or your family iBeacons/ iPhones  
======= initial setup =======  
--0. in config set basic parameters like repeat times, variables names, debug levels  
--1. define the plugins that participate(Broadcast)  (menu)  
--2. define the ON/off devices (menu) from these plugins you want to use  
--3. define the DOOR type devices (menu) from any ON/off device    
--4. Create a Trigger using the plugin configured EVENTS/events and subtypes (one/all/ home/away door/noDoor.. ) that can use one or many of the above defined devices to trigger actions
