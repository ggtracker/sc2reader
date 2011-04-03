from cStringIO import StringIO
from os import SEEK_CUR, SEEK_END, SEEK_SET

LITTLE_ENDIAN,BIG_ENDIAN = '<','>'

class ReplayBuffer(object):
    """ The ReplayBuffer is a wrapper over the cStringIO object and provides
        convenience functions for reading structured data from Stacraft II
        replay files. These convenience functions can be sorted into several
        different categories providing an interface as follows:
        
        Stream Manipulation::
            tell(self)
            skip(self, amount)
            reset(self)
            align(self)
            seek(self, position, mode=SEEK_CUR)
            
        Data Retrival::
            read_variable_int(self)
            read_string(self,additional)
            read_timestamp(self)
            read_count(self)
            read_data_structure(self)
            read_object_type(self, read_modifier=False)
            read_object_id(self)
            read_coordinate(self)
            read_bitmask(self)
        
        Basic Reading::
            read_byte(self)
            read_int(self)
            read_short(self)
            read_chars(self,length)
            
            shift(self,bits)
            read(bytes,bits)
            
        The ReplayBuffer additionally defines the following properties:
            left
            length
            cursor
    """
    
    def __init__(self, file):
        self.io = StringIO(file)

        # get length of stream
        self.io.seek(0, os.SEEK_END)
        self.length = self.io.tell()
        self.io.seek(0)

        # setup shift defaults
        self.bit_shift = 0
        self.last_byte = None

    '''
        Additional Properties
    '''
    @property
    def left(self): return self.length - self.cursor
    
    @property
    def cursor(self): return self.tell()
    
    '''
        Stream manipulation functions
    '''
    def tell(self): return self.io.tell()
    def skip(self, amount): self.seek(amount, SEEK_CUR)
    def reset(self): self.io.seek(0); self.bit_shift = 0
    def align(self): self.shift(8-self.bit_shift) if self.bit_shift else 0
    def seek(self, position, mode=SEEK_SET):
        self.io.seek(position, mode)
        if self.io.tell() and self.bit_shift:
            self.io.seek(-1, SEEK_CUR)
            self.shift(self,self.bit_shift)



    '''
        Read "basic" structures
    '''
    def read_byte(self):
        """ Basic byte read """
        return self.read(1)[0]

    def read_int(self, endian=LITTLE_ENDIAN):
        """ int32 read """
        return struct.unpack(endian+'I', self.read_chars(4))[0]
        
    def read_short(self, endian=LITTLE_ENDIAN):
        """ short16 read """
        return struct.unpack(endian+'H', self.read_chars(2))[0]
        
    def read_chars(self, length=0):
        return ''.join(chr(byte) for byte in self.read(length))
        
    '''
        Read replay-specific structures
    '''
    def read_count(self):
        return self.read_byte()/2
    
    def read_variable_int(self):
        """ Blizzard VL integer """
        byte = self.read_byte()
        shift, value = 1,byte & 0x7F
        while byte & 0x80 != 0:
            byte = self.read_byte()
            value = ((byte & 0x7F) << shift * 7) | value
            shift += 1
                
        #The last bit of the result is a sign flag
        return pow(-1, result & 0x1) * (result >> 1)

    def read_string(self, additional=0):
        """<length> ( <char>, .. ) as unicode"""
        return self.read_chars(self.read_byte() + additional).decode('utf-8')

    def read_timestamp(self):
        """
        Timestamps are 1-4 bytes long and represent a number of frames. Usually
        it is time elapsed since the last event. A frame is 1/16th of a second. 
        The least significant 2 bits of the first byte specify how many extra 
        bytes the timestamp has.
        """
        first = self.read_byte()
        time,count = first >> 2, first & 0x03
        for i in range(count):
            time = (time << 8) | self.read_byte()
        return time

    def read_data_struct(self):
        """
        Read a Blizzard data-structure. Structure can contain strings, lists,
        dictionaries and custom integer types.
        """
        #The first byte serves as a flag for the type of data to follow
        datatype = self.read_byte()
        if datatype == 0x02:
            #0x02 is a byte string with the first byte indicating
            #the length of the byte string to follow
            return self.read_string(self.get_count())
            
        elif datatype == 0x04:
            #0x04 is an serialized data list with first two bytes always 01 00
            #and the next byte indicating the number of elements in the list
            #each element is a serialized data structure
            self.skip(2)    #01 00
            return [self.read_data_struct() for i in range(self.read_count())]
            
        elif datatype == 0x05:
            #0x05 is a serialized key,value structure with the first byte
            #indicating the number of key,value pairs to follow
            #When looping through the pairs, the first byte is the key,
            #followed by the serialized data object value
            data = dict()
            for i in range(self.read_count()):
                key,value = self.read_count(), self.read_data_struct()
                data[key] = value #Done like this to keep correct parse order
            return data
            
        elif datatype == 0x06:
            return self.read_byte()/2
        elif datatype == 0x07:
            return self.read_int()/2
        elif datatype == 0x09:
            return self.read_variable_int()/2
            
        raise TypeError("Uknown Data Structure: '%s'" % datatype)
        
    def read_object_type(self, read_modifier=False):
        """ Object type is big-endian short16 """
        type = self.read_short(endian=BIG_ENDIAN)
        if read_modifier:
            type = (type << 8) | self.read_byte()
        return type

    def read_object_id(self):
        """ Object ID is big-endian int32 """
        return self.read_int(endian=BIG_ENDIAN)

    def read_coordinate(self):
        coord = self.read(bits=20)
        return [coord[0], coord[1] << 4 | coord[2],]

    def read_bitmask(self):
        """ Reads a bitmask given the current bitoffset """
        length = self.read_byte()
        bytes = reversed(self.read(bits=length))
        mask = 0
        for byte in bytes:
            mask = (mask << 8) | byte

        # Turn things like 10010011 into [True, False, False, True,...]
        def _make_mask(byte, bit_length, current=1):
            if current < bit_length:
                byte_mask = (2**(bit_length-current))
                bytes = [(byte & byte_mask) > 0,] 
                return bytes + _make_mask(byte, bit_length, current+1)
            else:
                return [byte & 0x1 == 0x01,]

        return list(reversed(_make_mask(mask, length)))

    '''
        Base read functions
    '''
    def shift(self, bits):
        """
        The only valid use of Buffer.shift is when you know that there are
        enough bits left in the loaded byte to accomodate your request.
        
        If there is no loaded byte, or the loaded byte has been exhausted,
        then Buffer.shift(8) could technically be used to read a single
        byte-aligned byte.
        """   
        if bits == 0:
            return 0
        
        elif bits <= (8-self.bit_shift):
            #Grab a new byte if the currently loaded one is exhausted
            if self.bit_shift == 0:
                self.last_byte = ord(self.io.read(1))
            
            #Get the requested bits from the byte, and adjust state
            ret = (self.last_byte >> self.bit_shift) & (2**bits-1)
            self.bit_shift = (self.bit_shift + bits) % 8
            return ret
        
        else:
            msg = "Cannot shift off %s bits. Only %s bits remaining."
            raise ValueError(msg % (bits, 8-self.bit_shift))
    
    def read(self, bytes=0, bits=0):
        bytes, bits = bytes+bits/8, bits%8,  
        bit_count = bytes*8+bits
        
        #check special case of not having to do any work
        if bit_count == 0: return []
        
        #check sepcial case of intra-byte read
        if bit_count <= (8-self.bit_shift):
            return [self.shift(bit_count)]
        
        #check special case of byte-aligned reads, performance booster
        if self.bit_shift == 0:
            base = [ord(self.io.read(1)) for byte in range(bytes)]
            if bits != 0:
                return base+[ord(self.shift(bits))]
            return base
        
        # Calculated shifts
        old_bit_shift = self.bit_shift 
        new_bit_shift = (self.bit_shift+bits) % 8
        
        # Masks
        lo_mask = 2**old_bit_shift-1
        lo_mask_inv = 0xFF - 2**(8-old_bit_shift)+1
        hi_mask = 0xFF ^ lo_mask
        hi_mask_inv = 0xFF ^ lo_mask_inv
        
        #last byte parameters
        if new_bit_shift == 0: #this means we filled the last byte (8)
            last_mask = 0xFF
            adjustment = 8-old_bit_shift
        else:
            last_mask = 2**new_bit_shift-1
            adjustment = new_bit_shift-old_bit_shift
        
        #Set up for the looping with a list, the bytes, and an initial part
        raw_bytes = list()
        prev, next = self.last_byte, ord(self.io.read(1))
        first = prev & hi_mask
        bit_count -= 8-old_bit_shift
        
        while bit_count > 0:
        
            if bit_count <= 8: #this is the last byte
                #The bits in the last byte are included in order starting at
                #the new_bit_shift boundary with extra bits bumped back a byte
                #because we can have odd bit requests, the bit shift can change
                last = (next & last_mask)

                # we need to bring the first byte closer
                # if the adjustment is lower than 0
                if adjustment < 0:
                    first = first >> abs(adjustment)
                
                raw_bytes.append(first | (last >> max(adjustment,0)))
                if adjustment > 0:
                    raw_bytes.append(last & (2**adjustment-1))
                    
                bit_count = 0
                
            if bit_count > 8: #We can do simple wrapping for middle bytes
                second = (next & lo_mask_inv) >> (8-old_bit_shift)
                raw_bytes.append(first | second)
                
                #To remain consistent, always shfit these bits into the hi_mask
                first = (next & hi_mask_inv) << old_bit_shift
                bit_count -= 8
                
                #Cycle down to the next byte
                prev,next = next,ord(self.io.read(1))
        
        #Make sure to set our internals back together
        self.last_byte = next
        self.bit_shift = new_bit_shift
        
        return raw_bytes
