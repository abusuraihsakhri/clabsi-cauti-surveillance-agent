"""Optional FastAPI interface for the surveillance engine."""

from dataclasses import asdict
from typing import Optional

from clabsi_cauti_surveillance import (
    calculate_sir_and_dur,
    evaluate_cauti,
    evaluate_clabsi,
)


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError(
            "FastAPI server dependencies are not installed. "
            "Install the project with the server extra."
        ) from exc

    app = FastAPI(
        title="CLABSI & CAUTI Surveillance Utilities",
        description=(
            "Screening utilities implementing selected 2026 CDC NHSN "
            "CLABSI and CAUTI surveillance criteria."
        ),
        version="2.1.0",
    )

    class CLABSIRequest(BaseModel):
        organism_name: str
        number_of_positive_blood_cultures: int = 1
        central_line_days: int = 4
        line_in_place_on_doe_or_removed_day_prior: bool = True
        patient_has_central_line: bool = True
        is_midline_or_peripheral_only: bool = False
        fever_gt_38c: bool = False
        hypotension_sbp_lt_90: bool = False
        chills_present: bool = False
        patient_age_years: int = 45
        hypothermia_lt_36c: bool = False
        apnea_or_bradycardia: bool = False
        absolute_neutrophil_count_anc: Optional[float] = None
        neutropenia_qualifying_days: int = 0
        is_hsct_with_gi_gvhd: bool = False
        has_matching_positive_site_culture: bool = False
        primary_site_of_infection: Optional[str] = None

    class CAUTIRequest(BaseModel):
        organism_name: str
        colony_count_cfu_ml: float = 100000.0
        number_of_organism_species_in_culture: int = 1
        catheter_days: int = 4
        catheter_in_place_on_doe_or_removed_day_prior: bool = True
        has_indwelling_urinary_catheter: bool = True
        fever_gt_38c: bool = False
        suprapubic_tenderness: bool = False
        costovertebral_angle_pain: bool = False
        urgency_frequency_dysuria: bool = False
        urinary_symptoms_occurred_without_iuc: bool = False
        blood_culture_matches_urine: bool = False

    class MetricsRequest(BaseModel):
        observed_events: int
        predicted_events: float
        device_days: int
        patient_days: int

    @app.get("/health")
    def health():
        return {"status": "healthy", "version": "2.1.0"}

    @app.post("/api/clabsi")
    def clabsi(req: CLABSIRequest):
        return asdict(evaluate_clabsi(**req.model_dump()))

    @app.post("/api/cauti")
    def cauti(req: CAUTIRequest):
        return asdict(evaluate_cauti(**req.model_dump()))

    @app.post("/api/metrics")
    def metrics(req: MetricsRequest):
        return asdict(calculate_sir_and_dur(**req.model_dump()))

    return app
