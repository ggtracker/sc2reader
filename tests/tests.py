from __future__ import absolute_import
import unittest
import sc2reader


class ColorTests(unittest.TestCase):
	def test_color(self):
		color = sc2reader.utils.Color(r=0x00, g=0x42, b=0xFF, a=75)
		self.assertEqual(color.rgba, (0x00,0x42,0xFF,75))
		self.assertEqual(color.hex, "0042FF")

class PersonDictTests(unittest.TestCase):

	def test_brackets(self):
		lookup = sc2reader.utils.PersonDict()
		lookup[1] = sc2reader.objects.Player(1, "player1")
		lookup[2] = sc2reader.objects.Player(2, "player2")
		self.assertEquals(lookup[1].name, "player1")
		self.assertEquals(lookup["player2"].pid, 2)

	def test_list_constructor(self):
		lookup = sc2reader.utils.PersonDict([
			sc2reader.objects.Player(1, "player1"),
			sc2reader.objects.Player(2, "player2")
		])

		self.assertEquals(lookup[1].name, "player1")
		self.assertEquals(lookup["player2"].pid, 2)

	def test_deletes(self):
		lookup = sc2reader.utils.PersonDict()
		lookup[1] = sc2reader.objects.Player(1, "player1")
		lookup[2] = sc2reader.objects.Player(2, "player2")
		with self.assertRaises(KeyError) as cm:
			del lookup[2]
			lookup[2].name
		self.assertEquals(cm.exception.message, 2)

class ReplayBufferTests(unittest.TestCase):
	"""All methods should throw EOFError when they hit the end of the
	wrapped buffer."""

	def test_empty(self):
		buffer = sc2reader.utils.ReplayBuffer("T35T")
		self.assertEquals(buffer.empty, False)
		buffer.read(4)
		self.assertEquals(buffer.empty, True)

	def test_seek(self):
		"""Should preserve the bitshift unless seeking back to beginning of
		the file. Seeking to position 0 leaves no bits behind to shift.

		The bits we are testing on
				01010100
				00110011
				00110101
				01010100
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35T")

		# Initial offset
		buffer.shift(8)
		buffer.shift(6)

		# Assertions
		self.assertEquals(buffer.bit_shift, 6)
		buffer.seek(1)
		self.assertEquals(buffer.bit_shift, 6)
		buffer.seek(0)
		self.assertEquals(buffer.bit_shift, 0)

	def test_shift(self):
		""" The bits we are testing on
				01010100
				00110011
				00110101
				01010100
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35T")

		self.assertEquals(buffer.shift(8), 0x54) # Whole byte reads are valid
		self.assertEquals(buffer.shift(3), 0x03) # Start reading from the right
		self.assertEquals(buffer.shift(4), 0x06) # Account for previous shift

		# But don't let them overshift a byte.
		with self.assertRaises(ValueError) as cm:
			buffer.shift(3)
		self.assertEquals(cm.exception.message, "Cannot shift off 3 bits. Only 1 bits remaining.")

		buffer.shift(1)
		buffer.shift(8)
		buffer.shift(8)

		# Also don't let them shift off the end of the buffer
		with self.assertRaises(EOFError) as cm:
			buffer.shift(8)
		self.assertEquals(cm.exception.message, "Cannot shift requested bits. End of buffer reached")

	def test_read(self):
		"""The bits we are testing on
				010 10100
				00110 011
				001 10101
				01010 100
				01 000 010
				010101 01
				010001 10
				0100 0110
				00110011
				01010010
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35TBUFF3R")

		# Simple shift
		self.assertEquals(buffer.read(bits=5), [0x14])
		# Byte overflow shift
		self.assertEquals(buffer.read(bits=6), [0x13])
		# Multi-byte unchanged bit_shift
		self.assertEquals(buffer.read(bytes=2), [0x31,0xAC])
		# Multi-byte increased bit_shift
		self.assertEquals(buffer.read(bytes=1, bits=3), [0x50, 0x02])
		# Mutli-byte decreased bit_shift
		self.assertEquals(buffer.read(bits=22), [0x55, 0x51, 0x26])

		# Run out of bytes, but don't leave the buffer dirty!
		initial_tell, initial_shift = buffer.tell(), buffer.bit_shift
		with self.assertRaises(EOFError) as cm:
			buffer.read(bytes=4)
		self.assertEquals(cm.exception.message, "Cannot read requested bits/bytes. only 2 bytes left in buffer.")
		self.assertEquals(initial_tell, buffer.tell())
		self.assertEquals(initial_shift, buffer.bit_shift)

	def test_read_byte(self):
		"""The bits we are testing on
				01010100
				00110011
				00110101
				01010100
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35T")
		self.assertEquals(buffer.read_byte(), 0x54)
		self.assertEquals(buffer.bit_shift, 0)
		buffer.shift(3) # Test Shifted
		self.assertEquals(buffer.read_byte(), 0x35)
		self.assertEquals(buffer.bit_shift, 3)
		with self.assertRaises(EOFError) as cm:
			buffer.read_byte()
			buffer.read_byte()
		self.assertEquals(cm.exception.message, "Cannot read byte; no bytes remaining")

	def test_read_short(self):
		"""The bits we are testing on
				01010100
				00110011
				00110 101
				010 10100
				01000 010
				01010101
				01000110
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35TBUF")
		self.assertEquals(buffer.read_short(), 0x3354)
		self.assertEquals(buffer.bit_shift, 0)
		buffer.shift(3) # Test Shifted
		self.assertEquals(buffer.read_short(), 0xA232)
		self.assertEquals(buffer.bit_shift, 3)
		with self.assertRaises(EOFError) as cm:
			buffer.read_short()
			buffer.read_short()
		self.assertEquals(cm.exception.message, "Cannot read short; only 0 bytes left in buffer")

	def test_read_int(self):
		"""The bits we are testing on
				01010100
				00110011
				00110101
				01010100
				01000 010
				010 10101
				010 00110
				010 00110
				00110 011
				01010010
		"""
		buffer = sc2reader.utils.ReplayBuffer("T35TBUFF3R")
		self.assertEquals(buffer.read_int(), 0x54353354)
		self.assertEquals(buffer.bit_shift, 0)
		buffer.shift(3) # Test shfited
		self.assertEquals(buffer.read_int(), 0x3332AA42)
		self.assertEquals(buffer.bit_shift, 3)
		with self.assertRaises(EOFError) as cm:
			buffer.read_int()
		self.assertEquals(cm.exception.message, "Cannot read int; only 1 bytes left in buffer")

	def test_read_range(self):
		buffer = sc2reader.utils.ReplayBuffer("T35TBUFF3R")
		self.assertEquals(buffer.read_range(2,6), "5TBU")
		self.assertEquals(buffer.tell(), 0)

	def test_read_bitmask(self):
		"""The bits we are testing on
				00001 010
				01010 111
				001 10011
				001101 01
		"""
		buffer = sc2reader.utils.ReplayBuffer("\nW35T")
		buffer.shift(3) #Shift to give us a managable size

		# Length = 00010101 = 15
		# Bytes Reversed = 1001101 01010001
		# Mask = 0x4E51
		# Bits Reversed = 100010101011001
		self.assertEquals(buffer.read_bitmask(), [
			True, False, False, False, True, False, True,
			False, True, False, True, True, False, False, True])
		self.assertEquals(buffer.bit_shift, 2)

	def test_read_variable_int(self):
		"""The bits we are testing on
				10101001
				00010111
				01111110
		"""
		buffer = sc2reader.utils.ReplayBuffer(chr(0xA9)+chr(0x17)+chr(0x7E))
		self.assertEquals(buffer.read_variable_int(), -0x5D4)
		self.assertEquals(buffer.read_variable_int(), 0x3F)
		self.assertEquals(buffer.bit_shift, 0)

	def test_read_coordinate(self):
		pass

	def test_read_timestamp(self):
		pass

	def test_read_data_struct(self):
		pass







if __name__ == '__main__':
	unittest.main()