#!~/develop/projects/odin/venv/bin/python

''' Display all device information in as similar a fashion as the webpage, as possible '''

from pscu_access import PSCUAccess
thePSCU = PSCUAccess()

if __name__ == "__main__":

    thePSCU = PSCUAccess()

    print "________________________________________________________________"
    print "Replicating \"Overall Health\", i.e. left-hand side of the webpage"

    print "Overall Health: {}".format(thePSCU.getOverall())
    print "Trace Status:   {}, Latched: {}".format(thePSCU.getKey(thePSCU.url+'trace/overall', 'overall'),
                                                thePSCU.getKey(thePSCU.url+'trace/latched', 'latched'))
    print "key enableall:  {}".format(thePSCU.getEnableall())
    print "key isarmed:    {}".format(thePSCU.getIsarmed())

    print "________________________________________________________________"
    

    # Quads
    quads = thePSCU.getKey(thePSCU.url + 'quad/quads', 'quads')
    channels = quads['0']['channels']
    print "Quads:"
    for quad in range(len( quads)):
        print "------"
        print "Quad {}".format(quad)
        
        for channel in range(len( channels)):
            quads[str(quad)]['channels'][str(channel)]
            chCurrent     = quads[str(quad)]['channels'][str(channel)]['current']
            chEnable      = quads[str(quad)]['channels'][str(channel)]['enable']
            chFeedback    = quads[str(quad)]['channels'][str(channel)]['feedback']
            chFuseVoltage = quads[str(quad)]['channels'][str(channel)]['fusevoltage']
            chVoltage     = quads[str(quad)]['channels'][str(channel)]['voltage']
            print "Channel{}:  ".format(channel),
            print "{0:.3f}A  ".format(chCurrent),
            print "Enable: {}  Fdbck: {}  Fuse: {}  ".format(chEnable,chFeedback, chFuseVoltage),
            print "Volt: {0:.3}V".format(chVoltage)

    print "________________________________________________________________"


    # Temperature:

    dTemperature = thePSCU.getKey(thePSCU.url + 'temperature', 'temperature')
    channels = len(dTemperature['sensors'])
    print "Temperature:"
    print "Status: {}  Latched: {}  ".format(dTemperature['overall'], dTemperature['latched'])
    for channel in range(channels):
        chInfo        = dTemperature['sensors'][str(channel)]
        print "Temp{0:>2}:  ".format(channel),
        print "{0:>6.1f}C  Setpoint {1:>6.1f}C  ".format(chInfo['temperature'], chInfo['setpoint']),
        print "Trace: {}  Enable: {}  Tripped: {} ".format(chInfo['trace'], (True if chInfo['disabled'] == 0 else False),
                                                           chInfo['tripped'])
    print "________________________________________________________________"

    # Humidity
    
    dHumidity = thePSCU.getKey( thePSCU.url + 'humidity', 'humidity')

    print "Humidity:"
    print "Status: {}  Latched: {}  ".format(dHumidity['overall'], dHumidity['latched'])
    channels = len(dHumidity['sensors'])
    for channel in range(channels):
        chInfo        = dHumidity['sensors'][str(channel)]
        print "Humidity{0:>2}:  ".format(channel),
        print "{0:>6.1f}%  Setpoint {1:>6.1f}%  ".format(chInfo['humidity'], chInfo['setpoint']),
        print "Trace: {}  Enable: {}  Tripped: {} ".format(chInfo['trace'], (True if chInfo['disabled'] == 0 else False),
                                                           chInfo['tripped'])
    print "________________________________________________________________"

    # Pump
    print "Pump info:"

    chPump = thePSCU.getKey(thePSCU.url, 'pump')
    print "Pump1 Status: {}  Latched: {}  ".format(chPump['overall'], chPump['latched'])
    print "{0:>2.1f}l/min  Setpoint {1:>2.1f}l/min  ".format(chPump['flow'], chPump['setpoint']),
    print "Tripped: {} ".format(chPump['tripped'])
    
    print "________________________________________________________________"
    
    
    # Fan
    print "Fan info:"

    chFan = thePSCU.getKey(thePSCU.url + 'fan', 'fan')
    print "Fan1 Status: {}  Latched: {}  ".format(chFan['overall'], chFan['latched'])
    print "{0:>2.1f}Hz  Setpoint {1:>2.1f}Hz  ".format(chFan['currentspeed'], chFan['setpoint']),
    print "Potentiometer: {0:>2.1f}%  ".format(chFan['potentiometer']),
    print "Tripped: {}      (target: {})".format(chFan['tripped'], chFan['target'])
    
    print "________________________________________________________________"


    
