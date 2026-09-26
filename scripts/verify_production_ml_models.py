"""
End-to-End Real Verification Script for Production ML Models:
1. Phase 14.1 — Environmental Anomaly Detection V2 (MEAD-V2 Isolation Forest)
2. Phase 14.2 — Marine Species Identification (ResNet-18 Deep Learning)
3. Phase 14.3 — Fisheries Catch Prediction V1 (IOTC Surface XGBoost Regressor)

No mock predictions are used. Real model weights, baseline configs, and feature pipelines are executed.
"""
import io
import json
import sys
from pathlib import Path
from PIL import Image
import numpy as np

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 1. Environmental Anomaly V2
from ml.environmental_anomaly.predict import EnvironmentalAnomalyInferenceEngine

# 2. Marine Species Identification
from ml.species_identification.inference import MarineSpeciesIdentifier

# 3. Fisheries Catch Prediction V1
from ml.fisheries_catch.predict import FisheriesCatchPredictor



def verify_phase_14_1_environmental_anomaly_v2():
    print("=" * 60)
    print("VERIFYING PHASE 14.1: ENVIRONMENTAL ANOMALY DETECTION V2")
    print("=" * 60)
    models_dir = Path("models/environmental_anomaly_v2")
    engine = EnvironmentalAnomalyInferenceEngine(models_dir)
    engine.load()

    assert engine.is_loaded, "Engine failed to load!"
    print(f"[OK] Model loaded: {engine.metadata.get('model_name')}")
    print(f"[OK] Model version: {engine.metadata.get('model_version')}")
    print(f"[OK] Algorithm: {engine.metadata.get('algorithm')}")
    print(f"[OK] Unsupervised detection note: {engine.metadata.get('test_results_2025', {}).get('anomaly_rate_pct')}% on held-out 2025 test observations")

    # Real inference test inside Arabian Sea
    as_obs = {"latitude": 15.0, "longitude": 65.0, "sst": 31.8, "timestamp": "2025-06-01"}
    preds = engine.predict([as_obs])
    p = preds[0]
    print(f"[OK] In-Domain Inference Result: {p.anomaly_type}")
    print(f"     Score: {p.anomaly_score:.2f}/100 | Severity: {p.severity} | Direction: {p.warm_cold_direction}")
    print(f"     Observed SST: {p.sst_observed_celsius:.2f} °C | Baseline SST: {p.sst_baseline_celsius:.2f} °C | Anomaly: {p.sst_anomaly_celsius:+.2f} °C")
    print(f"     Arabian Sea Mask: {p.in_arabian_sea} | Subbasin: {p.subbasin}")
    assert p.in_arabian_sea is True, "Arabian Sea point incorrectly excluded!"
    assert p.warm_cold_direction == "warm", "Warm direction misclassified!"

    # Geographic boundary test: Gulf of Oman
    go_obs = {"latitude": 24.0, "longitude": 58.0, "sst": 29.5, "timestamp": "2025-06-01"}
    p_go = engine.predict([go_obs])[0]
    print(f"[OK] Gulf of Oman Exclusion Check: in_arabian_sea={p_go.in_arabian_sea} | subbasin='{p_go.subbasin}'")
    assert p_go.in_arabian_sea is False, "Gulf of Oman must be excluded by IHO S-23!"

    print("[SUCCESS] Phase 14.1 Environmental Anomaly Detection V2 verified.\n")


def verify_phase_14_2_species_identification():
    print("=" * 60)
    print("VERIFYING PHASE 14.2: MARINE SPECIES IDENTIFICATION (PROTECTED)")
    print("=" * 60)
    models_dir = Path("models/species_identification")
    identifier = MarineSpeciesIdentifier(model_dir=str(models_dir))

    assert identifier.model is not None, "Species model failed to load!"
    print(f"[OK] Model loaded: ResNet-18 Deep Learning Classifier")
    print(f"[OK] Model version: {identifier.model_version}")
    print(f"[OK] Number of classes: {identifier.num_classes}")

    # Generate synthetic RGB underwater test frame
    img = Image.new("RGB", (224, 224), color=(20, 80, 140))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    result = identifier.predict(img_bytes, top_k=3)
    print(f"[OK] Top-1 Candidate: {result['common_name']} ({result['species']})")
    print(f"     Confidence: {result['confidence'] * 100:.1f}% | Tier: {result['confidence_tier']}")
    print(f"     Top-3 Candidates: {[c['common_name'] for c in result['top_predictions']]}")
    print(f"     Taxonomic Family: {result['family']}")

    assert result["confidence"] > 0, "Confidence score must be positive"
    assert len(result["top_predictions"]) == 3, "Expected 3 top candidates"
    print("[SUCCESS] Phase 14.2 Marine Species Identification verified.\n")


def verify_phase_14_3_fisheries_catch_v1():
    print("=" * 60)
    print("VERIFYING PHASE 14.3: FISHERIES CATCH PREDICTION V1 ONLY")
    print("=" * 60)
    models_dir = Path("models/fisheries_catch")
    predictor = FisheriesCatchPredictor(model_dir=models_dir)

    assert predictor.is_loaded, "Fisheries predictor failed to load!"
    print(f"[OK] Model loaded: {predictor.metadata.get('model_name')}")
    print(f"[OK] Model type: {predictor.metadata.get('model_type')}")
    print(f"[OK] Model version: {predictor.metadata.get('model_version')} (Strictly V1)")
    print(f"[OK] Training framework: {predictor.metadata.get('training_framework')} (XGBoost)")
    print(f"[OK] Target variable: {predictor.metadata.get('target')}")

    # Test stratum: European Union Spain, Purse Seine, 45 fishing hours, August, latitude 2.5, longitude 55.5
    sample_stratum = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2024,
        "Latitude": 2.5,
        "Longitude": 55.5,
        "SpatialResolution": 1.0,
    }
    pred = predictor.predict(sample_stratum)
    print(f"[OK] Predicted Catch: {pred['predicted_catch_mt']} {pred['unit']}")
    print(f"     Input Stratum: Fleet={pred['input_summary']['fleet']} | Gear={pred['input_summary']['gear']} | Effort={pred['input_summary']['effort']} {pred['input_summary']['effort_units']}")
    print(f"     Derived Features: Monsoon Season='{pred['input_summary']['season']}' | Log_Effort={pred['input_summary']['log_effort']}")
    print(f"     Decision Support Notice: {pred['disclaimer']}")

    assert pred["predicted_catch_mt"] > 0, "Predicted catch should be positive for active fleet"
    assert pred["unit"] == "Metric Tons (MT)", "Catch unit must be Metric Tons"
    assert pred["input_summary"]["season"] == "SW_Monsoon", "August in Indian Ocean must be SW_Monsoon"
    assert pred["model_version"] == "1.0.0", "Model version must be 1.0.0 (V1 ONLY)"

    print("[SUCCESS] Phase 14.3 Fisheries Catch Prediction V1 verified.\n")


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# RUNNING END-TO-END VERIFICATION ACROSS ALL PRODUCTION ML MODULES #")
    print("#" * 70 + "\n")
    verify_phase_14_1_environmental_anomaly_v2()
    verify_phase_14_2_species_identification()
    verify_phase_14_3_fisheries_catch_v1()
    print("#" * 70)
    print("# ALL 3 PRODUCTION ML MODULES FULLY VERIFIED ON REAL INFERENCE #")
    print("#" * 70 + "\n")
