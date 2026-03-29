import pytricia
from aquatools.db import GeneralConn, XLayerConn

#find all the asns associated with the IP
pyt = pytricia.PyTricia() 
asn = 15133
q = f""" SELECT cidr, default_asn FROM pfx2as WHERE default_asn={asn}; """  
cursor = GeneralConn.cursor() 
cursor.execute(q)
rows = cursor.fetchall()     

for cidr, asn in rows: 
    pyt.insert(cidr, asn)   

sets = [] 
#A is the replica ip file

for cdn_location, addrs in A['EdgeCast']['US'].items(): 
    ss = [] 
    for addr in addrs:
        if addr is None: continue 
        prefix = pyt.get_key(addr) 
        if prefix is None: continue
        ss.append(prefix) 
    print(f"########################## {cdn_location} ##########################")
    for x in sorted(list(set(ss))):
        print(x)
    sets.append(set(ss))
    print('.'*200) 

def get_IP_ASNs(ips):
    
    return asns
    
def jaccard_distance(set1, set2):
    # Calculate the size of intersection and union
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    # Handle edge case: if both sets are empty, define distance as 0
    if union == 0:
        return 0.0
    
    # Compute Jaccard distance
    return 1 - (intersection / union)

print(jaccard_distance(sets[0], sets[2]))
print(jaccard_distance(sets[0], sets[-1]))

    

