import json

cdn_mapping=json.load(open("results/AU/domaincdnmapping.json"))
mapping={}

for site in cdn_mapping:
	if site not in mapping:
		mapping[site]={}
	for cdn in cdn_mapping[site]:
		if cdn=="null":
			continue
		else:
			mapping[site][cdn]=list(set(cdn_mapping[site][cdn]))

with open("results/AU/domaincdnmappingAU.json", 'w') as fp:
    json.dump(mapping, fp)
