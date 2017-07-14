'''
Created on Aug 23, 2016

@author: tcn45
'''
import requests, json
import pprint 

url = 'http://pscu:8888/api/0.1/lpdpower/'

pp = pprint.PrettyPrinter()

response = requests.get(url)
pscu_status = response.json()
pp.pprint(pscu_status)
