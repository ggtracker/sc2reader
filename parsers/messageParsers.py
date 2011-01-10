from objects import ByteStream,Message

class MessageParser(object):
    def load(self,replay,filecontents):
        replay.messages = list()
        bytes,time = ByteStream(filecontents),0
        
        while(bytes.length!=0):
            time += bytes.getTimestamp()
            playerId = bytes.getBigInt(1) & 0x0F
            flags = bytes.getBigInt(1)
            
            if flags & 0xF0 == 0x80:
            
                #ping or something?
                if flags & 0x0F == 3:
                    bytes.skip(8)
                    
                #some sort of header code
                elif flags & 0x0F == 0:
                    bytes.skip(4)
                    replay.players[playerId].recorder = False
                    
            elif flags & 0x80 == 0:
                replay.messages.append(Message(time,playerId,flags,bytes))
        
        recorders = [player for player in replay.players if player and player.recorder==True]
        if len(recorders) != 1:
            raise ValueError("There should be 1 and only 1 recorder; %s were found" % len(recorders))
        replay.recorder = recorders[0]
            
            
        
