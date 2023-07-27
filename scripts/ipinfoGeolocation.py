import ipinfo
import json

def findInfoAllIPs(ips):
	try:
		result=json.load(open("results/allipsinfo.json")) 
	except:
		result={}
	access_token = ''#add your access token here
	handler = ipinfo.getHandler(access_token)
	ans=handler.getBatchDetails(ips)

	for ip in ans:
		result[ip]=ans[ip]

	with open("results/allipsinfo.json", 'w') as fp:
		json.dump(result, fp)


def ipInfoGeolocation(all_ips):
	try:
		result=json.load(open("results/ipcountrymap.json")) 
	except:
		result={}

	findInfoAllIPs(all_ips) 

	allipsinfo=json.load(open("results/allipsinfo.json")) 
	
	for ip in allipsinfo:
		try:
			result[ip]=allipsinfo[ip]['country']
		except Exception as e:
			print (ip,country,str(e))
	with open("results/ipcountrymap.json", 'w') as fp:
		json.dump(result, fp)

if __name__ == "__main__":
	#give this function full list of unique ip addresses or call this 
	# in batches (depending on the size of the list)
	ipInfoGeolocation(all_ips)