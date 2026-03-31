# Who Holds the Steering Wheel? Opacity and Consolidation in CDN Replica Selection

This repository contains the public workflow for measuring and analyzing CDN replica selection across multiple resolver locations using RIPE Atlas DNS and ping measurements.

The workflow has three main steps:

1. Run DNS measurements for a country against CDN-mapped domains using multiple resolver locations.
2. Run ping measurements to the replica IPs discovered by DNS.
3. Analyze the DNS and ping results to build RTT datasets, generate CDF plots, and compute resolver-scope KS distances.

## Citation

If you use this repository or build on this dataset or methodology, please cite the paper:

- Rashna Kumar, Fabián E. Bustamante, and Marcel Flores. "Who Holds the Steering Wheel? Opacity and Consolidation in CDN Replica Selection." 1st New Ideas in Networked Systems (NINeS 2026), Article 23. DOI: `10.4230/OASIcs.NINeS.2026.23`

```bibtex
@inproceedings{kumar2026steeringwheel,
  author = {Kumar, Rashna and Bustamante, Fabi{\'a}n E. and Flores, Marcel},
  title = {Who Holds the Steering Wheel? Opacity and Consolidation in CDN Replica Selection},
  booktitle = {1st New Ideas in Networked Systems (NINeS 2026)},
  series = {OASIcs},
  year = {2026},
  articleno = {23},
  doi = {10.4230/OASIcs.NINeS.2026.23},
  publisher = {Schloss Dagstuhl -- Leibniz-Zentrum f{\"u}r Informatik}
}
```

## Repository Layout

- `scripts/`
  - measurement and analysis scripts
- `data/`
  - configuration and supporting metadata used by the scripts
- `results/`
  - per-country measurement files and global analysis outputs
- `paper.pdf`
  - manuscript describing the study

## Scripts

### `scripts/runDNSMeasurements.py`

Runs RIPE Atlas DNS measurements for one country across five resolver scopes:

- `local`
- `diff_metro`
- `same_region`
- `neighboring_region`
- `non-neighboring_region`

Inputs:

- CLI:
  - positional `country`
- environment:
  - `RIPE_ATLAS_API_KEY`
- files:
  - `data/measurement_config.json`
  - `results/<country>/cdn_mapping.json`

Outputs:

- `results/<country>/dnsRipeResult_local.json`
- `results/<country>/dnsRipeResult_diff_metro.json`
- `results/<country>/dnsRipeResult_same_region.json`
- `results/<country>/dnsRipeResult_neighboring_region.json`
- `results/<country>/dnsRipeResult_non-neighboring_region.json`

Runtime working files:

- `results/<country>/dnsRipeMsmIds_<vantage>.json`

Example:

```bash
export RIPE_ATLAS_API_KEY=...
python3 scripts/runDNSMeasurements.py US
```

### `scripts/runPingMeasurements.py`

Runs RIPE Atlas ping measurements to replica IPs discovered in the DNS results for one country.

Inputs:

- CLI:
  - positional `country`
- environment:
  - `RIPE_ATLAS_API_KEY`
- files:
  - `data/measurement_config.json`
  - `results/<country>/dnsRipeResult_local.json`
  - `results/<country>/dnsRipeResult_diff_metro.json`
  - `results/<country>/dnsRipeResult_same_region.json`
  - `results/<country>/dnsRipeResult_neighboring_region.json`
  - `results/<country>/dnsRipeResult_non-neighboring_region.json`

Outputs:

- `results/<country>/PingRipeResult.json`

Runtime working file:

- `results/<country>/PingRipeMsmIds.json`

Example:

```bash
export RIPE_ATLAS_API_KEY=...
python3 scripts/runPingMeasurements.py US
```

### `scripts/analyze_replica_selection.py`

Builds RTT datasets from DNS and ping results, generates per-country RTT CDF plots, and computes resolver-scope KS distances.

Inputs:

- CLI:
  - none
- environment:
  - none
- files:
  - `data/analysis_config.json`
  - `results/<country>/cdn_mapping.json`
  - `results/<country>/PingRipeResult.json`
  - `results/<country>/dnsRipeResult_local.json`
  - `results/<country>/dnsRipeResult_diff_metro.json`
  - `results/<country>/dnsRipeResult_same_region.json`
  - `results/<country>/dnsRipeResult_neighboring_region.json`
  - `results/<country>/dnsRipeResult_non-neighboring_region.json`

Outputs:

- `results/<country>/RTTs.json`
- `results/resolver_scope_ks_distances.csv`
- `results/resolver_scope_ks_distances.json`

Helper functions in this script can also classify a CDN/country pair from the KS-distance JSON.

Example:

```bash
python3 scripts/analyze_replica_selection.py
```

## Data Directory

Required for the main workflow:

- `data/measurement_config.json`
  - per-country RIPE Atlas probe IDs
  - CDN lists
  - resolver IPs for the five scopes
- `data/analysis_config.json`
  - analysis country list
  - country-to-CDN mapping used by the analysis workflow
  - resolver labels used for analysis metadata

Other files in `data/` may still be useful, but they are not required for the main workflow described here.

## Results Directory

Each country has a subdirectory under `results/`, for example `results/US/`.

Per-country files used by the workflow:

- `cdn_mapping.json`
- `dnsRipeResult_local.json`
- `dnsRipeResult_diff_metro.json`
- `dnsRipeResult_same_region.json`
- `dnsRipeResult_neighboring_region.json`
- `dnsRipeResult_non-neighboring_region.json`
- `PingRipeResult.json`
- `RTTs.json`

Global analysis outputs:

- `results/resolver_scope_ks_distances.csv`
- `results/resolver_scope_ks_distances.json`

Runtime measurement state:

- `dnsRipeMsmIds_<vantage>.json`
- `PingRipeMsmIds.json`

Country folders may also contain resource-collection or auxiliary analysis files such as:

- `ResourcesF.json`
  - collected resource URLs observed for the country
- `ResourcescdnMapping.json`
  - mapping from CDN name to associated resource URLs
- `ResourcesDomainsF.json`
  - collected resource-domain lists from the earlier resource workflow
- `resourcesSizeType_*.json`
  - per-CDN resource metadata such as object size and content type

## Main Workflow

### 1. Run DNS measurements

```bash
export RIPE_ATLAS_API_KEY=...
python3 scripts/runDNSMeasurements.py US
```

### 2. Run ping measurements

```bash
export RIPE_ATLAS_API_KEY=...
python3 scripts/runPingMeasurements.py US
```

### 3. Run the analysis

```bash
python3 scripts/analyze_replica_selection.py
```

This reads the configured country set from `data/analysis_config.json`, writes per-country `RTTs.json`, generates per-country CDF plots, and writes the global KS-distance summaries.

## Inputs and Outputs Summary

Inputs you provide or maintain:

- `country` as a CLI argument for `runDNSMeasurements.py` and `runPingMeasurements.py`
- `RIPE_ATLAS_API_KEY` as an environment variable for `runDNSMeasurements.py` and `runPingMeasurements.py`
- `data/measurement_config.json`
- `data/analysis_config.json`
- `results/<country>/cdn_mapping.json`

Outputs produced by the workflow:

- `results/<country>/dnsRipeResult_<vantage>.json`
- `results/<country>/PingRipeResult.json`
- `results/<country>/RTTs.json`
- `results/resolver_scope_ks_distances.csv`
- `results/resolver_scope_ks_distances.json`
- `graphs/<country>/*.pdf`
