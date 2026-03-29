import re
import json
import requests
import pycountry_convert as pc



# ----------- Configuration ------------
input_data = """
# resolver_dict={"local":"local","diff_metro":"169.53.182.124","same_region":"209.250.128.6","neighboring_region":"45.188.158.141","neighboring_subregion":"159.69.114.157","non-neighboring_region":"103.29.118.157"} #US 
# resolver_dict={"local":"local","diff_metro":"203.201.60.12","same_region":"209.150.154.1","neighboring_subregion":"103.29.68.118","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #IN
# resolver_dict={"local":"local","diff_metro":"189.125.18.5","same_region":"190.151.144.21","neighboring_region":"209.250.128.6","neighboring_subregion":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #BR
# resolver_dict={"local":"local","diff_metro":"194.168.4.123","same_region":"193.26.6.215","neighboring_subregion":"159.69.114.157","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GB
# resolver_dict={"local":"local","diff_metro":"202.46.34.74","same_region":"103.29.68.118","neighboring_subregion":"203.201.60.12","neighboring_region":"159.69.114.157","non-neighboring_region":"190.151.144.21"} #CN
# resolver_dict={"local":"local","diff_metro":"196.15.170.131","same_region":"196.43.199.61","neighboring_subregion":"41.57.120.161","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ZA
# resolver_dict={"local":"local","diff_metro":"54.252.183.4","same_region":"210.48.77.68","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #AU
# resolver_dict={"local":"local","diff_metro":"90.159.2.208","same_region":"93.45.98.221","neighboring_subregion":"92.39.141.222","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #TR
# resolver_dict={"local":"local","diff_metro":"92.39.141.222","same_region":"176.107.115.226","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #RU
# resolver_dict={"local":"local","diff_metro":"95.111.253.234","same_region":"62.23.74.39","neighboring_subregion":"90.159.2.208","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #DE
# resolver_dict={"local":"local","diff_metro":"103.28.114.33","same_region":"112.213.88.45","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #ID
# resolver_dict={"local":"local","diff_metro":"83.110.78.132","same_region":"2.89.129.40","neighboring_subregion":"103.29.68.118","neighboring_region":"95.111.253.234","non-neighboring_region":"190.151.144.21"} #AE
# resolver_dict={"local":"local","diff_metro":"91.121.134.117","same_region":"80.113.19.90","neighboring_subregion":"91.190.142.200","neighboring_region":"103.29.118.157","non-neighboring_region":"190.151.144.21"} #FR
# resolver_dict={"local":"local","diff_metro":"190.151.144.21","same_region":"189.125.18.5","neighboring_subregion":"209.250.128.6","neighboring_region":"159.69.114.157","non-neighboring_region":"203.201.60.12"} #AR
# resolver_dict={"local":"local","diff_metro":"80.248.14.50","same_region":"102.176.81.146","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #NG
# resolver_dict={"local":"local","diff_metro":"41.155.240.28","same_region":"80.249.72.60","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #EG
# resolver_dict={"local":"local","diff_metro":"80.87.79.250","same_region":"80.248.14.50","neighboring_subregion":"196.15.170.131","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #GH
# resolver_dict={"local":"local","diff_metro":"80.249.72.60","same_region":"41.155.240.28","neighboring_subregion":"80.248.14.50","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #DZ
# resolver_dict={"local":"local","diff_metro":"90.160.140.67","same_region":"93.42.132.193","neighboring_subregion":"91.121.134.117","neighboring_region":"203.201.60.12","non-neighboring_region":"190.151.144.21"} #ES
"""

ipinfo_url = "https://ipinfo.io/{}/json"
region_fallback = "Unknown"
scope_name_map = {
    "Diff Metro": "Different Metro"
}
# --------------------------------------

def get_ipinfo(ip):
    try:
        r = requests.get(ipinfo_url.format(ip), timeout=3)
        data = r.json()
        country = data.get("country", "N/A")
        org = data.get("org", "")
        asn = org.split()[0] if org else "N/A"
        anycast = "Yes" if data.get("anycast") else "No"
        return country, asn, anycast
    except Exception as e:
        print(f"⚠️ Failed to fetch info for {ip}: {e}")
        return "N/A", "N/A", "Unknown"

def get_region(country_code):
    try:
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except:
        return region_fallback

def parse_resolver_blocks(text):
    matches = re.findall(r'resolver_dict={(.*?)}\s+#([A-Z]{2})', text, re.DOTALL)
    resolver_entries = []

    for block, vantage_country in matches:
        items = block.split(',')
        for item in items:
            key, value = item.strip().split(':')
            scope = key.strip('" ')
            ip = value.strip().strip('"')
            if ip != "local" and scope != "neighboring_subregion":
                formatted_scope = scope.replace('_', ' ').title()
                formatted_scope = scope_name_map.get(formatted_scope, formatted_scope)
                resolver_entries.append((ip, formatted_scope, vantage_country))
                # resolver_entries.append((ip, scope.replace('_', ' ').title(), vantage_country))
    return resolver_entries

# def build_table(entries):
#     print("| IP Address | Vantage Country | Resolver Country | Resolver Region | Scope | ASN | Anycast |")
#     print("|------------|------------------|-------------------|------------------|--------|------|---------|")
#     for ip, scope, vantage_country in entries:
#         resolver_country, asn, anycast = get_ipinfo(ip)
#         resolver_region = get_region(resolver_country)
#         print(f"| {ip} | {vantage_country} | {resolver_country} | {resolver_region} | {scope} | {asn} | {anycast} |")

# if __name__ == "__main__":
#     entries = parse_resolver_blocks(input_data)
#     build_table(entries)

def build_latex_table(entries):
    header = r"""\begin{table}[h]
	\centering
	\scriptsize
	\begin{tabular}{|l|l|l|l|l|l|c|}
		\hline
		\textbf{IP Address} & \textbf{Vantage Country} & \textbf{Resolver Country} & \textbf{Resolver Region} & \textbf{Scope} & \textbf{ASN} & \textbf{Anycast} \\
		\hline"""
    rows = []
    last_vantage = None
    for ip, scope, vantage_country in sorted(entries, key=lambda x: x[2]):
        if vantage_country != last_vantage:
            rows.append(r"\hline")
            last_vantage = vantage_country
        resolver_country, asn, anycast = get_ipinfo(ip)
        resolver_region = get_region(resolver_country)
        row = f"{ip} & {vantage_country} & {resolver_country} & {resolver_region} & {scope} & {asn} & {anycast} \\\\"
        rows.append(row)

    footer = r"""\hline
	\end{tabular}
	\caption{List of DNS resolvers used in our measurements, showing geographic and routing properties.}
	\label{tab:resolver_summary}
\end{table}"""

    full_table = "\n\t\t".join([header] + rows + [footer])
    return full_table

if __name__ == "__main__":
    entries = parse_resolver_blocks(input_data)
    latex_code = build_latex_table(entries)
    with open("results/resolver_summary_table.tex", "w") as f:
        f.write(latex_code)
    print("✅ LaTeX table written to resolver_summary_table.tex")
