"""
Analysis Service: Cross-domain correlation and trend computation.
"""

import math
from typing import Any, Dict, List, Optional
from backend.app.schemas.analysis import (
    AnalysisJobResponse,
    CorrelationAnalysisRequest,
    CorrelationAnalysisResponse
)
from backend.app.db.database import execute_query


class AnalysisService:

    @staticmethod
    def calculate_correlation(req: CorrelationAnalysisRequest) -> CorrelationAnalysisResponse:
        """
        Calculates Pearson correlation between oceanographic and fisheries variables.
        """
        # Query matched observations where both SST and catch weight exist
        query = """
        SELECT 
            o.temperature as val_x,
            f.catch_weight_kg as val_y
        FROM public.oceanographic_observations o
        JOIN public.fisheries_records f ON o.dataset_id = f.dataset_id
        WHERE o.temperature IS NOT NULL AND f.catch_weight_kg IS NOT NULL
        LIMIT 500;
        """
        rows = execute_query(query)
        
        if len(rows) < 2:
            return CorrelationAnalysisResponse(
                variable_x=req.variable_x,
                variable_y=req.variable_y,
                correlation_coefficient=None,
                sample_size=len(rows),
                data_points=[]
            )

        x_vals = [float(r["val_x"]) for r in rows]
        y_vals = [float(r["val_y"]) for r in rows]
        n = len(x_vals)

        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
        den_x = sum((x - mean_x) ** 2 for x in x_vals)
        den_y = sum((y - mean_y) ** 2 for y in y_vals)
        den = math.sqrt(den_x * den_y)

        r = round(num / den, 4) if den != 0 else 0.0

        sample_points = [{"x": x, "y": y} for x, y in zip(x_vals[:50], y_vals[:50])]

        return CorrelationAnalysisResponse(
            variable_x=req.variable_x,
            variable_y=req.variable_y,
            correlation_coefficient=r,
            sample_size=n,
            data_points=sample_points
        )
