#!/usr/bin/env python3
"""
Command-Line Interface for the CLABSI & CAUTI surveillance utilities.

Usage:
    python cli.py clabsi --organism "Staphylococcus aureus" --cultures 1 --days 5 --fever
    python cli.py clabsi --organism "Staphylococcus epidermidis" --cultures 2 --days 4 --fever
    python cli.py clabsi --organism "Escherichia coli" --cultures 1 --days 6 --anc 300
    python cli.py cauti --organism "Escherichia coli" --cfu 100000 --days 4 --fever
    python cli.py cauti --organism "Candida albicans" --cfu 100000 --days 5 --fever
    python cli.py metrics --observed 4 --predicted 5.2 --device-days 1200 --patient-days 3500
    python cli.py batch --input sample.csv --output results.csv
    python cli.py interactive
"""

import argparse
import json
import os
import sys
from dataclasses import asdict

from clabsi_cauti_surveillance import (
    DeviceHAISentinelEngine,
    SurveillanceVerdict,
    evaluate_clabsi,
    evaluate_cauti,
    calculate_sir_and_dur,
    process_batch_csv,
)


def cmd_clabsi(args):
    result = evaluate_clabsi(
        organism_name=args.organism,
        number_of_positive_blood_cultures=args.cultures,
        central_line_days=args.days,
        line_in_place_on_doe_or_removed_day_prior=not args.removed_early,
        patient_has_central_line=not args.no_central_line,
        is_midline_or_peripheral_only=args.midline,
        fever_gt_38c=args.fever,
        hypotension_sbp_lt_90=args.hypotension,
        chills_present=args.chills,
        patient_age_years=args.age,
        hypothermia_lt_36c=args.hypothermia,
        apnea_or_bradycardia=args.apnea_bradycardia,
        absolute_neutrophil_count_anc=args.anc,
        neutropenia_qualifying_days=args.anc_days,
        is_hsct_with_gi_gvhd=args.hsct_gvhd,
        has_matching_positive_site_culture=bool(args.secondary_site),
        primary_site_of_infection=args.secondary_site,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    else:
        print("=" * 70)
        print("  CDC NHSN CLABSI SURVEILLANCE ARBITRATION")
        print("=" * 70)
        print(f"  Surveillance Verdict:    [{result.verdict.value.upper()}]")
        print(f"  Classification Type:     {result.lcbi_type or 'None'}")
        print(f"  NHSN Public Reportable:  {'YES (Counted in CLABSI SIR)' if result.is_reportable_clabsi else 'NO'}")
        print(f"  Organism:                {result.organism_name} ({result.organism_type})")
        print(f"  Central Line Days:       {result.central_line_days} days")
        print("\n  Criteria Evaluated:")
        for c in result.criteria_met:
            print(f"    * {c}")
        if result.rule_out_rationale:
            print(f"\n  Rule-Out / Attribution Rationale:")
            print(f"    ! {result.rule_out_rationale}")
        if result.prevention_interventions:
            print("\n  Infection Prevention Interventions:")
            for p in result.prevention_interventions:
                print(f"    - {p}")
        print("=" * 70)
    return 0


def cmd_cauti(args):
    result = evaluate_cauti(
        organism_name=args.organism,
        colony_count_cfu_ml=args.cfu,
        number_of_organism_species_in_culture=args.species,
        catheter_days=args.days,
        catheter_in_place_on_doe_or_removed_day_prior=not args.removed_early,
        has_indwelling_urinary_catheter=not args.no_catheter,
        fever_gt_38c=args.fever,
        suprapubic_tenderness=args.suprapubic,
        costovertebral_angle_pain=args.cva_pain,
        urgency_frequency_dysuria=args.dysuria,
        urinary_symptoms_occurred_without_iuc=args.urinary_symptoms_without_iuc,
        blood_culture_matches_urine=args.blood_match,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    else:
        print("=" * 70)
        print("  CDC NHSN CAUTI SURVEILLANCE ARBITRATION")
        print("=" * 70)
        print(f"  Surveillance Verdict:    [{result.verdict.value.upper()}]")
        print(f"  Classification Type:     {result.cauti_type or 'None'}")
        print(f"  NHSN Public Reportable:  {'YES (Counted in CAUTI SIR)' if result.is_reportable_cauti else 'NO'}")
        print(f"  Organism:                {result.organism_name} ({result.colony_count_cfu_ml:.0f} CFU/mL)")
        print(f"  Catheter Dwell Time:     {result.catheter_days} days")
        print("\n  Criteria Evaluated:")
        for c in result.criteria_met:
            print(f"    * {c}")
        if result.rule_out_rationale:
            print(f"\n  Rule-Out / Exclusion Rationale:")
            print(f"    ! {result.rule_out_rationale}")
        if result.prevention_interventions:
            print("\n  Infection Prevention Interventions:")
            for p in result.prevention_interventions:
                print(f"    - {p}")
        print("=" * 70)
    return 0


def cmd_metrics(args):
    res = calculate_sir_and_dur(
        observed_events=args.observed,
        predicted_events=args.predicted,
        device_days=args.device_days,
        patient_days=args.patient_days,
    )

    if args.json:
        print(json.dumps(asdict(res), indent=2, default=str))
    else:
        print("=" * 70)
        print("  CDC NHSN EPIDEMIOLOGICAL METRICS & BENCHMARKS")
        print("=" * 70)
        print(f"  Observed HAIs:           {res.observed_events}")
        print(f"  Predicted HAIs:          {res.predicted_events}")
        print(f"  Device Days:             {res.device_days} (Patient Days: {res.patient_days})")
        print(f"  Standardized Ratio (SIR):{res.sir if res.sir is not None else 'N/A'}")
        print(f"  Approx. 95% SIR Interval:[{res.sir_confidence_interval_95[0]:.3f}, {res.sir_confidence_interval_95[1]:.3f}]")
        print(f"  Interpretation:          {res.sir_interpretation}")
        print(f"  Device Utilization (DUR):{res.device_utilization_ratio:.3f}")
        print(f"  Incidence Rate:          {res.infection_rate_per_1000_device_days:.2f} per 1,000 device days")
        print("=" * 70)
    return 0


def cmd_batch(args):
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        return 1
    count = process_batch_csv(args.input, args.output)
    print(f"Successfully processed {count} surveillance records from '{args.input}' -> '{args.output}'.")
    return 0


def cmd_interactive(args):
    print("=" * 70)
    print("  CDC NHSN DEVICE-ASSOCIATED INFECTION SURVEILLANCE WIZARD")
    print("=" * 70)
    print("Select Module: [1] CLABSI  [2] CAUTI  [3] Epidemiological SIR/DUR Calculator")
    choice = input("Choice (1/2/3): ").strip()

    if choice == "1":
        org = input("Isolated Organism (e.g. Staphylococcus aureus, S. epidermidis, E. coli): ").strip()
        cult_str = input("Number of positive blood culture bottles (default 1): ").strip() or "1"
        days_str = input("Central line dwell time in calendar days (default 4): ").strip() or "4"
        fever = input("Fever (>38.0°C) present? (y/n, default y): ").lower().startswith("y")
        anc_str = input("Absolute Neutrophil Count ANC in /mm³ (optional): ").strip()
        anc = float(anc_str) if anc_str else None
        anc_days_str = input("Separate days with ANC/WBC <500 in the 7-day MBI window (default 0): ").strip() or "0"
        sec = input("Secondary matching infection site if any (e.g. Urine, Lung, SSI, or leave blank): ").strip()

        res = evaluate_clabsi(
            organism_name=org,
            number_of_positive_blood_cultures=int(cult_str),
            central_line_days=int(days_str),
            fever_gt_38c=fever,
            absolute_neutrophil_count_anc=anc,
            neutropenia_qualifying_days=int(anc_days_str),
            has_matching_positive_site_culture=bool(sec),
            primary_site_of_infection=sec if sec else None,
        )
        print("\n")
        print(json.dumps(asdict(res), indent=2, default=str))

    elif choice == "2":
        org = input("Isolated Organism in urine (e.g. Escherichia coli, Candida albicans): ").strip()
        cfu_str = input("Colony count in CFU/mL (default 100000): ").strip() or "100000"
        days_str = input("Catheter dwell time in calendar days (default 4): ").strip() or "4"
        fever = input("Fever (>38.0°C) present? (y/n, default y): ").lower().startswith("y")
        supra = input("Suprapubic tenderness present? (y/n, default n): ").lower().startswith("y")

        res = evaluate_cauti(
            organism_name=org,
            colony_count_cfu_ml=float(cfu_str),
            number_of_organism_species_in_culture=1,
            catheter_days=int(days_str),
            fever_gt_38c=fever,
            suprapubic_tenderness=supra,
        )
        print("\n")
        print(json.dumps(asdict(res), indent=2, default=str))

    elif choice == "3":
        obs_str = input("Observed HAIs (e.g. 3): ").strip() or "3"
        pred_str = input("Predicted HAIs (e.g. 4.5): ").strip() or "4.5"
        dev_str = input("Device days (e.g. 1500): ").strip() or "1500"
        pat_str = input("Patient days (e.g. 4000): ").strip() or "4000"

        res = calculate_sir_and_dur(
            observed_events=int(obs_str),
            predicted_events=float(pred_str),
            device_days=int(dev_str),
            patient_days=int(pat_str),
        )
        print("\n")
        print(json.dumps(asdict(res), indent=2, default=str))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clabsi-cauti-surveillance-agent",
        description="CLABSI/CAUTI surveillance screening and epidemiological utilities based on selected 2026 CDC NHSN criteria",
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    subparsers = parser.add_subparsers(dest="command")

    # CLABSI
    p_clabsi = subparsers.add_parser("clabsi", help="Evaluate CLABSI criteria")
    p_clabsi.add_argument("--organism", required=True, help="Isolated blood organism name")
    p_clabsi.add_argument("--cultures", type=int, default=1, help="Number of positive blood culture bottles")
    p_clabsi.add_argument("--days", type=int, default=4, help="Central line dwell time (calendar days)")
    p_clabsi.add_argument("--fever", action="store_true", help="Fever > 38.0°C")
    p_clabsi.add_argument("--hypotension", action="store_true", help="Hypotension SBP < 90 mmHg")
    p_clabsi.add_argument("--chills", action="store_true", help="Chills present")
    p_clabsi.add_argument("--age", type=int, default=45, help="Patient age in years")
    p_clabsi.add_argument("--hypothermia", action="store_true", help="Hypothermia < 36.0°C (infants)")
    p_clabsi.add_argument("--apnea-bradycardia", action="store_true", help="Apnea or bradycardia (infants)")
    p_clabsi.add_argument("--anc", type=float, help="Absolute neutrophil count (for MBI host-factor screening)")
    p_clabsi.add_argument("--anc-days", type=int, default=0, help="Separate days with ANC/WBC <500 in the 7-day MBI window; NHSN requires >=2")
    p_clabsi.add_argument("--hsct-gvhd", action="store_true", help="Caller-verified current NHSN allogeneic-HSCT GI-GVHD/diarrhea host criterion")
    p_clabsi.add_argument("--secondary-site", help="Matching primary infection site (e.g. Urine, Lung, SSI)")
    p_clabsi.add_argument("--removed-early", action="store_true", help="Line removed > 1 day prior")
    p_clabsi.add_argument("--no-central-line", action="store_true", help="No central line present")
    p_clabsi.add_argument("--midline", action="store_true", help="Midline / peripheral line only")

    # CAUTI
    p_cauti = subparsers.add_parser("cauti", help="Evaluate CAUTI criteria")
    p_cauti.add_argument("--organism", required=True, help="Isolated urinary organism name")
    p_cauti.add_argument("--cfu", type=float, default=100000.0, help="Colony count CFU/mL")
    p_cauti.add_argument("--species", type=int, default=1, help="Number of organism species in culture")
    p_cauti.add_argument("--days", type=int, default=4, help="Catheter dwell time (calendar days)")
    p_cauti.add_argument("--fever", action="store_true", help="Fever > 38.0°C")
    p_cauti.add_argument("--suprapubic", action="store_true", help="Suprapubic tenderness")
    p_cauti.add_argument("--cva-pain", action="store_true", help="Costovertebral angle pain/tenderness")
    p_cauti.add_argument("--dysuria", action="store_true", help="Urinary urgency, frequency, or dysuria")
    p_cauti.add_argument("--urinary-symptoms-without-iuc", action="store_true", help="Confirm urinary urgency/frequency/dysuria occurred while IUC was not in place")
    p_cauti.add_argument("--blood-match", action="store_true", help="Matching bacterium/pathogen in blood (ABUTI)")
    p_cauti.add_argument("--removed-early", action="store_true", help="Catheter removed > 1 day prior")
    p_cauti.add_argument("--no-catheter", action="store_true", help="No indwelling catheter")

    # Metrics
    p_metrics = subparsers.add_parser("metrics", help="Calculate SIR and DUR epidemiological metrics")
    p_metrics.add_argument("--observed", type=int, required=True, help="Observed HAI count")
    p_metrics.add_argument("--predicted", type=float, required=True, help="Predicted HAI count")
    p_metrics.add_argument("--device-days", type=int, required=True, help="Total device days")
    p_metrics.add_argument("--patient-days", type=int, required=True, help="Total patient days")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process surveillance records from CSV")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="surveillance_results.csv", help="Output CSV file")

    # Interactive
    p_inter = subparsers.add_parser("interactive", help="Interactive surveillance arbiter")

    args = parser.parse_args(argv)

    if args.command == "clabsi":
        return cmd_clabsi(args)
    elif args.command == "cauti":
        return cmd_cauti(args)
    elif args.command == "metrics":
        return cmd_metrics(args)
    elif args.command == "batch":
        return cmd_batch(args)
    elif args.command == "interactive":
        return cmd_interactive(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
