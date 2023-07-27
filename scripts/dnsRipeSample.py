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



def runMeasurements(country,vantage,fullDomainList,runs,client_probeid,API_KEY,measurement_ids):
    status="complete"
    #insert the ip_address of the publicDNSresolvers to use for each vantage point (for a given region) from the doc.
    # resolver_dict={"local":"local","diff_metro":"149.112.112.112","same_region":"209.250.128.6","neighboring_subregion":"45.188.158.141","neighboring_region":"159.69.114.157","non-neighboring_region":"103.29.118.157"} #US 
    # resolver_dict={"local":"local","diff_metro":"203.201.60.12","same_region":"209.150.154.1","neighboring_subregion":"103.29.68.118","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #IN
   # resolver_dict={"local":"local","diff_metro":"189.125.18.5","same_region":"190.151.144.21","neighboring_subregion":"209.250.128.6","neighboring_region":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #BR
    # resolver_dict={"local":"local","diff_metro":"194.168.4.123","same_region":"193.26.6.215","neighboring_subregion":"159.69.114.157","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GB
    #resolver_dict={"local":"local","diff_metro":"202.46.34.74","same_region":"103.29.68.118","neighboring_subregion":"203.201.60.12","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #CN
    # resolver_dict={"local":"local","diff_metro":"196.15.170.131","same_region":"196.43.199.61","neighboring_subregion":"41.57.120.161","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ZA
    # resolver_dict={"local":"local","diff_metro":"54.252.183.4","same_region":"210.48.77.68","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #AU
    # resolver_dict={"local":"local","diff_metro":"90.159.2.208","same_region":"93.45.98.221","neighboring_subregion":"92.39.141.222","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #TR
    # resolver_dict={"local":"local","diff_metro":"92.39.141.222","same_region":"176.107.115.226","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #RU
    # resolver_dict={"local":"local","diff_metro":"95.111.253.234","same_region":"62.23.74.39","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #DE
    # resolver_dict={"local":"local","diff_metro":"103.28.114.33","same_region":"112.213.88.45","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #ID
    # resolver_dict={"local":"local","diff_metro":"83.110.78.132","same_region":"2.89.129.40","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #AE
    # resolver_dict={"local":"local","diff_metro":"91.121.134.117","same_region":"80.113.19.90","neighboring_subregion":"91.190.142.200","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #FR
    # resolver_dict={"local":"local","diff_metro":"190.151.144.21","same_region":"189.125.18.5","neighboring_subregion":"209.250.128.6","neighboring_region":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #AR
    # resolver_dict={"local":"local","diff_metro":"80.248.14.50","same_region":"102.176.81.146","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #NG
    # resolver_dict={"local":"local","diff_metro":"41.155.240.28","same_region":"80.249.72.60","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #EG
    # resolver_dict={"local":"local","diff_metro":"80.87.79.250","same_region":"80.248.14.50","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GH
    # resolver_dict={"local":"local","diff_metro":"80.249.72.60","same_region":"41.155.240.28","neighboring_subregion":"80.248.14.50","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #DZ
    resolver_dict={"local":"local","diff_metro":"90.160.140.67","same_region":"93.42.132.193","neighboring_subregion":"91.121.134.117","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ES

    for run in range(runs):
        print ("Doing run: ",run)
        count=0
        for domain in fullDomainList:
            if domain in measurement_ids:
                continue
            print ("running dnsRipe measurement for : ",domain," \% done: ",100*count/len(fullDomainList))
            count+=1

            status="incomplete"
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

            measurement_ids[domain]=str(_id[0])

            if not os.path.exists("results"):
                os.mkdir("results")
            with open("results/"+country+"/dnsRipeMsmIds_"+vantage+".json", 'w') as fp:
                json.dump(measurement_ids, fp)
    return status


def FetchResults(country,vantage):
    try:
        measurement_ids=json.load(open("results/"+country+"/dnsRipeMsmIds_"+vantage+".json"))
    except:
        return
    
    try:
        _dict=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
    except:
        _dict={}  
    
    count=0
    for domain in measurement_ids:
        if domain in _dict:
            continue
        id=measurement_ids[domain]
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
    vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
    # vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]


    # cdns=['EdgeCast','StackPath','Cloudfront','Fastly','Akamai','Google','Cloudflare','Highwinds','Yahoo','CDN77','Level3','Incapsula','MicrosoftAzure']#US
    # cdns=['CDNetworks', 'StackPath', 'EdgeCast', 'MicrosoftAzure', 'Facebook', 'CDN77', 'Medianova', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare']#TR
    # cdns=['EdgeCast', 'Facebook', 'CDN77', 'NGENIX', 'Cloudfront', 'CDNetworks', 'Fastly', 'Akamai', 'Google', 'Cloudflare']#RU
    # cdns=['Cloudflare', 'Akamai', 'Google', 'Cloudfront', 'Fastly', 'CDN77', 'StackPath', 'Highwinds', 'Yahoo', 'MicrosoftAzure', 'EdgeCast'] #DE
    # cdns=['EdgeCast', 'Yahoo', 'Taobao', 'Level3', 'CDN77', 'Facebook', 'Highwinds', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'] #ID
    # cdns=['EdgeCast', 'Yahoo', 'MicrosoftAzure', 'CDN77', 'Facebook', 'Highwinds', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'] #AE
    # cdns=['Yahoo', 'StackPath', 'Level3', 'CDN77', 'EdgeCast', 'Fastly', 'Cloudfront', 'Google', 'Akamai', 'Cloudflare'] #FR
    # cdns=['Yahoo', 'Azion', 'EdgeCast', 'Highwinds', 'Facebook', 'BunnyCDN', 'Telefonica', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'] #AR
    # cdns=['EdgeCast','Facebook', 'MicrosoftAzure', 'Taobao', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'] #NG
    # cdns=['EdgeCast','Facebook', 'MicrosoftAzure','Level3','BunnyCDN','Highwinds', 'Taobao', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'] #EG 
    # cdns=['Yahoo', 'Taobao', 'BunnyCDN', 'Highwinds', 'MicrosoftAzure', 'Facebook', 'EdgeCast', 'StackPath', 'CDN77', 'Cloudfront', 'Fastly', 'Google', 'Akamai', 'Cloudflare'] #GH
    # cdns=['Yahoo', 'EdgeCast', 'Taobao', 'Level3', 'Facebook', 'Highwinds', 'CDN77', 'StackPath', 'Cloudfront', 'Fastly', 'Akamai', 'Google', 'Cloudflare']#DZ
    cdns=['MicrosoftAzure', 'Highwinds', 'Yahoo', 'BunnyCDN', 'EdgeCast', 'StackPath', 'Telefonica', 'CDN77', 'Cloudfront', 'Fastly', 'Google', 'Akamai', 'Cloudflare'] #ES

    # client_probeid=54500 #AU add the probe_id from the doc for a given region
    # client_probeid=16441 #ZA add the probe_id from the doc for a given region
    # client_probeid=55328 #CN add the probe_id from the doc for a given region
    # client_probeid=1005555 #GB add the probe_id from the doc for a given region
    #client_probeid=1005287 #BR add the probe_id from the doc for a given region
    # client_probeid=60641 #IN add the probe_id from the doc for a given region
    # client_probeid=1005747 #US add the probe_id from the doc for a given region
    # client_probeid=1005636 #TR add the probe_id from the doc for a given region
    # client_probeid=1005693 #RU add the probe_id from the doc for a given region
    # client_probeid=1005728 #DE add the probe_id from the doc for a given region
    # client_probeid=1004317 #ID add the probe_id from the doc for a given region
    # client_probeid=1005737 #AE add the probe_id from the doc for a given region
    # client_probeid=1005784 #FR add the probe_id from the doc for a given region
    # client_probeid=1005222 #AR add the probe_id from the doc for a given region
    # client_probeid=61417 #NG add the probe_id from the doc for a given region
    # client_probeid=1003469 #EG add the probe_id from the doc for a given region
    # client_probeid=6612 #GH add the probe_id from the doc for a given region
    # client_probeid=1001421 #DZ add the probe_id from the doc for a given region
    client_probeid=1005792 #ES add the probe_id from the doc for a given region

    API_KEY="b7fb25c3-a5fc-4785-8f35-6830a6fdb6a4" #enter your API Key here
    country="ES"
    print ("country: ",country)
    cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
    for cdn in cdns:
        if cdn!=None:
            print (cdn,len(set(cdnMap[cdn])))

    fullDomainList=[]
    cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))

    for cdn in cdns:
        domains=cdnMap[cdn]
        fullDomainList+=set(domains)
    fullDomainList=set(fullDomainList)
    print (len(fullDomainList))

    while (1):
        countV=0
        for vantage in vantagePoints:
            # if vantage=="neighboring_subregion" or vantage=="non-neighboring_region":
            #     FetchResults(country,vantage)
            #     continue
            status="incomplete"
            print ("Running for vantage Point: ",vantage)
            try:
                measurement_ids=json.load(open("results/"+country+"/dnsRipeMsmIds_"+vantage+".json"))
                print (len(measurement_ids))
            except Exception:
                measurement_ids={}

            try:
                status=runMeasurements(country,vantage,fullDomainList,runs,client_probeid,API_KEY,measurement_ids)
            except Exception as e:
                print ("Error in running measurements: ",str(e))
                time.sleep(60)
            if status=="complete":
                print ("DNS measurements completed for vantage: ",vantage)
                countV+=1
                #FetchResults(country,vantage)
        if countV==len(vantagePoints):
            for vantage in vantagePoints:
                FetchResults(country,vantage)
            break
        #break





