#!~/develop/projects/odin/venv/bin/python

import requests, sys, time

print "Continuously reading all temperatures: (Use Ctrl-C to close script)"
try:
    while True:
        theLot = requests.get('http://beagle03.aeg.lan:8888/api/0.1/lpdpower/')
        # Read all 11 temperatures, display on the same line
        for index in range(11):
            print "{}: {:.1f}C  ".format(index, theLot.json()['temperature']['sensors'][str(index)]['temperature']),
        # Flush stream; add "heartbeat" before reading temps to same line
        sys.stdout.flush()
        time.sleep(0.8)
        print "\r.",
        sys.stdout.flush()
        time.sleep(0.2)
        print "\r",
except KeyboardInterrupt:
    print "\n"
print "\nAll Done"
