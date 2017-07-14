from backplane import Backplane
from odin.adapters.metadata_tree import MetadataTree

class PowerGood(object):
    def __init__(self, backplane, i):
        self.index = i
        self.backplane = backplane

    def get(self):
        return self.backplane.get_power_good(self.index)

class CurrentVoltage(object):
    def __init__(self, backplane, i):
        self.index = i
        self.backplane = backplane

        self.param_tree = MetadataTree({
            "name" : (self.backplane.get_adc_name(i), {"writeable" : False}),
            "current" : (self.get_current, {"units" : "mA"}),
            "voltage" : (self.get_voltage, {"units" : "V"})
        })

    def get_current(self):
        return self.backplane.get_current(self.index)

    def get_voltage(self):
        return self.backplane.get_voltage(self.index)

class Resistor(object):
    def __init__(self, backplane, i):
        self.index = i
        self.backplane = backplane
        
        self.param_tree = MetadataTree({
            "name" : (self.backplane.get_resistor_name(i), {"writeable" : False}),
            "value" : (self.get, self.set, {"units" : self.backplane.get_resistor_units(self.index)})
        })

    def get(self):
        return self.backplane.get_resistor_value(self.index)

    def set(self, value):
        self.backplane.set_resistor_value(self.index, value)

class BackplaneData(object):

    def __init__(self):
        self.backplane = Backplane()
        
        self.power_good = []
        for i in range(8):
            self.power_good.append(PowerGood(self.backplane, i))

        self.current_voltage = []
        for i in range(13):
            self.current_voltage.append(CurrentVoltage(self.backplane, i))

        self.resistors = []
        for i in range(7):
            self.resistors.append(Resistor(self.backplane, i))

        self.param_tree = MetadataTree({
            "clock" : (self.backplane.get_clock_frequency, self.backplane.set_clock_frequency, {"units" : "MHz"}),
            "psu_enabled" : (self.backplane.get_psu_enable, self.backplane.set_psu_enable),
            "power_good" : [pg.get for pg in self.power_good],
            "current_voltage" : [cv.param_tree for cv in self.current_voltage],
            "resistors" : [r.param_tree for r in self.resistors]
        })

    def get(self, path, metadata):
        return self.param_tree.get(path, metadata=metadata)

    def set(self, path, value):
        self.param_tree.set(path, value)
