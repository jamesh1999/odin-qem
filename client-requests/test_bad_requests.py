import requests, json
import pprint 

url = 'http://beagle03.aeg.lan:8888/api/0.1/lpdpower/'

pp = pprint.PrettyPrinter()

garbage_put = 'rubbish_1234'
headers = {"Content-Type" : 'application/json'}

response = requests.put(url, data=garbage_put, headers=headers)
print response.status_code, response.json()

get_bad_path = url + 'missing'
response = requests.get(get_bad_path)
print response.status_code, response.json()
