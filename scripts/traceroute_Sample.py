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
    Traceroute,
    AtlasSource,
    AtlasCreateRequest
)
from os.path import isfile, join
from copy import deepcopy
import os



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
    country=clientCountry
    client_probeid=client_probeid #add from the doc for a given region
    API_KEY="API_KEY" #enter your API Key here

    #load the full set of IPs collected from the dnsRipe measurements
    ips=[]
    vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
    
    for vantage in vantagePoints:
        replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
        for domain in replicasPerVantage:
            ips+=replicasPerVantage[domain]

    ips=set(ips)
    # print (ips)
    runs=1
    try:
        runMeasurements(ips,runs,country,client_probeid,API_KEY)
    except Exception as e:
        print ("Error in running measurements: ",str(e))
    FetchResults(country)

