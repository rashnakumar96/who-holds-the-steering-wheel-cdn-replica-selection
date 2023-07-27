import json
import pandas as pd
import matplotlib.pyplot as plt

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

PCA()