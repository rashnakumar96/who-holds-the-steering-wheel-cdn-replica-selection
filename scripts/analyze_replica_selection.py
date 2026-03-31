"""Analyze DNS and ping measurements to infer CDN steering behavior.

Inputs: analysis_config.json and per-country dnsRipeResult_<vantage>.json,
PingRipeResult.json, and cdn_mapping.json.
Outputs: per-country RTT CDF plots, RTTs.json, and resolver_scope_ks_distances.{csv,json}.
"""

import json
import os
import statistics
import ipaddress
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import tldextract
from tabulate import tabulate
from scipy.stats import ks_2samp


VANTAGE_POINTS = [
    "local",
    "diff_metro",
    "same_region",
    "neighboring_region",
    "non-neighboring_region",
]


def results_path(*parts):
    return os.path.join("results", *parts)


def graphs_path(*parts):
    return os.path.join("graphs", *parts)


def load_json(path):
    with open(path) as fp:
        return json.load(fp)


def dump_json(path, data):
    with open(path, "w") as fp:
        json.dump(data, fp)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_analysis_config():
    return load_json(os.path.join("data", "analysis_config.json"))


def ecdf(data):
    x = np.sort(data)
    n = x.size
    y = np.arange(1, n + 1) / float(n)
    return x, y

def collectResults(cdns, vantagePoints, country, latencyResult, cdnMap):
    results = {}

    for cdn in cdns:
        results[cdn] = {}
        domains = set(cdnMap[cdn])

        for vantage in vantagePoints:
            results[cdn][vantage] = []
            replicasPerVantage = load_json(results_path(country, f"dnsRipeResult_{vantage}.json"))

            ips = []
            for domain in domains:
                if domain in replicasPerVantage:
                    ips += replicasPerVantage[domain]

            for replicaip in set(ips):
                if replicaip in latencyResult and len(latencyResult[replicaip]) > 0:
                    latency = statistics.mean(latencyResult[replicaip])
                    results[cdn][vantage].append(latency)

            print(cdn, vantage, len(results[cdn][vantage]))
        print("\n")

    dump_json(results_path(country, "RTTs.json"), results)
    return results


def plotrttCDFs(country, results, resolver_dict, vantagePoints):
    ensure_dir("graphs")
    ensure_dir(graphs_path(country))

    colors = {
        "local": "purple",
        "diff_metro": "r",
        "same_region": "green",
        "neighboring_region": "brown",
        "non-neighboring_region": "blue",
    }
    label_mapping = {
        "local": "Local",
        "diff_metro": "Different Metro",
        "same_region": "Same Region",
        "neighboring_region": "Neighboring Region",
        "non-neighboring_region": "Non-Neighboring Region",
    }

    for cdn in results:
        print("country: ", country, cdn)

        for resolverVantage in vantagePoints:
            rtts = np.sort(results[cdn][resolverVantage])
            x, y = ecdf(rtts)
            formatted_label = label_mapping[resolverVantage]

            try:
                p10 = np.percentile(rtts, 20)
                p70 = np.percentile(rtts, 70)
                yvals = np.arange(len(rtts)) / float(len(rtts))
                idx = np.where((rtts >= p10) & (rtts <= p70))
                plt.scatter(
                    np.array(rtts)[idx],
                    yvals[idx],
                    color=colors[resolverVantage],
                    label=formatted_label,
                    linestyle="solid",
                    linewidth=2,
                )
            except Exception:
                plt.scatter(
                    x,
                    y,
                    color=colors[resolverVantage],
                    label=formatted_label,
                    linestyle="solid",
                    linewidth=2,
                )

        plot_name = "Edgio" if cdn == "EdgeCast" else cdn
        legend = plt.legend(
            loc="center right",
            bbox_to_anchor=(-0.08, 0.2),
            ncol=1,
            frameon=True,
        )
        legend.get_frame().set_linewidth(1.5)
        legend.get_frame().set_edgecolor("black")
        legend.get_frame().set_facecolor("white")
        for text in legend.get_texts():
            text.set_fontweight("bold")
            text.set_fontsize(20)

        plt.ylim(0.18, 0.72)
        for spine in plt.gca().spines.values():
            spine.set_linewidth(1.5)
            spine.set_edgecolor("black")

        plt.grid()
        plt.xlabel("RTT [ms]", fontsize=14, fontweight="bold")
        plt.ylabel("CDF", fontsize=14, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        if country == "GB":
            output_path = graphs_path(country, f"{plot_name}_UK.pdf")
        else:
            output_path = graphs_path(country, f"{plot_name}_{country}.pdf")
        plt.savefig(output_path, dpi=300, format="pdf")
        plt.clf()


def MiddlePercentileRTTs(rtts, lower_bound, upper_bound):
    rtts = np.sort(rtts)
    lower_percentile = np.percentile(rtts, lower_bound)
    upper_percentile = np.percentile(rtts, upper_bound)
    idx = np.where((rtts >= lower_percentile) & (rtts <= upper_percentile))
    return np.array(rtts)[idx]


def Kolmogorov_SmirnovTest(data1, data2):
    statistic, p_value = ks_2samp(data1, data2)
    return statistic, p_value


def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == "":
        ext = ext[1:]
    return ".".join(ext)


def computeCDFDistance(countries, cdnCountryMap, resolver_dict):
    distance_dict = {}

    for country in countries:
        latencyResult = load_json(results_path(country, "PingRipeResult.json"))
        cdnMap = load_json(results_path(country, "cdn_mapping.json"))
        results = collectResults(cdnCountryMap[country], VANTAGE_POINTS, country, latencyResult, cdnMap)
        plotrttCDFs(country, results, resolver_dict, VANTAGE_POINTS)

        for cdn in cdnCountryMap[country]:
            print(cdn)
            distance_dict.setdefault(cdn, {})
            distance_dict[cdn].setdefault(country, {})

            vantages = list(results[cdn])
            for i in range(len(vantages)):
                for j in range(i + 1, len(vantages)):
                    vantage_i = vantages[i]
                    vantage_j = vantages[j]
                    try:
                        ks_dist = Kolmogorov_SmirnovTest(
                            MiddlePercentileRTTs(results[cdn][vantage_i], 20, 70),
                            MiddlePercentileRTTs(results[cdn][vantage_j], 20, 70),
                        )
                    except Exception:
                        ks_dist = Kolmogorov_SmirnovTest(
                            results[cdn][vantage_i],
                            results[cdn][vantage_j],
                        )
                    distance_dict[cdn][country][f"{vantage_i}+{vantage_j}"] = ks_dist[0]

    resolver_short = {
        "local": "local",
        "diff_metro": "diff_metro",
        "same_region": "same_R",
        "neighboring_region": "neigh_R",
        "non-neighboring_region": "non-neigh_R",
    }
    ordered_vantage_pairs = [
        f"{left}+{right}"
        for index, left in enumerate(VANTAGE_POINTS)
        for right in VANTAGE_POINTS[index + 1 :]
    ]

    table = []
    vPs = []
    for vantages in ordered_vantage_pairs:
        left, right = vantages.split("+")
        vPs.append((resolver_short[left], resolver_short[right]))
    table.append(["CDN", "Country"] + vPs)

    for cdn in distance_dict:
        for country in distance_dict[cdn]:
            row = [cdn, country]
            for vantages in ordered_vantage_pairs:
                row.append(distance_dict[cdn][country].get(vantages, -1))
            table.append(row)

    content = tabulate(table, headers="firstrow", tablefmt="tsv")
    with open(results_path("resolver_scope_ks_distances.csv"), "w") as text_file:
        text_file.write(content)
    dump_json(results_path("resolver_scope_ks_distances.json"), distance_dict)
    return distance_dict


def classification(cdn, country):
    distance_dict = load_json(results_path("resolver_scope_ks_distances.json"))
    different_region = distance_dict[cdn][country]["local+non-neighboring_region"]
    same_region = distance_dict[cdn][country]["local+same_region"]

    if different_region < 0.4:
        return "Anycast"
    if different_region >= 0.7:
        if same_region < 0.4:
            return "Regional Anycast"
        return "DNS"
    return "Mixed Approach"


if __name__ == "__main__":
    config = load_analysis_config()
    resolver_dict = config["resolver_labels"]
    countries = config["countries"]
    cdnCountryMap = config["cdn_country_map"]

    computeCDFDistance(countries, cdnCountryMap, resolver_dict)
