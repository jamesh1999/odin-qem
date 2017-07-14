#!~/develop/projects/odin/venv/bin/python

#Trying to enable a channel in a Quad... but key value becomes nestled dictionary like this:
# I.e.
#         u'enable': False,
# becomes:
#         u'enable': { u'enable': True},

import requests, json
import pprint

def tryUpdateQuadEnable(quad, channel, bEnable):
    url = 'http://beagle03.aeg.lan:8888/api/0.1/lpdpower/'
    headers  = {'Content-Type' : 'application/json'}

    response = requests.get(url)
    dQuads   = response.json()
    quads    = dQuads['quad']['quads']

    print "Quad {}, channel {} enable value before we start:".format(quad, channel)

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(quads[str(quad)]['channels'][str(channel)])

    payload = {"enable": bEnable}

    path = 'quad/quads/{}/channels/{}/enable'.format(quad, channel)
    print "Path to target enable key: {}".format(path)

    rep = requests.put( url + path, data=json.dumps(payload), headers=headers)

    if rep.status_code != 200:
        print "error:  {} Couldn't change quad{}'s channel {}".format(rep.status_code, quad, channel)
    else:
        print "Success (Code:{})  changed quad{}'s channel {}".format(rep.status_code, quad, channel)

    # Check whether change worked.. #;
    rp = requests.get( url + path)
    if rp.status_code != 200:
        print "error:  {} Couldn't confirm quad channel set".format(rp.status_code)

    print "Quad {}, channel {} enable modified value".format(quad, channel)

    response = requests.get(url)
    dQuads   = response.json()
    quads    = dQuads['quad']['quads']

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(quads[str(quad)]['channels'][str(channel)])


if __name__ == "__main__":
    (quad, channel) = (0, 0)
    bEnable = False #True
    tryUpdateQuadEnable(quad, channel, bEnable)
