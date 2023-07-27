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
import dns
import dns.resolver


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
			self.driver.get("https://"+site)
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
					# if resource not in self.resources[site]:
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

	def collectPopularCDNResources(self,country):
		unique=[]
		with open(join(project_path, "analysis", "measurements", country, "AlexaUniqueResources.txt"),"w") as f:
			for cdn in self.cdn_mapping:
				for domain in self.cdn_mapping[cdn]:
					for resource in self.resources_mapping:
						if domain in resource:
							if resource not in unique:
								f.write(resource+"\n")
								unique.append(resource)
							
			f.close()


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

def findRDNS(domain):
	ips=[]
	result = dns.resolver.query(domain, 'A')
	for ipval in result:
		ips.append(ipval.to_text())
	# print (ips)
	r_ips=[]
	for ip in ips:
		ip = str(ip).strip()
		n = dns.reversename.from_address(ip)
		r_ips.append(str(dns.resolver.query(n,"PTR")[0]))
	# print ("\n")
	# print("Domain: ",domain," ips: ",ips," r_ips: ",r_ips)
	return r_ips

def findCNAME(domain):
	cnames=[]
	answers = dns.resolver.query(domain, 'CNAME')
	for rdata in answers:
		cnames.append(str(rdata.target))
	print(domain," : ",cnames) 
	return cnames
# findCNAME("fastlane.rubiconproject.com")
def findCNAME_RDNS(country):
	domaincdnmapping=json.load(open("results/"+country+"/domaincdnmapping.json"))
	mapping={}
	for site in domaincdnmapping:
		mapping[site]={}
		for cdn in domaincdnmapping[site]:
			if cdn!="null":
				mapping[site][cdn]={}
				for domain in domaincdnmapping[site][cdn]:
					mapping[site][cdn][domain]={}
					try:
						mapping[site][cdn][domain]["rdns"]=findRDNS(domain)
					except Exception as e:
						mapping[site][cdn][domain]["rdns"]=[]
						print (domain, str(e))

					try:
						mapping[site][cdn][domain]["cname"]=findCNAME(domain)
					except Exception as e:
						mapping[site][cdn][domain]["cname"]=[]
						print (domain, str(e))
	with open(join("results/"+country+"/domain_cname_rdnscdnmapping.json"), 'w') as fp:
		json.dump(mapping, fp)






def CDNFinder(domains):
	cdndomainMap={}
	domaincdnMap={}
	TD=0
	for site in domains:
		TD+=len(domains[site])
	x=0
	for site in domains:
		domaincdnMap[site]={}
		for domain in domains[site]:
			print ("running cdnfinder for domain: ",domain," \% done: ",100*x/TD)
			x+=1
			if x%100==0:
				with open(join("results/"+country+"/cdn_mapping.json"), 'w') as fp:
					json.dump(cdndomainMap, fp)
				with open(join("results/"+country+"/domaincdnmapping.json"), 'w') as fp:
					json.dump(domaincdnMap, fp)
			try:
				cmd='docker run -it turbobytes/cdnfinder cdnfindercli --phantomjsbin="/bin/phantomjs" --full http://'+domain
				mycmd=subprocess.getoutput(cmd)
				# print (mycmd)
				dict_response=str(mycmd).split("phantomjs is already installed")[1]
				ans = json.loads(dict_response)
				for _dict in ans['everything']:
					try:
						cdn=_dict["cdn"]
						if cdn==None:
							continue
						print ("CDN: ",cdn)
						if cdn not in cdndomainMap:
							cdndomainMap[cdn]=[]
						if domain not in cdndomainMap[cdn]:
							cdndomainMap[cdn].append(domain)
						# if cdn!="null":
						if cdn not in domaincdnMap[site]:
							domaincdnMap[site][cdn]={}
						if domain not in domaincdnMap[site][cdn]:
							domaincdnMap[site][cdn][domain]={}
							try:
								cnames=_dict['cnames']
							except:
								cnames=[]
							domaincdnMap[site][cdn][domain]["cnames"]=cnames
							# domaincdnMap[site][cdn][domain]["rdns"]=findRDNS(domain)
							print ("Domain: ",domain," cnames: ",cnames," rdns: ",domaincdnMap[site][cdn][domain]["rdns"],"\n")

					except:
						continue
					
			except Exception as e:
				print (domain," gives error with cdnfindercli",str(e))
	with open(join("results/"+country+"/cdn_mapping.json"), 'w') as fp:
		json.dump(cdndomainMap, fp)
	with open(join("results/"+country+"/domaincdnmapping.json"), 'w') as fp:
		json.dump(domaincdnMap, fp)	
	

def findWebsites():
	headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5)',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'en-US,en;q=0.9,de;q=0.8'
    }
	r = requests.get('https://www.similarweb.com/top-websites/united-states/',headers=headers)
	bs = BeautifulSoup(r.content, "html.parser")
	table = bs.find("main", { "class" : "app-layout__main" })
	
	td = table.find_all("span", { "class" : "tw-table__row-domain" })
	websites=[]
	for x in td:
		websites.append(x.text)
	return websites
		

if __name__ == "__main__":
	if not os.path.exists("results"):
		os.mkdir("results")
	country="DE" #specify the client's two letter country code

	# top50Sites= findWebsites() #add the top 50 sites of the country of a client from similarweb rankings
	# with open(join("results/"+country+"/similarwebTop50.json"), 'w') as fp:
	# 	json.dump(top50Sites, fp)
	top500Websites=json.load(open("data/alexaTop500SitesCountries.json"))
	sites=top500Websites[country]

	if not os.path.exists("results/"+country):
		os.mkdir("results/"+country)

	# print ("Extracting Resources for country: ",country)
	# extractResources(country,sites)
	# print ("Resource Extraction Done")
	
	all_domains=json.load(open("results/"+country+"/ResourcesDomainsF.json"))
	CDNFinder(all_domains)

	# findCNAME_RDNS(country)
	

	








