import time
import dns
import dns.resolver
import tldextract
import requests
from ripe.atlas.sagan import DnsResult
import random
import os
import json
from datetime import datetime
import pydig
import socket   
import subprocess
import shlex



def launchECSQueries(domains,distantSubnet,clientSubnet):
	
	ecsMap={}
	ind=0  
	# domains+=['ikea.com','tiktok.com']

	for domain in domains:
		print("%f: Done Running" % (100*ind/len(domains)),domain)

		ind+=1
		ecsMap[domain]={}
		try:
			answers = dns.resolver.query(domain,'NS')
		except Exception as e:
			print ("error in finding nameservers",domain,str(e))
			answers=[]
		nameservers=[]
		for server in answers:
			try:
				nameservers.append(str(server.target))
			except Exception as e:
				print ("error in finding server target",domain,server, str(e))
		print (nameservers)
		
		client_nsans=[]
		distant_nsans=[]

		client_googleans=[]
		distant_googleans=[]

		for x in range(3):
			for ns in nameservers:
				try:
					output_client = subprocess.check_output(["dig", "@"+ns, domain, "+subnet="+clientSubnet,"+short"],
		                                             timeout=15, input="", stderr=subprocess.STDOUT).decode("utf-8")
					client_nsans+=output_client.strip().split("\n")

					output_distant = subprocess.check_output(["dig", "@"+ns, domain, "+subnet="+distantSubnet,"+short"],
		                                             timeout=15, input="", stderr=subprocess.STDOUT).decode("utf-8")
					distant_nsans+=output_distant.strip().split("\n")

				except Exception as e:
					print (str(e))

			
			output_clientgoogle = subprocess.check_output(["dig", "@8.8.8.8", domain, "+subnet="+clientSubnet,"+short"],
	                                             timeout=15, input="", stderr=subprocess.STDOUT).decode("utf-8")
			client_googleans+=output_clientgoogle.strip().split("\n")

			output_distantgoogle= subprocess.check_output(["dig", "@8.8.8.8", domain, "+subnet="+distantSubnet,"+short"],
	                                             timeout=15, input="", stderr=subprocess.STDOUT).decode("utf-8")
			distant_googleans+=output_distantgoogle.strip().split("\n")

			
		print (domain," client_nsans: ",set(client_nsans)," client_googleans: ",client_googleans,"\n")
		print (domain," distant_nsans: ",set(distant_nsans)," distant_googleans ",distant_googleans,"\n")
		print ("\n\n")
	
		
		ecsMap[domain]["client_nsans"]=list(set(client_nsans))
		ecsMap[domain]["client_googleans"]=list(set(client_googleans))
		ecsMap[domain]["distant_nsans"]=list(set(distant_nsans))
		ecsMap[domain]["distant_googleans"]=list(set(distant_googleans))

		with open("results/ecsMap.json", 'w') as fp:
			json.dump(ecsMap, fp)

def runECS(domain,resolver):
	cmd='dig @'+resolver+' '+domain+' A +subnet='+clientSubnet
	proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)
	out,err=proc.communicate()
	_list=str(out).split(';')
	return _list

def ECSSupport(domains,distantSubnet,clientSubnet):
	try:
		ecsEnabled=json.load(open("results/ecsEnabled.json"))
		ecsEnabled=set(ecsEnabled)
	except:
		ecsEnabled=set()

	print ("TotalDomains: ",len(domains)," ecsEnabledSet: ",len(ecsEnabled))

	x=0
	# domains+=['ikea.com','tiktok.com']
	for domain in domains:
		# domain="tiktok.com"
		print("%f: Done Running" % (100*x/len(domains)),domain)
		x+=1
		if domain in ecsEnabled:
			continue
		ns=["8.8.8.8"]

		try:
			answers = dns.resolver.query(domain,'NS')
		except Exception as e:
			# print ("error in finding nameservers",domain,str(e))
			answers=[]
		
		for server in answers:
			try:
				ns.append(str(server.target))
			except Exception as e:
				# print ("error in finding server target",domain,server, str(e))
				continue

		# ns.append("8.8.8.8")
		# print (ns)
		breakCondition=False
		for resolver in ns: 
			_list=runECS(domain,resolver)
			for ele in  _list:
				if 'CLIENT-SUBNET:' in ele:
					scope=ele.split("CLIENT-SUBNET: ")[1][:-2].split('/')[2]
					if int(scope)>0:
						print (domain," scope: ",scope,ele,"\n")
						ecsEnabled.add(domain)
						breakCondition=True
						break
			if breakCondition:
				break

		if not breakCondition:
			try:
				_cnames = dns.resolver.query(domain,'CNAME')
			except:
				continue
				# _cnames=[]
			cnames=[]
			for cname in _cnames:
				cnames.append(cname.target)
			for cname in cnames:
				for resolver in ns: 
					_list=runECS(str(cname),resolver)
					for ele in  _list:
						if 'CLIENT-SUBNET:' in ele:
							scope=ele.split("CLIENT-SUBNET: ")[1][:-2].split('/')[2]
							if int(scope)>0:
								print (domain," CNAME: ",str(cname)," scope: ",scope,ele,"\n")
								ecsEnabled.add(domain)
								breakCondition=True
								break
					if breakCondition:
						break
				if breakCondition:
						break


	print ("TotalDomains: ",len(domains)," ecsEnabled: ",len(ecsEnabled))
	with open("results/ecsEnabled.json", 'w') as fp:
		json.dump(list(ecsEnabled), fp)

if __name__ == "__main__":

	cdnCountryMap={"BR":["Cloudflare","Google","Akamai","Cloudfront","Fastly","EdgeCast","Azion","CDN77"],
					"GB":["Cloudflare","Google","Akamai","Cloudfront","Fastly","CDN77","EdgeCast"],
					"ZA":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare'],
					"CN":["Cloudflare","Google","Akamai","Cloudfront","Fastly","Tencent","CDN77","EdgeCast","Taobao"],
					"AU":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare'],
					"IN":['EdgeCast','Cloudfront','Fastly','Akamai','Google','Cloudflare','CDN77'],
					"US":['EdgeCast','StackPath','Cloudfront','Fastly','Akamai','Google','Cloudflare','Highwinds','Yahoo','CDN77','Level3','Incapsula','MicrosoftAzure'],
					"ID":['EdgeCast', 'Taobao', 'CDN77', 'Facebook', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
					"AE":['EdgeCast', 'Yahoo', 'MicrosoftAzure', 'CDN77', 'Facebook', 'Highwinds', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
    				"FR":['Yahoo', 'StackPath', 'Level3', 'CDN77', 'EdgeCast', 'Fastly', 'Cloudfront', 'Google', 'Akamai', 'Cloudflare'],
				    "AR":['Yahoo', 'Azion', 'EdgeCast', 'Highwinds', 'Facebook', 'BunnyCDN', 'Telefonica', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare'],
				    "NG":['EdgeCast','Facebook', 'MicrosoftAzure', 'Taobao', 'CDN77', 'StackPath', 'Fastly', 'Cloudfront', 'Akamai', 'Google', 'Cloudflare']
	}
	clientSubnetCountryMap={"US":"149.112.112/24","IN":"203.201.60/24","AU":"103.108.92/24","GB":"62.100.211/24","BR":"185.89.250/24","ZA":"191.101.186/24"}
	distantSubnetCountryMap={"US":"203.201.60/24","IN":"149.112.112/24","AU":"149.112.112/24","GB":"149.112.112/24","BR":"203.201.60/24","ZA":"149.112.112/24"}
	# country="ZA"
	#Done: US,IN,AU,GB,BR,ZA
	
	countries=["ZA","AU","TR","RU","DE","GB","US","BR","IN","CN","ID","AE","FR","AR","NG"]
	
	fullDomainList=set()
	for country in countries:
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
		for cdn in cdnMap:
			domains=cdnMap[cdn]
			for domain in domains:
				fullDomainList.add(domain)

	print ("TotalDomains: ",len(fullDomainList))
	
	clientSubnet="149.112.112/24"
	distantSubnet="203.201.60/24"

	# launchECSQueries(list(fullDomainList),distantSubnet,clientSubnet)
	ECSSupport(list(fullDomainList),distantSubnet,clientSubnet)

	


#Run dig DNS command with ECS subnet of client location and with a distant location using ECS enabled resolver (8.8.8.8): 
#If CDN supports ECS we get different answers, otherwise we get the same answer with the two options
