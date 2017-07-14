"""SI570 - device access class for the SI570 I2C clock

This class adds support for the SI570 clock allowing it to be set to a specific
frequency with the necessary parameters being determined automatically.

James Hogge, STFC Application Engineering Group.
"""

from i2c_device import I2CDevice, I2CException
import math, sys

class SI570(I2CDevice):
	"""SI570 class.

	This class implements support for the SI570 I2C device, allowing the frequency
	of the clock to be controlled.
	"""
	
	SI570_A = 0
	SI570_B = 0
	SI570_C  = 1

	def __init__(self, address=0x55, model=SI570_C, **kwargs):
		"""Initialise the SI570 and determine the crystal frequency.
		This resets the device to the factory programmed frequency.
		"""

		I2CDevice.__init__(self, address, **kwargs)

		#Registers used are dependant on the device model
		self.__register = 13 if model == self.SI570_C else 7

		#Reset device to 156.25MHz and calculate fXTAL
		self.write8(135, 1 << 7)
		while self.readU8(135) & 1:
			continue;

		#Device is reset, read initial register configurations
		data = self.readList(self.__register, 6)
		self.__hs_div, self.__n1, self.__rfreq = self.__calculate_params(data)
		self.__fxtal = (156250000 * self.__hs_div * self.__n1) / self.__rfreq / 1000000

	def get_fxtal(self):
		"""Returns the crystal frequency of the device.

		:returns: Crystal frequency (Megahertz)
		"""
		return self.__fxtal

	def __calculate_params(self, data):
		
		hs_div = ((data[0] >> 5) & 0b111) + 4
                n1 = ((data[0] << 2) & 0b01111100) + ((data[1] >> 6) & 0b11) + 1
                rfreq = data[1] & 0b111111
                for i in range(2, 6):
                        rfreq <<= 8
                        rfreq += data[i]

                rfreq /= float(2**28)

		return (hs_div, n1, rfreq)

	def __str__(self):
		"""Provides a printable representation of the current device configuration

		:returns: String representing device configuration
		"""

		data = self.readList(self.__register, 6)

		ret = ""
		for i in range(len(data)):
			ret += "Register {0:2d}: 0x{1:02X}\n".format(i + self.__register, data[i])

		params = self.__calculate_params(data)
		ret += "HS_DIV:   {:d}\n".format(params[0])
		ret += "N1:       {:d}\n".format(params[1])
		ret += "RFREQ:    {:f}\n".format(params[2])

		ret += "fXTAL:    {:f}MHz\n".format(self.__fxtal)
		ret += "fCURRENT: {:f}MHz".format(self.__fxtal * params[2] / (params[1] * params[0]))

		return ret
		

	def set_frequency(self, freq):
		"""Sets the output frequency of the oscillator.
		
		:param freq: Desired frequency [10 - 945] (Megahertz)
		"""

		if not 10.0 <= freq <= 945.0:
			raise I2CException("The frequency %fMHz is out of the range of this device")

		#Determine divider combination to be used
		#Min/max dividers to use based on possible oscillator frequencies		
		divider_max = int(math.floor(5670.0 / freq))
		divider_min = int(math.ceil(4850.0 / freq))
		found = False


		for divider in range(divider_min, divider_max + 1):
			for hs_div in [11, 9, 7, 6, 5, 4]:
				n1 = int(float(divider) / hs_div)
				
				#If desired divider can be produced from HS_DIV and N1
				if n1 == float(divider) / hs_div and (n1 == 1 or n1 & 1 == 0):
					found = True
					self.__n1 = n1
					self.__hs_div = hs_div
					break;
			if found:
				break;
		else:
			raise I2CException("There is no possible divider combination for %f MHz" % freq)

		#Calculate RFREQ from divider choice
		self.__rfreq = freq * self.__hs_div * self.__n1 / self.__fxtal

		#Freeze the oscillator
		self.write8(137, self.readU8(137) | 0x10)
		
		#Update device with new values
		raw_hs_div = self.__hs_div - 4
		raw_n1 = self.__n1 - 1
		raw_rfreq = int(self.__rfreq * 2**28)
		self.writeList(self.__register,
			map(int,[(raw_hs_div << 5) + (raw_n1 >> 2),
			((raw_n1 & 0b11) << 6) + ((raw_rfreq >> 32) & 0b111111),
			(raw_rfreq >> 24) & 0xff,
			(raw_rfreq >> 16) & 0xff,
			(raw_rfreq >> 8) & 0xff,
			raw_rfreq & 0xff]))

		#Unfreeze the oscillator and set NEWFREQ flag
		self.write8(137, self.readU8(137) & 0xEF)
		self.write8(135, 0x40)


#Basic test for the device. Allows controlling of the output frequency
if __name__ == "__main__":
	si570 = SI570()
	print(si570)
	
	freq = 100
	if len(sys.argv) > 1:
		freq = float(sys.argv[1])
	si570.set_frequency(freq)

	print(si570)
