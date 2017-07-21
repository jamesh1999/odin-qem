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
            "name" : self.backplane.get_adc_name(i),
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
            "name" : self.backplane.get_resistor_name(i),
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

        pw_good = {str(i) : pg.get for i,pg in enumerate(self.power_good)}
        pw_good.update({"list" : True, "description" : "Power good inputs from the MCP23008"})

        self.param_tree = MetadataTree({
            "name" : "QEM Backplane",
            "description" : "Testing information for the backplane on QEM.",
            "clock" : (self.backplane.get_clock_frequency, self.backplane.set_clock_frequency, {"units" : "MHz", "description" : "Clock frequency for the SI570 oscillator"}),
            "psu_enabled" : (self.backplane.get_psu_enable, self.backplane.set_psu_enable, {"name" : "PSU Enabled"}),
            "power_good" : pw_good,
            "current_voltage" : [cv.param_tree for cv in self.current_voltage],
            "resistors" : [r.param_tree for r in self.resistors]
        })

    def get(self, path, metadata):
        return self.param_tree.get(path, metadata=metadata)

    def set(self, path, value):
        self.param_tree.set(path, value)
