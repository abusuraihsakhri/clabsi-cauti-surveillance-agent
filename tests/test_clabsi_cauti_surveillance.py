#!/usr/bin/env python3
"""
Unit Test Suite for CDC NHSN CLABSI & CAUTI Autonomous Surveillance Engine.
"""

import os
import tempfile
import unittest
from clabsi_cauti_surveillance import (
    DeviceHAISentinelEngine,
    SurveillanceVerdict,
    OrganismType,
    evaluate_clabsi,
    evaluate_cauti,
    calculate_sir_and_dur,
    process_batch_csv,
)


class TestCLABSISurveillance(unittest.TestCase):
    """Test CDC NHSN CLABSI, LCBI-1, LCBI-2, and LCBI-3 rules."""

    def test_lcbi_1_recognized_pathogen_staph_aureus(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus aureus",
            number_of_positive_blood_cultures=1,
            central_line_days=4,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-1")
        self.assertTrue(res.is_reportable_clabsi)

    def test_unknown_organism_requires_terminology_review(self):
        res = evaluate_clabsi(
            organism_name="Example organism not in registry",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.INDETERMINATE)
        self.assertFalse(res.is_reportable_clabsi)
        self.assertIn("Terminology Browser", res.rule_out_rationale)

    def test_lcbi_1_pseudomonas_aeruginosa(self):
        res = evaluate_clabsi(
            organism_name="Pseudomonas aeruginosa",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-1")

    def test_lcbi_2_common_commensal_two_bottles_with_fever(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus epidermidis",
            number_of_positive_blood_cultures=2,
            central_line_days=6,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-2")
        self.assertTrue(res.is_reportable_clabsi)

    def test_lcbi_2_single_commensal_bottle_contaminant(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus epidermidis",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_clabsi)
        self.assertIn("contaminant", res.rule_out_rationale.lower())

    def test_lcbi_2_two_commensal_bottles_no_symptoms_rule_out(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus hominis",
            number_of_positive_blood_cultures=2,
            central_line_days=5,
            fever_gt_38c=False,
            hypotension_sbp_lt_90=False,
            chills_present=False,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_clabsi)

    def test_lcbi_3_infant_hypothermia(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus capitis",
            number_of_positive_blood_cultures=2,
            central_line_days=4,
            patient_age_years=0,  # Infant
            hypothermia_lt_36c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-3")
        self.assertTrue(res.is_reportable_clabsi)

    def test_device_days_insufficient_rule_out(self):
        # Day 2 of line dwell time (<= 2 days does not meet > 2 calendar days rule)
        res = evaluate_clabsi(
            organism_name="Staphylococcus aureus",
            number_of_positive_blood_cultures=1,
            central_line_days=2,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.DEVICE_DAYS_INSUFFICIENT)
        self.assertFalse(res.is_reportable_clabsi)

    def test_midline_peripheral_exclusion(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus aureus",
            number_of_positive_blood_cultures=1,
            central_line_days=7,
            is_midline_or_peripheral_only=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.NO_EVENT)
        self.assertFalse(res.is_reportable_clabsi)
        self.assertIn("Midline and Peripheral IVs are excluded", res.rule_out_rationale)

    def test_line_removed_early_rule_out(self):
        res = evaluate_clabsi(
            organism_name="Staphylococcus aureus",
            number_of_positive_blood_cultures=1,
            central_line_days=6,
            line_in_place_on_doe_or_removed_day_prior=False,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.NO_EVENT)
        self.assertFalse(res.is_reportable_clabsi)


class TestMBILCBIAndSecondaryBSI(unittest.TestCase):
    """Test Mucosal Barrier Injury (MBI-LCBI) and Secondary BSI rules."""

    def test_mbi_lcbi_1_neutropenic_ecoli(self):
        res = evaluate_clabsi(
            organism_name="Escherichia coli",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
            absolute_neutrophil_count_anc=250.0,  # < 500/mm³
            neutropenia_qualifying_days=2,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.MBI_LCBI)
        self.assertEqual(res.lcbi_type, "MBI-LCBI-1")
        self.assertFalse(res.is_reportable_clabsi)  # Stratified separately

    def test_single_low_anc_day_does_not_meet_mbi_host_factor(self):
        res = evaluate_clabsi(
            organism_name="Escherichia coli",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
            absolute_neutrophil_count_anc=250.0,
            neutropenia_qualifying_days=1,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-1")

    def test_mbi_lcbi_1_hsct_gi_gvhd_enterococcus(self):
        res = evaluate_clabsi(
            organism_name="Enterococcus faecium",
            number_of_positive_blood_cultures=1,
            central_line_days=8,
            is_hsct_with_gi_gvhd=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.MBI_LCBI)
        self.assertEqual(res.lcbi_type, "MBI-LCBI-1")

    def test_mbi_lcbi_2_streptococcus_mitis_neutropenia(self):
        res = evaluate_clabsi(
            organism_name="Streptococcus mitis",
            number_of_positive_blood_cultures=2,
            central_line_days=5,
            fever_gt_38c=True,
            absolute_neutrophil_count_anc=100.0,
            neutropenia_qualifying_days=2,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.MBI_LCBI)
        self.assertEqual(res.lcbi_type, "MBI-LCBI-2")

    def test_mbi_lcbi_2_rothia_neutropenia(self):
        res = evaluate_clabsi(
            organism_name="Rothia mucilaginosa",
            number_of_positive_blood_cultures=2,
            central_line_days=5,
            fever_gt_38c=True,
            absolute_neutrophil_count_anc=100.0,
            neutropenia_qualifying_days=2,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.MBI_LCBI)
        self.assertEqual(res.lcbi_type, "MBI-LCBI-2")

    def test_secondary_bsi_attributed_to_urine(self):
        res = evaluate_clabsi(
            organism_name="Klebsiella pneumoniae",
            number_of_positive_blood_cultures=1,
            central_line_days=6,
            has_matching_positive_site_culture=True,
            primary_site_of_infection="Urine (CAUTI)",
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.SECONDARY_BSI)
        self.assertFalse(res.is_reportable_clabsi)
        self.assertIn("secondary", res.rule_out_rationale.lower())

    def test_secondary_bsi_attributed_to_lung(self):
        res = evaluate_clabsi(
            organism_name="Pseudomonas aeruginosa",
            number_of_positive_blood_cultures=1,
            central_line_days=7,
            has_matching_positive_site_culture=True,
            primary_site_of_infection="Pneumonia / VAP",
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.SECONDARY_BSI)
        self.assertEqual(res.lcbi_type, "Secondary BSI")


class TestCAUTISurveillance(unittest.TestCase):
    """Test CDC NHSN CAUTI SUTI-1a, SUTI-1b, ABUTI, and exclusions."""

    def test_suti_1a_ecoli_confirmed(self):
        res = evaluate_cauti(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CAUTI)
        self.assertEqual(res.cauti_type, "SUTI-1a")
        self.assertTrue(res.is_reportable_cauti)

    def test_suti_1a_proteus_suprapubic_pain(self):
        res = evaluate_cauti(
            organism_name="Proteus mirabilis",
            colony_count_cfu_ml=150000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=5,
            suprapubic_tenderness=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CAUTI)
        self.assertTrue(res.is_reportable_cauti)

    def test_candida_exclusion_strict_rule_out(self):
        res = evaluate_cauti(
            organism_name="Candida albicans",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=6,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_cauti)
        self.assertIn("STRICTLY EXCLUDED", res.rule_out_rationale)

    def test_mixed_flora_gt_2_species_rule_out(self):
        res = evaluate_cauti(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=3,  # > 2 species
            catheter_days=5,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_cauti)
        self.assertIn("mixed", res.rule_out_rationale.lower())

    def test_low_colony_count_rule_out(self):
        res = evaluate_cauti(
            organism_name="Klebsiella pneumoniae",
            colony_count_cfu_ml=25000.0,  # < 10^5 CFU/mL
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_cauti)

    def test_urinary_symptoms_do_not_count_while_iuc_in_place(self):
        res = evaluate_cauti(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            urgency_frequency_dysuria=True,
            urinary_symptoms_occurred_without_iuc=False,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)

    def test_urinary_symptoms_can_count_when_documented_without_iuc(self):
        res = evaluate_cauti(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            urgency_frequency_dysuria=True,
            urinary_symptoms_occurred_without_iuc=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CAUTI)

    def test_asymptomatic_bacteremic_uti_abuti(self):
        res = evaluate_cauti(
            organism_name="Enterococcus faecalis",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            fever_gt_38c=False,
            suprapubic_tenderness=False,
            blood_culture_matches_urine=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.ABUTI)
        self.assertEqual(res.cauti_type, "ABUTI")
        self.assertTrue(res.is_reportable_cauti)

    def test_asymptomatic_bacteriuria_no_blood_match(self):
        res = evaluate_cauti(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            fever_gt_38c=False,
            blood_culture_matches_urine=False,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONTAMINANT_OR_COLONIZATION)
        self.assertFalse(res.is_reportable_cauti)


class TestEpidemiologicalMetrics(unittest.TestCase):
    """Test SIR, DUR, and Poisson confidence interval calculations."""

    def test_sir_concordant(self):
        metrics = calculate_sir_and_dur(
            observed_events=4,
            predicted_events=4.2,
            device_days=1000,
            patient_days=2500,
        )
        self.assertAlmostEqual(metrics.sir, 0.952, places=2)
        self.assertEqual(metrics.device_utilization_ratio, 0.400)
        self.assertEqual(metrics.infection_rate_per_1000_device_days, 4.0)
        self.assertIn("NOT STATISTICALLY DIFFERENT", metrics.sir_interpretation)

    def test_sir_statistically_elevated(self):
        metrics = calculate_sir_and_dur(
            observed_events=18,
            predicted_events=4.0,
            device_days=2000,
            patient_days=5000,
        )
        self.assertGreater(metrics.sir, 1.0)
        self.assertGreater(metrics.sir_confidence_interval_95[0], 1.0)
        self.assertIn("STATISTICALLY ELEVATED", metrics.sir_interpretation)

    def test_sir_zero_events(self):
        metrics = calculate_sir_and_dur(
            observed_events=0,
            predicted_events=3.5,
            device_days=800,
            patient_days=2000,
        )
        self.assertEqual(metrics.sir, 0.0)
        self.assertEqual(metrics.sir_confidence_interval_95[0], 0.0)
        self.assertGreater(metrics.sir_confidence_interval_95[1], 0.0)

    def test_metrics_invalid_inputs(self):
        with self.assertRaises(ValueError):
            calculate_sir_and_dur(-1, 2.0, 100, 200)
        with self.assertRaises(ValueError):
            calculate_sir_and_dur(2, 2.0, 100, 0)


class TestBatchProcessingAndEngine(unittest.TestCase):
    """Test batch CSV pipeline and engine wrapper."""

    def test_sir_statistically_superior(self):
        metrics = calculate_sir_and_dur(
            observed_events=1,
            predicted_events=8.0,
            device_days=3000,
            patient_days=7500,
        )
        self.assertLess(metrics.sir, 1.0)
        self.assertLess(metrics.sir_confidence_interval_95[1], 1.0)
        self.assertIn("STATISTICALLY LOWER", metrics.sir_interpretation)

    def test_clabsi_serratia_marcescens(self):
        res = evaluate_clabsi(
            organism_name="Serratia marcescens",
            number_of_positive_blood_cultures=1,
            central_line_days=5,
            fever_gt_38c=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)
        self.assertEqual(res.lcbi_type, "LCBI-1")

    def test_cauti_cva_tenderness(self):
        res = evaluate_cauti(
            organism_name="Klebsiella pneumoniae",
            colony_count_cfu_ml=120000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=5,
            costovertebral_angle_pain=True,
        )
        self.assertEqual(res.verdict, SurveillanceVerdict.CONFIRMED_CAUTI)
        self.assertEqual(res.cauti_type, "SUTI-1a")

    def test_engine_wrapper_calls(self):
        engine = DeviceHAISentinelEngine()
        clabsi_res = engine.evaluate_clabsi_case(
            organism_name="Staphylococcus aureus",
            number_of_positive_blood_cultures=1,
            central_line_days=4,
        )
        self.assertEqual(clabsi_res.verdict, SurveillanceVerdict.CONFIRMED_CLABSI)

        cauti_res = engine.evaluate_cauti_case(
            organism_name="Escherichia coli",
            colony_count_cfu_ml=100000.0,
            number_of_organism_species_in_culture=1,
            catheter_days=4,
            fever_gt_38c=True,
        )
        self.assertEqual(cauti_res.verdict, SurveillanceVerdict.CONFIRMED_CAUTI)

    def test_batch_parses_false_boolean_strings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "bool_input.csv")
            out_csv = os.path.join(tmpdir, "bool_output.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("surveillance_type,organism,device_days,fever,num_cultures\n")
                f.write("clabsi,Staphylococcus epidermidis,5,false,2\n")
            process_batch_csv(in_csv, out_csv)
            with open(out_csv, "r", encoding="utf-8") as f:
                row = next(__import__("csv").DictReader(f))
            self.assertEqual(row["verdict"], "contaminant_or_colonization")

    def test_batch_csv_surveillance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "surv_input.csv")
            out_csv = os.path.join(tmpdir, "surv_output.csv")

            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("surveillance_type,organism,device_days,fever,anc,anc_qualifying_days,num_cultures\n")
                f.write("clabsi,Staphylococcus aureus,4,true,1800,0,1\n")
                f.write("clabsi,Escherichia coli,5,true,200,2,1\n")
                f.write("cauti,Candida albicans,6,true,,,1\n")

            count = process_batch_csv(in_csv, out_csv)
            self.assertEqual(count, 3)
            self.assertTrue(os.path.exists(out_csv))

            with open(out_csv, "r", encoding="utf-8") as f:
                rows = list(__import__("csv").DictReader(f))
                self.assertEqual(len(rows), 3)
                self.assertEqual(rows[0]["verdict"], "confirmed_clabsi")
                self.assertEqual(rows[1]["verdict"], "mbi_lcbi")
                self.assertEqual(rows[2]["verdict"], "contaminant_or_colonization")


if __name__ == "__main__":
    unittest.main()
