from flask import Flask
from flask_restful import Api, Resource, reqparse
from pprint import pprint
from time import sleep
import json
import os
import subprocess
import requests
import logging

#Logging configuration
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

app = Flask(__name__)
api = Api(app)
port = "2323"


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



def scan_network(port):
    response="nmap -sP 192.168.1.2/24"
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
            stats=requests.get("http://"+x+":"+port)
            #pprint(stats.json())
            worker_id=stats.json()['worker_id']
            hashrates=stats.json()['hashrate']['total']
            #print("found worker "+worker_id+" at "+x+":"+port)
            logging.info("Found worker "+worker_id+" at "+x+":"+port)
            workerList.append({"name":worker_id,"ip":x, "hashrate":{"10s":hashrates[0],"60s":hashrates[1],"15m":hashrates[2]}})
        except:
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
        logging.info("Rescanning network for workers on port "+port)
        workers = scan_network(port)
        logging.info("Stats updated for all workers ("+str(len(workers))+")")
        return workers

api.add_resource(Refresh, "/refresh")

class Machine(Resource):
    def get(self, name):
        for worker in workers:
            if(name == worker["name"]):
                stats=requests.get("http://"+worker['ip']+":"+port)
                hashrates=stats.json()['hashrate']['total']
                #print("updated stats for worker "+name+" at "+worker['ip']+":"+port)
                logging.info("Updated stats for worker "+name+" at "+worker['ip']+":"+port)
                worker['hashrate'] = {"10s":hashrates[0],"60s":hashrates[1],"15m":hashrates[2]}
                return worker, 200
        return "machine not found", 404

api.add_resource(Machine, "/machine/<string:name>")


workers=scan_network(port)
logging.info("Initial network scan complete.")
logging.info("Found "+str(len(workers))+" workers.")
app.run(debug=True)
