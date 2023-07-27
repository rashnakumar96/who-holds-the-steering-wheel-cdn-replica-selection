from ripe.atlas.cousteau import (
  Dns,
  AtlasSource,
  AtlasCreateRequest
)
from ripe.atlas.cousteau import AtlasSource
from datetime import datetime
from ripe.atlas.cousteau import AtlasResultsRequest
import json
from ripe.atlas.sagan import DnsResult
import time
import dns
import dns.resolver
import tldextract
import requests
from ripe.atlas.sagan import DnsResult
import random
from bson import ObjectId
from datetime import (
    datetime, 
    timedelta
)
from ripe.atlas.cousteau import (
    Ping,
    Traceroute,
    AtlasSource,
    AtlasCreateRequest
)
from os.path import isfile, join
from copy import deepcopy
import os

def runPingMeasurements(ips,runs,country,client_probeid,API_KEY,measurement_ids):
    ATLAS_API_KEY = API_KEY
    status="complete"
    for run in range(runs):     
        print ("Doing run: ",run)
        count=0
        for target_ip in ips:
            if target_ip in measurement_ids:
                continue
            status="incomplete"
            print ("running Ping measurement for : ",target_ip," \% done: ",100*count/len(ips))
            count+=1
            ping = Ping(af=4, target=target_ip, description="ping VPN Vantage Points")
            source = AtlasSource(type="probes", value=client_probeid, requested=1)
            # source = AtlasSource(type="probes", value=, requested=1)

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=ATLAS_API_KEY,
                measurements=[ping],
                sources=[source],
                is_oneoff=True
            )
            
            (is_success, response) = atlas_request.create()
            if is_success:
                _id=response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"],target_ip)
                if target_ip not in measurement_ids:
                    measurement_ids[target_ip]=[]
                measurement_ids[target_ip].append(str(_id[0]))
                print (str(_id[0]))

            else:
                print ("failed to create measurement: %s" % response,target_ip)
                raise Exception("failed to create measurement: %s" % response)
            # measurement_ids.append((target_ip,str(_id[0])))

            with open("results/"+country+"/PingRipeMsmIds.json", 'w') as fp:
                json.dump(measurement_ids, fp)
    return status


def FetchPing(country):
    try:
        measurement_ids=json.load(open("results/"+country+"/PingRipeMsmIds.json"))
    except:
        return
    try: 
        _dict=json.load(open("results/"+country+"/PingRipeResult.json"))
    except:
        _dict={} 

    count=0
    for target_ip in measurement_ids:
        id=measurement_ids[target_ip][0]
        # target_ip=ip_id[0]
        # id=ip_id[1]
        print (target_ip,id)

        if target_ip not in _dict:
            _dict[target_ip]=[]

        if count%20==0:
            time.sleep(0.2)
        count+=1
        
        kwargs = {
        "msm_id": id
        }
        is_success, results = AtlasResultsRequest(**kwargs).create()

        if is_success:
            print("Fetching %s" % id," \% done",100*count/len(measurement_ids))
            for r in results:
                try:
                    perRunRtt=[r['result'][x]['rtt'] for x in range(len(r['result']))]
                except:
                    continue
                _dict[target_ip].append(r['avg'])
           
        else:
            print ("Fetching wasn't successful: ",id)
            # raise Exception("failed to create measurement: %s" % response)
        _dict[target_ip]=list(set(_dict[target_ip]))
        
    with open("results/"+country+"/PingRipeResult.json", 'w') as fp:
        json.dump(_dict, fp)

    

def runMeasurements(ips,runs,country,client_probeid,API_KEY):
    measurement_ids=[]

   
    for run in range(runs):     
        print ("Doing run: ",run)
        for target_ip in ips:
            traceroute=Traceroute(
                af = 4,  # IPv4
                target = target_ip,
                description = "Traceroute Target %s %s" % (target_ip, str(datetime.now())),
                max_hops = 30,
                timeout = 4000,
                paris = 16,  # use Paris Traceroute to avoid load balancing
                protocol = "ICMP",
                is_public = False,
                resolve_on_probe = True  # use probe's locally assigned DNS
            )

            source = AtlasSource(
                type="probes",
                value=client_probeid, #enter the client probe_id here
                requested=1
            )

            
            ATLAS_API_KEY = API_KEY

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=ATLAS_API_KEY,
                measurements=[traceroute],
                sources=[source],
                is_oneoff=True
            )

            (is_success, response) = atlas_request.create()
            if is_success:
                _id=response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"],target_ip)
            else:
                print ("failed to create measurement: %s" % response,target_ip)
                raise Exception("failed to create measurement: %s" % response)
            print (str(_id[0]))
            measurement_ids.append((target_ip,str(_id[0])))

            with open("results/"+country+"/traceRouteRipeMsmIds.json", 'w') as fp:
                json.dump(measurement_ids, fp)

def FetchResults(country):
    try:
        measurement_ids=json.load(open("results/"+country+"/traceRouteRipeMsmIds.json"))
    except:
        return

    _dict={}
    count=0
    for ip_id in measurement_ids:
        target_ip=ip_id[0]
        id=ip_id[1]
        print (ip_id,target_ip,id)

        if target_ip not in _dict:
            _dict[target_ip]=[]
        if count%20==0:
            time.sleep(0.2)
        count+=1
        
        kwargs = {
        "msm_id": id
        }
        print("Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        operations=[]
        if is_success:
            for r in results:
                result = deepcopy(r)
                operations.append(result)
            _dict[target_ip].append(operations)   
        else:
            print ("Fetching wasn't successful: ",id)
            continue     
        
    with open("results/"+country+"/tracerouteRipeResult.json", 'w') as fp:
        json.dump(_dict, fp)


if __name__ == "__main__":
    

    client_probeid=60453 #add the probe_id from the doc for a given region
    API_KEY="" #enter your API Key here
    country="US"

    # #load the full set of IPs collected from the dnsRipe measurements
    while 1:
        try:
            vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
            # vantagePoints=["non-neighboring_region"]

            T_ips=[]
            for vantage in vantagePoints:
                ips=[]
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                for domain in replicasPerVantage:
                    ips+=replicasPerVantage[domain]
                ips=list(set(ips))
                T_ips+=ips
                print ("len_ips and replicasPerVantage",len(ips),len(replicasPerVantage))
        except:
            time.sleep(60)
            continue
        status="incomplete"
        T_ips=set(T_ips)
        print ("len_Tips",len(T_ips))
        runs=1
        try:
            measurement_ids=json.load(open("results/"+country+"/PingRipeMsmIds.json"))
            print (len(measurement_ids))
        except Exception:
            measurement_ids={}
        try:
            status=runPingMeasurements(T_ips,runs,country,client_probeid,API_KEY,measurement_ids)
        except Exception as e:
            print ("Error in running measurements: ",str(e))
            time.sleep(60)
        if status=="complete":
            print ("Ping measurements completed")
            FetchPing(country)
            break

