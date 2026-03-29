import json
import ipinfo

#perform validation of the CDNFinder


def findHomeAllIPs(ips):
	try:
		result=json.load(open("results/allipshome.json")) 
	except:
		result={}
	access_token = 'd7bdbc30b9a97b'
	handler = ipinfo.getHandler(access_token)
	ans=handler.getBatchDetails(ips)

	for ip in ans:
		if ip in result:
			print (ip,"Shouldn't Happen")
		else:
			result[ip]=ans[ip]

	with open("results/allipshome.json", 'w') as fp:
		json.dump(result, fp)


def collectDomainIPs(country):
	result=json.load(open("results/allipshome.json")) 

	cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
	domaincdnMap={}

	for cdn in cdnMap:
		for domain in cdnMap[cdn]:
			domaincdnMap[domain]=cdn

	vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
	validationMap={}
	ipSet=set()
	orgNotFound=set()
	allIPs=set()
	cdnNameMap={"Cloudfront":"Amazon","EdgeCast":"Edgecast","MicrosoftAzure":"Microsoft",
	"CDN77":"AS60068","BunnyCDN":"AS200325","Level3":"AS3356"}
	for vantage in vantagePoints:
		replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json"))
		for domain in replicasPerVantage:
			if domain not in validationMap:
				cdn=domaincdnMap[domain]

				validationMap[domain]={}
				if cdn in cdnNameMap:
					cdn=cdnNameMap[cdn]

				validationMap[domain]["CDNFinderCDN"]=cdn
				validationMap[domain]["IPtoASN"]={}

			for replicaip in replicasPerVantage[domain]:
				allIPs.add(replicaip)
				if replicaip in result:
					try:
						validationMap[domain]["IPtoASN"][replicaip]=result[replicaip]["org"]
					except:
						# orgNotFound[domain]=validationMap[domain]["CDNFinderCDN"]
						orgNotFound.add(replicaip)
				else:
					ipSet.add(replicaip)
	# findHomeAllIPs(ipSet)
	print ("total number of IPs",len(allIPs))
	print ("IPs not stored: ",len(ipSet))
	print ("IPs don't have org listed: ",len(orgNotFound))

	print (orgNotFound)

	with open("results/"+country+"/IPtoASN.json", 'w') as fp:
		json.dump(validationMap, fp)
	
	mismatch={}
	for domain in validationMap:
		match=False
		for org in validationMap[domain]["IPtoASN"].values():
			if validationMap[domain]["CDNFinderCDN"] in org:
				match=True
				break
		if not match:
			mismatch[domain]=validationMap[domain]
	print ("No. of domains that have a mismatch: ",len(mismatch))
	print ("Total No. of domains: ",len(validationMap))

	with open("results/"+country+"/IPASN_CDNFinderMismatch.json", 'w') as fp:
		json.dump(mismatch, fp)


# collectDomainIPs("US")
def updatedDomainCDNMap(country):
	result=json.load(open("results/allipshome.json")) 

	cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
	domaincdnMap={}
	orgNotFound=set()


	for cdn in cdnMap:
		for domain in cdnMap[cdn]:
			domaincdnMap[domain]=cdn

	# vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
	cdnNameMap={"ONLINE S.A.S.","The Rubicon Project","UNITED PARCEL SERVICE","American Express Company","Index Exchange Inc","Level 3","Internet content provider","New Relic"}
	updatedDomainCDNMap={}
	replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_local.json"))
	for domain in replicasPerVantage:
		for replicaip in replicasPerVantage[domain]:
			try:
				org=result[replicaip]["org"].replace(",","")
				orgName=org.split(" ")[1]
				found=False
				for orgN in cdnNameMap:
					if orgName in orgN:
						org=orgN
						found=True
						break
				if not found:
					org=orgName
				if org not in updatedDomainCDNMap:
					updatedDomainCDNMap[org]=[]
				if domain not in updatedDomainCDNMap[org]:
					updatedDomainCDNMap[org].append(domain)
			except:
				orgNotFound.add(replicaip)


	with open("results/"+country+"/updatedDomainCDNMap.json", 'w') as fp:
		json.dump(updatedDomainCDNMap, fp)
	print (updatedDomainCDNMap.keys())

updatedDomainCDNMap("US")

#now that we have updated domain list. Plot the ping latencies of all IPs of all domains of a given CDN and see how the plot changes.


