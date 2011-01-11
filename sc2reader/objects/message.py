class Message(object):
    
    def __init__(self,time,player,flags,bytes):
        self.time,self.player = time,player
        self.target = flags & 0x03
        length = bytes.getBigInt(1)
        
        if flags & 0x08:
            length += 64
            
        if flags & 0x10:
            length += 128
            
        self.text = bytes.getString(length)
        
    def __str__(self):
        time = ((self.time/16)/60,(self.time/16)%60)
        return "%s - Player %s - %s" % (time,self.player,self.text)
        
    def __repr__(self):
        return str(self)
