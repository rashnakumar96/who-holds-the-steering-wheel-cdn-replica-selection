import ipaddress
import json
import tldextract
import pyasn
from ipwhois import IPWhois
import time
import csv
import requests


def longest_matching_prefix(ip_address, prefix_list):
    # Convert the IP address to an IPv4Address object
    ip_address = ipaddress.IPv4Address(ip_address)

    # Initialize variables to store the longest prefix and its length
    longest_prefix = None
    longest_length = 0

    # Iterate through each prefix in the list
    for prefix in prefix_list:
        # Parse the prefix into an IPv4Network object
        network = ipaddress.IPv4Network(prefix, strict=False)

        # Check if the IP address is in the network
        if ip_address in network:
            # Update the longest prefix if the current prefix is longer
            if network.prefixlen > longest_length:
                longest_prefix = prefix
                longest_length = network.prefixlen

    return longest_prefix

def createPrefixlist():
    googleCloudIPs=json.load(open("data/googleCloudIPs.json"))
    googleNativeIPs=json.load(open("data/googleNativeIPs.json"))
    amazonIPs=json.load(open("data/amazonIPs.json"))


    cloudPrefixes=set()
    for prefixDict in googleCloudIPs["prefixes"]:
        if "ipv4Prefix" in prefixDict:
            cloudPrefixes.add(prefixDict["ipv4Prefix"])

    nativePrefixes=set()
    for prefixDict in googleNativeIPs["prefixes"]:
        if "ipv4Prefix" in prefixDict:
            nativePrefixes.add(prefixDict["ipv4Prefix"])

    services={}
    amazonPrefixes=set()
    for prefixDict in amazonIPs["prefixes"]:
        if "ip_prefix" in prefixDict:
            amazonPrefixes.add(prefixDict["ip_prefix"])
        services[prefixDict["ip_prefix"]]=prefixDict["service"]
    # print (services)

    return cloudPrefixes,nativePrefixes,amazonPrefixes,services

def findtld(website):
    return tldextract.extract(website).domain

def readManycast():
    prefixes=set()
    count=0
    with open("data/manycast_jan2022.json", 'r') as file:
        for line in file:
            # if count==10:
            #     break
            count+=1
            try:
                entry = json.loads(line)
                ip4_prefix = entry['ip4_prefix']
                prefix=find_prefix(ip4_prefix)
                prefixes.add(prefix)

                geolocation = entry['geolocation']

                # Iterate through each geolocation entry
                for location in geolocation:
                    code_country = location['code_country']
                    city = location['city']
                    latitude = location['latitude']
                    longitude = location['longitude']
            except json.JSONDecodeError:
                print("Error decoding JSON on this line:", line)
    # print (list(prefixes)[:10])
    return prefixes

def readManycast_2023():
    prefixes=set()
    file_path = "data/manycast_2023.txt"

    with open(file_path, 'r') as file:
        lines = [line.strip() for line in file.readlines()]

    for line in lines:
        try:
            prefix=find_prefix(line)
            prefixes.add(prefix)
        except:
            continue
    # print (list(prefixes))
    return prefixes

def find_prefix(ip_address):
    # Convert the IP address to an IPv4Address object
    ip = ipaddress.IPv4Address(ip_address)

    # Create an IPv4Network object with a /24 prefix
    network = ipaddress.IPv4Network(f"{ip}/24", strict=False)

    # Return the network address as a string
    return str(network.network_address)

def map_ip_to_asn(ips):
    try:
        IPtoASNMap=json.load(open("results/IPtoASNMap.json"))
    except:
        IPtoASNMap={}
    asndb = pyasn.pyasn('data/ip2asn20231017.dat')

    count=0
    for ip in ips:
        print (f"{100*count/len(ips)} % done")
        count+=1
        if ip not in IPtoASNMap:
            IPtoASNMap[ip]={}
            asn = asndb.lookup(ip)
            IPtoASNMap[ip]["ASN"]=asn[0]
            try:
                obj = IPWhois(ip)
                result = obj.lookup_rdap()

                asn_info = result.get('asn', 'ASN information not found')
                org = result.get('asn_description', 'Organization not found')

                if str(asn[0])!=str(asn_info):
                    print(f"MISMATCH IP: {ip} AS_PYASN {asn} AS_WHOIS {asn_info} \n")
                    if asn[0]==None:
                        IPtoASNMap[ip]["ASN"]=asn_info
                IPtoASNMap[ip]["ORG"]=org.split(",")[0]
            except Exception as e:
                print (str(e))
                time.sleep(2)


    with open("results/IPtoASNMap.json",'w') as fp:
        json.dump(IPtoASNMap,fp,indent=4)
    return IPtoASNMap

def findASNsofCDNs(cdns,countries):
    for cdn in cdns:
        ips=set()
        for country in countries:
            cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
            domains=set(cdnMap[cdn])
            if country=="AU":
                vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
            else:
                vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]

            for vantage in vantagePoints:
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                for domain in domains:
                    tld=findtld(domain)
                    if domain in replicasPerVantage:
                        for ip in set(replicasPerVantage[domain]):
                            ips.add(ip)
        print (f"{cdn} : length of IPs {len(ips)}")
        IPtoASNMap=map_ip_to_asn(ips)
        ASNs={}
        for ip in ips:
            try:
                ASNs[IPtoASNMap[ip]["ASN"]]=IPtoASNMap[ip]["ORG"]
            except:
                continue
        print (f"{cdn} : {ASNs} \n")
    return IPtoASNMap


def checkManycast(cdnCountryMap):
    
    countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]
    cloudflareAnnouncedList=["173.245.48.0/20","103.21.244.0/22","103.22.200.0/22","103.31.4.0/22","141.101.64.0/18","108.162.192.0/18","190.93.240.0/20","188.114.96.0/20","197.234.240.0/22","198.41.128.0/17","162.158.0.0/15","104.16.0.0/13","104.24.0.0/14","172.64.0.0/13","131.0.72.0/22"]
    manycastPrefixes=readManycast()
    # manycastPrefixes=readManycast_2023()

    cdns=set()
    for country in cdnCountryMap:
        for cdn in cdnCountryMap[country]:
            cdns.add(cdn)
    # print (cdns)
    cdns=["Akamai",'CDN77', 'MicrosoftAzure','StackPath', 'Azion', 'Taobao', 'Level3', 'Tencent', 'BunnyCDN', 'Facebook', 'NGENIX', 'Yahoo', 'Medianova','Cloudfront', 'Google', 'EdgeCast', 'Fastly', 'Cloudflare']
    
    IPtoASNMap=findASNsofCDNs(cdns,countries)
    exit()
    cdntoASN={"Fastly":[54113],"EdgeCast":[15133],"Cloudflare":[13335, 209242]}
    for cdn in cdns:
        prefixes=set()
        identifiedAnycast=set()
        unidentifiedAnycast=set()
        ASNOrg=set()
        for country in countries:
            cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
            domains=set(cdnMap[cdn])
            if country=="AU":
                vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
            else:
                vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]

            for vantage in vantagePoints:
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                ips=[]
                for domain in domains:
                    tld=findtld(domain)
                    if domain in replicasPerVantage:
                        ips+=replicasPerVantage[domain]
                ips=list(set(ips))
                
                for replicaip in ips:
                    prefix=find_prefix(replicaip)
                    if cdn=="Cloudflare":
                        matchingPrefix=longest_matching_prefix(prefix, cloudflareAnnouncedList)
                        if matchingPrefix!=None:
                            prefixes.add(prefix)
                            if prefix in manycastPrefixes:
                                identifiedAnycast.add(prefix)
                            else:
                                unidentifiedAnycast.add(prefix)
                    else:
                        if IPtoASNMap[replicaip]["ASN"] in cdntoASN[cdn]:
                            prefixes.add(prefix)
                            if prefix in manycastPrefixes:
                                identifiedAnycast.add(prefix)
                            else:
                                unidentifiedAnycast.add(prefix)

        print (f"{cdn}: Total Prefixes across Countries: {len(prefixes)}; identifiedAnycast: {len(identifiedAnycast)}; unidentifiedAnycast: {len(unidentifiedAnycast)} \n")
        print (unidentifiedAnycast,"\n\n")
    # CloudflarePrefixes=set()
    # notCloudflarePrefixes=set()
    # for prefix in unidentifiedAnycast:
    #     matchingPrefix=longest_matching_prefix(prefix, cloudflareAnnouncedList)
    #     if matchingPrefix==None:
    #         notCloudflarePrefixes.add(prefix)
    #     else:
    #         CloudflarePrefixes.add(prefix)
    # print (f"CloudflarePrefixes: {len(CloudflarePrefixes)}; notCloudflarePrefixes {len(notCloudflarePrefixes)}")
    # print (notCloudflarePrefixes)

    # print (list(unidentifiedAnycast))

def validateResolverIPs():
    resolver_dict={}
    resolver_dict["US"]={"diff_metro":"149.112.112.112","same_region":"209.250.128.6","neighboring_subregion":"45.188.158.141","neighboring_region":"159.69.114.157","non-neighboring_region":"103.29.118.157"} #US 
    resolver_dict["IN"]={"diff_metro":"203.201.60.12","same_region":"209.150.154.1","neighboring_subregion":"103.29.68.118","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #IN
    resolver_dict["BR"]={"diff_metro":"189.125.18.5","same_region":"190.151.144.21","neighboring_subregion":"209.250.128.6","neighboring_region":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #BR
    resolver_dict["GB"]={"diff_metro":"194.168.4.123","same_region":"193.26.6.215","neighboring_subregion":"159.69.114.157","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GB
    resolver_dict["CN"]={"diff_metro":"202.46.34.74","same_region":"103.29.68.118","neighboring_subregion":"203.201.60.12","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #CN
    resolver_dict["ZA"]={"diff_metro":"196.15.170.131","same_region":"196.43.199.61","neighboring_subregion":"41.57.120.161","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ZA
    resolver_dict["AU"]={"diff_metro":"54.252.183.4","same_region":"210.48.77.68","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #AU
    resolver_dict["TR"]={"diff_metro":"90.159.2.208","same_region":"93.45.98.221","neighboring_subregion":"92.39.141.222","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #TR
    resolver_dict["RU"]={"diff_metro":"92.39.141.222","same_region":"176.107.115.226","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #RU
    resolver_dict["DE"]={"diff_metro":"95.111.253.234","same_region":"62.23.74.39","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #DE
    resolver_dict["ID"]={"diff_metro":"103.28.114.33","same_region":"112.213.88.45","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #ID
    resolver_dict["AE"]={"diff_metro":"83.110.78.132","same_region":"2.89.129.40","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #AE
    resolver_dict["FR"]={"diff_metro":"91.121.134.117","same_region":"80.113.19.90","neighboring_subregion":"91.190.142.200","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #FR
    resolver_dict["AR"]={"diff_metro":"190.151.144.21","same_region":"189.125.18.5","neighboring_subregion":"209.250.128.6","neighboring_region":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #AR
    resolver_dict["NG"]={"diff_metro":"80.248.14.50","same_region":"102.176.81.146","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #NG
    resolver_dict["EG"]={"diff_metro":"41.155.240.28","same_region":"80.249.72.60","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #EG
    resolver_dict["DH"]={"diff_metro":"80.87.79.250","same_region":"80.248.14.50","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GH
    resolver_dict["DZ"]={"diff_metro":"80.249.72.60","same_region":"41.155.240.28","neighboring_subregion":"80.248.14.50","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #DZ
    resolver_dict["ES"]={"diff_metro":"90.160.140.67","same_region":"93.42.132.193","neighboring_subregion":"91.121.134.117","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ES    

    resolverIPs=set()
    for country in resolver_dict:
        for vantage in resolver_dict[country]:
            resolverIPs.add(resolver_dict[country][vantage])
    print (f" Resolver IPs: {resolverIPs}; length of set: {len(resolverIPs)}")


def sanityCheck():
    countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]
    cloudPrefixes,nativePrefixes,amazonPrefixes,services=createPrefixlist()
    print (f"len of cloud and native prefix intersection: {len(cloudPrefixes.intersection(nativePrefixes))}")
    sanityCheckSet=set()
    for country in countries:
        cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
        domains=set(cdnMap["Cloudfront"])
        print ("\n",country)
        

        if country=="AU":
            vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
        else:
            vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]

        for vantage in vantagePoints:
            amazonServices=set()
            cloudPrefixesCount=0
            nativePrefixesCount=0
            amazonPrefixesCount=0
            replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
            ips=[]
            for domain in domains:
                    tld=findtld(domain)
                    if domain in replicasPerVantage:
                        ips+=replicasPerVantage[domain]
            ips=list(set(ips))
            for replicaip in ips:
                # prefix=longest_matching_prefix(replicaip, cloudPrefixes)
                # if prefix!=None:
                #     cloudPrefixesCount+=1
                #     continue
                # prefix=longest_matching_prefix(replicaip, nativePrefixes)
                # if prefix!=None:
                #     nativePrefixesCount+=1
                #     continue
                prefix=longest_matching_prefix(replicaip, amazonPrefixes)
                if prefix!=None:
                    amazonPrefixesCount+=1
                    amazonServices.add(services[prefix])
                    continue
                sanityCheckSet.add(replicaip)
            print (f"{vantage}: Total IPs: {len(ips)}; amazonPrefixesCount: {amazonPrefixesCount}; services {amazonServices}")

        # print (f"{vantage}: Total IPs: {len(ips)}; sanityCheck: {cloudPrefixesCount+nativePrefixesCount}; cloudPrefixesCount: {cloudPrefixesCount}; nativePrefixesCount {nativePrefixesCount}")
    print (sanityCheckSet)

def jaccard_index(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union

def baselineExperiments(cdnCountryMap):
    countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]
    # countries=["US"]
    cdns=set()
    for country in cdnCountryMap:
        for cdn in cdnCountryMap[country]:
            cdns.add(cdn)
    print (cdns)
    cdns=["Cloudflare","Akamai","EdgeCast"]
    # cdns=["Cloudflare"]

    cdns=["Akamai",'CDN77','StackPath', 'Azion', 'Taobao', 'Level3', 'Tencent', 'BunnyCDN', 'Facebook', 'NGENIX', 'Yahoo', 'Medianova','Cloudfront', 'Google', 'EdgeCast', 'Fastly', 'Cloudflare']
    # cdns=["Akamai",'CDN77', 'MicrosoftAzure','StackPath', 'Azion', 'Taobao', 'Level3', 'Tencent', 'BunnyCDN', 'Facebook', 'NGENIX', 'Yahoo', 'Medianova','Cloudfront', 'Google', 'EdgeCast', 'Fastly', 'Cloudflare']


    prefixMap={}
    for cdn in cdns:
        if cdn not in prefixMap:
            prefixMap[cdn]={}
        for country in countries:
            cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
            try:
                domains=set(cdnMap[cdn])
            except:
                continue
            if country not in prefixMap[cdn]:
                prefixMap[cdn][country]={}
            if country=="AU":
                vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
            else:
                vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]

            for vantage in vantagePoints:
                if vantage not in prefixMap[cdn][country]:
                    prefixMap[cdn][country][vantage]=set()
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                ips=set()
                for domain in domains:
                    if domain in replicasPerVantage:
                        ips|=set(replicasPerVantage[domain])
                
                for replicaip in ips:
                    # prefix=find_prefix(replicaip)
                    prefixMap[cdn][country][vantage].add(replicaip)
                prefixMap[cdn][country][vantage]=list(prefixMap[cdn][country][vantage])
    with open("results/replicaipMap.json",'w') as fp:
        json.dump(prefixMap,fp,indent=4)
    exit()

    JaccardMap={}
    for cdn in prefixMap:
        rows=[
            ["country","Jaccard[1]-LocalvsSameRegion","Jaccard[3]-LocalvsNon-NeighRegion"]
        ]
        # print ("CDN: ",cdn)
        if cdn not in JaccardMap:
            JaccardMap[cdn]={}
        for country in prefixMap[cdn]:
            if cdn not in cdnCountryMap[country]:
                continue
            local=prefixMap[cdn][country]["local"]
            same_region= prefixMap[cdn][country]["same_region"]
            non_neigh_region=prefixMap[cdn][country]["non-neighboring_region"]
            if local and same_region and non_neigh_region:
                if cdn=="NGENIX":
                    print (cdn,country,"local: ",local,'\n\n',"Same region: ",same_region,'\n\n',"Non-Neigh_Region",non_neigh_region)
                Jaccard_1=jaccard_index(local, same_region)
                Jaccard_3=jaccard_index(local, non_neigh_region)
                Jaccard_tupple=(Jaccard_1,Jaccard_3)
                JaccardMap[cdn][country]=Jaccard_tupple
                # print (f"{country}: J_1: {Jaccard_1}; J_3: {Jaccard_3}")
                rows.append([country,Jaccard_1,Jaccard_3])
        with open('results/prefix_JaccardDist_'+cdn+'.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        # print ("\n\n")

def getOffnetIPs(file,filename):
    if filename!="all":
        offnetIPs={ip for asn in file for ip in file[asn]}
    else:
        offnetIPs = {ip for cdn in file for asn in file[cdn] for ip in file[cdn][asn]}
    return offnetIPs

def checkOffnets(cdnCountryMap):
    countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]

    cdns=set()
    for country in cdnCountryMap:
        for cdn in cdnCountryMap[country]:
            cdns.add(cdn)
    print (cdns)
    # cdns=["Akamai",'CDN77', 'MicrosoftAzure','StackPath', 'Azion', 'Taobao', 'Level3', 'Tencent', 'BunnyCDN', 'Facebook', 'NGENIX', 'Yahoo', 'Medianova','Cloudfront', 'Google', 'EdgeCast', 'Fastly', 'Cloudflare']
    
    google_offnets=getOffnetIPs(json.load(open("data/google_off_net_candidates_2023_googlevideo.json")),"google")
    fbcdn_offnets=getOffnetIPs(json.load(open("data/facebook_fbcdn_offnet_ips_per_as.json")),"fbcdn")
    all_offnets=getOffnetIPs(json.load(open("data/off_net_candidates.json")),"all")

    offnetIPs=google_offnets | fbcdn_offnets | all_offnets

    for cdn in cdns:
        for country in countries:
            cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
            try:
                domains=set(cdnMap[cdn])
            except:
                continue
            if country=="AU":
                vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
            else:
                vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
            for vantage in vantagePoints:
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                ips=set()
                for domain in domains:
                    if domain in replicasPerVantage:
                        ips|=set(replicasPerVantage[domain])
                
    offnetIPsInOurMeasurements=ips&offnetIPs

    print (f"offnetIPsInOurMeasurements: {len(offnetIPsInOurMeasurements)}; total replica ips: {len(ips)}; combined offnets: {len(offnetIPs)}; google offnets: {len(google_offnets)},fbcdn offnets: {len(fbcdn_offnets)},all_offnets: {len(all_offnets)}")

def is_cacheable(headers):
    no_cache_keywords=['no-store','private','no-cache']
    cache_control = headers.get('Cache-Control', '')
    print ("cache-control: ",cache_control)
    for keyword in no_cache_keywords:
    # if 'no-store' in cache_control or 'private' in cache_control or 'no-cache' in cache_control:
        if keyword in cache_control:
            return False, keyword
    if 'max-age' in cache_control:
        return True, 'max-age'
    expires = headers.get('Expires')
    if expires:
        return True, 'expires'
    return False, 'Not Found'

def check_cache_status(url,cacheDict,timeout=30):
    try:
        response = requests.head(url,timeout=timeout)
        headers = response.headers
        cache_ans=is_cacheable(headers)

        print (url)
        if cache_ans[0]:
            print("The content is cacheable.",cache_ans[1])
            cacheDict[url]=cache_ans
        elif response.status_code == 304:
            cacheDict[url]=(True,'response_code_304')
            print("The content was retrieved from the cache. response.status_code==304")
        else:
            cacheDict[url]=cache_ans
            print("The content is not cacheable.",cache_ans[1])
        print("\n")
    except requests.exceptions.Timeout:
        print(f"Request to {url} timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def checkCacheableContent(cdnCountryMap):
    #modify to check for urls and not domains
    countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]

    cdns=set()
    for country in cdnCountryMap:
        for cdn in cdnCountryMap[country]:
            cdns.add(cdn)
    print (cdns)
    urls=set()
    for cdn in cdns:
        for country in countries:
            cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
            try:
                domains=set(cdnMap[cdn])
            except:
                continue
            if country=="AU":
                vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
            else:
                vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
            for vantage in vantagePoints:
                replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
                for domain in domains:
                    if domain in replicasPerVantage:
                        urls.add("https://"+domain)
    cacheDict={}
    print (f"len of urls: {len(urls)}")
    # urls = [
    #     "https://example.com",
    #     "https://youtube.com"
    # ]
    for url in list(urls):
        # try:
        check_cache_status(url,cacheDict)
        # except Exception as e:
            # print (str(e))
    
    # print (cacheDict)

        with open("results/cacheDict.json",'w') as fp:
            json.dump(cacheDict,fp,indent=4)

  



    


if __name__ == "__main__":
    cdnCountryMap={"BR":["Cloudflare","Google","Akamai","Cloudfront","Fastly","EdgeCast","Azion","CDN77"],
                    "GB":["Cloudflare","Google","Akamai","Cloudfront","Fastly","CDN77","EdgeCast"],
                    "ZA":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare'],
                    "CN":["Cloudflare","Google","Akamai","Cloudfront","Fastly","Tencent","CDN77","EdgeCast","Taobao"],
                    "AU":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare'],
                    "IN":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare','CDN77'],
                    "TR":['EdgeCast', 'CDN77', 'Medianova', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
                    "RU":['EdgeCast', 'CDN77', 'NGENIX', 'Cloudfront', 'Fastly', 'Akamai', 'Google', 'Cloudflare'],
                    "DE":['Cloudflare', 'Akamai', 'Google', 'Cloudfront', 'Fastly', 'CDN77', 'Yahoo', 'EdgeCast'],
                    "US":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare','Yahoo','CDN77'],
                    "ID":['EdgeCast', 'Taobao', 'CDN77', 'Facebook', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare',"Yahoo"],
                    "AE":['EdgeCast', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'], 
                    "FR":['StackPath', 'Level3', 'CDN77', 'EdgeCast', 'Fastly', 'Cloudfront', 'Google', 'Akamai', 'Cloudflare',"Yahoo"],
                    "AR":['EdgeCast', 'Facebook', 'BunnyCDN','CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare',"Yahoo"],
                    "NG":['EdgeCast','Facebook', 'MicrosoftAzure', 'Taobao', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
                    "EG":['EdgeCast','Facebook', 'MicrosoftAzure','Level3', 'Taobao', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
                    "ES":['EdgeCast', 'StackPath', 'CDN77', 'Cloudfront', 'Fastly', 'Google', 'Akamai', 'Cloudflare'], 
                    "GH":['Facebook', 'EdgeCast', 'StackPath', 'CDN77', 'Cloudfront', 'Fastly', 'Google', 'Akamai', 'Cloudflare',"Yahoo"],
                    "DZ":['EdgeCast','Facebook', 'CDN77', 'Cloudfront', 'Fastly', 'Akamai', 'Google', 'Cloudflare',"Yahoo"]
    }
    # sanityCheck()
    # validateResolverIPs()
    # exit()
    # checkManycast(cdnCountryMap)

    baselineExperiments(cdnCountryMap)
    # checkOffnets(cdnCountryMap)
    # checkCacheableContent(cdnCountryMap)

    

