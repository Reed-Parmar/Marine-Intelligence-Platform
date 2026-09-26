"""
Evaluation Suite for Marine Environmental Anomaly Detection.

Implements rigorous unsupervised evaluation metrics without fabricating ground-truth accuracy.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

from .config import RESULTS_DIR

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvaluationReport:
    """Detailed evaluation metrics for unsupervised anomaly detector."""
    total_observations: int
    anomaly_count: int
    anomaly_rate_pct: float
    score_distribution: Dict[str, float]
    severity_breakdown: Dict[str, int]
    temporal_monthly_distribution: Dict[str, Dict[str, Any]]
    spatial_latitudinal_distribution: Dict[str, Dict[str, Any]]
    persistence_summary: Dict[str, Any]
    correlation_with_sst_deviation: Dict[str, float]
    top_positive_mhw_anomalies: List[Dict[str, Any]]
    top_negative_cold_anomalies: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def print_summary(self):
        """Prints a human-readable summary of the evaluation report."""
        print("=" * 85)
        print("ENVIRONMENTAL ANOMALY DETECTION EVALUATION REPORT")
        print("=" * 85)
        print(f"Total Evaluated Records : {self.total_observations:,}")
        print(f"Flagged Anomalies       : {self.anomaly_count:,} ({self.anomaly_rate_pct:.2f}%)")
        print("-" * 85)
        print("SEVERITY BREAKDOWN:")
        for sev, count in self.severity_breakdown.items():
            pct = (count / self.total_observations * 100) if self.total_observations > 0 else 0
            print(f"  • {sev.capitalize():12s}: {count:6,} ({pct:.1f}%)")
        print("-" * 85)
        print("SCORE DISTRIBUTION (0-100 normalized):")
        print(f"  Mean: {self.score_distribution['mean']} | Std: {self.score_distribution['std']} | Median: {self.score_distribution['p50']}")
        print(f"  P10: {self.score_distribution['p10']} | P90: {self.score_distribution['p90']} | P99: {self.score_distribution['p99']}")
        print("-" * 85)
        print("ALIGNMENT WITH PHYSICAL SST DEVIATION (|SST - Baseline|):")
        print(f"  Pearson Correlation r  : {self.correlation_with_sst_deviation.get('pearson_r')} (p={self.correlation_with_sst_deviation.get('pearson_p')})")
        print(f"  Spearman Rank rho     : {self.correlation_with_sst_deviation.get('spearman_rho')} (p={self.correlation_with_sst_deviation.get('spearman_p')})")
        print("-" * 85)
        print("PERSISTENCE ANALYSIS:")
        print(f"  Max Consecutive Events in Local Grid : {self.persistence_summary.get('max_consecutive_days', 1)} days")
        print(f"  Multi-day Persistent Clusters Found : {self.persistence_summary.get('persistent_clusters_count', 0)}")
        print("=" * 85 + "\n")


class EnvironmentalAnomalyEvaluator:
    """
    Computes unsupervised statistical evaluation metrics and diagnostics.
    """

    @staticmethod
    def evaluate(df: pd.DataFrame) -> AnomalyEvaluationReport:
        """
        Evaluates predictions DataFrame containing:
        ['timestamp', 'latitude', 'longitude', 'analysed_sst', 'baseline_sst', 'sst_anomaly', 'anomaly_score', 'anomaly_label', 'severity']
        """
        required_cols = ["analysed_sst", "baseline_sst", "sst_anomaly", "anomaly_score", "anomaly_label"]
        for c in required_cols:
            if c not in df.columns:
                raise ValueError(f"Missing required column for evaluation: '{c}'")

        n_total = len(df)
        if n_total == 0:
            raise ValueError("Cannot evaluate empty DataFrame.")

        is_anomaly = df["anomaly_label"] == -1
        n_anomalies = int(is_anomaly.sum())
        anomaly_rate = round(float(n_anomalies / n_total * 100), 2)

        # 1. Score Distribution
        scores = df["anomaly_score"]
        score_dist = {
            "mean": round(float(scores.mean()), 2),
            "std": round(float(scores.std()), 2),
            "min": round(float(scores.min()), 2),
            "p10": round(float(scores.quantile(0.10)), 2),
            "p25": round(float(scores.quantile(0.25)), 2),
            "p50": round(float(scores.median()), 2),
            "p75": round(float(scores.quantile(0.75)), 2),
            "p90": round(float(scores.quantile(0.90)), 2),
            "p95": round(float(scores.quantile(0.95)), 2),
            "p99": round(float(scores.quantile(0.99)), 2),
            "max": round(float(scores.max()), 2),
        }

        # 2. Severity Breakdown
        sev_counts = df["severity"].value_counts().to_dict() if "severity" in df.columns else {}
        severity_breakdown = {k: int(sev_counts.get(k, 0)) for k in ["low", "moderate", "high", "critical"]}

        # 3. Temporal Distribution by Month
        monthly_dist: Dict[str, Dict[str, Any]] = {}
        if "month" in df.columns:
            for m, grp in df.groupby("month"):
                m_total = len(grp)
                m_anom = int((grp["anomaly_label"] == -1).sum())
                monthly_dist[f"month_{int(m)}"] = {
                    "total": m_total,
                    "anomalies": m_anom,
                    "anomaly_rate_pct": round(float(m_anom / m_total * 100), 2) if m_total > 0 else 0.0,
                    "mean_sst_anomaly": round(float(grp["sst_anomaly"].mean()), 3),
                }

        # 4. Spatial Latitudinal Distribution (5-degree bins)
        lat_dist: Dict[str, Dict[str, Any]] = {}
        temp_df = df.copy()
        temp_df["lat_bin"] = temp_df["latitude"].apply(lambda l: f"{int(np.floor(l / 5.0) * 5)}°N-{int(np.floor(l / 5.0) * 5 + 5)}°N")
        for b, grp in temp_df.groupby("lat_bin"):
            b_total = len(grp)
            b_anom = int((grp["anomaly_label"] == -1).sum())
            lat_dist[b] = {
                "total": b_total,
                "anomalies": b_anom,
                "anomaly_rate_pct": round(float(b_anom / b_total * 100), 2) if b_total > 0 else 0.0,
                "mean_sst": round(float(grp["analysed_sst"].mean()), 2),
            }

        # 5. Correlation with Physical Deviation (|SST - Baseline|)
        abs_anom = df["sst_anomaly"].abs()
        pr, pp = stats.pearsonr(scores, abs_anom)
        sr, sp = stats.spearmanr(scores, abs_anom)
        corr_dict = {
            "pearson_r": round(float(pr), 4),
            "pearson_p": float(pp),
            "spearman_rho": round(float(sr), 4),
            "spearman_p": float(sp),
        }

        # 6. Persistence Analysis
        # Check for consecutive anomalous days in same ~1° cell
        persistence_summary = {"max_consecutive_days": 1, "persistent_clusters_count": 0}
        if "day_of_year" in df.columns:
            temp_df["spatial_cell"] = temp_df.apply(
                lambda r: f"{round(np.floor(r['latitude']), 1)}_{round(np.floor(r['longitude']), 1)}", axis=1
            )
            anom_df = temp_df[temp_df["anomaly_label"] == -1].sort_values(["spatial_cell", "day_of_year"])
            
            cluster_count = 0
            max_streak = 1
            for _, grp in anom_df.groupby("spatial_cell"):
                doys = grp["day_of_year"].values
                if len(doys) > 1:
                    streak = 1
                    for i in range(1, len(doys)):
                        if doys[i] - doys[i - 1] == 1:
                            streak += 1
                            max_streak = max(max_streak, streak)
                        else:
                            if streak >= 3:
                                cluster_count += 1
                            streak = 1
                    if streak >= 3:
                        cluster_count += 1
            persistence_summary = {
                "max_consecutive_days": max_streak,
                "persistent_clusters_count": cluster_count,
            }

        # 7. Top Positive (MHW) and Negative (Cold) Anomalies
        anom_rows = df[df["anomaly_label"] == -1]
        top_mhw = anom_rows.sort_values("sst_anomaly", ascending=False).head(10)
        top_cold = anom_rows.sort_values("sst_anomaly", ascending=True).head(10)

        fmt_cols = ["timestamp", "latitude", "longitude", "analysed_sst", "baseline_sst", "sst_anomaly", "anomaly_score", "severity"]
        top_mhw_records = [
            {k: round(float(v), 3) if isinstance(v, (float, np.floating)) else v for k, v in row.items()}
            for row in top_mhw[fmt_cols].to_dict(orient="records")
        ]
        top_cold_records = [
            {k: round(float(v), 3) if isinstance(v, (float, np.floating)) else v for k, v in row.items()}
            for row in top_cold[fmt_cols].to_dict(orient="records")
        ]

        return AnomalyEvaluationReport(
            total_observations=n_total,
            anomaly_count=n_anomalies,
            anomaly_rate_pct=anomaly_rate,
            score_distribution=score_dist,
            severity_breakdown=severity_breakdown,
            temporal_monthly_distribution=monthly_dist,
            spatial_latitudinal_distribution=lat_dist,
            persistence_summary=persistence_summary,
            correlation_with_sst_deviation=corr_dict,
            top_positive_mhw_anomalies=top_mhw_records,
            top_negative_cold_anomalies=top_cold_records,
        )

    @staticmethod
    def save_evaluation_results(
        report: AnomalyEvaluationReport,
        df_predictions: pd.DataFrame,
        output_dir: Optional[Union[str, Path]] = None,
    ):
        """Saves evaluation JSON and predictions CSV to results directory."""
        target_dir = Path(output_dir or RESULTS_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save JSON Report
        with open(target_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)

        # 2. Save Predictions Sample/Subset (top anomalies + representative inliers)
        anomalies_df = df_predictions[df_predictions["anomaly_label"] == -1]
        inliers_sample = df_predictions[df_predictions["anomaly_label"] == 1].sample(
            min(5000, len(df_predictions) - len(anomalies_df)), random_state=42
        ) if len(df_predictions) > len(anomalies_df) else pd.DataFrame()

        export_df = pd.concat([anomalies_df, inliers_sample]).sort_values("anomaly_score", ascending=False)
        export_df.to_csv(target_dir / "predictions_sample.csv", index=False)

        logger.info(f"Evaluation report and predictions sample saved to {target_dir}")
