"""Run RIPE Atlas ping measurements for DNS-discovered replica IPs.

Inputs: country code, measurement_config.json, dnsRipeResult_<vantage>.json files,
RIPE_ATLAS_API_KEY.
Outputs: results/<country>/PingRipeMsmIds.json and results/<country>/PingRipeResult.json.
"""

import argparse
import json
import os
import time
from datetime import datetime

from ripe.atlas.cousteau import AtlasCreateRequest
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.cousteau import AtlasSource
from ripe.atlas.cousteau import Ping


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


def ping_measurement_ids_path(country):
    return os.path.join(results_dir(country), "PingRipeMsmIds.json")


def ping_results_path(country):
    return os.path.join(results_dir(country), "PingRipeResult.json")


def dns_results_path(country, vantage):
    return os.path.join(results_dir(country), f"dnsRipeResult_{vantage}.json")


def load_json(path):
    with open(path) as fp:
        return json.load(fp)


def dump_json(path, data):
    with open(path, "w") as fp:
        json.dump(data, fp)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run RIPE Atlas ping measurements for a country."
    )
    parser.add_argument(
        "country",
        nargs="?",
        default="US",
        help="Two-letter country code matching data/measurement_config.json (default: US).",
    )
    return parser.parse_args()


def load_existing_ping_measurement_ids(country):
    try:
        return load_json(ping_measurement_ids_path(country))
    except FileNotFoundError:
        return {}


def build_target_ips(country):
    target_ips = set()
    for vantage in VANTAGE_POINTS:
        replicasPerVantage = load_json(dns_results_path(country, vantage))
        ips = []
        for domain in replicasPerVantage:
            ips += replicasPerVantage[domain]
        ips = list(set(ips))
        target_ips.update(ips)
        print("len_ips and replicasPerVantage", len(ips), len(replicasPerVantage))
    print("len_Tips", len(target_ips))
    return list(target_ips)


def runPingMeasurements(ips, runs, country, client_probeid, API_KEY, measurement_ids):
    status = "complete"
    for run in range(runs):
        print("Doing run: ", run)
        count = 0
        for target_ip in ips:
            if target_ip in measurement_ids:
                continue
            status = "incomplete"
            print(
                "running Ping measurement for : ",
                target_ip,
                " \\% done: ",
                100 * count / len(ips),
            )
            count += 1
            ping = Ping(af=4, target=target_ip, description="ping VPN Vantage Points")
            source = AtlasSource(type="probes", value=client_probeid, requested=1)

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=API_KEY,
                measurements=[ping],
                sources=[source],
                is_oneoff=True,
            )

            (is_success, response) = atlas_request.create()
            if is_success:
                _id = response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"], target_ip)
                if target_ip not in measurement_ids:
                    measurement_ids[target_ip] = []
                measurement_ids[target_ip].append(str(_id[0]))
                print(str(_id[0]))

            else:
                print("failed to create measurement: %s" % response, target_ip)
                raise Exception("failed to create measurement: %s" % response)

            dump_json(ping_measurement_ids_path(country), measurement_ids)
    return status


def FetchPingResults(country):
    try:
        measurement_ids = load_json(ping_measurement_ids_path(country))
    except FileNotFoundError:
        return
    try:
        _dict = load_json(ping_results_path(country))
    except FileNotFoundError:
        _dict = {}

    count = 0
    for target_ip in measurement_ids:
        id = measurement_ids[target_ip][0]
        print(target_ip, id)

        if target_ip not in _dict:
            _dict[target_ip] = []

        if count % 20 == 0:
            time.sleep(0.2)
        count += 1

        kwargs = {"msm_id": id}
        is_success, results = AtlasResultsRequest(**kwargs).create()

        if is_success:
            print("Fetching %s" % id, " \\% done", 100 * count / len(measurement_ids))
            for r in results:
                _dict[target_ip].append(r["avg"])
        else:
            print("Fetching wasn't successful: ", id)
        _dict[target_ip] = list(set(_dict[target_ip]))

    dump_json(ping_results_path(country), _dict)


if __name__ == "__main__":
    args = parse_args()
    country = args.country
    os.makedirs(results_dir(country), exist_ok=True)

    config = load_measurement_config(country)
    client_probeid = int(config["client_probeid"])

    API_KEY = os.environ["RIPE_ATLAS_API_KEY"]

    while 1:
        try:
            T_ips = build_target_ips(country)
        except Exception:
            time.sleep(60)
            continue

        status = "incomplete"
        runs = 1
        measurement_ids = load_existing_ping_measurement_ids(country)
        if measurement_ids:
            print(len(measurement_ids))

        try:
            status = runPingMeasurements(
                T_ips, runs, country, client_probeid, API_KEY, measurement_ids
            )
        except Exception as e:
            print("Error in running measurements: ", str(e))
            time.sleep(60)
        if status == "complete":
            print("Ping measurements completed")
            FetchPingResults(country)
            break
