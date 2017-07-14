import requests, json

def toggleEnableAll():
    
    base_url = 'http://pscu:8888/api/0.1/lpdpower/'
    enable_path = 'allEnabled'
    headers = {'Content-Type': 'application/json'}
    
    url = base_url + enable_path
    response = requests.get(url)
    
    if response.status_code != 200:
        print "Requesting global enable state failed with status_code {} : {}".format(
            response.status_code, response.json()
        )
        return
    
    
    enabled = response.json()[enable_path]
    print "Current quad enableAll state is {}".format(enabled)
    payload = {enable_path: not enabled}

    response = requests.put(base_url, data=json.dumps(payload), headers=headers)
    
    if response.status_code != 200:
        print "Setting global enable state to {} failed with status_code {} : {}".format(
            not enabled, response.status_code, response.json()
        )
        return
    
    print "Quad enableAll state is now {}".format(response.json()[enable_path])
    
if __name__ == '__main__':
    toggleEnableAll()