#!/usr/bin/env python3
"""
CLABSI & CAUTI Surveillance Utilities
=====================================
Deterministic clinical epidemiology utilities implementing selected 2026 CDC
NHSN (National Healthcare Safety Network) surveillance criteria:
- Central Line-Associated Bloodstream Infection (CLABSI)
- Catheter-Associated Urinary Tract Infection (CAUTI)
- Mucosal Barrier Injury Laboratory-Confirmed Bloodstream Infection (MBI-LCBI)
- Secondary Bloodstream Infection (BSI) Attribution Matrix
- Standardized Infection Ratio (SIR) & Device Utilization Ratio (DUR)

Stdlib only — no external dependencies.
"""

import csv
import datetime
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set


# ==============================================================================
# ENUMS & TAXONOMY REGISTRIES
# ==============================================================================

class DeviceType(str, Enum):
    CENTRAL_LINE = "central_line"
    PICC = "picc"
    PORT = "implanted_port"
    TUNNELED_CVC = "tunneled_cvc"
    NON_TUNNELED_CVC = "non_tunneled_cvc"
    DIALYSIS_CATHETER = "dialysis_catheter"
    UMBILICAL_CATHETER = "umbilical_catheter"
    FOLEY_CATHETER = "indwelling_urinary_catheter"
    MIDLINE = "midline"  # NOT a central line per NHSN
    PERIPHERAL_IV = "peripheral_iv"  # NOT a central line


class OrganismType(str, Enum):
    RECOGNIZED_PATHOGEN = "recognized_pathogen"
    COMMON_COMMENSAL = "common_commensal"
    MBI_ORGANISM = "mbi_organism"
    YEAST_FUNGAL = "yeast_fungal"
    CONTAMINANT_EXCLUDED = "excluded_pathogen"


class SurveillanceVerdict(str, Enum):
    CONFIRMED_CLABSI = "confirmed_clabsi"
    MBI_LCBI = "mbi_lcbi"
    SECONDARY_BSI = "secondary_bsi"
    CONFIRMED_CAUTI = "confirmed_cauti"
    ABUTI = "asymptomatic_bacteremic_uti"
    CONTAMINANT_OR_COLONIZATION = "contaminant_or_colonization"
    DEVICE_DAYS_INSUFFICIENT = "device_days_insufficient"
    NO_EVENT = "no_infection_event"


# CDC NHSN Organism Knowledge Base
NHSN_ORGANISM_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Recognized Bacterial / Fungal Pathogens (LCBI-1)
    "staphylococcus aureus": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "mrsa": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "mssa": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "enterococcus faecalis": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "enterococcus faecium": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "vre": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "escherichia coli": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "klebsiella pneumoniae": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "klebsiella oxytoca": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "pseudomonas aeruginosa": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "enterobacter cloacae": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "serratia marcescens": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "proteus mirabilis": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "citrobacter freundii": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "acinetobacter baumannii": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "stenotrophomonas maltophilia": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False},
    "bacteroides fragilis": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True},
    "candida albicans": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True, "fungal": True},
    "candida glabrata": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True, "fungal": True},
    "candida parapsilosis": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False, "fungal": True},
    "candida tropicalis": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True, "fungal": True},
    "candida krusei": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": True, "fungal": True},
    "candida auris": {"type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False, "fungal": True},

    # Common Skin Commensals (LCBI-2: Requires >= 2 separate positive cultures + symptoms)
    "coagulase-negative staphylococcus": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "staphylococcus epidermidis": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "staphylococcus hominis": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "staphylococcus haemolyticus": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "staphylococcus capitis": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "corynebacterium": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "corynebacterium striatum": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "bacillus": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "micrococcus": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "micrococcus luteus": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "cutibacterium acnes": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "propionibacterium acnes": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": False},
    "viridans streptococci": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": True},
    "streptococcus mitis": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": True},
    "streptococcus oralis": {"type": OrganismType.COMMON_COMMENSAL, "is_mbi": True},
}


# ==============================================================================
# CLABSI SURVEILLANCE ENGINE
# ==============================================================================

@dataclass
class CLABSIAssessment:
    verdict: SurveillanceVerdict
    lcbi_type: Optional[str]  # LCBI-1, LCBI-2, LCBI-3, MBI-LCBI-1, MBI-LCBI-2, Secondary
    is_reportable_clabsi: bool
    organism_name: str
    organism_type: str
    central_line_days: int
    criteria_met: List[str]
    rule_out_rationale: Optional[str]
    prevention_interventions: List[str]


def evaluate_clabsi(
    organism_name: str,
    number_of_positive_blood_cultures: int,
    central_line_days: int,
    line_in_place_on_doe_or_removed_day_prior: bool = True,
    patient_has_central_line: bool = True,
    is_midline_or_peripheral_only: bool = False,
    fever_gt_38c: bool = False,
    hypotension_sbp_lt_90: bool = False,
    chills_present: bool = False,
    patient_age_years: int = 45,
    hypothermia_lt_36c: bool = False,
    apnea_or_bradycardia: bool = False,
    absolute_neutrophil_count_anc: Optional[float] = None,
    neutropenia_qualifying_days: int = 0,
    is_hsct_with_gi_gvhd: bool = False,
    has_matching_positive_site_culture: bool = False,
    primary_site_of_infection: Optional[str] = None,
) -> CLABSIAssessment:
    """
    Evaluate selected CDC NHSN CLABSI / MBI-LCBI / Secondary BSI criteria.

    neutropenia_qualifying_days is the number of separate days in the
    7-day MBI window with ANC and/or WBC <500 cells/mm3. NHSN requires at
    least two qualifying days. is_hsct_with_gi_gvhd should only be set after
    the caller has verified the current NHSN allogeneic-HSCT host criterion.
    """
    org_key = organism_name.strip().lower()
    org_info = NHSN_ORGANISM_REGISTRY.get(org_key, {
        "type": OrganismType.RECOGNIZED_PATHOGEN, "is_mbi": False
    })
    org_type = org_info["type"]
    is_mbi_eligible = org_info.get("is_mbi", False)

    # 1. Device Eligibility Check
    if is_midline_or_peripheral_only or not patient_has_central_line:
        return CLABSIAssessment(
            verdict=SurveillanceVerdict.NO_EVENT,
            lcbi_type=None,
            is_reportable_clabsi=False,
            organism_name=organism_name,
            organism_type=org_type.value,
            central_line_days=central_line_days,
            criteria_met=[],
            rule_out_rationale="Patient does not have an eligible Central Line (Midline and Peripheral IVs are excluded from NHSN CLABSI definition).",
            prevention_interventions=["Ensure correct vascular access device documentation in EHR."],
        )

    if central_line_days <= 2:
        return CLABSIAssessment(
            verdict=SurveillanceVerdict.DEVICE_DAYS_INSUFFICIENT,
            lcbi_type=None,
            is_reportable_clabsi=False,
            organism_name=organism_name,
            organism_type=org_type.value,
            central_line_days=central_line_days,
            criteria_met=[f"Central line dwell time {central_line_days} days (NHSN requires > 2 consecutive calendar days)."],
            rule_out_rationale=f"Central line in place for {central_line_days} calendar days; NHSN CLABSI criteria require central line in place > 2 consecutive calendar days (Day 1 = insertion day).",
            prevention_interventions=["Track line days daily; continue central line maintenance bundle."],
        )

    if not line_in_place_on_doe_or_removed_day_prior:
        return CLABSIAssessment(
            verdict=SurveillanceVerdict.NO_EVENT,
            lcbi_type=None,
            is_reportable_clabsi=False,
            organism_name=organism_name,
            organism_type=org_type.value,
            central_line_days=central_line_days,
            criteria_met=[],
            rule_out_rationale="Central line was removed > 1 calendar day prior to the Date of Event (DOE).",
            prevention_interventions=[],
        )

    # 2. Secondary BSI Attribution Check
    if has_matching_positive_site_culture and primary_site_of_infection:
        return CLABSIAssessment(
            verdict=SurveillanceVerdict.SECONDARY_BSI,
            lcbi_type="Secondary BSI",
            is_reportable_clabsi=False,
            organism_name=organism_name,
            organism_type=org_type.value,
            central_line_days=central_line_days,
            criteria_met=[f"Blood isolate matches organism from primary infection site ({primary_site_of_infection}) within Infection Window Period."],
            rule_out_rationale=f"BSI is secondary to documented {primary_site_of_infection} infection. Excluded from primary CLABSI reporting per NHSN Secondary BSI Attribution rules.",
            prevention_interventions=[f"Treat primary source of infection ({primary_site_of_infection})."],
        )

    # 3. Mucosal Barrier Injury (MBI-LCBI) Check
    has_low_anc = absolute_neutrophil_count_anc is not None and absolute_neutrophil_count_anc < 500.0
    is_severely_neutropenic = has_low_anc and neutropenia_qualifying_days >= 2
    is_mbi_candidate = (is_severely_neutropenic or is_hsct_with_gi_gvhd) and is_mbi_eligible

    # 4. LCBI Evaluation
    has_symptoms = fever_gt_38c or hypotension_sbp_lt_90 or chills_present
    is_infant = (patient_age_years <= 1)
    has_infant_symptoms = has_symptoms or hypothermia_lt_36c or apnea_or_bradycardia

    # Case A: Recognized Pathogen
    if org_type == OrganismType.RECOGNIZED_PATHOGEN:
        if number_of_positive_blood_cultures >= 1:
            if is_mbi_candidate:
                return CLABSIAssessment(
                    verdict=SurveillanceVerdict.MBI_LCBI,
                    lcbi_type="MBI-LCBI-1",
                    is_reportable_clabsi=False,  # MBI-LCBIs are stratified separately from public CLABSI rates
                    organism_name=organism_name,
                    organism_type=org_type.value,
                    central_line_days=central_line_days,
                    criteria_met=[
                        "Recognized pathogen from >= 1 blood culture.",
                        f"Eligible MBI organism ({organism_name}).",
                        f"MBI host factor present: {'ANC < 500/mm³ (Severe Neutropenia)' if is_severely_neutropenic else 'HSCT with GI-GVHD'}.",
                    ],
                    rule_out_rationale="Categorized as Mucosal Barrier Injury LCBI (MBI-LCBI-1). Excluded from standard institutional CLABSI denominator.",
                    prevention_interventions=["Gut translocation prophylaxis and oncology supportive care."],
                )
            else:
                return CLABSIAssessment(
                    verdict=SurveillanceVerdict.CONFIRMED_CLABSI,
                    lcbi_type="LCBI-1",
                    is_reportable_clabsi=True,
                    organism_name=organism_name,
                    organism_type=org_type.value,
                    central_line_days=central_line_days,
                    criteria_met=[
                        "Central line in place > 2 consecutive calendar days.",
                        f"Recognized pathogen ({organism_name}) isolated from >= 1 blood culture.",
                        "No secondary site of infection identified.",
                    ],
                    rule_out_rationale=None,
                    prevention_interventions=[
                        "Perform prompt central line removal evaluation with attending physician.",
                        "Review central line maintenance bundle compliance (chlorhexidine dressing, hub scrub 15s).",
                        "Obtain repeat blood cultures at 48h to verify clearance.",
                    ],
                )

    # Case B: Common Commensal Organism
    elif org_type == OrganismType.COMMON_COMMENSAL:
        if number_of_positive_blood_cultures >= 2:
            symptoms_met = has_infant_symptoms if is_infant else has_symptoms
            if symptoms_met:
                if is_mbi_candidate:
                    return CLABSIAssessment(
                        verdict=SurveillanceVerdict.MBI_LCBI,
                        lcbi_type="MBI-LCBI-2",
                        is_reportable_clabsi=False,
                        organism_name=organism_name,
                        organism_type=org_type.value,
                        central_line_days=central_line_days,
                        criteria_met=[
                            f"Common commensal ({organism_name}) from >= 2 separate blood cultures.",
                            "Clinical signs of systemic infection present.",
                            "Host meets MBI criteria (neutropenia or HSCT).",
                        ],
                        rule_out_rationale="Categorized as MBI-LCBI-2; tracked separately from standard CLABSI.",
                        prevention_interventions=["Skin and mucosal barrier protection protocols."],
                    )
                else:
                    lcbi_name = "LCBI-3" if is_infant else "LCBI-2"
                    return CLABSIAssessment(
                        verdict=SurveillanceVerdict.CONFIRMED_CLABSI,
                        lcbi_type=lcbi_name,
                        is_reportable_clabsi=True,
                        organism_name=organism_name,
                        organism_type=org_type.value,
                        central_line_days=central_line_days,
                        criteria_met=[
                            "Central line in place > 2 consecutive calendar days.",
                            f"Common commensal ({organism_name}) isolated from >= 2 separate blood specimens drawn on same/consecutive days.",
                            f"Clinical symptom verified: {'Fever / Hypotension / Chills' if not is_infant else 'Hypothermia / Apnea / Bradycardia'}.",
                        ],
                        rule_out_rationale=None,
                        prevention_interventions=[
                            "Assess for catheter hub or endoluminal colonization; consider line replacement.",
                            "Reinforce aseptic sterile blood draw technique to avoid skin contamination.",
                        ],
                    )
            else:
                return CLABSIAssessment(
                    verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
                    lcbi_type=None,
                    is_reportable_clabsi=False,
                    organism_name=organism_name,
                    organism_type=org_type.value,
                    central_line_days=central_line_days,
                    criteria_met=[f"Common commensal ({organism_name}) in 2 blood cultures but NO clinical symptoms (fever/hypotension/chills)."],
                    rule_out_rationale="Common commensal isolated without documented fever (>38.0°C), chills, or hypotension (SBP < 90). Does NOT meet LCBI-2 criteria.",
                    prevention_interventions=["Clinical observation; monitor for emerging fever or hemodynamics."],
                )
        else:
            # Single commensal bottle
            return CLABSIAssessment(
                verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
                lcbi_type=None,
                is_reportable_clabsi=False,
                organism_name=organism_name,
                organism_type=org_type.value,
                central_line_days=central_line_days,
                criteria_met=[f"Single blood culture isolate of common commensal ({organism_name})."],
                rule_out_rationale="Single positive blood culture with common commensal is classified as a contaminant / non-event per NHSN rules.",
                prevention_interventions=["Audit venipuncture skin antisepsis technique."],
            )

    return CLABSIAssessment(
        verdict=SurveillanceVerdict.NO_EVENT,
        lcbi_type=None,
        is_reportable_clabsi=False,
        organism_name=organism_name,
        organism_type=org_type.value,
        central_line_days=central_line_days,
        criteria_met=[],
        rule_out_rationale="Surveillance criteria not met.",
        prevention_interventions=[],
    )


# ==============================================================================
# CAUTI SURVEILLANCE ENGINE
# ==============================================================================

@dataclass
class CAUTIAssessment:
    verdict: SurveillanceVerdict
    cauti_type: Optional[str]  # SUTI-1a, SUTI-1b, ABUTI
    is_reportable_cauti: bool
    organism_name: str
    colony_count_cfu_ml: float
    catheter_days: int
    criteria_met: List[str]
    rule_out_rationale: Optional[str]
    prevention_interventions: List[str]


def evaluate_cauti(
    organism_name: str,
    colony_count_cfu_ml: float,
    number_of_organism_species_in_culture: int,
    catheter_days: int,
    catheter_in_place_on_doe_or_removed_day_prior: bool = True,
    has_indwelling_urinary_catheter: bool = True,
    fever_gt_38c: bool = False,
    suprapubic_tenderness: bool = False,
    costovertebral_angle_pain: bool = False,
    urgency_frequency_dysuria: bool = False,
    urinary_symptoms_occurred_without_iuc: bool = False,
    blood_culture_matches_urine: bool = False,
) -> CAUTIAssessment:
    """
    Evaluate selected CDC NHSN CAUTI (SUTI-1a and catheter-associated ABUTI)
    criteria.

    Urinary urgency, frequency, or dysuria can only be used when the symptom
    occurred while the indwelling urinary catheter was not in place.
    """
    org_key = organism_name.strip().lower()

    # 1. Exclusion of Yeast / Fungi per NHSN CAUTI Criteria
    if any(fungus in org_key for fungus in ["candida", "yeast", "torulopsis", "aspergillus", "fungus"]):
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[f"Yeast / Fungal isolate: {organism_name}"],
            rule_out_rationale="Candida spp., yeast, and fungal organisms are STRICTLY EXCLUDED from CDC NHSN CAUTI definition.",
            prevention_interventions=["Avoid unnecessary antifungal therapy for asymptomatic candiduria; remove urinary catheter."],
        )

    # 2. Catheter Eligibility Check
    if not has_indwelling_urinary_catheter:
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.NO_EVENT,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[],
            rule_out_rationale="Patient does not have an indwelling urinary catheter (condom catheters / straight in-and-out catheterizations are excluded).",
            prevention_interventions=[],
        )

    if catheter_days <= 2:
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.DEVICE_DAYS_INSUFFICIENT,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[f"Catheter in place {catheter_days} days (requires > 2 consecutive calendar days)."],
            rule_out_rationale=f"Catheter dwell time of {catheter_days} days does not meet the NHSN > 2 calendar days threshold.",
            prevention_interventions=["Assess daily catheter necessity to prevent prolonged catheterization."],
        )

    if not catheter_in_place_on_doe_or_removed_day_prior:
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.NO_EVENT,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[],
            rule_out_rationale="Catheter was removed > 1 calendar day prior to event date.",
            prevention_interventions=[],
        )

    # 3. Colony Count & Species Criteria
    if number_of_organism_species_in_culture > 2:
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[f"Mixed flora culture with {number_of_organism_species_in_culture} organism species."],
            rule_out_rationale="Urine cultures with > 2 organism species are classified as mixed / contaminated specimens per NHSN guidelines.",
            prevention_interventions=["Obtain clean catheter port specimen if clinical signs of UTI persist."],
        )

    if colony_count_cfu_ml < 100000.0:  # < 10^5 CFU/mL
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[f"Colony count {colony_count_cfu_ml:.0f} CFU/mL (< 100,000 CFU/mL threshold)."],
            rule_out_rationale="Urine colony count is below NHSN SUTI threshold of >= 100,000 (10^5) CFU/mL.",
            prevention_interventions=[],
        )

    # 4. Symptoms Check
    eligible_urinary_symptoms = urgency_frequency_dysuria and urinary_symptoms_occurred_without_iuc
    has_local_symptoms = suprapubic_tenderness or costovertebral_angle_pain or eligible_urinary_symptoms
    has_symptoms = fever_gt_38c or has_local_symptoms

    if has_symptoms:
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.CONFIRMED_CAUTI,
            cauti_type="SUTI-1a",
            is_reportable_cauti=True,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[
                "Indwelling urinary catheter in place > 2 consecutive calendar days.",
                f"Positive urine culture >= 10^5 CFU/mL of bacterial pathogen ({organism_name}).",
                f"Documented symptom: {'Fever (>38.0°C)' if fever_gt_38c else 'Localized urologic tenderness/dysuria'}.",
            ],
            rule_out_rationale=None,
            prevention_interventions=[
                "Remove or replace indwelling catheter immediately under sterile technique.",
                "Initiate targeted antimicrobial therapy guided by urine sensitivities.",
                "Review daily indications for catheter continuation.",
            ],
        )

    elif blood_culture_matches_urine:
        # Asymptomatic Bacteremic UTI (ABUTI)
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.ABUTI,
            cauti_type="ABUTI",
            is_reportable_cauti=True,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=[
                "Catheter in place > 2 calendar days.",
                f"Urine culture >= 10^5 CFU/mL ({organism_name}).",
                "No local urologic symptoms, but matching blood culture isolate confirmed.",
            ],
            rule_out_rationale=None,
            prevention_interventions=[
                "Treat systemic bacteremia secondary to asymptomatic urinary source.",
                "Discontinue indwelling urinary catheter.",
            ],
        )
    else:
        # Asymptomatic bacteriuria
        return CAUTIAssessment(
            verdict=SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION,
            cauti_type=None,
            is_reportable_cauti=False,
            organism_name=organism_name,
            colony_count_cfu_ml=colony_count_cfu_ml,
            catheter_days=catheter_days,
            criteria_met=["Urine culture >= 10^5 CFU/mL but NO clinical symptoms (asymptomatic bacteriuria)."],
            rule_out_rationale="Asymptomatic bacteriuria without fever or local symptoms does NOT meet NHSN CAUTI criteria. Antimicrobial treatment is generally NOT indicated.",
            prevention_interventions=["Avoid inappropriate antibiotic treatment for asymptomatic catheter colonization."],
        )


# ==============================================================================
# EPIDEMIOLOGICAL METRICS ENGINE (SIR, DUR, INCIDENCE RATES)
# ==============================================================================

@dataclass
class EpidemiologicalMetrics:
    observed_events: int
    predicted_events: float
    device_days: int
    patient_days: int
    sir: Optional[float]
    sir_confidence_interval_95: Tuple[float, float]
    sir_interpretation: str
    device_utilization_ratio: float
    infection_rate_per_1000_device_days: float


def calculate_sir_and_dur(
    observed_events: int,
    predicted_events: float,
    device_days: int,
    patient_days: int,
) -> EpidemiologicalMetrics:
    """
    Calculate Standardized Infection Ratio (SIR), a Byar-approximation 95%
    confidence interval for the observed Poisson count, and Device Utilization
    Ratio (DUR).
    """
    if patient_days <= 0 or device_days < 0 or observed_events < 0:
        raise ValueError("Patient days must be positive; device days and observed events non-negative.")

    dur = round(device_days / patient_days, 3)
    rate_per_1000 = round((observed_events / device_days * 1000.0), 2) if device_days > 0 else 0.0

    if predicted_events <= 0:
        sir = None
        ci_lower, ci_upper = (0.0, 0.0)
        interp = "Predicted events zero or missing; SIR cannot be calculated."
    else:
        sir = round(observed_events / predicted_events, 3)

        # Approximate Poisson 95% confidence interval for SIR using Byar's
        # approximation. The zero-event upper bound uses the exact Poisson
        # 95% upper limit for zero observed events.
        if observed_events == 0:
            ci_lower = 0.0
            ci_upper = round(3.689 / predicted_events, 3)
        else:
            # Poisson 95% bounds for count
            # Lower: 0.5 * chi2_inv(0.025, 2*O)
            # Upper: 0.5 * chi2_inv(0.975, 2*(O+1))
            # Accurate approximation:
            o = observed_events
            lower_count = o * math.pow(1.0 - (1.0 / (9.0 * o)) - (1.96 / (3.0 * math.sqrt(o))), 3)
            upper_count = (o + 1) * math.pow(1.0 - (1.0 / (9.0 * (o + 1))) + (1.96 / (3.0 * math.sqrt(o + 1))), 3)
            ci_lower = max(0.0, round(lower_count / predicted_events, 3))
            ci_upper = round(upper_count / predicted_events, 3)

        if sir > 1.0 and ci_lower > 1.0:
            interp = "STATISTICALLY ELEVATED: the approximate 95% SIR interval is entirely above 1.0."
        elif sir < 1.0 and ci_upper < 1.0:
            interp = "STATISTICALLY LOWER: the approximate 95% SIR interval is entirely below 1.0."
        else:
            interp = "NOT STATISTICALLY DIFFERENT: the approximate 95% SIR interval includes 1.0."

    return EpidemiologicalMetrics(
        observed_events=observed_events,
        predicted_events=predicted_events,
        device_days=device_days,
        patient_days=patient_days,
        sir=sir,
        sir_confidence_interval_95=(ci_lower, ci_upper),
        sir_interpretation=interp,
        device_utilization_ratio=dur,
        infection_rate_per_1000_device_days=rate_per_1000,
    )


# ==============================================================================
# MASTER SENTINEL & BATCH PROCESSING
# ==============================================================================

class DeviceHAISentinelEngine:
    """Master Clinical Surveillance Engine for NHSN CLABSI & CAUTI."""

    def evaluate_clabsi_case(self, **kwargs) -> CLABSIAssessment:
        return evaluate_clabsi(**kwargs)

    def evaluate_cauti_case(self, **kwargs) -> CAUTIAssessment:
        return evaluate_cauti(**kwargs)

    def calculate_metrics(self, **kwargs) -> EpidemiologicalMetrics:
        return calculate_sir_and_dur(**kwargs)


def process_batch_csv(input_csv_path: str, output_csv_path: str) -> int:
    """Processes batch surveillance records from CSV."""
    engine = DeviceHAISentinelEngine()
    processed_count = 0

    with open(input_csv_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    if not rows:
        return 0

    output_rows = []
    for row in rows:
        surveillance_type = row.get("surveillance_type", row.get("type", "clabsi")).strip().lower()
        org = row.get("organism", row.get("organism_name", "Staphylococcus aureus"))
        line_days = int(row.get("device_days", row.get("line_days", 4)))
        fever = str(row.get("fever", "true")).lower() in ("true", "1", "yes")
        hypotension = str(row.get("hypotension", "false")).lower() in ("true", "1", "yes")
        anc_val = float(row.get("anc", 1500.0)) if "anc" in row and row["anc"] else None
        num_cultures = int(row.get("num_cultures", 1))

        if "cauti" in surveillance_type:
            cfu = float(row.get("colony_count", 100000.0))
            num_species = int(row.get("num_species", 1))
            res = engine.evaluate_cauti_case(
                organism_name=org,
                colony_count_cfu_ml=cfu,
                number_of_organism_species_in_culture=num_species,
                catheter_days=line_days,
                fever_gt_38c=fever,
            )
            out = dict(row)
            out["verdict"] = res.verdict.value
            out["classification_type"] = res.cauti_type or "None"
            out["lcbi_type"] = "N/A (CAUTI)"
            out["cauti_type"] = res.cauti_type or "None"
            out["is_reportable"] = res.is_reportable_cauti
            out["rule_out_reason"] = res.rule_out_rationale or "Meets Criteria"
        else:
            secondary = str(row.get("secondary_site", "")).strip()
            res = engine.evaluate_clabsi_case(
                organism_name=org,
                number_of_positive_blood_cultures=num_cultures,
                central_line_days=line_days,
                fever_gt_38c=fever,
                hypotension_sbp_lt_90=hypotension,
                absolute_neutrophil_count_anc=anc_val,
                has_matching_positive_site_culture=bool(secondary),
                primary_site_of_infection=secondary if secondary else None,
            )
            out = dict(row)
            out["verdict"] = res.verdict.value
            out["classification_type"] = res.lcbi_type or "None"
            out["lcbi_type"] = res.lcbi_type or "None"
            out["cauti_type"] = "N/A (CLABSI)"
            out["is_reportable"] = res.is_reportable_clabsi
            out["rule_out_reason"] = res.rule_out_rationale or "Meets Criteria"

        output_rows.append(out)
        processed_count += 1

    fieldnames = []
    for r in output_rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(output_csv_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    return processed_count
