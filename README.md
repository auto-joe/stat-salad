# stat-salad (working title)
## A simple REST backend to be used for creating miner monitoring dashboards.


## Overview
(Work in progress)
This is a simple python REST server written with Flask. It is intended to be used as the backend for other applications e.g. a monitoring dashboard. On startup, it will find the LAN IP range, then scan through the network attempting to communicate with mining software (XMRig for now- plan to support XMR-stak as well in the future) on the port specified in `config.json`. Once the server has finished startup, it serves information about which workers are available and those workers stats. A refresh/rescan to find new workers or purge old ones can be triggered via POST

## Configuration
Set the port that you have your XMRig workers running the XMRig API on in `config.json`

## Usage
To run:
`python app.py`
