from time import ctime

from objects.player import Player
from objects.bytestream import ByteStream


class DetailParser(object):
    def load(self,replay,filecontents):
        data =  ByteStream(filecontents).parseSerializedData()
        
        replay.players = [None] #Pad the front for proper IDs
        for pid,pdata in enumerate(data[0]):
            replay.players.append(Player(pid+1,pdata)) #shift the id to start @ 1
            
        replay.map = data[1].decode("hex")
        replay.file_time = data[5]
        replay.date = ctime( (data[5]-116444735995904000)/10000000 )
