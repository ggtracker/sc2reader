class PlayerDict(dict):
    """Delete is supported on the pid index only"""
    def __init__(self,*args,**kwargs):
        self._key_map = dict()
        
        if args:
            print args
            for arg in args[0]:
                self[arg[0]] = arg[1]
                
        if kwargs:
            print kwargs
            for key,value in kwargs.iteritems():
                self[key] = value
        
    def __getitem__(self,key):
        if isinstance(key,str):
            key = self._key_map[key]

        return super(PlayerDict,self).__getitem__(key)

    def __setitem__(self,key,value):
        if isinstance(key,str):
            self._key_map[key] = value.pid
            key = value.pid
        elif isinstance(key,int):
            self._key_map[value.name] = key
            
        super(PlayerDict,self).__setitem__(value.pid,value)
        
        
        
class ByteStream(object):
    """Track and return the bytes for investigative and debugging purposes"""
    """Most functions will return the byte_code as well when requested"""
    
    def __init__(self, stream):
        self.__cbyte = 0
        self.cursor = -1 #First element is 0
        self.stream = stream.encode("hex").upper()
        
    def get_big(self, number, byte_code=False):
        #Do a sanity check, if streams are parsed right this won't ever happen
        if len(self.stream)-self.__cbyte < number*2:
            msg = "Stream only has %s bytes left; %s bytes requested"
            raise ValueError(msg % (self.remaining, number) )
        
        #For big endian, the byte_string is the result
        result = self.stream[self.__cbyte:self.__cbyte+number*2]
        
        #Move the ByteStream forward
        self.__cbyte = self.__cbyte + number*2
        self.cursor = self.cursor + number
        
        if byte_code:
            return result, result
        return result
        
    def skip(self, number, byte_code=False):
        #This is just an alias for get_big really, still return the byte_string
        #so that it can be recorded for event analysis
        if byte_code:
            return self.get_big(number)
        self.get_big(number)
        
    def peek(self, number):
        return self.stream[self.__cbyte:self.__cbyte + number*2]
        
    def get_little(self, number, byte_code=False):
        #Get a list of the next 'number' of bytes from the stream
        bytes = [self.get_big(1) for i in range(0,number)]
        
        #Little endian is just the bytes in reverse order
        result = "".join(reversed(bytes))
        
        #But the byte_string must match original
        byte_string = "".join(bytes)
        
        if byte_code:
            return result, byte_string 
        return result
    
    def get_string(self, length, byte_code=False):
        string, bytes = self.get_big(length, byte_code=True)
        if byte_code:
            return string.decode("hex"), bytes
        return string.decode("hex")
        
    def get_big_int(self, number, byte_code=False):
        result, byte_string = self.get_big(number, byte_code=True)
        if byte_code:
            return int(result, 16), byte_string
        return int(result, 16)
        
    def get_little_int(self, number, byte_code=False):
        result, byte_string = self.get_little(number, byte_code=True)
        if byte_code:
            return int(result, 16), byte_string
        return int(result, 16)

    def get_count(self, byte_code=False):
        #Counts are always single byte, doubled values in replay files
        num, byte_string = self.get_big_int(1, byte_code=True)
        if byte_code:
            return num/2, byte_string
        return num/2
        
    def get_timestamp(self, byte_code=False):
        #Get the first byte
        byte, byte_string = self.get_big_int(1, byte_code=True)
        
        #The 7-8 bits of the byte indicate the byte length of the
        #timestamp, shift them off the time and loop through them
        time = byte >> 2
        for i in range(0,byte & 0x03):
            more, byte = self.get_big_int(1, byte_code=True)
            time = (time << 8) | more
            byte_string += byte
        
        if byte_code:
            return time, byte_string
        return time
        
    def get_vlf(self, byte_code=False):
        result, count, byte_string = 0, 0, ""
            
        #Loop through bytes until the first bit is zero
        #build the result by adding new bits to the right
        while(True):
            num, byte = self.get_big_int(1,byte_code=True)
            byte_string += byte
            if num & 0x80 > 0:
                result += (num & 0x7F) << (7*count)
                count = count + 1
            else:
                result += num << (7*count)
                break
        
        #The last bit of the result is a sign flag
        result = pow(-1, result & 0x1) * (result >> 1)
        
        if byte_code:
            return result, byte_string
        return result
        
    def parse_serialized_data(self, byte_code=False):
        #The first byte serves as a flag for the type of data to follow
        datatype, type_code = self.get_big_int(1, byte_code=True)
        
        if datatype == 0x02:
            #0x02 is a byte string with the first byte indicating the length of
            #the byte string to follow
            length, byte = self.get_count(byte_code=True)
            
            data, bytes = self.get_big(length, byte_code=True)
            bytes = byte + bytes
            
        elif datatype == 0x04:
            #0x04 is an serialized data list with first two bytes always 01 00
            #and the next byte indicating the number of elements in the list
            bytes = self.skip(2, byte_code=True)    #01 00
            count, byte = self.get_count(byte_code=True)
            bytes += byte
            
            #Return a parsed list of the indicated elements
            data = list()
            for i in range(0, count):
                ret, ret_bytes = self.parse_serialized_data(byte_code=True)
                data.append(ret)
                bytes += ret_bytes
            
        elif datatype == 0x05:
            #0x05 is a serialized key,value structure with the first byte
            #indicating the number of key,value pairs to follow
            data, (count, bytes) = dict(), self.get_count(byte_code=True)
            
            #When looping through the pairs, the first byte is the key,
            #followed by the serialized data object value
            for i in range(0,count):
                index, byte = self.get_count(byte_code=True)
                ret, ret_bytes = self.parse_serialized_data(byte_code=True)
                data[index] = ret
                bytes += byte + ret_bytes
            
        elif datatype == 0x06:
            data, bytes = self.get_big_int(1, byte_code=True)
            
        elif datatype == 0x07:
            data, bytes = self.get_big_int(4, byte_code=True)
            
        elif datatype == 0x09:
            data, bytes = self.get_vlf(byte_code=True)
            
        else:
            raise TypeError("Uknown Data Type: '%s'" % datatype)
        
        if byte_code:
            return data, type_code+bytes
        return data
        
    @property
    def remaining(self):
        return len(self.stream)-self.__cbyte
