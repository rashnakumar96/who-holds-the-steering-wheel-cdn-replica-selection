"""Run RIPE Atlas DNS measurements for CDN-mapped domains.

Inputs: country code, measurement_config.json, results/<country>/cdn_mapping.json,
RIPE_ATLAS_API_KEY.
Outputs: results/<country>/dnsRipeMsmIds_<vantage>.json and
results/<country>/dnsRipeResult_<vantage>.json.
"""

import argparse
import json
import os
import time
from datetime import datetime

from ripe.atlas.cousteau import AtlasCreateRequest
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.cousteau import AtlasSource
from ripe.atlas.cousteau import Dns
from ripe.atlas.sagan import DnsResult


VANTAGE_POINTS = [
    "local",
    "diff_metro",
    "same_region",
    "neighboring_region",
    "non-neighboring_region",
]


def load_measurement_config(country):
    with open("data/measurement_config.json") as fp:
        config = json.load(fp)

    if country not in config:
        raise KeyError(f"Unsupported country: {country}")

    return config[country]


def results_dir(country):
    return os.path.join("results", country)


def dns_measurement_ids_path(country, vantage):
    return os.path.join(results_dir(country), f"dnsRipeMsmIds_{vantage}.json")


def dns_results_path(country, vantage):
    return os.path.join(results_dir(country), f"dnsRipeResult_{vantage}.json")


def cdn_mapping_path(country):
    return os.path.join(results_dir(country), "cdn_mapping.json")


def load_json(path):
    with open(path) as fp:
        return json.load(fp)


def dump_json(path, data):
    with open(path, "w") as fp:
        json.dump(data, fp)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run RIPE Atlas DNS measurements for a country."
    )
    parser.add_argument(
        "country",
        nargs="?",
        default="US",
        help="Two-letter country code matching data/measurement_config.json (default: US).",
    )
    return parser.parse_args()


def build_dns_measurement(vantage, domain, resolver_dict):
    if vantage == "local":
        return Dns(
            af=4,
            description="Dns Resolution",
            query_class="IN",
            query_type="A",
            query_argument=domain,
            set_rd_bit=True,
            type="dns",
            include_qbuf=True,
            include_Abuf=True,
            use_probe_resolver=True,
        )

    return Dns(
        af=4,
        target=resolver_dict[vantage],
        description="Dns Resolution",
        query_class="IN",
        query_type="A",
        query_argument=domain,
        set_rd_bit=True,
        type="dns",
        include_qbuf=True,
        include_Abuf=True,
        use_probe_resolver=False,
    )


def load_existing_measurement_ids(country, vantage):
    path = dns_measurement_ids_path(country, vantage)
    try:
        return load_json(path)
    except FileNotFoundError:
        return {}


def runDNSMeasurements(
    country,
    vantage,
    fullDomainList,
    runs,
    client_probeid,
    API_KEY,
    measurement_ids,
    resolver_dict,
):

    status = "complete"
    for run in range(runs):
        print("Doing run: ", run)
        count = 0
        for domain in fullDomainList:
            if domain in measurement_ids:
                continue
            print(
                "running dnsRipe measurement for : ",
                domain,
                " \\% done: ",
                100 * count / len(fullDomainList),
            )
            count += 1

            status = "incomplete"
            dns = build_dns_measurement(vantage, domain, resolver_dict)
            source = AtlasSource(
                type="probes",
                value=client_probeid,
                requested=1,
            )

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=API_KEY,
                measurements=[dns],
                sources=[source],
                is_oneoff=True,
            )
            (is_success, response) = atlas_request.create()
            if is_success:
                _id = response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"], domain)
            else:
                print("failed to create measurement: %s" % response)
                raise Exception("failed to create measurement: %s" % response)

            print(str(_id[0]))

            measurement_ids[domain] = str(_id[0])
            dump_json(dns_measurement_ids_path(country, vantage), measurement_ids)
    return status


def FetchDNSResults(country, vantage):
    try:
        measurement_ids = load_json(dns_measurement_ids_path(country, vantage))
    except FileNotFoundError:
        return

    try:
        _dict = load_json(dns_results_path(country, vantage))
    except FileNotFoundError:
        _dict = {}

    count = 0
    for domain in measurement_ids:
        if domain in _dict:
            continue
        id = measurement_ids[domain]
        if count % 20 == 0:
            time.sleep(0.2)
        count += 1

        kwargs = {"msm_id": id}
        print(domain, "Fetching %s" % id, " \\% done", 100 * count / len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        if is_success:
            try:
                my_result = DnsResult(results[0])
            except Exception as e:
                print("Fetching wasn't successful: ", domain, id, str(e))
                continue
        else:
            continue
        try:
            dnsAnswer = my_result.responses[0].abuf.answers
        except Exception as e:
            print("Couldn't decode the answer: ", domain, id, str(e))
            continue
        if domain not in _dict:
            _dict[domain] = []

        for result in dnsAnswer:
            try:
                ip_addr = result.address
                _dict[domain].append(ip_addr)
            except Exception as e:
                print("Error in fetching ip from ans: ", str(e))
                continue
    dump_json(dns_results_path(country, vantage), _dict)


def build_full_domain_list(country, cdns):
    cdnMap = load_json(cdn_mapping_path(country))
    for cdn in cdns:
        if cdn is not None:
            print(cdn, len(set(cdnMap[cdn])))

    fullDomainList = set()
    for cdn in cdns:
        fullDomainList.update(cdnMap[cdn])

    print(len(fullDomainList))
    return fullDomainList


if __name__ == "__main__":
    args = parse_args()
    country = args.country
    os.makedirs(results_dir(country), exist_ok=True)

    config = load_measurement_config(country)

    runs = 1
    cdns = config["cdns"]
    client_probeid = int(config["client_probeid"])
    resolver_dict = config["resolvers"]
    API_KEY = os.environ["RIPE_ATLAS_API_KEY"]

    print("country: ", country)
    fullDomainList = build_full_domain_list(country, cdns)

    while 1:
        countV = 0
        for vantage in VANTAGE_POINTS:
            status = "incomplete"
            print("Running for vantage Point: ", vantage)
            measurement_ids = load_existing_measurement_ids(country, vantage)
            if measurement_ids:
                print(len(measurement_ids))

            try:
                status = runDNSMeasurements(
                    country,
                    vantage,
                    fullDomainList,
                    runs,
                    client_probeid,
                    API_KEY,
                    measurement_ids,
                    resolver_dict,
                )
            except Exception as e:
                print("Error in running measurements: ", str(e))
                time.sleep(60)
            if status == "complete":
                print("DNS measurements completed for vantage: ", vantage)
                countV += 1
        if countV == len(VANTAGE_POINTS):
            for vantage in VANTAGE_POINTS:
                FetchDNSResults(country, vantage)
            break
