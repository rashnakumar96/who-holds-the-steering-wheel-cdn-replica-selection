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
import os

def runMeasurements(country,API_KEY,domain):
    measurement_ids={}
            
    dns = Dns(
        af=4,
        description="Dns Resolution",
        query_class="IN",
        query_type="A",
        query_argument=domain,
        set_rd_bit= True, 
        type= "dns", 
        include_qbuf=True,
        include_Abuf=True,
        use_probe_resolver= True #(set this to true if you want to use the probe's resolver
    )
           
                
    source = AtlasSource(
        type="country",
        value=country, 
        requested=1
    )

    ATLAS_API_KEY = API_KEY



    atlas_request = AtlasCreateRequest(
        start_time=datetime.utcnow(),
        key=ATLAS_API_KEY,
        measurements=[dns],
        sources=[source],
        is_oneoff=True
    )
    (is_success, response) = atlas_request.create()
    if is_success:
        _id=response["measurements"]
        print ("print Result: ",response)
        print("SUCCESS: measurement created: %s" % response["measurements"],domain)
    else:
        print ("failed to create measurement: %s" % response)
        raise Exception("failed to create measurement: %s" % response)

    print (str(_id[0]))

    measurement_ids[domain]=str(_id[0])
    print (measurement_ids)
    return measurement_ids
 

def FetchResults(country,measurement_ids):
    count=0
    for domain in measurement_ids:
        id=measurement_ids[domain]
        if count%20==0:
            time.sleep(0.2)
        count+=1
        
        kwargs = {
        "msm_id": id
        }
        print(domain,"Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        if is_success:
            try:
                my_result = DnsResult(results[0])
                print ("print Result: ",str(my_result).split("Probe #")[1])
                probeId=str(my_result).split("Probe #")[1]
                print (domain,id,"probeId: ",probeId)
                # continue
            except Exception as e:
                print ("Fetching wasn't successful: ",domain,id, str(e))
                continue
        else:
            continue
        
       
if __name__ == "__main__":
    country="US"
    API_KEY="b7fb25c3-a5fc-4785-8f35-6830a6fdb6a4"
    domain="google.com"
    # measurement_ids=runMeasurements(country,API_KEY,domain)
    measurement_ids={'google.com': '49763272'}

    FetchResults(country,measurement_ids)
    
    
