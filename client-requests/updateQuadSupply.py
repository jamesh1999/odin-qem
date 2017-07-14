#!~/develop/projects/odin/venv/bin/python

''' Demonstrate how temperature sensor data type is either int/bool for dictionary key 'disabled' '''

from pscu_access import PSCUAccess
thePSCU = PSCUAccess()

# Within quad, what does the 'supply' key within each do?
# I.e.:
##>>> pp.pprint(d['quad']['quads'])
##{ u'0': { u'channels': { u'0': { u'current': 0.11721611721611722,
##                                 u'enable': False,
##                                 u'feedback': False,
##                                 u'fusevoltage': 0,
##                                 u'voltage': 1.1135531135531136},
##                         u'1': { u'current': 0.0,
##                                 ...,
##          u'supply': 0},                                    <--  This key !
##  u'1': { u'channels': { u'0': { u'current': 20.0,
##                                 ...,
##          u'supply': 0},                                    <--  etc..
##  u'2': { u'channels': { u'0': { u'current': 20.0,

# NOTE: Like Quad's 'enable', if it's changed once then the int type value, becomes a key,value pair
# i.e.
#        u'supply': 0,
# Becomes
#        u'supply': {u'supply': 1}},

def toggleQuadSupply(quad):
    
    quadPath = 'quad/quads/{}/supply'.format(quad)
    # It can be changed:
    currentValue = thePSCU.getKey(thePSCU.url + quadPath, 'supply')
    
    print "Quad{}'s 'supply' is of ".format(quad), type(currentValue)

    # Extract value, first if it's a simply integer value:
    try:
        currentValue = int(currentValue['supply'])
    except TypeError:
        # Not integer, let's try key,value pair
        currentValue = int(currentValue) # Extract value from key and convert Unicode into int..

    print "Quad{}'s 'supply' value: ".format(quad), currentValue

    # Let's invert the current value
    newValue = (1 if currentValue == 0 else 0)
    print "Let's change {} to {}".format(currentValue, newValue)
    thePSCU.setKey(thePSCU.url + quadPath, 'supply', newValue)

    # Confirm key updated
    modifiedValue = thePSCU.getKey(thePSCU.url + quadPath, 'supply')
    print "Updated value: {}".format(modifiedValue['supply'])

if __name__ == "__main__":
    quad = 3
    toggleQuadSupply(quad)
