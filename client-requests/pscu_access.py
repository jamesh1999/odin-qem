import requests, sys, time, json, pprint

class PSCUAccess(object):
    ''' Provide access to PSCU's i2c devices '''
    def __init__(self, bDebugMsgs=False):
        self.bDebug = bDebugMsgs
        self.url = 'http://beagle03.aeg.lan:8888/api/0.1/lpdpower/'
	self.response = requests.get(self.url)
        self.dict     = self.response.json()
        # Headers don't change
        self.headers = {'Content-Type' : 'application/json'}

    ''' Establish access methods for first level keys that do not
            containing nestled dictionary '''
    
    def getArm(self):
        self.dict     = requests.get(self.url).json()
        return self.dict['arm']

    def getIsarmed(self):
        self.dict     = requests.get(self.url).json()
        return self.dict['isarmed']

    def getEnableall(self):
        self.dict     = requests.get(self.url).json()
        return self.dict['enableall']

    def getOverall(self):
        self.dict     = requests.get(self.url).json()
        return self.dict['overall']

    def setArm(self, bToggle):
        payload = {"arm": bToggle}
        rep = requests.put(self.url, data=json.dumps(payload), headers=self.headers)
        if rep.status_code != 200:
            print "Error: %d Couldn't updated key 'arm'!" % rep.status_code

     
    def setQuadChannel(self, quad, channel, bEnable):
        ''' Set 'enable' key value to True/False in a specific Quad's Channel '''
        payload = {"enable": bEnable}
        path = 'quad/quads/{}/channels/{}/enable'.format(quad, channel)
        if self.bDebug:
            rp = requests.get( self.url + path)
            print "DEBUG, before: {} receiving: {}".format(rp.status_code, rp.text)

        rep = requests.put( self.url + path, data=json.dumps(payload), headers=self.headers)
        if rep.status_code != 200:
            print "error:  {} Couldn't change quad{}'s channel {}".format(rep.status_code, quad, channel)
        else:
            if self.bDebug:
                print "Success {}  changed quad{}'s channel {}".format(rep.status_code, quad, channel)

    def getKey(self, path, aKey):
        rp = requests.get(path)
        if rp.status_code != 200:
            print "Error {}: getKey() failed on key '{}'".format(rp.status_code, aKey)
        return rp.json()[aKey]

    def setKey(self, path, aKey, aValue):
        payload = {aKey: aValue}

        if self.bDebug:
            rp = requests.get(path)
            print "Before modification: (Code: {}) received: \n\t'{}'".format(rp.status_code, rp.text[:100])

        rep = requests.put(path, data=json.dumps(payload), headers=self.headers)
        if rep.status_code != 200:
            print "error {}: Couldn't change key: '{}' to be '{}' in path: '{}'".format(rep.status_code, aKey, aValue, path)
        else:
            if self.bDebug:
                print "Successfully changed key: '{}' to: '{}' ".format(aKey, aValue)

    def testFanSpeeds(self):
        # Manually set target speed at 40%
        print "Changing fan speed to 40%; Monitor speed decrease for 5 seconds.."
        fanPath = 'http://beagle03.aeg.lan:8888/api/0.1/lpdpower/fan'
        thePSCU.setKey(fanPath, 'target', 40)
        for index in range(5):
            dFan = thePSCU.getKey(fanPath, 'fan')
            print "\rCurrent Speed is:   {0:2.1f}Hz (Target: {1}%)".format(dFan['currentspeed'], dFan['target']),
            sys.stdout.flush()
            time.sleep(1)

        # Manually set target speed at 80%
        print "\nChanging fan speed to 80%; Watch speed increase for 5 seconds.."
        thePSCU.setKey(fanPath, 'target', 80)
        for index in range(5):
            dFan = thePSCU.getKey(fanPath, 'fan')
            print "\rCurrent Speed is:   {0:2.1f}Hz (Target: {1}%)".format(dFan['currentspeed'], dFan['target']),
            sys.stdout.flush()
            time.sleep(1)
        print ""


if __name__ == "__main__":

    thePSCU = PSCUAccess()

    # Toggle arm - Switch off if armed, Switch on if not
    bArmStatus = thePSCU.getArm()
    print "Arm is set to: {}, while the system is: {}".format(bArmStatus, ("Armed" if thePSCU.getIsarmed() == True else "Not Armed"))
    bToggle = (True if bArmStatus == False else False)

    # Toggle arm, pause before checking 'arm'
    thePSCU.setArm(bToggle)    
    time.sleep(0.2)
    bArmStatus = thePSCU.getArm()
    print "Setting arm to: {}, Now system is: {}".format(bArmStatus, ("Armed" if thePSCU.getIsarmed() == True else "Not Armed"))

    # Enable/Disabled a quad channel:
    (bEnable, quad, channel) = (True, 0, 1)
    print "Quad {}, channel {} after change:".format(quad, channel)
    print "[key 'enable' type changes..]"
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(requests.get('http://beagle03.aeg.lan:8888/api/0.1/lpdpower/quad/quads/0/channels/3').json())
    
    thePSCU.setQuadChannel(quad, channel, bEnable)
    print "Quad {}, channel {} after change:".format(quad, channel)
    pp.pprint(requests.get('http://beagle03.aeg.lan:8888/api/0.1/lpdpower/quad/quads/0/channels/3').json())

    
    # Test that we can change the fan speed
    thePSCU.testFanSpeeds()
