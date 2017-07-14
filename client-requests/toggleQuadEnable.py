import sys, requests, json, pprint

def toggleQuadEnable(quad, channel):
    
    base_url = 'http://beagle03.aeg.lan:8888/api/0.1/lpdpower/'
    
    path = 'quad/quads/{}/channels/{}'.format(quad, channel)
    url = base_url + path    
    headers  = {'Content-Type' : 'application/json'}

    pp = pprint.PrettyPrinter()
    
    # Get the appropriate quad channel status
    response = requests.get(url)
    chan_status   = response.json()[str(channel)]
    print "Quad {} channel {} status before toggling enable:".format(quad, channel)
    pp.pprint(chan_status)
    chan_enable = chan_status['enable']
    
    # Toggle the enable state
    payload = {"enable": not chan_enable}
    rep = requests.put(url, data=json.dumps(payload), headers=headers)
  
    if rep.status_code != 200:
        print "error:  {} Couldn't change quad {} channel {}".format(rep.status_code, quad, channel)
    else:
        print "Success (Code:{}) changed quad {} channel {}".format(rep.status_code, quad, channel)
  
    # Get the status again
    response = requests.get(url)
    chan_status = response.json()[str(channel)]

    print "Quad {} channel {} status after toggling enable:".format(quad, channel)    
    pp.pprint(chan_status)

if __name__ == "__main__":
    
    quad = 0
    channel = 0
    
    if len(sys.argv) > 1:
        quad = int(sys.argv[1])
        
    if len(sys.argv) > 2:
        channel = int(sys.argv[2])
        
    toggleQuadEnable(quad, channel)
