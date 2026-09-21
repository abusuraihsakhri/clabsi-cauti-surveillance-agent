# CLABSI & CAUTI Surveillance Utilities

Browser and command-line utilities for screening selected **2026 CDC National Healthcare Safety Network (NHSN)** CLABSI, CAUTI, MBI-LCBI, and device-associated infection metrics.

The project is intended for surveillance workflow support, testing, and education. It is **not** a complete implementation of every NHSN rule, the NHSN Terminology Browser, or facility-specific reporting policy, and it does not replace infection-prevention review.

## What it includes

- CLABSI screening for selected LCBI-1, LCBI-2, and LCBI-3 elements.
- Selected MBI-LCBI host-factor handling, including the 2026 requirement for at least two qualifying ANC/WBC days in the seven-day window.
- Secondary BSI attribution input for a documented matching primary site.
- CAUTI SUTI-1a and catheter-associated ABUTI screening.
- Correct handling of urgency/frequency/dysuria timing: these symptoms are only eligible when documented while the indwelling urinary catheter is not in place.
- SIR, approximate 95% SIR interval, device-utilization ratio, and infection rate per 1,000 device-days.
- CSV batch processing.
- A compact browser UI that runs the Python surveillance module client-side with Pyodide.
- Optional FastAPI endpoints for local/server use.

## Browser application

The GitHub Pages interface uses the same `clabsi_cauti_surveillance.py` module as the command-line workflow. Python runs in the browser through a pinned Pyodide runtime.

Form values are processed locally by the application and are not sent to an application backend. The browser must fetch Pyodide from jsDelivr when the runtime loads, so normal browser/network metadata may still be visible to that CDN. Do not enter protected health information into public/shared devices or workflows without appropriate institutional controls.

A verified live application link will be placed here after the Pages deployment is confirmed.

## Installation

Requires Python 3.10 or later.

```bash
git clone https://github.com/abusuraihsakhri/clabsi-cauti-surveillance-agent.git
cd clabsi-cauti-surveillance-agent
python -m pip install -e .
```

For the optional FastAPI service:

```bash
python -m pip install -e ".[server]"
clabsi-cauti-surveillance-agent serve
```

## Command-line examples

CLABSI:

```bash
clabsi-cauti-surveillance-agent clabsi \
  --organism "Staphylococcus aureus" \
  --cultures 1 \
  --days 5 \
  --fever
```

MBI host-factor screening with two qualifying low-count days:

```bash
clabsi-cauti-surveillance-agent clabsi \
  --organism "Escherichia coli" \
  --cultures 1 \
  --days 6 \
  --anc 300 \
  --anc-days 2
```

CAUTI:

```bash
clabsi-cauti-surveillance-agent cauti \
  --organism "Escherichia coli" \
  --cfu 100000 \
  --days 4 \
  --fever
```

If urgency, frequency, or dysuria is used, explicitly confirm that the symptom occurred while the IUC was absent:

```bash
clabsi-cauti-surveillance-agent cauti \
  --organism "Escherichia coli" \
  --cfu 100000 \
  --days 4 \
  --dysuria \
  --urinary-symptoms-without-iuc
```

SIR/DUR metrics:

```bash
clabsi-cauti-surveillance-agent metrics \
  --observed 4 \
  --predicted 5.2 \
  --device-days 1200 \
  --patient-days 3500
```

Batch processing:

```bash
clabsi-cauti-surveillance-agent batch -i sample.csv -o surveillance_results.csv
```

The batch reader supports the core fields demonstrated in `sample.csv`, including `anc_qualifying_days`, CAUTI symptom fields, matching blood culture, and secondary-site attribution.

## Python API

```python
from clabsi_cauti_surveillance import evaluate_clabsi

result = evaluate_clabsi(
    organism_name="Staphylococcus aureus",
    number_of_positive_blood_cultures=1,
    central_line_days=4,
)

print(result.verdict.value)
```

## Validation

Run the test suite and CLI smoke tests:

```bash
python -m pytest -p no:zarr -q
clabsi-cauti-surveillance-agent clabsi --organism "Staphylococcus aureus" --cultures 1 --days 4
python cli.py batch -i sample.csv -o out_smoke.csv
```

GitHub Actions also compiles the source, installs the package, runs the tests on supported Python versions, exercises the installed console entry point, checks the batch workflow, and validates the static Pages inputs.

## Clinical scope and limitations

The core engine intentionally implements a bounded set of criteria rather than claiming full NHSN conformance. In particular:

- The local organism registry is a convenience subset and does not replace the current NHSN Terminology Browser. Unlisted CLABSI organisms return an indeterminate terminology-review result rather than being assumed to be recognized pathogens.
- The caller is responsible for establishing Infection Window Period, Repeat Infection Timeframe, present-on-admission/healthcare-associated timing, location attribution, and other criteria not represented by the function arguments.
- The HSCT MBI flag is caller-verified; the code does not reconstruct transplant timing or GI-GVHD/diarrhea documentation.
- Secondary BSI attribution is represented as an explicit input rather than a complete site-specific attribution engine.
- SIR confidence bounds use a Byar approximation for non-zero observed counts. Use official NHSN analytic outputs for regulatory reporting.
- Output fields and follow-up notes are surveillance aids, not treatment recommendations.

For current definitions, use the official CDC NHSN Patient Safety Component manuals and checklists:

- [Bloodstream Infection (BSI) Event](https://www.cdc.gov/nhsn/pdfs/pscmanual/4psc_clabscurrent.pdf)
- [Urinary Tract Infection (UTI) Event](https://www.cdc.gov/nhsn/pdfs/pscmanual/7psccauticurrent.pdf)
- [NHSN Patient Safety Component](https://www.cdc.gov/nhsn/psc/index.html)

## Technology

- Python standard library for the core surveillance engine.
- Pyodide 314.0.7 for browser-side Python execution.
- HTML/CSS/JavaScript for the static interface.
- Optional FastAPI and Uvicorn for local API service.
- GitHub Actions for tests and GitHub Pages deployment.

The browser interface targets current Chromium, Firefox, and Safari releases with WebAssembly support. JavaScript must be enabled.

## License

MIT. See [LICENSE](LICENSE).
