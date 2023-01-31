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



def runMeasurements(country,vantage,fullDomainList,runs,client_probeid,API_KEY):
    #insert the ip_address of the publicDNSresolvers to use for each vantage point (for a given region) from the doc.
    resolver_dict={"local":"local","diff_metro":diff_metroIP,"same_region":same_regionIP,"neighboring_region":neighboring_regionIP,
     "non-neighboring_region":non_neighboring_regionIP} 
    
    measurement_ids=[]
    for run in range(runs):
        print ("Doing run: ",run)
        for domain in fullDomainList:
            if vantage=="local":
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
            else:
                dns = Dns(
                    af=4,
                    target=resolver_dict[vantage],
                    description="Dns Resolution",
                    query_class="IN",
                    query_type="A",
                    query_argument=domain,
                    set_rd_bit= True, 
                    type= "dns", 
                    include_qbuf=True,
                    include_Abuf=True,
                    use_probe_resolver= False #(set this to False if you want to use the specified resolver and set the
                    #value of target to the resolver's IP)
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

            measurement_ids.append((domain,str(_id[0])))

            if not os.path.exists("results"):
                os.mkdir("results")
            with open("results/"+country+"/dnsRipeMsmIds_"+vantage+".json", 'w') as fp:
                json.dump(measurement_ids, fp)


def FetchResults():
    try:
        measurement_ids=json.load(open("results/"+country+"/dnsRipeMsmIds_"+vantage+".json"))
    except:
        return
    
    _dict={}  
    
    count=0
    for domain,id in measurement_ids:
        if count%20==0:
            time.sleep(0.2)
        count+=1
        
        kwargs = {
        "msm_id": id
        }
        print(domain,"Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        # print (results)
        if is_success:
            try:
                my_result = DnsResult(results[0])
                print ("print Result: ",str(my_result).split("Probe #")[1])
                probeId=str(my_result).split("Probe #")[1]
                print (domain,id,probeId)
                # continue
            except Exception as e:
                print ("Fetching wasn't successful: ",domain,id, str(e))
                continue
        else:
            continue
        try:
            dnsAnswer=my_result.responses[0].abuf.answers
        except Exception as e:
            print ("Couldn't decode the answer: ",domain,id, str(e))
            continue
        if domain not in _dict:
            _dict[domain]=[]
          

        for result in dnsAnswer:
            try:
                ip_addr=result.address
                _dict[domain].append(ip_addr)

            except Exception as e:
                # print (domain,id,result, str(e))
                print ("Error in fetching ip from ans: ",str(e))
                continue
    with open("results/"+country+"/dnsRipeResult_"+vantage+".json", 'w') as fp:
        json.dump(_dict, fp)
        

if __name__ == "__main__":
    
    runs=1
    vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
    cdns=["Google","Fastly","EdgeCast","Akamai","Amazon Cloudfront"]
    client_probeid=client_probeid #add from the doc for a given region
    API_KEY="API_KEY" #enter your API Key here

    fullDomainList=[]
    for cdn in cdns:
        cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
        domains=cdnMap[cdn]
        fullDomainList+=domains
    fullDomainList=set(fullDomainList)
    print (fullDomainList)
    replicaIPs=[]
    for vantage in vantagePoints:
        try:
            runMeasurements(country,vantage,fullDomainList,runs,client_probeid,API_KEY)
        except Exception as e:
            print ("Error in running measurements: ",str(e))
            time.sleep(300)
        time.sleep(300)
        FetchResults()






