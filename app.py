from flask import Flask
from flask_restful import Api, Resource, reqparse
from pprint import pprint
from time import sleep
import json
import os
import subprocess
import requests
import logging
import os
import socket


#Logging configuration
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

#Get config.json values
with open('config.json', 'r') as f:
    config = json.load(f)


app = Flask(__name__)
api = Api(app)
workerPort = config['worker_port']
broadcastPort = config['broadcast_port']
debugging = config['debug']

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


def find_ip(str):
    str = str.split('(')
    if len(str) > 1:
        if 'latency' not in str[1] and 'nmap.org' not in str[1] and 'scanned' not in str[1]:
            ip = str[1]
        else:
            ip = None
    else:
        ip = None
    if ip !=None:
        ip = ip.strip(')')
    return ip



def scan_network(port, ip):
    ip=ip.rsplit(".", 1)[0]
    ip=ip+".0"
    response="nmap -sP "+ip+"/24"
    #response="nmap -sP 192.168.1.2/24"
    response=response.split(" ")
    response=subprocess.check_output(response)
    #response=str(response).split('\n')
    response=response.split("\n")
    ipList = []
    for x in response:
            ip = find_ip(str(x))
            if ip != None:
                ipList.append(ip)

    workerList = []

    for x in ipList:
        try:
            stats=requests.get("http://"+x+":"+workerPort, timeout=.01)
            #pprint(stats.json())
            worker_id=stats.json()['worker_id']
            hashrates=stats.json()['hashrate']['total']
            #print("found worker "+worker_id+" at "+x+":"+workerPort)
            logging.info("Found worker "+worker_id+" at "+x+":"+workerPort)
            workerList.append({"name":worker_id,"ip":x, "hashrate":{"10s":hashrates[0],"60s":hashrates[1],"15m":hashrates[2]}})
        except:
            logging.warning("No worker at "+x+":"+workerPort)
            pass
    return workerList

def retrieveCluster():
    with open('machines') as f:
        cluster=json.load(f)
    return cluster

class Cluster(Resource):
    def get(self):
        if len(workers) >=1:
            return workers, 200
        else:
            return "failed to fetch machines", 500

api.add_resource(Cluster, "/cluster")

class Refresh(Resource):
    def post(self):
        global workers
        logging.info("Rescanning network for workers on port "+workerPort)
        workers = scan_network(workerPort, ip)
        logging.info("Stats updated for all workers ("+str(len(workers))+")")
        return workers

api.add_resource(Refresh, "/refresh")

class Machine(Resource):
    def get(self, name):
        for worker in workers:
            if(name == worker["name"]):
                stats=requests.get("http://"+worker['ip']+":"+workerPort)
                hashrates=stats.json()['hashrate']['total']
                #print("updated stats for worker "+name+" at "+worker['ip']+":"+workerPort)
                logging.info("Updated stats for worker "+name+" at "+worker['ip']+":"+workerPort)
                worker['hashrate'] = {"10s":hashrates[0],"60s":hashrates[1],"15m":hashrates[2]}
                return worker, 200
        return "machine not found", 404

api.add_resource(Machine, "/machine/<string:name>")

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])
ip = get_lan_ip()
logging.info("Localhost IP is: "+str(ip))
workers=scan_network(workerPort, ip)
logging.info("Searched on port: "+workerPort)
logging.info("Initial network scan complete.")
logging.info("Found "+str(len(workers))+" workers.")
app.run(debug=debugging, port=int(broadcastPort))
