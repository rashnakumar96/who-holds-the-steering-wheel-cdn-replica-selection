import json
import statistics
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import numpy as np
import tldextract
from scipy import stats
import scipy.stats
from scipy.stats import norm
from scipy.stats import gaussian_kde
from scipy.stats import wasserstein_distance
from scipy.spatial import distance
import numpy as np
import ipinfo
import pandas as pd
from tabulate import tabulate
import requests
import urllib.request
import certifi
import ssl
import sys
import ipaddress
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import FuncFormatter

def collectResults(cdns,vantagePoints,country,latencyResult,cdnMap):
	results={}
	cloudPrefixes,nativePrefixes,cloudfrontPrefixes=createPrefixlist()
	for cdn in cdns:
		# customerResults=customerSpecificVariation(cdn,cdnMap,vantagePoints,country,latencyResult)
		# badCustomersAcrossScopes,outlierBounds=boxplotdata(customerResults,cdn,country) #uncomment this to remove customers that are outliers
		# poorplatform=findServers(cdn,vantagePoints,country,latencyResult,cdnMap)


		results[cdn]={}
		domains=set(cdnMap[cdn])
		for vantage in vantagePoints:
			if vantage not in results[cdn]:
				results[cdn][vantage]=[]
			ips=[]
			replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 

			#uncomment this to remove customers that are outliers
			# lower_bound=outlierBounds[vantage][0]
			# upper_bound=outlierBounds[vantage][1]

			for domain in domains:
				tld=findtld(domain)

				# if cdn=="Google":
				# 	if tld in badCustomersAcrossScopes: #uncomment this to remove customers that are outliers
				# 		# print ("here")
				# 		continue
				if domain in replicasPerVantage:
					ips+=replicasPerVantage[domain]
			ips=list(set(ips))
			# zlatencies=[]
			for replicaip in ips:
				if cdn=="Google":
					# prefix=longest_matching_prefix(replicaip, nativePrefixes)
					prefix=longest_matching_prefix(replicaip, cloudPrefixes)

					if prefix!=None:
						if replicaip in latencyResult and len(latencyResult[replicaip])>0:
							latency=statistics.mean(latencyResult[replicaip])
							results[cdn][vantage].append(latency)
				if cdn=="Cloudfront":
					prefix=longest_matching_prefix(replicaip, cloudfrontPrefixes)
					if prefix!=None:
						if replicaip in latencyResult and len(latencyResult[replicaip])>0:
							latency=statistics.mean(latencyResult[replicaip])
							results[cdn][vantage].append(latency)        		
				else:
					if replicaip in latencyResult and len(latencyResult[replicaip])>0:
						latency=statistics.mean(latencyResult[replicaip])
						results[cdn][vantage].append(latency)

					# zlatencies=latencyResult[replicaip]
					# if latency<=lower_bound or latency>=upper_bound:
					# 	continue
					# results[cdn][vantage]+=zlatencies

			# z = np.abs(stats.zscore(zlatencies))
			# threshold = 3
			# not_outliers=np.where(z > 3)
			# results[cdn][vantage]=[ele for idx, ele in enumerate(zlatencies) if idx not in not_outliers[0]]
			
			print (cdn,vantage,len(results[cdn][vantage]))
		print ("\n\n")
	with open("results/"+country+"/"+"RTTs.json", 'w') as fp:
		json.dump(results, fp)
	return results

def compareEdgioAusIPs():
	country="AU"
	replicasPerVantageLocal=json.load(open("results/"+country+"/dnsRipeResult_local.json")) 
	replicasPerVantageNeighR=json.load(open("results/"+country+"/dnsRipeResult_neighboring_region.json")) 
	cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
	totalDomains=0
	commonDomains=0
	# localIPs=set()
	# neighRIPs=set()
	for domain in cdnMap["EdgeCast"]:
		# for domain in replicasPerVantageLocal[domain]:
		# 	for replicaip in 

		if domain in replicasPerVantageLocal and domain in replicasPerVantageNeighR:
			local=set(replicasPerVantageLocal[domain])
			neighR=set(replicasPerVantageNeighR[domain])

			commonIps=local.intersection(neighR)
			print (domain,local,neighR,commonIps)
			if len(commonIps)>0:
				commonDomains+=1
			totalDomains+=1

	print (commonDomains,totalDomains)



def cdnThreshold(countries):

	for country in countries:
		cdnThresholdMap={}
		domaincdnMap={}
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))

		for cdn in cdnMap:
			for domain in cdnMap[cdn]:
				domaincdnMap[domain]=cdn

		if country=="AU":
			vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		else:
			vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
		total=set()
		rttCount={}
		latencyMap=json.load(open("results/"+country+"/PingRipeResult.json"))
		_sum=0
		for vantage in vantagePoints:
			replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json"))

			for domain in replicasPerVantage:
				cdn=domaincdnMap[domain]
				# for cdn in cdns:
				if cdn not in cdnThresholdMap:
					cdnThresholdMap[cdn]=set()
				if cdn not in rttCount:
					rttCount[cdn]=0
				for replicaip in replicasPerVantage[domain]:
					cdnThresholdMap[cdn].add(replicaip)
					total.add(replicaip)
					if replicaip in latencyMap:
						rttCount[cdn]+=len(latencyMap[replicaip])
						_sum+=len(latencyMap[replicaip])

		countDict={}
		for cdn in cdnThresholdMap:
			if cdn=="Amazon AWS":
				continue
			countDict[cdn]=round((100*len(cdnThresholdMap[cdn])/len(total)),2)
		sortedcdnCount=dict(sorted(countDict.items(), key=lambda item: item[1]))
		# print (country,sortedcdnCount,"\n")

		countDict={}
		for cdn in rttCount:
			if cdn=="Amazon AWS":
				continue
			countDict[cdn]=round((100*rttCount[cdn]/_sum),2)
		sortedcdnCount=dict(sorted(countDict.items(), key=lambda item: item[1]))
		print (country,sortedcdnCount,"\n")


def find_close_values(element, value, tolerance):
	if abs(element - value) <= tolerance:
		return True
	return False

def findServers(cdn,vantagePoints,country,latencyResult,cdnMap):
	# results={}
	print ("Total Number of Servers of CDN: ",cdn)
	domains=set(cdnMap[cdn])
	poorplatform={}
	customerResults=customerSpecificVariation(cdn,cdnMap,vantagePoints,country,latencyResult)
	replicasLocal=json.load(open("results/"+country+"/dnsRipeResult_local.json")) 
	ips=[]
	for domain in domains:
		if domain in replicasLocal:
			ips+=replicasLocal[domain]	
	ips=list(set(ips))
	latencies=[]
	for replicaip in ips:
		if replicaip in latencyResult:
			latencies+=latencyResult[replicaip]
	median_local=statistics.median(latencies)
	print ("median_local",median_local)

	for vantage in vantagePoints:
		close={}
		distant={}

		mapping={}
		if vantage=="local":
			continue
		ips=[]
		replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
		ips_vantage=[]
		for domain in domains:
			if domain in replicasPerVantage:
				ips_vantage+=replicasPerVantage[domain]
		ips_vantage=list(set(ips_vantage))
		latencies=[]
		for replicaip in ips_vantage:
			if replicaip in latencyResult:
				latencies+=latencyResult[replicaip]
		median_vantage=statistics.median(latencies)
		print ("median_",vantage," : ",median_vantage," median_local: ",median_local)
		if find_close_values(median_vantage, median_local, 5):
			poorplatform[vantage]=[]
			continue


		for domain in domains:
			if domain not in replicasPerVantage:
				continue
			ips+=replicasPerVantage[domain]
			tld=findtld(domain)
			if tld not in mapping:
				mapping[tld]={}
			if domain not in mapping[tld]:
				mapping[tld][domain]={}
			for server in set(replicasPerVantage[domain]):
				if server not in mapping[tld][domain]:
					mapping[tld][domain][server]={}
				if len(latencyResult[server])>0:
					mapping[tld][domain][server]=latencyResult[server][0]
					if find_close_values(mapping[tld][domain][server], median_local, 5):
						if tld not in close:
							close[tld]=set()
						close[tld].add(server)
					else:
						if tld not in distant:
							distant[tld]=set()
						distant[tld].add(server)

		overlapping=set()
		for customer in close:
			if customer in distant:
				overlapping.add(customer)

		close_no=[]
		distant_no=[]
		close_servers=[]
		for tld in close:
			close_no.append(len(close[tld]))
			close_servers+=[server for server in close[tld]]

		for tld in distant:
			distant_no.append(len(distant[tld]))

		ips=list(set(ips))
		print (vantage," : ",len(ips))
		# print ("close   ",sum(close_no),statistics.mean(close_no),statistics.median(close_no),statistics.stdev(close_no))
		# print ("distant   ",sum(distant_no),statistics.mean(distant_no),statistics.median(distant_no),statistics.stdev(distant_no))
		print ("\n")
		poorplatform[vantage]=list(set(close_servers))
	print ("\n\n")
	return poorplatform




def findtld(website):
    return tldextract.extract(website).domain

def customerSpecificVariation(cdn,cdnMap,vantagePoints,country,latencyResult):
	domains=set(cdnMap[cdn])
	customers={}
	for domain in domains:
		tld=findtld(domain)
		if tld not in customers:
			customers[tld]=[]
		customers[tld].append(domain)
	# print (customers)
	# for tld in customers:
	# 	if len(tld)>1:
	# 		print (tld,len(tld))

	results={}
	for tld in customers:
		for vantage in vantagePoints:
			if vantage not in results:
				results[vantage]={}
			if tld not in results[vantage]:
				results[vantage][tld]=[]
			ips=[]
			replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json"))
			for domain in customers[tld]:
				if domain in replicasPerVantage:
					ips+=replicasPerVantage[domain]
			ips=list(set(ips))
			for replicaip in ips:
				if replicaip in latencyResult and len(latencyResult[replicaip])>0:
					latency=statistics.median(latencyResult[replicaip])
					results[vantage][tld].append(latency)

	# print (results["local"])
	latencyThreshold={"Google":{"GB":10,"BR":20,"ZA":100,"CN":40,"AU":10,"IN":10},"Fastly":{"GB":10,"BR":40,"ZA":10,"CN":6,"AU":20,"IN":10}}
	resolverScope={}
	localized=set()
	non_localized=set()
	for vantage in vantagePoints:
		resolverScope[vantage]=set()
		for tld in results[vantage]:
			if len(results[vantage][tld])>1:
				latency=statistics.median(results[vantage][tld])
			elif len(results[vantage][tld])>0:
				latency=results[vantage][tld][0]
			else:
				continue
			if cdn=="Google" or cdn=="Fastly":
				if country in latencyThreshold[cdn]:
					if latency>latencyThreshold[cdn][country]:
						resolverScope[vantage].add(tld)
						localized.add(tld)
					else:
						if vantage!="local":
							non_localized.add(tld)

		# if cdn=="Google":
		# 	print (country," : ",vantage," : ",resolverScope[vantage],"\n")

		with open("results/"+country+"/"+cdn+vantage+"_perCustomerLatency.json", 'w') as fp:
			json.dump(results[vantage], fp)
	if cdn=="Google" or cdn=="Fastly":
		# lowLatencyCustomers=set.intersection(*[resolverScope[vantage] for vantage in resolverScope])
		# print (country," : ",lowLatencyCustomers,"\n")
		localized_and_nonlocalized=localized.intersection(non_localized)
		print ("Localized: ",len(localized),"Non-Localized: ",len(non_localized),"Localized and non_localized: ",len(localized_and_nonlocalized))
		for tld in localized_and_nonlocalized:
			localized.remove(tld)
			non_localized.remove(tld)

		print (country,cdn,"Localized: ",localized,"\n Non-Localized: ",non_localized)



	return results,localized,non_localized

def compute_js(x0, x1, b=10):

    bins = np.linspace(min(min(x0), min(x1)), max(max(x0), max(x1)), b)
    
    h0 = np.histogram(x0, bins=bins, density=True)[0]
    h1 = np.histogram(x1, bins=bins, density=True)[0]

    return distance.jensenshannon(h0, h1)


def Kolmogorov_SmirnovTest(data1,data2):
	from scipy.stats import ks_2samp
	statistic, p_value = ks_2samp(data1, data2)

	return statistic,p_value


def plotkde(data,country,cdn,vantage,maxRTT,N):
	import numpy as np
	from scipy.stats import gaussian_kde

	# Example data
	data = np.array(data)

	# Compute the kernel density estimate
	kde = gaussian_kde(data, weights=uniform_weights)

	# Evaluate the KDE at a set of points
	x = np.linspace(0,maxRTT,N)
	y = kde(x)
	return y
	# Plot the data and the KDE
	# import matplotlib.pyplot as plt
	# plt.clf()
	# if not os.path.exists("graphs/"+country+"/kde"):
	# 	os.mkdir("graphs/"+country+"/kde")

	# plt.hist(data, density=True, alpha=0.5)
	# plt.plot(x, y, '-r')
	# plt.savefig("graphs/"+country+"/kde/"+cdn+"_"+vantage+"_kde")

def ecdf(data):
    """ Compute ECDF """
    x = np.sort(data)
    n = x.size
    y = np.arange(1, n + 1) / float(n)
    return(x, y)


def plotrttCDFsMixedApproach(country,results,resolver_dict,vantagePoints,cdn):
	if not os.path.exists("graphs"):
		os.mkdir("graphs")
	if not os.path.exists("graphs/"+country):
		os.mkdir("graphs/"+country)
	from scipy.stats import norm
	
	
	pdfs={}
	countDict={}
	print ("country: ",country,cdn)
	pdfs[cdn]={}
	countDict[cdn]=[]
	_maxLocal=statistics.median(results[cdn]["local"])
	anycastcustomer={}
	non_anycastcustomer={}

	for resolverVantage in results[cdn]:
		rtts = results[cdn][resolverVantage]

		anycastcustomer[resolverVantage]=[]
		non_anycastcustomer[resolverVantage]=[]

		for rtt in rtts:
			# print (_maxLocal,rtt)

			if float(rtt) > (_maxLocal+5):
				non_anycastcustomer[resolverVantage].append(rtt)
			else:
				anycastcustomer[resolverVantage].append(rtt)

	non_anycastcustomer["local"]=results[cdn]["local"]
	if country=="RU":
		non_anycastcustomer["diff_metro"]=results[cdn]["diff_metro"]

	def plotDiffCustomers(customer,resolver_dict,cdn,country,customerType):
		# colors={'local':'purple','diff_metro':'r','same_region':'green','neighboring_subregion':'orange','neighboring_region':'brown','non-neighboring_region':'blue'}
		colors={'local':'purple','diff_metro':'r','same_region':'green','neighboring_subregion':'brown','neighboring_region':'brown','non-neighboring_region':'blue'}
		resolverVantages=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		ind=0
		countries_subst=["US","BR","AR"]
		plt.figure(figsize=(11, 6))

		label_mapping = {
			'local': 'Local',
			'diff_metro': 'Different Metro',
			'same_region': 'Same Region',
			'neighboring_subregion': 'Neighboring Region',
			'neighboring_region': 'Neighboring Region',
			'non-neighboring_region': 'Non-Neighboring Region'
		}

		for resolverVantage in resolverVantages:
			if country in countries_subst and resolverVantage=="neighboring_region":
				resolverVantage="neighboring_subregion"
				location=resolver_dict[country][resolverVantage].split("(")[1]
				region="neigh_region("
				resolver_dict[country][resolverVantage]=region+location
			rtts=customer[resolverVantage]
			x, y = ecdf(rtts)
			rtts=np.sort(rtts)

			if resolverVantage in resolver_dict[country]:
				original_label = resolver_dict[country][resolverVantage]
				# location = original_label.split('(')[1].rstrip(')')
				formatted_label = f"{label_mapping[resolverVantage]}"
			try:
				p10 = np.percentile(rtts, 20)
				p70 = np.percentile(rtts, 70)

				new_x = np.linspace(p10, p70, 100)

				yvals = np.arange(len(rtts)) / float(len(rtts))
				idx = np.where((rtts >= p10) & (rtts <= p70))
				
				rtts=np.array(rtts)
				plt.scatter(rtts[idx], yvals[idx],color=colors[resolverVantage],label=formatted_label,linestyle="solid",linewidth=2)
			except:
				plt.scatter(x,y,color=colors[resolverVantage],label=formatted_label,linestyle="solid",linewidth=2)
			ind+=1
		if cdn=="EdgeCast":
			cdn="Edgio"
		# plt.xscale('log')
		

		legend=plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=True)
		handles, _ = plt.gca().get_legend_handles_labels()  # get from current Axes
		legend = plt.legend(
			handles,
			["Local", "Diff Metro", "Same Reg", "Neigh Reg", "Non-Neigh"],
			loc='center right',          # anchor the right side of legend box
			bbox_to_anchor=(-0.08, 0.2), # move outside: x negative = further left, y=0.5 = vertical center
			ncol=1,
			frameon=True
		)

		legend.get_frame().set_linewidth(1.5)
		legend.get_frame().set_edgecolor('black')
		legend.get_frame().set_facecolor('white')

		for text in legend.get_texts():
			text.set_fontweight('bold')
			text.set_fontsize(20)

		

		# Make x and y ticks bold using a direct loop
		# ax = plt.gca()  # Get the current axis
		# ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2f}'))
		# for label in ax.get_xticklabels() + ax.get_yticklabels():
		# 	label.set_fontweight('bold')

		# Set bold labels for x and y axes
		# plt.xlabel('RTT [ms]', fontweight='bold')
		# plt.ylabel('CDF', fontweight='bold')


		y_min = 0.2
		y_max = 0.7
		padding = 0.02  # Adjust padding as needed
		plt.ylim(y_min - padding, y_max + padding)

		plt.xlabel('RTT [ms]',fontsize=14, fontweight='bold')
		plt.ylabel('CDF',fontsize=14, fontweight='bold')
		# plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
		ax = plt.gca()  # Get the current axis
		for label in ax.get_xticklabels():  # Adjust x-axis tick labels
			label.set_fontweight('bold')
			label.set_fontsize(14)  # Set the font size
			label.set_color('0.2')  # Set the color to a dark gray

		for label in ax.get_yticklabels():  # Adjust y-axis tick labels
			label.set_fontweight('bold')
			label.set_fontsize(14)  # Set the font size
			label.set_color('0.2')  # Set the color to a dark gray

		# Customize the borders of the figure
		plt.gca().spines['top'].set_linewidth(1.5)
		plt.gca().spines['right'].set_linewidth(1.5)
		plt.gca().spines['left'].set_linewidth(1.5)
		plt.gca().spines['bottom'].set_linewidth(1.5)

		plt.gca().spines['top'].set_edgecolor('black')
		plt.gca().spines['right'].set_edgecolor('black')
		plt.gca().spines['left'].set_edgecolor('black')
		plt.gca().spines['bottom'].set_edgecolor('black')
		plt.grid()
		plt.tight_layout(rect=[0, 0, 1, 0.95])
		# plt.savefig("graphs/"+country+"/"+cdn+"_"+customerType)

		# legend=plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=True,fontsize=14,title_fontsize='x-large')

		
		
		if country=="GB":
			plt.savefig("graphs/"+country+"/"+cdn+"_"+customerType+"_UK.pdf",dpi=300, format='pdf')
		else:
			plt.savefig("graphs/"+country+"/"+cdn+"_"+customerType+"_"+country+".pdf",dpi=300, format='pdf')
		plt.clf()

	def computeMixedKS(cdn,customer,country,customerType):
		CRVs=["same_region","non-neighboring_region"]
		for CRV in CRVs:
			try:
				ks_dist=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(customer["local"],20,70),MiddlePercentileRTTs(customer[CRV],20,70))
			except:
				ks_dist=Kolmogorov_SmirnovTest(customer["local"],customer[CRV])
			print ("CRV: ",customerType,CRV,ks_dist[0])
		# distance_dict[cdn][country][vantage_i+"+"+vantage_j]=ks_dist[0]

	plotDiffCustomers(anycastcustomer,resolver_dict,cdn,country,"Anycast")
	plotDiffCustomers(non_anycastcustomer,resolver_dict,cdn,country,"Non-Anycast")

	computeMixedKS(cdn,anycastcustomer,country,"Anycast")
	computeMixedKS(cdn,non_anycastcustomer,country,"Non-Anycast")

	print (country)
	anycastcustomerLen=[]
	non_anycastcustomerLen=[]
	# total=[]
	for resolverVantage in anycastcustomer:
		if resolverVantage=="local" or resolverVantage=="diff_metro":
			continue
		anycastcustomerLen.append(len(anycastcustomer[resolverVantage]))
		non_anycastcustomerLen.append(len(non_anycastcustomer[resolverVantage]))

	print (anycastcustomerLen,non_anycastcustomerLen)
	anycastTotal=statistics.median(anycastcustomerLen)
	non_anycastTotal=statistics.median(non_anycastcustomerLen)
	print ("NS-based",100*non_anycastTotal/(anycastTotal+non_anycastTotal))
	print ("anycastcustomer",100*anycastTotal/(anycastTotal+non_anycastTotal))
	print ("\n")

def plotrttCDFs(country,results,resolver_dict,vantagePoints):
	if not os.path.exists("graphs"):
		os.mkdir("graphs")
	if not os.path.exists("graphs/"+country):
		os.mkdir("graphs/"+country)
	from scipy.stats import norm
	
	countries_subst=["US","BR","AR"]
	
	colors={'local':'purple','diff_metro':'r','same_region':'green','neighboring_subregion':'brown','neighboring_region':'brown','non-neighboring_region':'blue'}
	resolverVantages=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
	pdfs={}
	countDict={}
	# plt.figure(figsize=(11, 6))
	fig, ax = plt.subplots(figsize=(11,6))   # identical size for all


	label_mapping = {
		'local': 'Local',
		'diff_metro': 'Different Metro',
		'same_region': 'Same Region',
		'neighboring_subregion': 'Neighboring Region',
		'neighboring_region': 'Neighboring Region',
		'non-neighboring_region': 'Non-Neighboring Region'
	}

	for cdn in results:
		print ("country: ",country,cdn)
		ind=0
		pdfs[cdn]={}
		countDict[cdn]=[]
		for resolverVantage in resolverVantages:
			if country in countries_subst and resolverVantage=="neighboring_region":
				resolverVantage="neighboring_subregion"
				location=resolver_dict[country][resolverVantage].split("(")[1]
				region="neigh_region("
				print (region,location)
				resolver_dict[country][resolverVantage]=region+location
			rtts = results[cdn][resolverVantage]
			x, y = ecdf(rtts)

			rtts=np.sort(rtts)

			
			countDict[cdn].append(len(rtts))
			if resolverVantage in resolver_dict[country]:
				original_label = resolver_dict[country][resolverVantage]
				location = original_label.split('(')[1].rstrip(')')
				# formatted_label = f"{label_mapping[resolverVantage]} - {location}"
				formatted_label = f"{label_mapping[resolverVantage]}"


			try:
				p10 = np.percentile(rtts, 20)
				p70 = np.percentile(rtts, 70)

				new_x = np.linspace(p10, p70, 100)

				yvals = np.arange(len(rtts)) / float(len(rtts))
				idx = np.where((rtts >= p10) & (rtts <= p70))
				
				rtts=np.array(rtts)
				plt.scatter(rtts[idx], yvals[idx],color=colors[resolverVantage],label=formatted_label,linestyle="solid",linewidth=2)
			except:
				plt.scatter(x,y,color=colors[resolverVantage],label=formatted_label,linestyle="solid",linewidth=2)

			ind+=1
		if cdn=="EdgeCast":
			cdn="Edgio"
		# if cdn!="Cloudflare":
		

		legend=plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=True)


		handles, _ = plt.gca().get_legend_handles_labels()  # get from current Axes
		legend = plt.legend(
			handles,
			["Local", "Diff Metro", "Same Reg", "Neigh Reg", "Non-Neigh"],
			loc='center right',          # anchor the right side of legend box
			bbox_to_anchor=(-0.08, 0.2), # move outside: x negative = further left, y=0.5 = vertical center
			ncol=1,
			frameon=True
		)

		legend.get_frame().set_linewidth(1.5)
		legend.get_frame().set_edgecolor('black')
		legend.get_frame().set_facecolor('white')

		for text in legend.get_texts():
			text.set_fontweight('bold')
			text.set_fontsize(20)


		
		# plt.xscale('log')


		y_min = 0.2
		y_max = 0.7
		padding = 0.02  # Adjust padding as needed
		plt.ylim(y_min - padding, y_max + padding)

		# Customize the borders of the figure
		plt.gca().spines['top'].set_linewidth(1.5)
		plt.gca().spines['right'].set_linewidth(1.5)
		plt.gca().spines['left'].set_linewidth(1.5)
		plt.gca().spines['bottom'].set_linewidth(1.5)

		plt.gca().spines['top'].set_edgecolor('black')
		plt.gca().spines['right'].set_edgecolor('black')
		plt.gca().spines['left'].set_edgecolor('black')
		plt.gca().spines['bottom'].set_edgecolor('black')
		plt.grid()
	
			 
		# Set bold labels for x and y axes
		# legend=plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=True,fontsize=14,title_fontsize='x-large')

		plt.xlabel('RTT [ms]',fontsize=14, fontweight='bold')
		plt.ylabel('CDF',fontsize=14, fontweight='bold')
		
		plt.tight_layout(rect=[0, 0, 1, 0.95])
		
		if country=="GB":
			plt.savefig("graphs/"+country+"/"+cdn+"_UK.pdf",dpi=300, format='pdf')
		else:
			plt.savefig("graphs/"+country+"/"+cdn+"_"+country+".pdf",dpi=300, format='pdf')
		plt.clf()

# def plotrttCDFs(country,results,resolver_dict,vantagePoints):
# 	if not os.path.exists("graphs"):
# 		os.mkdir("graphs")
# 	if not os.path.exists("graphs/"+country):
# 		os.mkdir("graphs/"+country)
# 	from scipy.stats import norm
	
	
# 	colors={'local':'purple','diff_metro':'r','same_region':'green','neighboring_subregion':'orange','neighboring_region':'brown','non-neighboring_region':'blue'}
# 	pdfs={}
# 	countDict={}
# 	for cdn in results:
# 		print ("country: ",country,cdn)
# 		ind=0
# 		pdfs[cdn]={}
# 		countDict[cdn]=[]
# 		for resolverVantage in results[cdn]:
# 			rtts = results[cdn][resolverVantage]
# 			x, y = ecdf(rtts)

# 			rtts=np.sort(rtts)

			
# 			countDict[cdn].append(len(rtts))

# 			try:
# 				p10 = np.percentile(rtts, 20)
# 				p70 = np.percentile(rtts, 70)

# 				# # Define a new range of x-values that correspond to the 20th to 80th percentile range
# 				new_x = np.linspace(p10, p70, 100)

# 				# # Find the indices of the y-values that correspond to the new range of x-values
# 				yvals = np.arange(len(rtts)) / float(len(rtts))
# 				idx = np.where((rtts >= p10) & (rtts <= p70))
# 				# print (idx)
# 				# data = np.random.normal(loc=0, scale=1, size=1000)
# 				# print ("data: ",data)
# 				# print ("rtts: ",rtts,len(rtts),len(idx))
# 				rtts=np.array(rtts)
# 				# Plot only the portion of the CDF that corresponds to the new range of x-values and y-values
# 				plt.scatter(rtts[idx], yvals[idx],color=colors[resolverVantage],label=resolver_dict[country][resolverVantage],linestyle="solid")
# 			except:
# 				plt.scatter(x,y,color=colors[resolverVantage],label=resolver_dict[country][resolverVantage],linestyle="solid")



# 			# print ("slope: ",resolverVantage," = ",slope)
# 			# plt.scatter(x,y,color=colors[ind],label=resolver_dict[country][resolverVantage],linestyle="solid")
# 			ind+=1
# 		if cdn=="EdgeCast":
# 			cdn="Edgio"
# 		plt.xscale('log')
# 		plt.legend()

# 		plt.xlabel('RTT [ms]')
# 		plt.ylabel(cdn+"_"+country)
# 		plt.grid()
# 		plt.savefig("graphs/"+country+"/"+cdn)
# 		plt.clf()

def MiddlePercentileRTTs(rtts,lower_bound,upper_bound):
	rtts=np.sort(rtts)
	p10 = np.percentile(rtts, lower_bound)
	p70 = np.percentile(rtts, upper_bound)

	# # Find the indices of the y-values that correspond to the new range of x-values
	idx = np.where((rtts >= p10) & (rtts <= p70))

	rtts=np.array(rtts)
	return rtts[idx]

def createResourcesCDNMapping(country):
	resources=json.load(open("results/"+country+"/ResourcesF.json"))
	cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
	domaincdnMap=json.load(open("results/"+country+"/domaincdnmapping.json"))

	cdnResourcesMap={}

	all_domains={}
	ind=0
	for site in resources:	
		print (100*ind/len(resources)," sites done running")
		ind+=1
		# all_domains[site]=[]
		for resource in resources[site]:
			domain=url_to_domain(resource)
			if 'www.' in domain:
				domain=domain.replace('www.','')
			try:
				cdns=domaincdnMap[site][domain]['cdns']
			except:
				continue
			for cdn in cdns:
				if cdn not in cdnResourcesMap:
					cdnResourcesMap[cdn]=set()
				cdnResourcesMap[cdn].add(resource)
			# if domain not in all_domains[site]:
			# 	all_domains[site].append(domain)
	for cdn in cdnResourcesMap:
		cdnResourcesMap[cdn]=list(cdnResourcesMap[cdn])
	with open("results/"+country+"/ResourcescdnMapping.json", 'w') as fp:
		json.dump(cdnResourcesMap, fp)
	return cdnResourcesMap

def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == '':
        ext = ext[1:]
    return ".".join(ext)

def contentSizeType(countries):
	#create a map of all resources to it's cdn and store that.
	#use that to find the % of resources that each cdn sees on top sites and the content type and length.
	# resources=["https://www.leasingmarkt.de/res/v3/css/app.css?id=33e7a51c78bdac4af4bc","https://www.ksta.de/_nuxt/entry.9ca99ca7.js"]
	# for resource in resources:
	# 	info=requests.head(resource)
		
	# 	try:
	# 		fileLength=info.headers['Content-Length']
	# 	except:
	# 		resp = requests.get(resource) #Getting the site
	# 		fileLength=len(resp.content)
	# 	fileType=info.headers['Content-Type']
	# 	print (resource,"Length: ",fileLength,"Type: ",fileType)
	# exit()

		
	for country in countries:
		print ("Running for country: ",country)
		
		try:
			cdnResourcesMap=json.load(open("results/"+country+"/ResourcescdnMapping.json"))
			print ("CDN Resource Map exsits for the country: ",country)
		except:
			cdnResourcesMap=createResourcesCDNMapping(country)
			print ("Done collecting cdnResource Map for country: ",country)

		ind=0
		for cdn in cdnResourcesMap:
			if country=="GH" and cdn=="Rackspace":
				continue
			try:
				sizeTypeMap=json.load(open("results/"+country+"/resourcesSizeType_"+cdn+".json"))
			# print ("resourcesSizeTypeMap exists for the country: ",country)
			# continue
			except:
				sizeTypeMap={}
			print (100*ind/len(cdnResourcesMap)," CDNs done running")
			ind+=1
			indR=0
			if cdn not in sizeTypeMap:
				sizeTypeMap[cdn]={}
			print (country,"CDN: ",cdn," no. of resources: ",len(cdnResourcesMap[cdn]))
			for resource in cdnResourcesMap[cdn]:
				# print (indR)
				indR+=1
				if resource in sizeTypeMap[cdn]:
					# print ("resource found: ",indR)
					continue
				if indR%100==0 and indR>0:
					print (100*indR/len(cdnResourcesMap[cdn])," resources done running")
					# print ("check")
					with open("results/"+country+"/resourcesSizeType_"+cdn+".json", 'w') as fp:
						json.dump(sizeTypeMap, fp)
					# print ("check2")

				
				sizeTypeMap[cdn][resource]={}
				fileType="unknown"
				try:
					info=requests.head(resource,timeout=20)
					try:
						fileType=info.headers['Content-Type']
					except:
						fileType="unknown"
					fileLength=info.headers['Content-Length']
					# print ("try: ",fileLength,fileType,resource)
				except:
					try:
						# print (resource,"except")
						resp = requests.get(resource,timeout=20) #Getting the site
						fileLength=len(resp.content)
						# print ("except: ",fileLength,fileType,resource)
					except:
						continue
				
				# print (resource,"Length: ",fileLength,"Type: ",fileType)
				sizeTypeMap[cdn][resource]["size"]=fileLength
				sizeTypeMap[cdn][resource]["type"]=fileType
			with open("results/"+country+"/resourcesSizeType_"+cdn+".json", 'w') as fp:
				json.dump(sizeTypeMap, fp)
		with open("results/"+country+"/resourcesSizeType_"+cdn+".json", 'w') as fp:
			json.dump(sizeTypeMap, fp)

def groupedBoxPlot(plot_x,plot_sameRegion,plot_diffRegion,fname):
	# sns.boxplot(x = data['day'],
 #            y = data['total_bill'],
 #            hue = data['sex'])

	df = pd.DataFrame({'CDNs':plot_x,\
                  'Same Region (CRV[1])':plot_sameRegion,'Different Region (CRV[3])':plot_diffRegion})
	df = df[['CDNs','Same Region (CRV[1])','Different Region (CRV[3])']]


	plt.figure(figsize=(15,8))
	dd=pd.melt(df,id_vars=['CDNs'],value_vars=['Same Region (CRV[1])','Different Region (CRV[3])'],var_name='Region Type')
	gfg=sns.boxplot(x='CDNs',y='value',data=dd,hue='Region Type')
	plt.setp(gfg.get_legend().get_texts(), fontsize='20',fontweight='bold')
	plt.setp(gfg.get_legend().get_title(), fontsize='20',fontweight='bold')
	plt.tick_params(axis='both', which='major', labelsize=14,labelweight='bold') 
	plt.ylabel('Coefficient of CDN Regionalization',fontsize="20",fontweight='bold')
	plt.xlabel('CDNs',fontsize="20",fontweight='bold')
	plt.ylim(0, 1.02)
	plt.savefig('graphs/KSThreshold'+fname+'.pdf',dpi=300, format='pdf')

def plotKSValues(countries,distance_dict):	
	# cdns={"Akamai":"Akamai (DNS)","Cloudflare":"Cloudflare (Anycast)","EdgeCast":"Edgio (Regional Anycast)","Google":"Google (Mixed Approach)"}
	cdns={"Akamai":"Akamai (DNS)","Cloudflare":"Cloudflare (Anycast)","EdgeCast":"Edgio (Regional Anycast)"}

	plot_x=[]
	plot_diffRegion=[]
	plot_sameRegion=[]
	i=0
	for cdn in cdns:
		sameRegion=[]
		diffRegion=[]
		data=[]
		for country in countries:
			try:
				diffRegion.append(distance_dict[cdn][country]["local+non-neighboring_region"])
				if country=="AU":
					sameRegion.append(distance_dict[cdn][country]["local+same_region"])
				else:
					sameRegion.append(min(distance_dict[cdn][country]["local+same_region"],distance_dict[cdn][country]["local+neighboring_subregion"]))
			except:
				continue
		# data.append(sorted(sameRegion))
		# data.append(sorted(diffRegion))
		plot_x+=[cdns[cdn] for x in range(len(sameRegion))]
		plot_diffRegion+=diffRegion
		plot_sameRegion+=sameRegion


		# print (cdn,"local-non-neighRegion: ",diffRegion)
		# print (cdn,"local-sameRegion: ",sameRegion)

		# print ("Lengths of the arrays: ",i," : ",len(plot_x),len(diffRegion),len(sameRegion))
		i+=1

	print ("High Confidence: ",plot_x)
	groupedBoxPlot(plot_x,plot_sameRegion,plot_diffRegion,"")

def plotKSValuesLessPopular(countries,distance_dict):	
	cdns=["Cloudfront","Fastly","Google"]


	plot_x=[]
	plot_diffRegion=[]
	plot_sameRegion=[]
	i=0
	for cdn in cdns:
		sameRegion=[]
		diffRegion=[]
		data=[]
		for country in countries:
			try:
				diffRegion.append(distance_dict[cdn][country]["local+non-neighboring_region"])
				if country=="AU":
					sameRegion.append(distance_dict[cdn][country]["local+same_region"])
				else:
					sameRegion.append(min(distance_dict[cdn][country]["local+same_region"],distance_dict[cdn][country]["local+neighboring_subregion"]))
			except:
				continue
		# data.append(sorted(sameRegion))
		# data.append(sorted(diffRegion))
		plot_x+=[cdn for x in range(len(sameRegion))]
		plot_diffRegion+=diffRegion
		plot_sameRegion+=sameRegion
		i+=1

	print ("Test-Set: ",plot_x)
	groupedBoxPlot(plot_x,plot_sameRegion,plot_diffRegion,"testSet")

		# plotboxplot(data,["same region","different region"],cdn+" KS-Values","KSValuesBoxplot_"+cdn)

def plotKSValuesCDN(countries,distance_dict,cdns):	
	cdns={"Akamai":"Akamai (DNS)","Cloudflare":"Cloudflare (Anycast)",
	"EdgeCast":"Edgio (Regional Anycast)","Cloudfront":"Cloudfront",
	"Fastly":"Fastly","Google":"Google"
	}
	countryMap={
	"Akamai":("United Kingdom","Russia","US"),
	"Cloudflare":("Brazil","United Kingdom","India"),
	"EdgeCast":("Brazil","United Kingdom","Australia"),
	"Cloudfront":("US","India","South Africa"),
	"Fastly":("Brazil","Turkey","South Africa"),
	"Google":("Brazil","Russia","India"),
	}
	sameRegionMap={"Akamai":(1, 0.9, 1),"Cloudflare":(0.008,0.049,0.010),
	"EdgeCast":(0.2,0.3,0.2),
	"Cloudfront":(1.0,1.0,0.8),
	"Fastly":(0.35,0.2,0.4),
	"Google":(0.68,0.64,0.52)
	}
	DiffRegionMap={"Akamai":(1, 1, 1),"Cloudflare":(0.007,0.015,0.009),
	"EdgeCast":(1.0,1.0,1.0),
	"Cloudfront":(1.0,1.0,1.0),
	"Fastly":(0.37,0.29,0.40),
	"Google":(0.77,0.85,0.70)
	}

	for cdn in cdns:
		countries = countryMap[cdn] #UK,RU,US
		ks_values = {
		    'Same Region (CRV[1])': sameRegionMap[cdn],
		    'Different Region (CRV[3])': DiffRegionMap[cdn],
		}

		x = np.arange(len(countries))  # the label locations
		width = 0.25  # the width of the bars
		multiplier = 0

		fig, ax = plt.subplots(layout='constrained')

		for attribute, measurement in ks_values.items():
		    offset = width * multiplier
		    rects = ax.bar(x + offset, measurement, width, label=attribute)
		    ax.bar_label(rects, padding=3,fmt='%.1f', fontsize=14, fontweight='bold')
		    multiplier += 1

		# Add some text for labels, title and custom x-axis tick labels, etc.
		ax.set_ylabel('Coefficient of Regionalization', fontsize=14, fontweight='bold')
		ax.set_xticks(x + width, countries)
		ax.set_xticklabels(countries, fontsize=14, fontweight='bold')
		# ax.legend(loc='upper left', ncols=3,fontsize=14, frameon=True)
		ax.set_ylim(0, 1.15)

		legend=ax.legend(
			loc='upper center',  # Position the legend above the plot
			bbox_to_anchor=(0.5, 1.2),  # Adjust placement to center it above the plot
			ncol=1,  # Reduce the number of columns to make it stack vertically
			fontsize=14,  # Set font size
			frameon=True  # Keep the frame for the legend
		)
		for text in legend.get_texts():
			text.set_fontweight('bold')

		# Bold y-tick labels
		for label in ax.get_yticklabels():
			label.set_fontweight('bold')
			label.set_fontsize(14)

		# Bold x-tick labels (reapplied to ensure boldness)
		for label in ax.get_xticklabels():
			label.set_fontweight('bold')
			label.set_fontsize(14)

		# Customize spines
		for spine in ax.spines.values():
			spine.set_linewidth(1.5)

		# ax.set_title(cdns[cdn])
		plt.savefig('graphs/KSThreshold_'+cdn+'.pdf',dpi=300, format='pdf')

	# plt.show()

def plotbarPlot(labels,numbers,cdn):
	fig = plt.figure()
	# ax = fig.add_axes([0,0,1,1])
	plt.bar(labels,numbers)
	plt.xticks(rotation=20, ha='right')
	plt.title(cdn)
	plt.savefig("graphs/objectTypeDistribution_"+cdn)

def objectTypeDistribution(countries,cdnCountryMap):
	contentTypeCount={}
	ignorecontenttypes=["*",'','i']
	for country in countries:
		# print (country)
		cdnResourcesMap=json.load(open("results/"+country+"/ResourcescdnMapping.json"))
		for cdn in cdnCountryMap[country]:
			if cdn not in contentTypeCount:
				contentTypeCount[cdn]={}
			resourceSizeType=json.load(open("results/"+country+"/resourcesSizeType_"+cdn+".json"))
			for resource in resourceSizeType[cdn]:
				try:
					contenttype=resourceSizeType[cdn][resource]["type"]
				except Exception as e:
					# print (country,cdn,str(e))
					continue
				try:
					contenttype=contenttype.split('/')[0]
				except:
					contenttype=contenttype
				if contenttype in ignorecontenttypes:
					continue
				if contenttype not in contentTypeCount[cdn]:
					contentTypeCount[cdn][contenttype]=0
				contentTypeCount[cdn][contenttype]+=1

	for cdn in contentTypeCount:
		sortedcontentTypeCount=dict(sorted(contentTypeCount[cdn].items(), key=lambda item: item[1]))
		labels=[]
		data=[]
		for _type in sortedcontentTypeCount:
			labels.append(_type)
			data.append(sortedcontentTypeCount[_type])
		plotbarPlot(labels,data,cdn)
		print (cdn,len(sortedcontentTypeCount),sortedcontentTypeCount,"\n")
	print ("\n\n")


def KSThreshold(countries,distance_dict):

	countriesPerRegion={"North America":["US"],"South America":["BR","AR"],"Asia":["IN","CN","ID","AE"],"Europe":["FR","GB","TR","RU","DE"],"Oceania":["AU"],"Africa":["ZA","EG","NG"]}
	# countriesPerRegion={"Africa":["ZA","EG",]}
	
	table=[]
	resolver_short={"local":"local","diff_metro":"diff_metro","same_region":"same_R","neighboring_subregion":"neigh_subR","neighboring_region":"neigh_R","non-neighboring_region":"non-neigh_R"}

	vPs=[]

	for vantages in distance_dict["Akamai"]["BR"]:
		if vantages=="local+non-neighboring_region" or vantages=="local+same_region" or vantages=="local+neighboring_subregion":
			V=vantages.split("+")
			_vantages=(resolver_short[V[0]],resolver_short[V[1]])
			vPs.append(_vantages)
	row=["Country","CDN"]+["percentage of resources"]+["bytes of resources"]+vPs+["label"]
	table.append(row)

	countryCDNApproachMap={}

	cdnApproachMap={}

	for country in countries:
		countryCDNApproachMap[country]={}
		
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
		cdnResourcesMap=json.load(open("results/"+country+"/ResourcescdnMapping.json"))
		totalResources=set()
		totalBytes=0

		for cdn in cdnResourcesMap:
			resourceSizeType=json.load(open("results/"+country+"/resourcesSizeType_"+cdn+".json"))
			for resource in resourceSizeType[cdn]:
				try:
					totalBytes+=int(resourceSizeType[cdn][resource]["size"])
					resourceByteMap[resource]=int(resourceSizeType[cdn][resource]["size"])
				except Exception as e:
					continue
			for resource in cdnResourcesMap[cdn]:
				totalResources.add(resource)

		tresourcesCount=len(totalResources)
		for cdn in distance_dict:
				# resourceSizeType[cdn][resource]["type"]=fileType
			if cdn not in cdnApproachMap:
				cdnApproachMap[cdn]={}
			temp=[country,cdn]
			try:
				resourcesCount=len(set(cdnResourcesMap[cdn]))	
				label=classification(cdn,country)
				if label not in cdnApproachMap[cdn]:
					cdnApproachMap[cdn][label]=0
				if label not in countryCDNApproachMap[country]:
					countryCDNApproachMap[country][label]={}
					countryCDNApproachMap[country][label]["CDNs"]=[]
					countryCDNApproachMap[country][label]["bytes"]=0
					countryCDNApproachMap[country][label]["resourcesCount"]=0

				cdnApproachMap[cdn][label]+=1
				bytesServedbyCDN=0
				resourceSizeType=json.load(open("results/"+country+"/resourcesSizeType_"+cdn+".json"))
				for resource in resourceSizeType[cdn]:
					try:
						bytesServedbyCDN+=int(resourceSizeType[cdn][resource]["size"])

					except Exception as e:
						# print (country,cdn,str(e))
						continue
			except Exception as e:
				# print (str(e),country,cdn,)
				continue
			if cdn not in countryCDNApproachMap[country][label]["CDNs"]:
				countryCDNApproachMap[country][label]["CDNs"].append(cdn)
				countryCDNApproachMap[country][label]["bytes"]+=bytesServedbyCDN
				countryCDNApproachMap[country][label]["resourcesCount"]+=resourcesCount


			temp.append(100*resourcesCount/tresourcesCount)
			temp.append(100*bytesServedbyCDN/totalBytes)
			for vantages in distance_dict["Akamai"]["BR"]:
				if vantages=="local+non-neighboring_region" or vantages=="local+same_region" or vantages=="local+neighboring_subregion":
					try:
						temp.append(distance_dict[cdn][country][vantages])
					except:
						temp.append(-1)
			temp.append(label)
			table.append(temp)
		table.append([])
		for label in countryCDNApproachMap[country]:
			countryCDNApproachMap[country][label]["pbytes"]=100*countryCDNApproachMap[country][label]["bytes"]/totalBytes
			countryCDNApproachMap[country][label]["presourcesCount"]=100*countryCDNApproachMap[country][label]["resourcesCount"]/tresourcesCount

	
	content=tabulate(table,headers='firstrow', tablefmt="tsv")
	text_file=open("results/KSThreshold.csv","w")
	text_file.write(content)
	text_file.close()

	cdnClassificationMap={}
	for cdn in cdnApproachMap:
		temp=0
		for label in cdnApproachMap[cdn]:
			if cdnApproachMap[cdn][label]>=temp:
				cdnClassificationMap[cdn]=label
				temp=cdnApproachMap[cdn][label]
	print (cdnClassificationMap,len(cdnClassificationMap))

	#country->/country 
	# region->/region #unique resources per label, divide by total resources of that label
	# worldwide->/all

	countryCDNApproachMap["worldwide"]={}
	countryCDNApproachMap["worldwide"]["tbytes"]=0
	countryCDNApproachMap["worldwide"]["tresources"]=0
	worldwideLabels=set()
	resourcesPerRegionLabel={}
	resourcesBytes={}
	resourcesWorldwideLabel={}
	resourcesCountryLabel={}
	labels=["DNS","Anycast","Regional Anycast","Mixed Approach"]

	table_resourceCount=[]	
	table_resourcebytes=[]
	row=["Location","Internet Users","DNS","DNS-Adjusted","Anycast","Anycast-Adjusted","Regional Anycast","Regional Anycast-Adjusted","Mixed Approach","Mixed Approach-Adjusted"]
	table_resourceCount.append(row)
	table_resourcebytes.append(row)

	regionalInternetUsersMap,countryInternetUsersMap=internetUsersMap()

	for region in countriesPerRegion:
		# labels=set()
		for country in countriesPerRegion[region]:
			temp_resourceCount=[country]
			temp_resourceBytes=[country]
			resourcesCountryLabel[country]={}

			if country not in countryCDNApproachMap:
				countryCDNApproachMap[country]={}

			if region not in countryCDNApproachMap:
				countryCDNApproachMap[region]={}
			if region not in resourcesPerRegionLabel:
				resourcesPerRegionLabel[region]={}

			cdnResourcesMap=json.load(open("results/"+country+"/ResourcescdnMapping.json"))
			for cdn in cdnResourcesMap:
				try:
					resourcesCount=len(set(cdnResourcesMap[cdn]))
					if cdn in cdnClassificationMap:	
						label=cdnClassificationMap[cdn]
					else:
						continue

					if label not in countryCDNApproachMap[country]:
						countryCDNApproachMap[country][label]={}

					if label not in countryCDNApproachMap[region]:
						countryCDNApproachMap[region][label]={}

					if label not in countryCDNApproachMap["worldwide"]:
						countryCDNApproachMap["worldwide"][label]={}
						
					if label not in resourcesCountryLabel[country]:
						resourcesCountryLabel[country][label]=[]

					if label not in resourcesPerRegionLabel[region]:
						resourcesPerRegionLabel[region][label]=[]

					if label not in resourcesWorldwideLabel:
						resourcesWorldwideLabel[label]=[]

					# labels.add(label)
					# worldwideLabels.add(label)

					# bytesServedbyCDN=0
					resourceSizeType=json.load(open("results/"+country+"/resourcesSizeType_"+cdn+".json"))
					for resource in resourceSizeType[cdn]:
						try:
							# bytesServedbyCDN+=int(resourceSizeType[cdn][resource]["size"])
							resourcesBytes[resource]=int(resourceSizeType[cdn][resource]["size"])
							resourcesPerRegionLabel[region][label].append(resource)
							resourcesWorldwideLabel[label].append(resource)
							resourcesCountryLabel[country][label].append(resource)
						except Exception as e:
							# print (country,cdn,str(e))
							continue
				except Exception as e:
					print (country,cdn,str(e))
					continue

				
				

			totalBytes=0
			totalResources=0
			for label in resourcesCountryLabel[country]:
				bytesPerLabel=0
				resourceCountPerLabel=len(resourcesCountryLabel[country][label])
				totalResources+=len(resourcesCountryLabel[country][label])

				for resource in resourcesCountryLabel[country][label]:
					bytesPerLabel+=resourcesBytes[resource]
					totalBytes+=resourcesBytes[resource]

				countryCDNApproachMap[country][label]["resourcesCount"]=resourceCountPerLabel
				countryCDNApproachMap[country][label]["bytes"]=bytesPerLabel

			
			regionalInternetUserFraction=countryInternetUsersMap[country]/regionalInternetUsersMap["worldwide"]
			temp_resourceCount.append(round(100*regionalInternetUserFraction,1))
			temp_resourceBytes.append(round(100*regionalInternetUserFraction,1))


			for label in labels:
				countryCDNApproachMap[country][label]["presourcesCount"]=100*(countryCDNApproachMap[country][label]["resourcesCount"]/totalResources)
				countryCDNApproachMap[country][label]["pbytes"]=100*(countryCDNApproachMap[country][label]["bytes"]/totalBytes)

				countryCDNApproachMap[country][label]["presourcesCount-weighted"]=100*0.66*(countryCDNApproachMap[country][label]["resourcesCount"]/totalResources)*regionalInternetUserFraction
				countryCDNApproachMap[country][label]["pbytes-weighted"]=100*0.66*(countryCDNApproachMap[country][label]["bytes"]/totalBytes)*regionalInternetUserFraction
				print (country, label," percent bytes: ",countryCDNApproachMap[country][label]["pbytes"]," percent resources: ",countryCDNApproachMap[country][label]["presourcesCount"])
				temp_resourceCount.append(countryCDNApproachMap[country][label]["presourcesCount"])
				temp_resourceBytes.append(countryCDNApproachMap[country][label]["pbytes"])
				temp_resourceCount.append(countryCDNApproachMap[country][label]["presourcesCount-weighted"])
				temp_resourceBytes.append(countryCDNApproachMap[country][label]["pbytes-weighted"])
			print("\n")

			table_resourceCount.append(temp_resourceCount)
			table_resourcebytes.append(temp_resourceBytes)

		for x in range(2):
			table_resourceCount.append([])
			table_resourcebytes.append([])



	content=tabulate(table_resourceCount,headers='firstrow', tablefmt="tsv")
	text_file=open("results/CountryResourceCount.csv","w")
	text_file.write(content)
	text_file.close()

	content=tabulate(table_resourcebytes,headers='firstrow', tablefmt="tsv")
	text_file=open("results/CountryResourceBytes.csv","w")
	text_file.write(content)
	text_file.close()


	table_resourceCount=[]	
	table_resourcebytes=[]
	table_resourceCount.append(row)
	table_resourcebytes.append(row)
	
	
	for region in countriesPerRegion:
		temp_resourceCount=[region]
		temp_resourceBytes=[region]
		totalBytes=0
		totalResources=0
		for label in resourcesPerRegionLabel[region]:
			bytesPerLabel=0
			resourceCountPerLabel=len(resourcesPerRegionLabel[region][label])
			totalResources+=len(resourcesPerRegionLabel[region][label])

			for resource in resourcesPerRegionLabel[region][label]:
				bytesPerLabel+=resourcesBytes[resource]
				totalBytes+=resourcesBytes[resource]

			countryCDNApproachMap[region][label]["resourcesCount"]=resourceCountPerLabel
			countryCDNApproachMap[region][label]["bytes"]=bytesPerLabel

		regionalInternetUser=0
		for country in countriesPerRegion[region]:
			regionalInternetUser+=countryInternetUsersMap[country]

		regionalInternetUserFraction=regionalInternetUser/regionalInternetUsersMap["worldwide"]
		temp_resourceCount.append(round(100*regionalInternetUserFraction,1))
		temp_resourceBytes.append(round(100*regionalInternetUserFraction,1))

		for label in labels:
			countryCDNApproachMap[region][label]["presourcesCount-weighted"]=100*0.66*(countryCDNApproachMap[region][label]["resourcesCount"]/totalResources)*regionalInternetUserFraction
			countryCDNApproachMap[region][label]["pbytes-weighted"]=100*0.66*(countryCDNApproachMap[region][label]["bytes"]/totalBytes)*regionalInternetUserFraction
			countryCDNApproachMap[region][label]["presourcesCount"]=100*(countryCDNApproachMap[region][label]["resourcesCount"]/totalResources)
			countryCDNApproachMap[region][label]["pbytes"]=100*(countryCDNApproachMap[region][label]["bytes"]/totalBytes)

			print (region,regionalInternetUserFraction, label," percent bytes: ",countryCDNApproachMap[region][label]["pbytes"]," percent resources: ",countryCDNApproachMap[region][label]["presourcesCount"])
			temp_resourceCount.append(countryCDNApproachMap[region][label]["presourcesCount"])
			temp_resourceBytes.append(countryCDNApproachMap[region][label]["pbytes"])
			temp_resourceCount.append(countryCDNApproachMap[region][label]["presourcesCount-weighted"])
			temp_resourceBytes.append(countryCDNApproachMap[region][label]["pbytes-weighted"])
		print("\n")
		table_resourceCount.append(temp_resourceCount)
		table_resourcebytes.append(temp_resourceBytes)

	

	totalBytes=0
	totalResources=0
	for label in resourcesWorldwideLabel:
		bytesPerLabel=0
		resourceCountPerLabel=len(resourcesWorldwideLabel[label])
		totalResources+=len(resourcesWorldwideLabel[label])

		for resource in resourcesWorldwideLabel[label]:
			bytesPerLabel+=resourcesBytes[resource]
			totalBytes+=resourcesBytes[resource]

		countryCDNApproachMap["worldwide"][label]["resourcesCount"]=resourceCountPerLabel
		countryCDNApproachMap["worldwide"][label]["bytes"]=bytesPerLabel
	temp_resourceCount=["World Total","66.0"]
	temp_resourceBytes=["World Total","66.0"]
	for label in labels:
		countryCDNApproachMap["worldwide"][label]["presourcesCount"]=100*(countryCDNApproachMap["worldwide"][label]["resourcesCount"]/totalResources)
		countryCDNApproachMap["worldwide"][label]["pbytes"]=100*(countryCDNApproachMap["worldwide"][label]["bytes"]/totalBytes)
		countryCDNApproachMap["worldwide"][label]["presourcesCount-weighted"]=100*0.66*(countryCDNApproachMap["worldwide"][label]["resourcesCount"]/totalResources)
		countryCDNApproachMap["worldwide"][label]["pbytes-weighted"]=100*0.66*(countryCDNApproachMap["worldwide"][label]["bytes"]/totalBytes)
		print ("worldwide", label," percent bytes: ",countryCDNApproachMap["worldwide"][label]["pbytes"]," percent resources: ",countryCDNApproachMap["worldwide"][label]["presourcesCount"])
		temp_resourceCount.append(countryCDNApproachMap["worldwide"][label]["presourcesCount"])
		temp_resourceBytes.append(countryCDNApproachMap["worldwide"][label]["pbytes"])
		temp_resourceCount.append(countryCDNApproachMap["worldwide"][label]["presourcesCount-weighted"])
		temp_resourceBytes.append(countryCDNApproachMap["worldwide"][label]["pbytes-weighted"])
	
	table_resourceCount.append(temp_resourceCount)
	table_resourcebytes.append(temp_resourceBytes)
	
	content=tabulate(table_resourceCount,headers='firstrow', tablefmt="tsv")
	text_file=open("results/RegionalResourceCount.csv","w")
	text_file.write(content)
	text_file.close()

	content=tabulate(table_resourcebytes,headers='firstrow', tablefmt="tsv")
	text_file=open("results/RegionalResourceBytes.csv","w")
	text_file.write(content)
	text_file.close()

	CDNByLabels={}
	for cdn in cdnClassificationMap:
		label=cdnClassificationMap[cdn]
		if label not in CDNByLabels:
			CDNByLabels[label]=set()
		CDNByLabels[label].add(cdn)
	print (CDNByLabels)
	# with open("results/k-distGoogleRankings.json", 'w') as fp:
	# 	json.dump(distance_dict, fp)

def internetUsersMap():
	regionalMap={"Africa":601940784,"Asia":3123650952,"Europe":747214734,"South America":369970548,"North America":347916694,"Oceania":30549185,"worldwide":5385798406}
	
	countryMap={"US":297322868,"BR":178100000,"AR":42000000,
	"GB":65045228,"FR":60421689,"TR":72500000,"RU":124630000,"DE":79127551,
	"CN":1010740000,"IN":833710000,"ID":212354070,"AE":12176400,
	"ZA":34545165,"EG":54741493,"NG":154301195,"AU":23391152
	}
	return regionalMap,countryMap

def computeCDFDistance(countries,cdnCountryMap,resolver_dict):
	distance_dict={}
	for country in countries:
		if country=="AU":
			vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		else:
			vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]

		latencyResult=json.load(open("results/"+country+"/PingRipeResult.json"))
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))


		results=collectResults(cdnCountryMap[country],vantagePoints,country,latencyResult,cdnMap)
		# results=json.load(open("results/"+country+"/"+"RTTs.json"))

		plotrttCDFs(country,results,resolver_dict,vantagePoints)


		for cdn in cdnCountryMap[country]:
			print (cdn)
			if cdn not in distance_dict:
				distance_dict[cdn]={}
			if country not in distance_dict[cdn]:
				distance_dict[cdn][country]={}
			vantages=[x for x in results[cdn]]
			for i in range(len(vantages)):
				for j in range(i+1,len(vantages)):
					vantage_i=vantages[i]
					vantage_j=vantages[j]					

					#following line computes for rtts between 20th and 70th percentile
					try:
						ks_dist=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(results[cdn][vantage_i],20,70),MiddlePercentileRTTs(results[cdn][vantage_j],20,70))
					except:
					# K-S Distance
						ks_dist=Kolmogorov_SmirnovTest(results[cdn][vantage_i],results[cdn][vantage_j])
					distance_dict[cdn][country][vantage_i+"+"+vantage_j]=ks_dist[0]

					# Jenson-Shannon Distance
					# js_dist=compute_js(results[cdn][vantage_i],results[cdn][vantage_j],b=10)
					# distance_dict[cdn][country][vantage_i+"+"+vantage_j]=js_dist

					# Earth mover's/wasserstein_distance Distance
					# ws_dist=wasserstein_distance(results[cdn][vantage_i],results[cdn][vantage_j])
					# distance_dict[cdn][country][vantage_i+"+"+vantage_j]=ws_dist

	# plotKSValues(countries,distance_dict)

	# KSThreshold(countries,distance_dict,cdnCountryMap)
	# exit()
	return()

	table=[]
	resolver_short={"local":"local","diff_metro":"diff_metro","same_region":"same_R","neighboring_subregion":"neigh_subR","neighboring_region":"neigh_R","non-neighboring_region":"non-neigh_R"}
	
	vPs=[]
	for vantages in distance_dict["Akamai"]["BR"]:
		V=vantages.split("+")
		_vantages=(resolver_short[V[0]],resolver_short[V[1]])
		vPs.append(_vantages)
	row=["CDN","Country"]+vPs
	table.append(row)

	for cdn in distance_dict:
		# print ("CDN: ",cdn)
		for country in distance_dict[cdn]:
			
			# print ("Country: ",country)
			temp=[cdn,country]
			for vantages in distance_dict["Akamai"]["BR"]:
				# print (vantages," : ",distance_dict[cdn][country][vantages])
				try:
					temp.append(distance_dict[cdn][country][vantages])
				except:
					temp.append(-1)
			table.append(temp)
			# print ("\n")
		# print ("\n\n")
	# print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))
	content=tabulate(table, headers='firstrow', tablefmt="tsv")
	text_file=open("results/k-distGoogleRankings.csv","w")
	text_file.write(content)
	text_file.close()
	with open("results/k-distGoogleRankings.json", 'w') as fp:
		json.dump(distance_dict, fp)

			# for vantage in results[cdn]:
			# 	if vantage=="local":
			# 		continue
			# 	rtts = results[cdn][vantage]

			# 	# print ("CDN: ",cdn," Vantage: ",vantage," Earth Mover's_distance: ",e_dist)
			# 	js_dist=compute_js(results[cdn]["local"],results[cdn][vantage], b=10)
			# 	print (vantage," : ",js_dist)

def classification(cdn,country):
	results=json.load(open("results/"+country+"/"+"RTTs.json"))
	distance_dict=json.load(open("results/k-distGoogleRankings.json"))
	vantages="local+non-neighboring_region"
	if distance_dict[cdn][country][vantages]<0.4:
		return "Anycast"
	elif distance_dict[cdn][country][vantages]>=0.7:
		if distance_dict[cdn][country]["local+same_region"]<0.4 or (country!="AU" and distance_dict[cdn][country]["local+neighboring_subregion"]<0.4):
			return "Regional Anycast"
		else:
			return "DNS"
	return "Mixed Approach"
	
	lower_bound=0
	upper_bound=100
	diff=5
	# print (country,cdn)
	while 1:
		if upper_bound<diff:
			return "undetermined"
		vantage_i="local"
		vantage_j="non-neighboring_region"
		# if country=="GB" and cdn=="Google":
		# 	local=MiddlePercentileRTTs(results[cdn][vantage_i],0,50)
		# 	non_neigh=MiddlePercentileRTTs(results[cdn][vantage_j],0,50)

		# 	print (country,cdn,Kolmogorov_SmirnovTest(local,non_neigh))
		# 	exit()


		ks_dist_lower=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(results[cdn][vantage_i],lower_bound,upper_bound-diff),MiddlePercentileRTTs(results[cdn][vantage_j],lower_bound,upper_bound-diff))[0]
		ks_dist_upper=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(results[cdn][vantage_i],upper_bound-diff,100),MiddlePercentileRTTs(results[cdn][vantage_j],upper_bound-diff,100))[0]
		print (country,cdn,lower_bound,upper_bound-diff,ks_dist_lower)
		print (country,cdn,upper_bound-diff,100,ks_dist_upper)

		if ks_dist_lower<0.3:
			approacha="Anycast"
			return "Mixed-Primary="+approacha

		elif ks_dist_upper>=0.7:
			vantage_j="same_region"
			ks_dist_sameregion=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(results[cdn][vantage_i],upper_bound-diff,100),MiddlePercentileRTTs(results[cdn][vantage_j],upper_bound-diff,100))[0]
			if country!="AU":
				vantage_j="neighboring_subregion"
				ks_dist_neighsubregion=Kolmogorov_SmirnovTest(MiddlePercentileRTTs(results[cdn][vantage_i],upper_bound-diff,100),MiddlePercentileRTTs(results[cdn][vantage_j],upper_bound-diff,100))[0]
			if ks_dist_sameregion<0.3 or (country!="AU" and ks_dist_neighsubregion<0.3):
				approacha="Regional Anycast"
				return "Mixed-Primary="+approacha

			else:
				approacha="DNS"
				return "Mixed-Primary="+approacha

			# approacha="DNS"
		upper_bound=upper_bound-diff

	# return "Mixed-Primary="+approacha+",Secondary="+approachb
	# return "Mixed-Primary="+approacha





#To Do: keep domains whose RTTs we have across all scopes.

def PCA():
	k_dist=json.load(open("results/k-dist.json"))
	d={}
	d["CDN"]=[]
	d["Country"]=[]
	resolver_short={"same_region":"same_R","neighboring_region":"neigh_R","non-neighboring_region":"non-neigh_R","local":"local","diff_metro":"diff_metro"}


	VP=[]
	for cdn in k_dist:
		for country in k_dist[cdn]:
			d["CDN"].append(cdn)
			d["Country"].append(country)
			for vantages in k_dist[cdn][country]:
				V=vantages.split("+")
				_vantages=resolver_short[V[0]]+"+"+resolver_short[V [1]]
				if _vantages not in d:
					d[_vantages]=[]
				d[_vantages].append(k_dist[cdn][country][vantages])
				if _vantages not in VP:
					VP.append(_vantages)
	print ("features: ",VP)
	df = pd.DataFrame(d)
	print("Original DataFrame:\n",df,"\n")
	
	df= df[VP]

	print("DataFrame without CDN and Country Labels:\n",df,"\n")


	from sklearn.preprocessing import StandardScaler
	import seaborn as sns
	from sklearn.decomposition import PCA

	scaler = StandardScaler()
	scaler.fit(df)
	scaled_data = scaler.transform(df)

	pca = PCA(n_components=2)
	pca.fit(scaled_data)
	x_pca = pca.transform(scaled_data)
	
	map= pd.DataFrame(pca.components_,columns=VP)
	plt.figure(figsize=(16,16))
	sns.heatmap(map,cmap='twilight')
	plt.savefig('graphs/PCA.png')
	

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


def findHome(cdnCountryMap):
	try:
		result=json.load(open("results/ipcountrycdnmap.json")) 
	except:
		result={}

	# countries=["US","IN","ZA","KR","AU","IN_allCDNs","US_allCDNs"]
	countries=["ZA","CN","BR","GB","AU"]

	allipshome=json.load(open("results/allipshome.json"))
	all_ips=set()
	overlapping_ips=set()
	# for ip in allipshome:
	# 	all_ips.add(ip)
	# print (len(all_ips)) 
	ipmap={}

	for country in countries:
		ipmap[country]={}
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))	
		if country=="AU":
			vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		else:
			vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
		for cdn in cdnCountryMap[country]:
			if cdn=="null" or cdn==None:
				continue
			ipmap[country][cdn]=[]


			domains=set(cdnMap[cdn])
			ips=[]
			for vantage in vantagePoints:
				replicasPerVantage=json.load(open("results/"+country+"/dnsRipeResult_"+vantage+".json")) 
				for domain in domains:
					if domain in replicasPerVantage:
						ips+=replicasPerVantage[domain]
						for ip in replicasPerVantage[domain]:
							# if country in result and cdn in result[country]:
							# 	if ip not in result[country][cdn]:
							# 		all_ips.add(ip)
							if ip not in allipshome:
								all_ips.add(ip)
							else:
								overlapping_ips.add(ip)


			ips=list(set(ips))
			ipmap[country][cdn]=ips

	all_ips=list(all_ips)

	print ("Len of all_ips: ",len(all_ips))
	print ("Len of overlapping_ips: ",len(overlapping_ips))

	# exit()

	findHomeAllIPs(all_ips) 

	allipshome=json.load(open("results/allipshome.json")) 

	for country in ipmap:
		result[country]={}
		for cdn in ipmap[country]:
			if cdn=="null" or cdn==None:
				continue
			result[country][cdn]={}
			for ip in ipmap[country][cdn]:
				if ip not in result[country][cdn] and ip in allipshome:
					# if 'country' in allipshome[ip]:
					try:
						result[country][cdn][ip]=allipshome[ip]['country']
					except Exception as e:
						print (ip,cdn,country,str(e))
	with open("results/ipcountrycdnmap.json", 'w') as fp:
		json.dump(result, fp)

def homeAnalysis():
	allipshome=json.load(open("results/ipcountrycdnmap.json")) 
	serverCount={}
	for country in allipshome:
		serverCount[country]={}
		print ("country: ",country)
		for cdn in allipshome[country]:
			serverCount[country][cdn]={}
			for server in allipshome[country][cdn]:
				server_location=allipshome[country][cdn][server]
				if server_location not in serverCount[country][cdn]:
					serverCount[country][cdn][server_location]=0
				serverCount[country][cdn][server_location]+=1
			# sortedServerCount = sorted(serverCount[country][cdn], key=serverCount[country][cdn].get,reverse=True)
			sortedServerCount=dict(sorted(serverCount[country][cdn].items(), key=lambda item: item[1]))

			print ("CDN: ",cdn," serverCount sorted: ",sortedServerCount,"\n")
		print ("\n\n")

	# print (serverCount)

def aggregatedDeployment():
	import pandas as pd
	import plotly as py
	import plotly.graph_objects as go
	# from plotly.offline import download_plotlyjs,init_notebook_mode,plot,iplot
	allipshome=json.load(open("results/ipcountrycdnmap.json"))
	countryCodesToNames=json.load(open("data/countryCodesToNames.json"))


	cdnDeployment={} 
	for country in allipshome:
		for cdn in allipshome[country]:
			if cdn not in cdnDeployment:
				cdnDeployment[cdn]={}
			for server in allipshome[country][cdn]:
				server_location=allipshome[country][cdn][server]
				cdnDeployment[cdn][server]=server_location
	cdnCount={}
	# cdns=["Akamai","EdgeCast","Amazon"]
	cdns=["Akamai","EdgeCast","Cloudfront","Fastly","Google","Cloudflare","Azion","Tencent","Taobao","CDN77"]

	for cdn in cdns:
		cdnCount[cdn]={}
		for server in cdnDeployment[cdn]:
			country_location=cdnDeployment[cdn][server]
			if country_location not in cdnCount[cdn]:
				cdnCount[cdn][country_location]=0
			else:
				cdnCount[cdn][country_location]+=1
		sortedServerCount=dict(sorted(cdnCount[cdn].items(), key=lambda item: item[1]))
		# print (cdn," : ",sortedServerCount,"\n\n")
		print (cdn)
		countries=[]
		serverCount=[]
		for country in sortedServerCount:
			try:
				if sortedServerCount[country]<1:
					continue
				countries.append(countryCodesToNames[country])
				serverCount.append(sortedServerCount[country])
			except Exception as e:
				print (country,sortedServerCount[country],str(e))
				continue
		print (sortedServerCount)
		print (countries)
		print (serverCount,"\n\n")

		_max=max(serverCount)

		data = dict(
		type = 'choropleth',
		colorscale = 'RdBu',
		locations = countries,
		locationmode = "country names",
		zmin=1, 
		zmax=_max,
		z = serverCount,
		text = countries,
		colorbar = {'title' : 'Server Count'},
		)
		layout = dict(title = cdn, geo = dict(showframe = False,projection = {'type':'mercator'})
		)
		fig = go.Figure(data = [data],layout = layout)
		# iplot(chmap)
		fig.show()
		# break


def plotboxplot(data,ylabels,title,filename):
	plt.clf()
	fig = plt.figure(figsize =(10, 7))
	ax = fig.add_subplot(111)
	 
	# Creating axes instance
	bp = ax.boxplot(data, patch_artist = True,
	                notch ='True', vert = 0)
	 
	colors = ['#0000FF', '#00FF00',
	          '#FFFF00', '#FF00FF']
	 
	for patch, color in zip(bp['boxes'], colors):
	    patch.set_facecolor(color)
	 
	# changing color and linewidth of
	# whiskers
	for whisker in bp['whiskers']:
	    whisker.set(color ='#8B008B',
	                linewidth = 1.5,
	                linestyle =":")
	 
	# changing color and linewidth of
	# caps
	for cap in bp['caps']:
	    cap.set(color ='#8B008B',
	            linewidth = 2)
	 
	# changing color and linewidth of
	# medians
	for median in bp['medians']:
	    median.set(color ='red',
	               linewidth = 3)
	 
	# changing style of fliers
	for flier in bp['fliers']:
	    flier.set(marker ='D',
	              color ='#e7298a',
	              alpha = 0.5)
	     
	# x-axis labels
	ax.set_yticklabels(ylabels)
	 
	# Adding title
	plt.title(title)
	plt.xlim([0, 1])
	 
	# Removing top axes and right axes
	# ticks
	ax.get_xaxis().tick_bottom()
	ax.get_yaxis().tick_left()

	# show plot
	plt.savefig("graphs/"+filename)

def detect_outlier(data):
    q1, q3 = np.percentile(sorted(data), [25, 75])
 
    iqr = q3 - q1
 
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
 
    # outliers = [x for x in data if x <= lower_bound or x >= upper_bound]
 
    # return outliers
    return lower_bound,upper_bound

def boxplotdata(results,cdn,country):
	print (cdn)
	mean_data=[]
	variance_data=[]

	badCustomersPerScope=[]
	highVariancePerScope=[]

	outlierBounds={}

	for vantage in results:
		vantage_mean=[]
		vantage_variance=[]
		acrosstlds=[]

		badCustomers=set()
		highVarianceCustomers=set()

		for tld in results[vantage]:
			if len(results[vantage][tld])>0:
				# print (tld,len(results[vantage][tld]),statistics.mean(results[vantage][tld]),statistics.variance(results[vantage][tld]))
				acrosstlds+=results[vantage][tld]
				# vantage_variance.append(statistics.variance(results[vantage][tld]))
			if len(results[vantage][tld])>1:
				if statistics.variance(results[vantage][tld])>5000:
					highVarianceCustomers.add(tld)
		highVariancePerScope.append(highVarianceCustomers)
		lower_bound,upper_bound=detect_outlier(acrosstlds) #outliers across all replicas per scope.
		outlierBounds[vantage]=(lower_bound,upper_bound)

		for tld in results[vantage]:
			if len(results[vantage][tld])>0:
				# for latency in results[vantage][tld]:
				# 	if latency<=lower_bound or latency>=upper_bound:
				# 		badCustomers.add(tld)

				if statistics.mean(results[vantage][tld])<=lower_bound or statistics.mean(results[vantage][tld])>=upper_bound:
					badCustomers.add(tld)
		badCustomersPerScope.append(badCustomers)




		# mean_data.append(vantage_mean)
		# variance_data.append(vantage_variance)
	badCustomersAcrossScopes=set()
	for customers in badCustomersPerScope:
		badCustomersAcrossScopes=badCustomersAcrossScopes|customers
	# badCustomersAcrossScopes=badCustomersPerScope[0]|badCustomersPerScope[1]|badCustomersPerScope[2]|badCustomersPerScope[3]|badCustomersPerScope[4]
	# highVarianceAcrossScopes=highVariancePerScope[0]&highVariancePerScope[1]&highVariancePerScope[2]&highVariancePerScope[3]&highVariancePerScope[4]
	
	# print ("badCustomersAcrossScopes: ",badCustomersAcrossScopes)
	# print ("highVarianceAcrossScopes: ",highVarianceAcrossScopes)

	return badCustomersAcrossScopes,outlierBounds
	# plotboxplot(variance_data,['local', 'metro','same_region', 'neigh_region','non-neigh_region'],"Per Customer Variance",country,cdn)
	# plotboxplot(mean_data,['local', 'metro','same_region', 'neigh_region','non-neigh_region'],"Per Customer Mean",country,cdn)
def validate_ip_address(ipSet):
	temp=set()
	for ip in ipSet:
		try:
			ip_object = ipaddress.ip_address(ip)
			# print("The IP address '{ip_object}' is valid.")
		except ValueError:
			# print("The IP address '{ip_string}' is not valid")
			temp.add(ip)
	for ip in temp:
		ipSet.remove(ip)
	return ipSet


def checkECSSupport():
	
	countries=["ZA","AU","TR","RU","DE","GB","US","BR","IN","CN"]
	fullcdnMap={}
	for country in countries:
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
		for cdn in cdnMap:
			if cdn not in fullcdnMap:
				fullcdnMap[cdn]=set()
			domains=cdnMap[cdn]
			for domain in domains:
				fullcdnMap[cdn].add(domain)
	ecsMap=json.load(open("results/ecsMap.json"))
	ecsEnabled=json.load(open("results/ecsEnabled.json"))
	

	ecsSupport={} #based on distinct replies
	ecsEnabledPerCDN={} #based on >0 prefix scope in replies

	table=[]
	row=["CDN","Total Domains","ECS Scope>0(support ECS)","(%)","use ECS"]
	table.append(row)

	for cdn in fullcdnMap:
		ecsSupport[cdn]=[]
		
		ecsEnabledPerCDN[cdn]=[]

		ecsEnabledSet=set()
		temp=set()

		for domain in fullcdnMap[cdn]:
			if domain in ecsEnabled:
				ecsEnabledSet.add(domain)
			if domain in ecsMap:

				client_nsans=set(ecsMap[domain]["client_nsans"])
				distant_nsans=set(ecsMap[domain]["distant_nsans"])

				client_googleans=set(ecsMap[domain]["client_googleans"])
				distant_googleans=set(ecsMap[domain]["distant_googleans"])

				# if "" in client_googleans:
				# 	client_googleans.remove("")
				# if "" in distant_googleans:
				# 	distant_googleans.remove("")
				client_nsans=validate_ip_address(client_nsans)
				distant_nsans=validate_ip_address(distant_nsans)
				client_googleans=validate_ip_address(client_googleans)
				distant_googleans=validate_ip_address(distant_googleans)


				ns_intersect=client_nsans.intersection(distant_nsans)
				google_intersect=client_googleans.intersection(distant_googleans)


				if (len(ns_intersect)==0 and (len(client_nsans)>0 or len(distant_nsans)>0)) or (len(google_intersect)==0 and (len(client_googleans)>0 or len(distant_googleans)>0)):
					temp.add(domain)
		ecsSupport[cdn]=list(temp)
		ecsEnabledPerCDN[cdn]=list(ecsEnabledSet)
		# if len(ecsEnabledPerCDN[cdn])>0:
		# 	print ("CDN: ",cdn," Total domains: ",len(fullcdnMap[cdn])," domains that have ECS scope >0: ",len(ecsEnabledSet)," domains with different vector set with ECS option: ",len(ecsSupport[cdn]),"\n")
		
			# tableTemp=[cdn,len(fullcdnMap[cdn]),len(ecsEnabledSet),len(ecsSupport[cdn])]
			# table.append(tableTemp)
	# sortedcdnCount=dict(sorted(fullcdnMap[cdn].items(), key=lambda item: item[1]))

	print (len(ecsEnabledPerCDN["EdgeCast"]),len(fullcdnMap["EdgeCast"]))
	sendToMarcel=set()
	for domain in fullcdnMap["EdgeCast"]:
		if domain not in ecsEnabledPerCDN["EdgeCast"]:
			sendToMarcel.add(domain)
	print (len(sendToMarcel),sendToMarcel)
	# exit()
	sortedcdnCount = sorted(fullcdnMap, key=fullcdnMap.get,reverse=True)

	for cdn in sortedcdnCount:
		if cdn=="Amazon AWS":
			continue

		scopeEnabled=round((100*len(ecsEnabledPerCDN[cdn])/len(fullcdnMap[cdn])),2)
		diffIP=round((100*len(ecsSupport[cdn])/len(fullcdnMap[cdn])),2)
		if diffIP>0 and scopeEnabled>0:
			useEcs="Yes"
		else:
			useEcs="No"
		print (cdn,scopeEnabled,diffIP,useEcs)
		if cdn=="EdgeCast":
			tableTemp=["Edgio",len(fullcdnMap[cdn]),len(ecsEnabledPerCDN[cdn]),scopeEnabled,useEcs]
		else:
			tableTemp=[cdn,len(fullcdnMap[cdn]),len(ecsEnabledPerCDN[cdn]),scopeEnabled,useEcs]
		table.append(tableTemp)


	content=tabulate(table, headers='firstrow', tablefmt="tsv")
	text_file=open("results/ecsSupport.csv","w")
	text_file.write(content)
	text_file.close()
	# with open("results/ecsSupport.json", 'w') as fp:
	# 	json.dump(ecsSupport, fp)
	print ("\n\n")

def internetUserPopulation(countries):
	internetPopulationData=json.load(open("data/internetUserPopulation.json"))
	dataRep=0
	total=0
	dataPerRegion={}
	totalPerRegion={}
	# regions=["Asia","North America","Africa",]
	regions=set()
	for entry in internetPopulationData:
		total+=entry["pop2023"]
		regions.add(entry["region"])
		region=entry["region"]
		if region not in totalPerRegion:
			totalPerRegion[region]=0
		totalPerRegion[region]+=entry["pop2023"]

		if entry["cca2"] in countries:
			# internetPopMap[entry["cca2"]]=entry["pop2023"]
			dataRep+=entry["pop2023"]
			region=entry["region"]
			if region not in dataPerRegion:
				dataPerRegion[region]=0
			dataPerRegion[region]+=entry["pop2023"]

	print ("% Internet Users represented in our dataset: ",100*dataRep/total,"\n")
	# print ("Regions in datasource: ",regions)

	for region in regions:
		print ("% Internet Users from ",region," : ",100*dataPerRegion[region]/totalPerRegion[region])

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

    amazonPrefixes=set()
    for prefixDict in amazonIPs["prefixes"]:
        if "ip_prefix" in prefixDict and prefixDict["service"]=="CLOUDFRONT":
            amazonPrefixes.add(prefixDict["ip_prefix"])

    return cloudPrefixes,nativePrefixes,amazonPrefixes

def expectedPlots():

	rtts_dns={"local":10,"diff_metro":20,"same_region":45,"neighboring_subregion":75,"neighboring_region":120,"non-neighboring_region":200}
	rtts_anycast={"local":30,"diff_metro":30.1,"same_region":30.2,"neighboring_subregion":30.3,"neighboring_region":30.4,"non-neighboring_region":30.5}
	rtts_regionalanycast={"local":30,"diff_metro":30.5,"same_region":31,"neighboring_subregion":75,"neighboring_region":120,"non-neighboring_region":200}
	
	colors={'local':'purple','diff_metro':'r','same_region':'green','neighboring_subregion':'orange','neighboring_region':'brown','non-neighboring_region':'blue'}

	approaches=[rtts_dns,rtts_anycast,rtts_regionalanycast]
	approachNames=["DNS-Based","Anycast","Regional Anycast"]
	resolver_markers={"local":"o","diff_metro":"^","same_region":".","neighboring_subregion":"8","neighboring_region":"p","non-neighboring_region":"s"}
	lValue={"local":2,"diff_metro":1.5,"same_region":1,"neighboring_subregion":1,"neighboring_region":1,"non-neighboring_region":1}
	alphaValue={"local":1,"diff_metro":0.6,"same_region":0.8,"neighboring_subregion":0.85,"neighboring_region":0.7,"non-neighboring_region":0.75}


	ind=0
	for approach in approaches:
		l=1
		for resolverScope in approach:
			rtt=approach[resolverScope]
			if approach=="DNS-Based":
				rtts=[rtt for x in range(20)]
				l=1
				a=1
			else:
				rtts=[rtt-(x/4) for x in range(20)]
				rtts+=[rtt+(x/6) for x in range(60)]
				rtts+=[rtt+(x/4) for x in range(20)]
				l=lValue[resolverScope]
				a=alphaValue[resolverScope]
			# print (approach,approachNames[ind],rtts)
			# print (len(rtts),rtts)		
			x, y = ecdf(rtts)

			plt.scatter(x, y,color=colors[resolverScope],label=resolverScope,marker=resolver_markers[resolverScope],linewidth=l,alpha=a)
			l+=0.5
		approachName=approachNames[ind]
		ind+=1

		
		plt.xscale('log')
		plt.legend()

		plt.xlabel('RTT [ms]')
		plt.ylabel(approachName)
		plt.grid()
		plt.savefig("graphs/expectedPlot_"+approachName)
		plt.clf()

if __name__ == "__main__":

	
	resolver_dict={}
	resolver_dict["CN"] = {
	    "local": "local(Hangzhou, China)", 
	    "diff_metro": "diff_metro(Shanghai,China)", 
	    "same_region": "same_region(Japan)",
	    "neighboring_subregion": "neigh_subregion(India)", #remove
	    "neighboring_region": "neigh_region(Germany)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["IN"] = {
	    "local": "local(Mumbai,India)", 
	    "diff_metro": "diff_metro(Bengaluru,India)", 
	    "same_region": "same_region(Pakistan)",
	    "neighboring_subregion": "neigh_subregion(Japan)", #remove
	    "neighboring_region": "neigh_region(Germany)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["ID"] = {
	    "local": "local(Jakarta,Indonesia)", 
	    "diff_metro": "diff_metro(Madiun,Indonesia)", 
	    "same_region": "same_region(Vietnam)",
	    "neighboring_subregion": "neigh_subregion(Japan)", #remove
	    "neighboring_region": "neigh_region(Germany)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["AE"] = {
	    "local": "local(Dubai,UAE)", 
	    "diff_metro": "diff_metro(Sharjah,UAE)", 
	    "same_region": "same_region(Saudi Arabia)",
	    "neighboring_subregion": "neigh_subregion(Japan)", #remove
	    "neighboring_region": "neigh_region(Germany)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["DZ"] = {
	    "local": "local(Souk Ahras,Algeria)", 
	    "diff_metro": "diff_metro(Algiers,Algeria)", 
	    "same_region": "same_region(Egypt)",
	    "neighboring_subregion": "neigh_subregion(Nigeria)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["GH"] = {
	    "local": "local(Kumasi,Ghana)", 
	    "diff_metro": "diff_metro(Prestea,Ghana)", 
	    "same_region": "same_region(Nigeria)",
	    "neighboring_subregion": "neigh_subregion(South Africa)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	
	resolver_dict["ZA"] = {
	    "local": "local(Piet Retief,South Africa)", 
	    "diff_metro": "diff_metro(Prestondale,South Africa)", 
	    "same_region": "same_region(Zimbabwe)",
	    "neighboring_subregion": "neigh_subregion(Nigeria)",
	    "neighboring_region": "neigh_region(India)", #non-neighboring region
	    "non-neighboring_region": "non-neigh_region(Argentina)" #neighboring region
	}

	resolver_dict["NG"] = {
	    "local": "local(Abuja,Nigeria)", 
	    "diff_metro": "diff_metro(Lagos,Nigeria)", 
	    "same_region": "same_region(Ghana)",
	    "neighboring_subregion": "neigh_subregion(South Africa)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["EG"] = {
	    "local": "local(Al Khankah,Egypt)", 
	    "diff_metro": "diff_metro(Cairo,Egypt)", 
	    "same_region": "same_region(Algeria)",
	    "neighboring_subregion": "neigh_subregion(South Africa)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}
	

	resolver_dict["US"] = {
	    "local": "local(Indianapolis,US)", 
	    "diff_metro": "diff_metro(San Francisco,US)", 
	    "same_region": "same_region(Canada)",
	    "neighboring_subregion": "neigh_subregion(Brazil)", #keep
	    "neighboring_region": "neigh_region(Germany)", #remove
	    "non-neighboring_region": "non-neigh_region(India)"
	}

	resolver_dict["AR"] = {
	    "local": "local(San Isidro,Argentina)", 
	    "diff_metro": "diff_metro(Buenos Aires,Argentina)", 
	    "same_region": "same_region(Brazil)",
	    "neighboring_subregion": "neigh_subregion(Canada)",
	    "neighboring_region": "neigh_region(Germany)", 
	    "non-neighboring_region": "non-neigh_region(India)"
	}
	

	resolver_dict["BR"] = {
	    "local": "local(Anapolis,Brazil)", 
	    "diff_metro": "diff_metro(Cotia,Brazil)", 
	    "same_region": "same_region(Argentina)",
	    "neighboring_subregion": "neigh_subregion(Canada)", #keep
	    "neighboring_region": "neigh_region(Germany)", #remove
	    "non-neighboring_region": "non-neigh_region(India)"
	}

	resolver_dict["GB"] = {
	    "local": "local(Brighton,UK)", 
	    "diff_metro": "diff_metro(Maidenhead,UK)", 
	    "same_region": "same_region(Sweden)",
	    "neighboring_subregion": "neigh_subregion(Germany)", #remove
	    "neighboring_region": "neigh_region(India)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["TR"] = {
	    "local": "local(Antalya,Turkey)", 
	    "diff_metro": "diff_metro(Istanbul,Turkey)", 
	    "same_region": "same_region(Italy)",
	    "neighboring_subregion": "neigh_subregion(Russia)",#remove
	    "neighboring_region": "neigh_region(India)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["RU"] = {
	    "local": "local(Ryazan',Russia)", 
	    "diff_metro": "diff_metro(Polyany,Russia)", 
	    "same_region": "same_region(Poland)",
	    "neighboring_subregion": "neigh_subregion(Turkey)", #remove
	    "neighboring_region": "neigh_region(India)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["DE"] = {
	    "local": "local('Donzdorf',Germany)", 
	    "diff_metro": "diff_metro('Munich',Germany)", 
	    "same_region": "same_region(France)",
	    "neighboring_subregion": "neigh_subregion(Turkey)", #remove
	    "neighboring_region": "neigh_region(India)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["FR"] = {
	    "local": "local(Paris,France)", 
	    "diff_metro": "diff_metro(Roubaix,France)", 
	    "same_region": "same_region(Netherlands)",
	    "neighboring_subregion": "neigh_subregion(Sweden)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["ES"] = {
	    "local": "local(Morales,Spain)", 
	    "diff_metro": "diff_metro(Madrid,Spain)", 
	    "same_region": "same_region(Italy)",
	    "neighboring_subregion": "neigh_subregion(France)",
	    "neighboring_region": "neigh_region(India)", 
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}

	resolver_dict["AU"] = {
	    "local": "local(New Castle,Australia)", 
	    "diff_metro": "diff_metro(Sydney,Australia)", 
	    "same_region": "same_region(New Zealand)",
	    "neighboring_region": "neigh_region(India)", #keep
	    "non-neighboring_region": "non-neigh_region(Argentina)"
	}


	# latencyResult=json.load(open("results/"+country+"/PingRipeResult.json"))
	# cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))	

# 	# findServers("Akamai",vantagePoints,country,latencyResult,cdnMap)

# #imp two commands to collect results and plot the graphs.
	# countries=["BR","GB","ZA","CN","AU","IN","TR","RU","DE","ID","AE","AR","FR","US","NG","EG"]
	countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","GH","NG","AU"]
	# countries=["US","BR","AR","GB","FR","ES","TR","RU","DE","CN","IN","ID","AE","DZ","ZA","EG","NG","AU"]


	# countries=["ID"]
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

	# countries=["US","IN","ZA"]
	# cdnCountryMap={"BR":["Cloudfront"],
	# 				"GB":["Cloudfront"],
	# 				"ZA":["Cloudfront"],
	# 				"CN":["Cloudfront"],
	# 				"AU":["Cloudfront"],
	# 				"IN":["Cloudfront"],
	# 				"TR":["Cloudfront"],
	# 				"RU":["Cloudfront"],
	# 				"DE":["Cloudfront"],
	# 				"US":["Cloudfront"],
	# 				"ID":["Cloudfront"],
	# 				"AE":["Cloudfront"], 
    # 				"FR":["Cloudfront"],
    # 				"AR":["Cloudfront"],
	# 			    "NG":["Cloudfront"],
	# 			    "EG":["Cloudfront"],
	# 			    "ES":["Cloudfront"], 
	# 			    "GH":["Cloudfront"],
	# 			    "DZ":["Cloudfront"]
	# }
	# countries=["IN"]

	#imp two commands to collect results and plot the graphs.
	computeCDFDistance(countries,cdnCountryMap,resolver_dict)
	anycastGoogleCustomers=[]
	for country in ["BR","IN","RU"]:
	# for country in ["IN"]:
		if country=="AU":
			vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		else:
			vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
		latencyResult=json.load(open("results/"+country+"/PingRipeResult.json"))
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
		results=json.load(open("results/"+country+"/"+"RTTs.json"))
		plotrttCDFsMixedApproach(country,results,resolver_dict,vantagePoints,"Google")
		plotrttCDFsMixedApproach(country,results,resolver_dict,vantagePoints,"Fastly")
		res,localized,non_localized=customerSpecificVariation("Google",cdnMap,vantagePoints,country,latencyResult)
		if len(non_localized)>0:
			anycastGoogleCustomers.append(list(non_localized))
	print ("\n","Google customers using Anycast: ",set.intersection(*map(set,anycastGoogleCustomers)))

	distance_dict=json.load(open("results/k-distGoogleRankings.json"))
	# KSThreshold(countries,distance_dict)
	# countries=["BR","GB","ZA","CN","AU","IN","TR","RU","DE","ID","AE","AR","FR","US","NG","EG"]
	# plotKSValues(countries,distance_dict)
	# plotKSValuesLessPopular(countries,distance_dict)
	plotKSValuesCDN([],distance_dict,"CDNs")
	# compareEdgioAusIPs()

	exit()
	for country in countries:
		for cdn in cdnCountryMap[country]:
			print (country,cdn,classification(cdn,country))
		print ("\n\n")

					



	# objectTypeDistribution(countries,cdnCountryMap)
	# internetUserPopulation(countries+["AE","NG","EG","DZ","AR","GH","FR","IT","PL"])
	# checkECSSupport()
	# expectedPlots()
	# cdnThreshold(["BR","GB","ZA","CN","AU","IN","TR","RU"])
	# contentSizeType(countries)

	anycastGoogleCustomers=[]
	for country in ["BR","IN","RU"]:
		if country=="AU":
			vantagePoints=["local","diff_metro","same_region","neighboring_region","non-neighboring_region"]
		else:
			vantagePoints=["local","diff_metro","same_region","neighboring_subregion","neighboring_region","non-neighboring_region"]
		latencyResult=json.load(open("results/"+country+"/PingRipeResult.json"))
		cdnMap=json.load(open("results/"+country+"/cdn_mapping.json"))
		results=json.load(open("results/"+country+"/"+"RTTs.json"))
		# plotrttCDFsMixedApproach(country,results,resolver_dict,vantagePoints,"Google")
		# plotrttCDFsMixedApproach(country,results,resolver_dict,vantagePoints,"Fastly")
		res,localized,non_localized=customerSpecificVariation("Google",cdnMap,vantagePoints,country,latencyResult)
		if len(non_localized)>0:
			anycastGoogleCustomers.append(list(non_localized))
	print ("\n","Google customers using Anycast: ",set.intersection(*map(set,anycastGoogleCustomers)))



	distance_dict=json.load(open("results/k-distGoogleRankings.json"))
	# KSThreshold(countries,distance_dict)
	# countries=["BR","GB","ZA","CN","AU","IN","TR","RU","DE","ID","AE","AR","FR","US","NG","EG"]
	# plotKSValues(countries,distance_dict)
	# plotKSValuesLessPopular(countries,distance_dict)
	plotKSValuesCDN([],distance_dict,"CDNs")
	# compareEdgioAusIPs()



	# results=customerSpecificVariation("Akamai",cdnMap,vantagePoints,country,latencyResult)
	# boxplotdata(results,"Akamai",country)
	
#To find the home country of all servers of a cdn across the countries so 
# we can compare measurements of the client in that country compared to other countries.
	# findHome(cdnCountryMap)
	# homeAnalysis()
	# aggregatedDeployment()
	# computeCDFDistance(["US","IN","KR"])

	# PCA()
 
	


