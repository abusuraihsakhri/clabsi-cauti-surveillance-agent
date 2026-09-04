# CLABSI & CAUTI Autonomous Surveillance Engine (DeviceHAI Sentinel)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Surveillance Standard: CDC NHSN](https://img.shields.io/badge/Surveillance%20Standard-CDC%20NHSN%20Guidelines-red.svg)](https://www.cdc.gov/nhsn/psc/index.html)
[![Clinical Standard: CLSI M100 / EUCAST](https://img.shields.io/badge/Clinical%20Standard-CLSI%20M100%20%7C%20EUCAST-darkgreen.svg)](https://clsi.org/)

An autonomous, deterministic clinical epidemiology and healthcare-associated infection (HAI) arbitration engine implementing official **CDC NHSN (National Healthcare Safety Network)** surveillance algorithms. DeviceHAI Sentinel eliminates subjective clinician variation by objectively adjudicating Central Line-Associated Bloodstream Infections (**CLABSI**), Catheter-Associated Urinary Tract Infections (**CAUTI**), Mucosal Barrier Injury Laboratory-Confirmed Bloodstream Infections (**MBI-LCBI**), and Secondary Bloodstream Infection (BSI) attributions while computing risk-adjusted Standardized Infection Ratios (**SIR**) and Device Utilization Ratios (**DUR**).

---

## 1. Clinical Epidemiology & Surveillance Standards

Hospital-acquired device-associated infections represent a substantial source of preventable morbidity, mortality, and financial penalty under CMS Hospital-Acquired Condition Reduction Programs (HACRP). This engine automates surveillance according to the following guidelines:

### Central Line-Associated Bloodstream Infection (CLABSI / BSI)
* **Device Eligibility:** Eligible Central Vascular Catheters (CVC, PICC, tunneled/non-tunneled lines, hemodialysis catheters, umbilical catheters). Midline catheters and peripheral IV lines are **strictly excluded**.
* **Dwell Time Requirement:** Central line in place for **> 2 consecutive calendar days** (where Day 1 is the calendar day of device placement) and still present on the Infection Window Period / Date of Event (DOE) or removed on the day prior.
* **Criterion LCBI-1 (Recognized Pathogen):** Recognized pathogen (e.g., *Staphylococcus aureus*, *Enterococcus faecalis*, *Pseudomonas aeruginosa*, *Escherichia coli*, *Klebsiella pneumoniae*, *Candida* spp.) cultured from >= 1 blood specimens, not related to an infection at another site.
* **Criterion LCBI-2 (Common Commensal):** Organism considered normal skin flora (e.g., Coagulase-negative Staphylococci / *S. epidermidis*, *Corynebacterium* spp., *Cutibacterium acnes*, *Bacillus* spp., viridans group *Streptococci*) isolated from >= 2 blood cultures drawn on separate occasions within the Infection Window Period, accompanied by at least one systemic sign:
  * Fever (> 38.0 C), chills, or hypotension (SBP < 90 mmHg) in patients > 1 year.
  * Hypothermia (< 36.0 C), apnea, or bradycardia in infants <= 1 year.
* **Mucosal Barrier Injury (MBI-LCBI):** Patients with severe neutropenia (Absolute Neutrophil Count ANC <= 500 cells/mm3) or allogeneic Hematopoietic Stem Cell Transplant (HSCT) with gastrointestinal Graft-versus-Host Disease (GI-GVHD) isolating designated enterococci, Enterobacteriaceae, viridans streptococci, or *Candida*. MBI-LCBI cases are tracked separately and excluded from public reporting hospital-wide CLABSI denominators.
* **Secondary BSI Attribution:** Positive blood culture meeting NHSN Secondary BSI attribution rules when matched with an established primary source (e.g., CAUTI, pneumonia, surgical site infection).

### Catheter-Associated Urinary Tract Infection (CAUTI / SUTI / ABUTI)
* **Device Eligibility:** Indwelling urethral Foley or suprapubic catheter in place for **> 2 consecutive calendar days** and present on DOE or removed the calendar day prior. Condom catheters, external female collection pouches, straight in-and-out catheterizations, and nephrostomy tubes are **excluded**.
* **Symptomatic UTI (SUTI-1a):**
  * Catheter dwell time > 2 calendar days.
  * Quantitative urine culture yielding >= 10^5 CFU/mL of <= 2 species of microorganisms.
  * At least one clinical symptom: fever (> 38.0 C), suprapubic tenderness, costovertebral angle (CVA) pain/tenderness, or dysuria/urgency/frequency.
* **Fungal Exclusion Rule:** Per CDC NHSN revisions, *Candida* species, yeasts, and molds isolated from urine are **strictly excluded** from CAUTI reporting (classified as colonization/contaminant).
* **Asymptomatic Bacteremic UTI (ABUTI):** Patient without urinary symptoms who has an indwelling catheter > 2 days, urine culture >= 10^5 CFU/mL, and a concurrent positive blood culture matching the identical urinary microorganism.

---

## 2. Epidemiological Benchmark Formulations

```
+-------------------------------------------------------------------------------+
|                       CDC NHSN SURVEILLANCE FORMULAS                         |
+-------------------------------------------------------------------------------+
|                                                                               |
|  1. Standardized Infection Ratio (SIR):                                       |
|                                                                               |
|            Observed HAI Events (O)                                            |
|     SIR = -------------------------                                           |
|            Predicted HAI Events (E)                                           |
|                                                                               |
|  2. Poisson Exact 95% Confidence Interval (Byar's Approximation):             |
|                                                                               |
|                 [                                     1.96  ]3                |
|     O_lower = O * [ 1 - (1 / (9 * O)) - -------------------- ]                |
|                 [                        3 * sqrt(O)         ]                |
|                                                                               |
|                     [                                         1.96  ]3        |
|     O_upper = (O+1) * [ 1 - (1 / (9 * (O + 1))) + -------------------- ]      |
|                     [                              3 * sqrt(O + 1)   ]        |
|                                                                               |
|     SIR_95_CI = [ O_lower / E ,  O_upper / E ]                                |
|                                                                               |
|  3. Device Utilization Ratio (DUR):                                           |
|                                                                               |
|            Device Days (Central Line Days or Foley Catheter Days)             |
|     DUR = --------------------------------------------------------            |
|                           Patient Inpatient Days                              |
|                                                                               |
|  4. Device-Associated Infection Rate:                                         |
|                                                                               |
|                      Observed HAI Events                                      |
|     Rate per 1,000 = --------------------- * 1,000                            |
|                           Device Days                                         |
|                                                                               |
+-------------------------------------------------------------------------------+
```

---

## 3. NHSN Case Classification Matrix

```
+------------------+-------------------+----------------+---------------------+-------------------+
| Clinical Feature | Recognized Path.  | Skin Commensal | Neutropenic (MBI)   | Secondary Source  |
+------------------+-------------------+----------------+---------------------+-------------------+
| Blood Cultures   | >= 1 positive     | >= 2 positive  | >= 1 MBI pathogen   | Matched organism  |
| Central Line     | > 2 calendar days | > 2 cal. days  | > 2 cal. days       | Any dwell time    |
| Systemic Signs   | Not required      | Fever/Chills/BP| Fever / ANC <= 500  | Primary site signs|
| Secondary Site   | None (primary)    | None (primary) | GI tract mucosal    | Positive site cul.|
| Final Verdict    | CONFIRMED_CLABSI  | CONFIRMED_CLAB | MBI_LCBI            | SECONDARY_BSI     |
| Classification   | LCBI-1            | LCBI-2         | MBI-LCBI-1 / 2      | Secondary BSI     |
| Public Reportable| YES (NHSN SIR)    | YES (NHSN SIR) | NO (CMS exempt)     | NO (BSI excluded) |
+------------------+-------------------+----------------+---------------------+-------------------+
```

```
+------------------+--------------------+---------------------+--------------------+--------------------+
| CAUTI Feature    | Bacterial SUTI-1a  | Fungal (Candida)    | Low Colony Count   | ABUTI              |
+------------------+--------------------+---------------------+--------------------+--------------------+
| Catheter Dwell   | > 2 calendar days  | > 2 calendar days   | > 2 calendar days  | > 2 calendar days  |
| Organism Isolated| E. coli, Klebsiella| Candida albicans/spp| Any pathogen       | Matching blood/urin|
| Quantitative CFU | >= 10^5 CFU/mL     | >= 10^5 CFU/mL      | < 10^5 CFU/mL      | >= 10^5 CFU/mL     |
| Clinical Signs   | Fever / CVA / Pain | Any symptoms        | Any symptoms       | Asymptomatic       |
| Final Verdict    | CONFIRMED_CAUTI    | CONTAMINANT/EXCLUDE | CONTAMINANT        | ABUTI              |
| Classification   | SUTI-1a            | Colonization        | Below threshold    | ABUTI              |
| Public Reportable| YES (NHSN SIR)     | NO (NHSN Excluded)  | NO                 | YES (Reportable)   |
+------------------+--------------------+---------------------+--------------------+--------------------+
```

---

## 4. CLI Quickstart & Subcommands

The CLI entry point `cli.py` provides full support for single case evaluations, epidemiological calculations, and batch CSV processing.

### CLABSI Evaluation
```bash
# LCBI-1: Single bottle S. aureus with central line > 2 days
python cli.py clabsi --organism "Staphylococcus aureus" --cultures 1 --days 5 --fever

# LCBI-2: Common commensal (S. epidermidis) requiring 2 positive culture bottles
python cli.py clabsi --organism "Staphylococcus epidermidis" --cultures 2 --days 4 --fever

# MBI-LCBI: Gram-negative bacteremia in neutropenic patient (ANC <= 500)
python cli.py clabsi --organism "Escherichia coli" --cultures 1 --days 6 --anc 300

# JSON Output formatting
python cli.py --json clabsi --organism "Klebsiella pneumoniae" --cultures 1 --days 4 --fever
```

### CAUTI Evaluation
```bash
# Confirmed SUTI-1a with E. coli >= 10^5 CFU/mL and fever
python cli.py cauti --organism "Escherichia coli" --cfu 100000 --days 4 --fever

# Candida rule-out: Strictly excluded under NHSN criteria
python cli.py cauti --organism "Candida albicans" --cfu 100000 --days 5 --fever

# Asymptomatic Bacteremic UTI (ABUTI)
python cli.py cauti --organism "Proteus mirabilis" --cfu 150000 --days 5 --blood-match
```

### Epidemiological SIR & DUR Metrics
```bash
# Compute facility SIR with exact Poisson 95% CI and Device Utilization Ratio
python cli.py metrics --observed 4 --predicted 5.2 --device-days 1200 --patient-days 3500
```

### Batch Surveillance Processing
Process inpatient surveillance records from an input CSV file and output standardized arbitration verdicts:
```bash
# Batch process sample records
python cli.py batch -i sample.csv -o results.csv

# Long flag syntax
python cli.py batch --input sample.csv --output results.csv
```

### Interactive Wizard
```bash
python cli.py interactive
```

---

## 5. Input Data Schema (`sample.csv`)

| Field | Type | Description | Example |
|:------|:-----|:------------|:--------|
| `case_id` | String | Unique surveillance record identifier | `CASE-001` |
| `patient_id` | String | De-identified patient token | `PT-5120` |
| `surveillance_type` | String | Surveillance protocol (`clabsi` or `cauti`) | `clabsi` |
| `organism` | String | Isolated microorganism taxon | `Staphylococcus aureus` |
| `device_days` | Integer | Consecutive calendar days catheter/line in place | `4` |
| `fever` | Boolean | Body temperature > 38.0 C | `true` |
| `hypotension` | Boolean | Systolic blood pressure < 90 mmHg | `false` |
| `anc` | Float | Absolute neutrophil count in cells/mm3 | `2100` |
| `num_cultures` | Integer | Count of positive blood culture bottles | `1` |
| `colony_count` | Float | Quantitative urine bacterial colony count in CFU/mL | `150000` |
| `num_species` | Integer | Microorganism species count in urine culture | `1` |
| `secondary_site` | String | Documented primary site matching organism | `Urine (CAUTI)` |

---

## 6. Output Schema (`results.csv`)

The engine appends adjudicated surveillance findings to each input record:

| Output Field | Description | Possible Values |
|:-------------|:------------|:----------------|
| `verdict` | Final NHSN surveillance adjudication | `confirmed_clabsi`, `confirmed_cauti`, `mbi_lcbi`, `secondary_bsi`, `contaminant_or_colonization`, `device_days_insufficient`, `no_infection_event` |
| `classification_type` | Specific NHSN case definition code | `LCBI-1`, `LCBI-2`, `LCBI-3`, `MBI-LCBI-1`, `SUTI-1a`, `ABUTI`, `Secondary BSI`, `None` |
| `lcbi_type` | CLABSI-specific classification | `LCBI-1`, `LCBI-2`, `LCBI-3`, `MBI-LCBI-1`, `Secondary BSI` |
| `cauti_type` | CAUTI-specific classification | `SUTI-1a`, `ABUTI`, `None` |
| `is_reportable` | Whether event is reportable in NHSN public SIR | `True` / `False` |
| `rule_out_reason` | Clinical justification and guideline citation | Detailed clinical explanation |

---

## 7. Verification & CI/CD

Run test suite:
```bash
python -m pytest -p no:zarr -v
```

Execute CLI batch smoke test:
```bash
python cli.py batch -i sample.csv -o out_smoke.csv
```

All 36 unit tests validate complete coverage of:
1. NHSN LCBI-1, LCBI-2, and LCBI-3 clinical criteria.
2. Mucosal Barrier Injury (MBI-LCBI) oncology/neutropenia exemptions.
3. Secondary BSI attribution matrices (Urine, Pneumonia, SSI).
4. Indwelling urinary catheter SUTI-1a and ABUTI definitions.
5. Strict exclusion of *Candida* and fungal urinary isolates.
6. Exact Poisson 95% confidence intervals and SIR interpretations.
7. Batch CSV intake and automated surveillance reporting.
