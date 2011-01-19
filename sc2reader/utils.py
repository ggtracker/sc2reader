class ByteStream(object):
    """Track and return the bytes for investigative and debugging purposes"""
    """Most functions will return the byteCode as well when requested"""
    
    def __init__(self,stream):
        self.cursor = -1 #First element is 0
        self.stream = stream.encode("hex").upper()
        
    def getBig(self,number,byteCode=False):
        #Do a sanity check, if streams are parsed right this won't ever happen
        if len(self.stream) < number*2:
            msg = "Stream is only %s bytes long; %s bytes requested"
            raise ValueError(msg % (self.length,number) )
        
        #For big endian, the byteString is the result
        result = self.stream[:number*2]
        
        #Move the ByteStream forward
        self.stream = self.stream[number*2:]
        self.cursor = self.cursor + number
        
        if byteCode:
            return result,result
        return result
        
    def skip(self,number,byteCode=False):
        #This is just an alias for getBig really, still return the byteString
        #so that it can be recorded for event analysis
        if byteCode:
            return self.getBig(number)
        self.getBig(number)
        
    def peek(self,number):
        return self.stream[:number*2]
        
    def getLittle(self,number,byteCode=False):
        #Get a list of the next 'number' of bytes from the stream
        bytes = [self.getBig(1) for i in range(0,number)]
        
        #Little endian is just the bytes in reverse order
        result = "".join(reversed(bytes))
        
        #But the byteString must match original
        byteString = "".join(bytes)
        
        if byteCode:
            return result,byteString 
        return result
    
    def getString(self,length,byteCode=False):
        string, bytes = self.getBig(length,byteCode=True)
        if byteCode:
            return string.decode("hex"),bytes
        return string.decode("hex")
        
    def getBigInt(self,number,byteCode=False):
        result, byteString = self.getBig(number,byteCode=True)
        if byteCode:
            return int(result,16),byteString
        return int(result,16)
        
    def getLittleInt(self,number,byteCode=False):
        result, byteString = self.getLittle(number,byteCode=True)
        if byteCode:
            return int(result,16),byteString
        return int(result,16)

    def getCount(self,byteCode=False):
        #Counts are always single byte, doubled values in replay files
        num,byteString = self.getBigInt(1,byteCode=True)
        if byteCode:
            return num/2,byteString
        return num/2
        
    def getTimestamp(self,byteCode=False):
        #Get the first byte
        byte,byteString = self.getBigInt(1,byteCode=True)
        
        #The 7-8 bits of the byte indicate the byte length of the
        #timestamp, shift them off the time and loop through them
        time = byte >> 2
        for i in range(0,byte & 0x03):
            more,byte = self.getBigInt(1,byteCode=True)
            time = (time << 8) | more
            byteString += byte
        
        if byteCode:
            return time,byteString
        return time
        
    def getVLF(self,byteCode=False):
        result,count,byteString = 0,0,""
            
        #Loop through bytes until the first bit is zero
        #build the result by adding new bits to the right
        while(True):
            num,byte = self.getBigInt(1,byteCode=True)
            byteString += byte
            if num & 0x80 > 0:
                result += (num & 0x7F) << (7*count)
                count = count + 1
            else:
                result += num << (7*count)
                break
        
        #The last bit of the result is a sign flag
        result = pow(-1,result & 0x1) * (result >> 1)
        
        if byteCode:
            return result,byteString
        return result
        
    def parseSerializedData(self,byteCode=False):
        #The first byte serves as a flag for the type of data to follow
        datatype,typeCode = self.getBigInt(1,byteCode=True)
        
        if datatype == 0x02:
            #0x02 is a byte string with the first byte indicating the length of
            #the byte string to follow
            length,byte = self.getCount(byteCode=True)
            
            data,bytes = self.getBig(length,byteCode=True)
            bytes = byte + bytes
            
        elif datatype == 0x04:
            #0x04 is an serialized data list with first two bytes always 01 00
            #and the next byte indicating the number of elements in the list
            bytes = self.skip(2,byteCode=True)    #01 00
            count,byte = self.getCount(byteCode=True)
            bytes += byte
            
            #Return a parsed list of the indicated elements
            data = list()
            for i in range(0,count):
                ret, retBytes = self.parseSerializedData(byteCode=True)
                data.append(ret)
                bytes += retBytes
            
        elif datatype == 0x05:
            #0x05 is a serialized key,value structure with the first byte
            #indicating the number of key,value pairs to follow
            data,(count,bytes) = dict(),self.getCount(byteCode=True)
            
            #When looping through the pairs, the first byte is the key,
            #followed by the serialized data object value
            for i in range(0,count):
                index,byte = self.getCount(byteCode=True)
                ret, retBytes = self.parseSerializedData(byteCode=True)
                data[index] = ret
                bytes += byte + retBytes
            
        elif datatype == 0x06:
            data,bytes = self.getBigInt(1,byteCode=True)
            
        elif datatype == 0x07:
            data,bytes = self.getBigInt(4,byteCode=True)
            
        elif datatype == 0x09:
            data,bytes = self.getVLF(byteCode=True)
            
        else:
            raise TypeError("Uknown Data Type: '%s'" % datatype)
        
        if byteCode:
            return data,typeCode+bytes
        return data
        
    @property
    def length(self):
        return len(self.stream)
