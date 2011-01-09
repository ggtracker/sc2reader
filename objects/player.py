class Player(object):
    
    def __init__(self,pid, data):
        self.pid = pid
        self.name = data[0].decode("hex")
        self.uid = data[1][4]
        self.uidIndex = data[1][2]
        self.url = "http://us.battle.net/sc2/en/profile/%s/%s/%s/" % (self.uid,self.uidIndex,self.name)
        self.race = data[2].decode("hex")
        self.rgba = dict([
                ['r',data[3][1]],
                ['g',data[3][2]],
                ['b',data[3][3]],
                ['a',data[3][0]],
            ])
        self.recorder = True
        self.handicap = data[6]
        
    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid,self.name,self.race)
        
    def __repr__(self):
        return str(self)

