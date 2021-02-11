""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import yaml
import io
import re
import schedule
import time
from capture import start

# For taking input of the ip address and interfaces
def take_input():
    data = []

    while True:
        same_credentials = input("Do you have the same credentials (SSH) for all switches to be captured? [y/n] ")
        if same_credentials == "y":
            username = input("Username: ")
            password = input("Password: ")
            break
        elif same_credentials == "n":
            print("Please enter the username and password for each switch later on.")
            break
        else:
            print("Please enter a valid answer [y/n].")
            continue

    while True:
        try:
            num_of_switches = int(input("Number of switches to be captured: "))
            break
        except Exception:
            print("Please enter an intger.")
            continue
    for j in range(num_of_switches):
        values = {}

        while True:
            ip = input(f"IP address of switch #{str(j+1)}: ")
            if is_valid_address(ip):
                if not is_repeated_address(ip, data):
                    break
                else:
                    print("This IP address is added already. Please enter another IP address.")
            else:
                print("Please enter a valid IP address.")
                continue
        values['ip'] = ip

        if same_credentials == "y":
            values['username'] = username
            values['password'] = password
        else:
            values['username'] = input(f"Username of switch #{str(j+1)}: ")
            values['password'] = input(f"Password of switch #{str(j+1)}: ")

        while True:
            try:
                num_of_interfaces = int(input(f"Number of interfaces to be captured from switch #{str(j+1)} ({ip}): [input 0 to choose all interfaces] "))
                break
            except Exception:
                print("Please enter an integer.")
                continue
        if num_of_interfaces == 0:
            interfaces = ["all"]
        else:
            interfaces = []
            for i in range(num_of_interfaces):
                while True:
                    interface = input(f"Interface #{str(i+1)} ")
                    if is_valid_interface(interface):
                        if interface not in interfaces:
                            interfaces.append(interface)
                            break
                        else:
                            print("This interface is added already. Please enter another interface.")
                            continue
                    else:
                        print("Please enter a valid interface.")
                        continue
        values["interfaces"] = interfaces

        data.append(values)

    return data

# Validate whether or not the entered IP address is valid
def is_valid_address(address):
    return re.search("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", address)

# Check against added IP address to make sure there is no duplicate
def is_repeated_address(address, data):
    return any(ip['ip'] == address for ip in data)

def is_valid_interface(interface):
    return re.search("^[a-zA-z]+([ ])?\d+((\/\d+)+)?(\.\d+)?$", interface)

# Write YAML file
def write_yaml(data):
    with io.open('switches.yaml', 'w', encoding='utf8') as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

if __name__ == '__main__':
    print("""
     ----------------------------------------------------------------------
    |                                                                      |
    |               Welcome to Packet Capture Automation Tool              |
    |                                                                      |
    |   This tool will ask for the number of switches and interfaces to    |
    |    be captured. All these data are stored in switches.yaml file.     |
    |       A packet capture script will run and capture the traffic       |
    |       counters on the interfaces stated. Eventually these data       |
    |                  are exported in traffic.xlsx file.                  |
    |                                                                      |
    |     Alternately, you can prepare your own switches.yaml if you       |
    |      do not want to type in CLI. You can refer to sample.yaml        |
    |     for the required data format. Then run "python capture.py".      |
    |                                                                      |
     ----------------------------------------------------------------------
    """)
    data = take_input()
    write_yaml(data)

    while True:
        capture_now = input("Do you want to start capturing traffic now? [y/n] ")
        if capture_now == "y":
            break
        elif capture_now == "n":
            print("You can keep the current switches.yaml file. When you want to start capturing, you can run \"python capture.py\".")
            break
        else:
            print("Please enter a valid answer [y/n].")
            continue

    if capture_now == "y":
        start()
