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
from netmiko import ConnectHandler
import schedule
import time
import pandas as pd
from openpyxl import load_workbook
import re

def get_counters():
    with open("switches.yaml", 'r') as config:
        switches = yaml.safe_load(config)

    device = {
        'device_type': 'cisco_ios'
    }

    all_data = []

    for switch in switches:
        data = {
            'Time': [],
            'Switch': [],
            'Interface': [],
            'rx_bps': [],
            'rx_packets': [],
            'tx_bps': [],
            'tx_packets': []
        }

        device['host'] = switch['ip']
        device['username'] = switch['username']
        device['password'] = switch['password']

        if switch['interfaces'] == ["all"]:
            try:
                with ConnectHandler(**device) as conn:
                    show_ip_int_bri = conn.send_command("show ip int brief")
                    int_names = re.finditer(r"[a-zA-z]+([ ])?\d+((\/\d+)+)?(\.\d+)?", show_ip_int_bri, re.MULTILINE)
                    int_list = []
                    for int_num, int_name in enumerate(int_names, start=1):
                        int_list.append(int_name.group())
                    switch['interfaces'] = int_list
            except Exception:
                t_tuple = time.localtime()
                t = time.strftime("%d/%m/%Y %H:%M:%S", t_tuple)
                print(f"{t}: Failed to connect to switch with IP address {switch['ip']} to fetch all interfaces")

        try:
            with ConnectHandler(**device) as conn:
                for interface in switch['interfaces']:
                    t_tuple = time.localtime()
                    t = time.strftime("%d/%m/%Y %H:%M:%S", t_tuple)
                    try:
                        output = conn.send_command("show int {}".format(interface))
                        input_rate = output.find("5 minute input")
                        output_rate = output.find("5 minute output")
                        first_bps = output.find(" bits/sec")
                        second_bps = output.find(" bits/sec", first_bps+1)
                        rx_bps = int(output[input_rate+20:first_bps])
                        rx_packets = int(output[first_bps+11:output.find(" packets/sec")])
                        tx_bps = int(output[output_rate+21:second_bps])
                        tx_packets = int(output[second_bps+11:output.find(" packets/sec", second_bps)])

                        data['Time'].append(t)
                        data['Switch'].append(switch['ip'])
                        data['Interface'].append(interface)
                        data['rx_bps'].append(rx_bps)
                        data['rx_packets'].append(rx_packets)
                        data['tx_bps'].append(tx_bps)
                        data['tx_packets'].append(tx_packets)

                        print(f"{t}: Collected traffic counters from switch with IP address {switch['ip']} interface {interface}")
                    except Exception:
                        print(f"{t}: Failed to collect traffic counters from switch with IP address {switch['ip']} interface {interface}")
            all_data.append(data)
        except Exception:
            t_tuple = time.localtime()
            t = time.strftime("%d/%m/%Y %H:%M:%S", t_tuple)
            print(f"{t}: Failed to connect to switch with IP address {switch['ip']}")

    try:
        for d in all_data:
            df = pd.DataFrame(d)
            writer = pd.ExcelWriter('traffic.xlsx', engine='openpyxl')
            writer.book = load_workbook('traffic.xlsx')
            writer.sheets = dict((ws.title, ws) for ws in writer.book.worksheets)
            try:
                reader = pd.read_excel('traffic.xlsx', sheet_name=d['Switch'][0])
            except:
                df.to_excel(writer, index=False, header=True, startrow=0, sheet_name=d['Switch'][0])
                writer.save()
            else:
                df.to_excel(writer, index=False, header=False, startrow=len(reader)+1, sheet_name=d['Switch'][0])
            writer.save()
        writer.close()
    except Exception as e:
        t_tuple = time.localtime()
        t = time.strftime("%d/%m/%Y %H:%M:%S", t_tuple)
        print(f"{t}: Fail to write data into traffic.xlsx. Error: {e}")

def start():
    print("Running it once to check if there's any issue")
    time.sleep(2)
    get_counters()
    print("\nPlease check any error above. If needed, stop this script by Ctrl + C.")
    while True:
        try:
            frequency = int(input("To continue, enter the frequency to capture traffic per day: "))
            break
        except Exception:
            print("Please enter an intger.")
            continue
    hours = []
    print("Specify the time to run capturing in a format of HH:MM, e.g. 09:00 / 20:30.")
    for i in range(frequency):
        while True:
            hour = input(f"{str(i+1)}: ")
            if is_valid_hour(hour):
                hours.append(hour)
                break
            else:
                print("Please follow the HH:MM format.")
                continue
    for hr in hours:
        schedule.every().day.at(hr).do(get_counters)
    print("Capturing traffic counters at the specified interval.")
    while True:
        schedule.run_pending()
        time.sleep(30)

def is_valid_hour(hour):
    return re.search("^([01]?[0-9]|2[0-3]):[0-5][0-9]$", hour)

if __name__ == '__main__':
    start()
