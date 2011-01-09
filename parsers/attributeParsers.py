from collections import defaultdict

from .objects.attribute import Attribute

from .utils.bytestream import ByteStream

class AttributeParser(object):
    def load(self,replay,filecontents):
        bytes = ByteStream(filecontents)
        bytes.skip(4,byteCode=True)                      #Always start with 4 nulls
        size = bytes.getLittleInt(4)       #get total attribute count
        
        replay.attributes = list()
        data = defaultdict(dict)
        for i in range(0,size):
            #Get the attribute data elements
            attr_data = [
                    bytes.getBig(4),        #Header
                    bytes.getLittleInt(4),  #Attr Id
                    bytes.getBigInt(1),      #Player
                    bytes.getLittle(4)      #Value
                ]
            
            #Complete the decoding in the attribute object
            attr = Attribute(attr_data)
            replay.attributes.append(attr)
            
            #Uknown attributes get named as such and are not stored
            #Index by player, then name for ease of access later on
            if attr.name != "Unknown":
                data[attr.player][attr.name] = attr.value
            
        #Get global settings first
        replay.speed = data[16]['Game Speed']
        replay.category = data[16]['Category']
        replay.type = data[16]['Game Type']
        
        #Set player attributes as available, requires already populated player list
        for pid,attributes in data.iteritems():
            if pid == 16: continue
            player = replay.players[pid]
            player.color = attributes['Color']
            player.team = attributes['Teams'+replay.type]
            player.race2 = attributes['Race']
            player.difficulty = attributes['Difficulty']
            
            #Computer players can't record games
            player.type = attributes['Player Type']
            if player.type == "Computer":
                player.recorder = False
        
