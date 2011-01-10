from objects.event import *
from utils.bytestream import ByteStream


class EventParser(object):
    def load(self,replay,filecontents):
        #set up eventObjectlist, start the timer, and process the file contents
        replay.events = list()
        elapsedTime,bytes = 0,ByteStream(filecontents)
        
        while bytes.length > 0:
            #First section is always a timestamp marking the elapsed time
            #since the last eventObjectlisted
            timeDiff,timeBytes = bytes.getTimestamp(byteCode=True)
            elapsedTime += timeDiff
            
            #Next is a compound byte where the first 3 bits XXX00000 mark the
            #eventType, the 4th bit 000X0000 marks the eventObjectas local or global,
            #and the remaining bits 0000XXXX mark the player id number.
            first,byte1 = bytes.getBigInt(1,byteCode=True)
            globalFlag = first & 0x10
            playerId = first & 0xF
            eventType = first >> 5
            
            #The following byte completes the unique eventObjectidentifier
            eventCode,byte2 = bytes.getBigInt(1,byteCode=True)
            
            #use the parsed information to load an eventObjecttype
            eventType = self.loadEvent(eventType,eventCode,replay,bytes)
            
            #execute the eventObjecttype with the information and byte stream
            #this will move the byte stream forward as required and set all
            #relevant eventObjectfields
            currentEvent = eventType(elapsedTime,eventType,globalFlag,playerId,eventCode,bytes)
            currentEvent.bytes = timeBytes+byte1+byte2+currentEvent.bytes
            replay.events.append(currentEvent)
        
    def loadEvent(self,replay,bytes):
        raise TypeError("No valid EventParser found for build %s" % replay.build)
        
class EventParser_16561(EventParser):
    def loadEvent(self,eventType,eventCode,replay,bytes):
        #
        #Game Initialization Events
        if eventType == 0x00:
            if eventCode == 0x1B or eventCode == 0x20 or eventCode == 0x0B:
                eventObject = PlayerJoinEvent()
            elif eventCode == 0x05:
                eventObject = GameStartEvent()
            elif eventCode == 0x09:
                eventObject = PlayerLeaveEvent()
            elif eventCode == 0x15:
                eventObject = WierdInitializationEvent()
            else:
                raise TypeError("Unknown event: %s - %s at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
                
        #
        #Player Action Events
        elif eventType == 0x01:
            if eventCode == 0x09:
                eventObject = PlayerLeaveEvent()
            elif (eventCode & 0x0F == 0xB) and (eventCode >> 4 <= 0x9):
                eventObject = AbilityEvent()
            elif (eventCode & 0xF == 0xC) and (eventCode >> 4) <= 0xA:
                eventObject = SelectionEvent()
            elif (eventCode & 0x0F == 0xD) and (eventCode >> 4 <= 0x9):
                eventObject = HotkeyEvent()
            elif (eventCode & 0x0F == 0xF) and (eventCode >> 4 <= 0x9):
                eventObject = ResourceTransferEvent()
            else:
                raise TypeError("Unknown event: %s - %s at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
                
        #
        #Unknown Function Events
        elif eventType == 0x02:
            if eventCode == 0x06:
                eventObject = UnknownEvent_02_06()
            elif eventCode == 0x07:
                eventObject = UnknownEvent_02_07()
            else:
                raise TypeError("Uknown event: %s - %s at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
                
        #
        #Camera Movement Events   
        elif eventType == 0x03:
            #print "Time %s - Player %s moves screen; eventObjectcode: %s" % (timestr,player,hex(eventCode))
            if eventCode == 0x87:
                eventObject = CameraMovementEvent_87()
            elif eventCode == 0x08:
                eventObject = CameraMovementEvent_08()
            elif eventCode == 0x18:
                eventObject = CameraMovementEvent_18()
            elif eventCode & 0xF == 1:
                eventObject = CameraMovementEvent_X1()
            else:
                raise TypeError("Uknown event: %s - %s at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
            
        #
        #Unknown Function Events
        elif eventType == 0x04:
            if eventCode & 0x0F == 2:
                UnknownEvent_04_X2()
            elif eventCode == 0x16:
                UnknownEvent_04_16()
            elif eventCode == 0xC6:
                UnknownEvent_04_C6()
            elif eventCode == 0x18 or eventCode == 0x87:
                eventObject = UnknownEvent_04_18or87()
            elif eventCode == 0x00:
                eventObject = UnknownEvent_04_00()
            #This doesn't make sense, isn't possible?
            #elif eventCode & 0x0C == 2:
            #    continue
            #This doesn't make sense either, why do nothing?
            #elif eventCode == 0x1C:
            #    continue
            else:
                raise TypeError("Uknown event: %s - %s  at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
        
        #
        #Unknown Function Events
        elif eventType == 0x05:
            if eventCode == 0x89:
                eventObject = UnknownEvent_05_89()
            else:
                raise TypeError("Uknown event: %s - %s  at location %s" % (hex(eventType),hex(eventCode),hex(bytes.cursor)))
                
        #
        #Unknown eventType found
        else:
            raise TypeError("Unknown eventType: %s at location %s" % (hex(eventType),hex(bytes.cursor)))

        return eventObject
