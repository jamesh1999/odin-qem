import argparse
import requests
import json
import time

pscu_addr = 'pscu'
pscu_port = 8888
arm_path = 'armed'
enable_path = 'allEnabled'

def pscu_control(args):
    
    base_url = 'http://{addr:s}:{port:d}/api/0.1/lpdpower/'.format(addr=args.addr, port=args.port)

    if args.arm or args.disarm:
        set_pscu_path(base_url, arm_path, args.arm)
        
    if args.enable or args.disable:
        set_pscu_path(base_url, enable_path, args.enable)    

def set_pscu_path(base_url, path, target_state):
          
    url = base_url + path
    response = requests.get(url)
    
    if response.status_code != 200:
        print('Requesting PSCU {} state failed with status_code {} : {}'.format(
                    path, response.status_code, response.json()
            ))
        return

    print response.json()
    
    current_state = response.json()[path]
    print('Current {} state is {}'.format(path, current_state))
    
    if target_state != current_state:
        print('Setting {} state to {}'.format(path, target_state))
        
        payload = {path: target_state}
        headers = {'Content-Type': 'application/json'}
        
        response = requests.put(base_url, data=json.dumps(payload), headers=headers)
    
        if response.status_code != 200:
            print('Setting {} state to {} failed with status code {} : {}'.format(
                path, target_state, response.status_code, response.json()
                ))
            return
        
        time.sleep(0.5)
        response = requests.get(url)
        print 'PSCU {} state is now {}'.format(path, response.json()[path])
        
    return
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='pscu_control.py - control ARM and enable state of LPD PSCU')
    
    parser.add_argument('--addr', help='PSCU host address', type=str, default=pscu_addr)
    parser.add_argument('--port', help='PSCU host address', type=int, default=pscu_port)
    
    arm_group = parser.add_mutually_exclusive_group()
    arm_group.add_argument('--arm', help='Arm the PSCU', action='store_true')
    arm_group.add_argument('--disarm', help='Disarm the PSCU', action='store_true')
    
    enable_group = parser.add_mutually_exclusive_group()
    enable_group.add_argument('--enable', help='Arm the PSCU', action='store_true')
    enable_group.add_argument('--disable', help='Disarm the PSCU', action='store_true')
    
    args = parser.parse_args()
    print(args)
    
    pscu_control(args)