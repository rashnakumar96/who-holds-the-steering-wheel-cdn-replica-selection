from selenium import webdriver
import json
from browsermobproxy import Server
from bs4 import BeautifulSoup
import os, time
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
from os.path import isfile, join
import tldextract
import subprocess
import dns.resolver
import requests
from lxml.html import fromstring
import findcdn
import operator
from tabulate import tabulate




project_path=os.path.dirname(os.path.abspath(__file__))

class Har_generator:
	def __init__(self):
		self.hars = {}
		self.server = Server(join(project_path, "browsermob-proxy-2.1.4", "bin", "browsermob-proxy"))
		self.server.start()
		self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
		options = webdriver.ChromeOptions()
		options.add_argument("--proxy-server={}".format(self.proxy.proxy))	
		options.add_argument("--ignore-ssl-errors=yes")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument("--headless")

		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)

	def __del__(self):
		self.server.stop()
		self.driver.quit()

	# loads up a site
	# takes a site url
	# returns a json har object
	def get_har(self, site):
		
		try:
			name = site
			self.proxy.new_har(name)
			#uncomment for Alexa
			# self.driver.get("https://"+site)
			self.driver.get(site)
			# time.sleep(1)
			return self.proxy.har
		except Exception as e:
			print(str(e))
			return None

		
	# calls get_har for each site
	# takes a list of site urls
	# returns a dictionary of site url and json har objects
	def get_hars(self, sites):
		x = 0
		hars = {}
		self.driver.set_page_load_timeout(20)
		for site in sites:

			print("%d: Working on %s" % (x, site))
			har = self.get_har(site)
			hars[site]=har
			self.hars[site]=har
			x = x + 1
		return hars

class Resource_collector:
	def __init__(self):
		self.resources = {}

	def dump(self,country):
		# utils.dump_json(self.resources, join(fn_prefix,"alexaResources"+country+".json"))
		with open(join("results/"+country+"/ResourcesF.json"), 'w') as fp:
			json.dump(self.resources, fp)

		# utils.dump_json(self.resources, join(project_path,fn_prefix,"alexaResources"+country+".json"))


	# extracts all the resources from each har object
	# takes a list of har json objects
	# stores in the object resources
	def collect_resources(self,hars,country):
		for site in hars:
			self.resources[site]=[]
			har=hars[site]
			if har and "log" in har.keys() and "entries" in har["log"].keys():
				for entry in har["log"]["entries"]:
					resource = entry["request"]["url"]
					if resource not in self.resources[site]:
						self.resources[site].append(str(resource))


class Url_processor:
	def __init__(self,country):
		self.cdn_mapping = {}
		# self.resources_mapping = utils.load_json(join(project_path, "analysis", "measurements", country, "alexaResources"+country+".json"))
		# self.domains=json.load(open("uniqueDomains"+country+".json"))

		self.options = webdriver.ChromeOptions()
		self.options.add_argument("--ignore-ssl-errors=yes")
		self.options.add_argument("--ignore-certificate-errors")
		# self.options.add_argument("--headless")
		self.country=country

		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=self.options)

	def __del__(self):
		self.driver.quit()

	def restart_drive(self):
		print("Restarting...")
		self.driver.quit()
		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=self.options)

	def dump(self, fn_prefix):
		utils.dump_json(self.cdn_mapping, join(fn_prefix,"PopularcdnMapping.json"))



	# Find cdn given a file of the resources
	# Takes a list of unique domains
	# Returns a dictionary containing the found CDNs for each domain
	def find_cdn(self,domains):
		i = 0
		self.driver.get("https://www.cdnplanet.com/tools/cdnfinder/")
		total = len(domains)
		for resource in domains:
			if i > 0 and i % 50 == 0:
				self.restart_drive()
				self.driver.get("https://www.cdnplanet.com/tools/cdnfinder/")

			print("%.2f%% completed" % (100 * i / total))

			for _ in range(3):
				try:
					self.driver.find_element_by_xpath("//*[@id=\"tool-form-main\"]").clear()
					self.driver.find_element_by_xpath("//*[@id=\"tool-form-main\"]").send_keys(resource)
					self.driver.find_element_by_xpath("//*[@id=\"hostname-or-url\"]").click()
					self.driver.find_element_by_xpath("//*[@id=\"tool-form\"]/button").click()
					time.sleep(3)

					doc = BeautifulSoup(self.driver.page_source, "html.parser")
					domain=doc.findAll('code', attrs={"class" : "simple"})
					cdn=doc.findAll('strong')
					site=domain[0].text
					cdn=cdn[0].text
					print (site,cdn)
					if cdn not in self.cdn_mapping:
						self.cdn_mapping[cdn]=[]
					self.cdn_mapping[cdn].append(resource)
					break

				except Exception as e:
					print("error: ",str(e))
					time.sleep(2)


			time.sleep(2)
			i += 1
		with open("results/"+self.country+"/cdn_mapping.json", 'w') as fp:
			json.dump(self.cdn_mapping, fp)   

	# def collectPopularCDNResources(self,country):
	# 	unique=[]
	# 	with open(join(project_path, "analysis", "measurements", country, "AlexaUniqueResources.txt"),"w") as f:
	# 		for cdn in self.cdn_mapping:
	# 			for domain in self.cdn_mapping[cdn]:
	# 				for resource in self.resources_mapping:
	# 					if domain in resource:
	# 						if resource not in unique:
	# 							f.write(resource+"\n")
	# 							unique.append(resource)
							
	# 		f.close()


def extractResources(country,sites):
	hm = Har_generator()
	rc = Resource_collector()

	hars = hm.get_hars(sites)
	rc.collect_resources(hars,country)
	rc.dump(country)
	del hm
	del rc

	resources=json.load(open("results/"+country+"/ResourcesF.json"))
	all_domains={}
	for site in resources:	
		all_domains[site]=[]
		for resource in resources[site]:
			domain=url_to_domain(resource)
			if 'www.' in domain:
				domain=domain.replace('www.','')
			if domain not in all_domains[site]:
				all_domains[site].append(domain)
	with open(join("results/"+country+"/ResourcesDomainsF.json"), 'w') as fp:
		json.dump(all_domains, fp)

def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == '':
        ext = ext[1:]
    return ".".join(ext)

def dump_json(data, fn):
    with open(fn, 'w') as fp:
        json.dump(data, fp)

def findcdnFunc(domains,country):
	for i in range(0,len(domains),100):
		start=i
		if i+100<len(domains):
			end=i+100
		else:
			end=len(domains)
		print("Running CDN Finder for domains in range: ",start,end)

		try:
			dumped_domaintoCDN=json.load(open("results/"+country+"/dumped_domaintoCDN_"+str(start)+".json"))
		except:
			counter=0
			while 1:
				counter+=1
				try:
					resp_json = findcdn.main(domains[start:end], output_path="results/"+country+"/dumped_domaintoCDN_"+str(start)+".json", double_in=True, threads=23)
					dumped_domaintoCDN = json.loads(resp_json)
					break
				except Exception as e:
					if counter>3:
						time.sleep(60)
						errorDomain=str(e)
						print (errorDomain[0])
						if errorDomain[0] in domains:
							domains.remove(errorDomain)
					print (str(e))
					# resp_json = findcdn.main(domains[start:end], output_path="results/"+country+"/dumped_domaintoCDN_"+str(start)+".json", double_in=True, threads=23)
					# dumped_domaintoCDN = json.loads(resp_json)
				# exit()
				# resp_json = findcdn.main(domains[start:end], output_path="results/"+country+"/dumped_domaintoCDN_"+str(start)+".json", double_in=True, threads=23)
				# dumped_domaintoCDN = json.loads(resp_json)				

	_dict={}
	for i in range(0,len(domains),100):
		dumped_domaintoCDN=json.load(open("results/"+country+"/dumped_domaintoCDN_"+str(i)+".json"))
		for domain in dumped_domaintoCDN["domains"]:
			if domain not in _dict:
				_dict[domain]=dumped_domaintoCDN["domains"][domain]
			else:
				try:
					if _dict[domain]['cdns_by_names']!=dumped_domaintoCDN["domains"][domain]['cdns_by_names']:
						print (domain,_dict[domain]['cdns_by_names'])
						_dict[domain]['cdns_by_names']+=","+dumped_domaintoCDN["domains"][domain]['cdns_by_names']
						print (domain,_dict[domain]['cdns_by_names'])

						# _dict[domain]['IP']+=dumped_domaintoCDN["domains"][domain]["IP"]
						# _dict[domain]['cdns']+=dumped_domaintoCDN["domains"][domain]['cdns']
						# _dict[domain]['cdns_by_names']+=dumped_domaintoCDN["domains"][domain]['cdns_by_names']
						# exit()
				except Exception as e:
					# print (str(e),_dict[domain]['IP'])
					print ("inconsistently repeating: ",domain,_dict[domain],dumped_domaintoCDN["domains"][domain],"\n")
	print (len(_dict))
	with open(join("results/"+country+"/dumped_domaintoCDN_all.json"), 'w') as fp:
		json.dump(_dict, fp)

	domaincdnMap={}
	cdndomainMap={}

	count=0
	ResourcesDomains=json.load(open("results/"+country+"/ResourcesDomainsF.json"))

	for website in ResourcesDomains:
		# print ("Running for website: ",website,100*count/len(ResourcesDomains))
		count+=1
		cdns=[]
		for domain in ResourcesDomains[website]:
			if domain in _dict:
				if website not in domaincdnMap:
					domaincdnMap[website]={}
				if domain not in domaincdnMap[website]:
					domaincdnMap[website][domain]={}
					domaincdnMap[website][domain]["cnames"]=[]
					domaincdnMap[website][domain]["cdns"]=[]
				totalCDNs=set()
				totalCNames=set()
				_cdns=_dict[domain]["cdns_by_names"]
				_cdns=_cdns.split(",")
				# print (_cdns)
				for cdn in _cdns:
					_cdn=cdn.strip()
					# print ("CDN Strip",_cdn)
					totalCDNs.add(_cdn.replace("'",""))
					if _cdn not in cdndomainMap:
						cdndomainMap[_cdn]=[]
					if domain not in cdndomainMap[_cdn]:
						cdndomainMap[_cdn].append(domain)

					cnames=_dict[domain]["cdns"]
					cnames=cnames.split(",")
					for cname in cnames:
						_cname=cname.strip()
						totalCNames.add(_cname.replace("'",""))
				# print ("TotalCDNS: ",totalCDNs)
				domaincdnMap[website][domain]["cnames"]=list(totalCNames)
				domaincdnMap[website][domain]["cdns"]=list(totalCDNs)
	_dict={}
	for cdn in cdndomainMap:
		_cdn=cdn.strip("'")
		_dict[_cdn]=cdndomainMap[cdn]

	with open(join("results/"+country+"/cdn_mapping.json"), 'w') as fp:
		json.dump(_dict, fp)
	with open(join("results/"+country+"/domaincdnmapping.json"), 'w') as fp:
		json.dump(domaincdnMap, fp)	
               
		
if __name__ == "__main__":
	if not os.path.exists("results"):
		os.mkdir("results")
	country="DE" #specify the client's two letter country code

	topWebsites=json.load(open("data/googleTop1000SitesCountries.json"))
	sites=topWebsites[country]

	if not os.path.exists("results/"+country):
		os.mkdir("results/"+country)

	print ("Extracting Resources for country: ",country)
	extractResources(country,sites)
	print ("Resource Extraction Done")
	
	siteResources=json.load(open("results/"+country+"/ResourcesDomainsF.json"))
	unique_resources=set()
	for site in siteResources:
		for res in siteResources[site]:
			unique_resources.add(res)
	
	print (len(unique_resources))
	findcdnFunc(list(unique_resources),country) #run this func for CDN analysis

	











