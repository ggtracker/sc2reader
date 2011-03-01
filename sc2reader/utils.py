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
        
        
from StringIO import StringIO
from os import SEEK_CUR,SEEK_END
from struct import unpack

class ByteStream(object):
    def __init__(self, stream):
        self.stream = StringIO(stream)
        self.stream.seek(0, SEEK_END)
        self.length = self.stream.tell()
        self.stream.seek(0)
    
    @property
    def remaining(self):
        return self.length-self.cursor
        
    @property
    def cursor(self):
        return self.stream.tell()
        
    def get_bytes(self, number, byte_code=False):
        bytes = self.stream.read(number)
        if byte_code: return bytes,bytes
        else: return bytes
        
    def get_little_bytes(self, number, byte_code=False):
        bytes = [self.stream.read(1) for i in range(0,number)]
        little = ''.join(reversed(bytes))
        if byte_code: return little, ''.join(bytes)
        else: return little
        
    def skip(self, number, byte_code=False):
        if byte_code: return self.stream.read(number)
        else: self.stream.read(number)
        
    def peek(self, number, byte_code=False):
        bytes = self.stream.read(number)
        self.stream.seek(-number,SEEK_CUR)
        return bytes
        
    def get_string(self, number, byte_code=False):
        #This would be easier if I knew the encoding of the bytes
        hex, bytes = self.get_hex(number, byte_code=True)
        if byte_code: return hex.decode("hex"),bytes
        else: return hex.decode("hex")
        
    def get_hex(self, number, byte_code=False):
        bytes = self.stream.read(number)
        if byte_code: return bytes.encode("hex"),bytes
        else: return bytes.encode("hex")
        
    def get_big_8(self, byte_code=False):
        byte = self.stream.read(1)
        if byte_code: return unpack('B', byte)[0], byte
        else: return unpack('B', byte)[0]

    def get_big_16(self, byte_code=False):
        bytes = self.stream.read(2)
        if byte_code: return unpack('>H', bytes)[0], bytes
        else: return unpack('>H', bytes)[0]

    def get_big_32(self, byte_code=False):
        bytes = self.stream.read(4)
        if byte_code: return unpack('>I', bytes)[0], bytes
        else: return unpack('>I', bytes)[0]

    def get_big_64(self, byte_code=False):
        bytes = self.stream.read(8)
        if byte_code: return unpack('>Q', bytes)[0], bytes
        else: return unpack('>Q', bytes)[0]    

    def get_little_8(self, byte_code=False):
        byte = self.stream.read(1)
        if byte_code: return unpack('B', byte)[0], byte
        else: return unpack('B', byte)[0]

    def get_little_16(self, byte_code=False):
        bytes = self.stream.read(2)
        if byte_code: return unpack('<H', bytes)[0], bytes
        else: return unpack('<H', bytes)[0]

    def get_little_32(self, byte_code=False):
        bytes = self.stream.read(4)
        if byte_code: return unpack('<I', bytes)[0], bytes
        else: return unpack('<I', bytes)[0]

    def get_little_64(self, byte_code=False):
        bytes = self.stream.read(8)
        if byte_code: return unpack('<Q', bytes)[0], bytes
        else: return unpack('<Q', bytes)[0]           
        
    def get_count(self, byte_code=False):
        #For some reason counts are always doubled
        number, bytes = self.get_big_8(byte_code=True)
        if byte_code: return number/2,bytes
        else: return number/2
        
    def get_timestamp(self, byte_code=False):
        #Get the first byte
        byte, byte_string = self.get_big_8(byte_code=True)
        
        #The 7-8 bits of the byte indicate the byte length of the
        #timestamp, shift them off the time and loop through them
        time = byte >> 2
        for i in range(0,byte & 0x03):
            more, byte = self.get_big_8(byte_code=True)
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
            num, byte = self.get_big_8(byte_code=True)
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
        datatype, type_code = self.get_big_8(byte_code=True)
        
        if datatype == 0x02:
            #0x02 is a byte string with the first byte indicating the length of
            #the byte string to follow
            length, byte = self.get_count(byte_code=True)
            data, bytes = self.get_hex(length, byte_code=True)
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
            data, bytes = self.get_big_8(byte_code=True)
            
        elif datatype == 0x07:
            data, bytes = self.get_big_32(byte_code=True)
            
        elif datatype == 0x09:
            data, bytes = self.get_vlf(byte_code=True)
            
        else:
            raise TypeError("Uknown Data Type: '%s'" % datatype)
        
        if byte_code:
            return data, type_code+bytes
        return data  
        
        
        
'''
class ByteStream(object):
    """Track and return the bytes for investigative and debugging purposes"""
    """Most functions will return the byte_code as well when requested"""
    
    def __init__(self, stream):
        self.__cbyte = 0
        self.cursor = -1 #First element is 0
        self.stream = StringIO(stream)
        
    def get_big(self, number, byte_code=False):
        result = self.stream.read(number)
        if byte_code:
            return result, result
        return result
        
    def skip(self, number, byte_code=False):
        #This is just an alias for get_big, return the byte_string if asked
        #so that it can be recorded for event analysis
        if byte_code:
            return self.get_big(number)
        self.get_big(number)
        
    def peek(self, number):
        ret = self.stream.read(number)
        self.stream.seek(-number,SEEK_CUR)
        return ret
        
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
            #This would be easier if I knew what the original encoding was
            return string.endcode("hex").decode("hex"), bytes
        return string.encode("hex").decode("hex")
        
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
'''