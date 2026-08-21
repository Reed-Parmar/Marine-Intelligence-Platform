"""
Phase 7 — Otolith Morphological Feature Extraction.
Extracts measurable geometric, intensity, and texture features from preprocessed otolith images.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Protocol

import numpy as np

from data_pipeline.specialized_science.otolith.preprocessing import PreprocessedImage


@dataclass
class OtolithFeatureVector:
    """Standardized numerical feature vector extracted from an otolith image."""
    features: Dict[str, float]
    feature_names: List[str]
    dimension: int
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "features": {k: round(v, 4) for k, v in self.features.items()},
            "summary": self.summary,
        }

    def to_numpy(self) -> np.ndarray:
        """Returns values as an ordered 1D NumPy float array for ML inference."""
        return np.array([self.features[k] for k in self.feature_names], dtype=np.float32)


class ImageFeatureExtractor(Protocol):
    """
    Protocol for otolith image feature extractors.
    Phase 8 can inject CNN backbone embeddings (e.g. ResNet, EfficientNet) using this interface.
    """
    def extract(self, preprocessed_image: PreprocessedImage) -> OtolithFeatureVector:
        ...


class BaselineMorphologicalFeatureExtractor:
    """
    Baseline feature extractor computing geometric, intensity, and gradient metrics.
    Operates on 2D normalized grayscale arrays.
    """

    def extract(self, preprocessed_image: PreprocessedImage) -> OtolithFeatureVector:
        arr = preprocessed_image.normalized_array
        if arr.ndim == 3:
            # If 3-channel RGB, convert to 2D luminance for statistics
            arr = np.mean(arr, axis=2)

        h, w = arr.shape
        orig_w, orig_h = preprocessed_image.original_dimensions

        # 1. Geometric Features
        aspect_ratio = orig_w / float(orig_h) if orig_h > 0 else 1.0
        area_px = float(orig_w * orig_h)

        # 2. Intensity Statistics
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        median_val = float(np.median(arr))

        # Contrast ratio
        contrast_ratio = (max_val - min_val) / (max_val + min_val + 1e-6)

        # 3. Simple Texture / Gradient Energy (horizontal and vertical differences)
        if h > 1 and w > 1:
            diff_h = np.abs(arr[:, 1:] - arr[:, :-1])
            diff_v = np.abs(arr[1:, :] - arr[:-1, :])
            grad_h_energy = float(np.mean(diff_h ** 2))
            grad_v_energy = float(np.mean(diff_v ** 2))
            grad_mag_mean = float(np.mean(diff_h) + np.mean(diff_v)) / 2.0
        else:
            grad_h_energy = 0.0
            grad_v_energy = 0.0
            grad_mag_mean = 0.0

        # 4. Approximate Image Entropy
        hist, _ = np.histogram(arr, bins=16, range=(0.0, 1.0), density=True)
        hist = hist[hist > 0]
        entropy = -float(np.sum(hist * np.log2(hist + 1e-9))) if len(hist) > 0 else 0.0

        # 5. Estimated Circularity (ratio of central mass vs perimeter)
        center_y, center_x = h // 2, w // 2
        radius = min(h, w) // 4
        y_coords, x_coords = np.ogrid[:h, :w]
        mask_center = (x_coords - center_x) ** 2 + (y_coords - center_y) ** 2 <= radius ** 2
        center_mass = float(np.mean(arr[mask_center])) if np.any(mask_center) else mean_val
        circ_estimate = center_mass / (mean_val + 1e-6)

        features: Dict[str, float] = {
            "aspect_ratio": aspect_ratio,
            "orig_width": float(orig_w),
            "orig_height": float(orig_h),
            "mean_intensity": mean_val,
            "std_intensity": std_val,
            "min_intensity": min_val,
            "max_intensity": max_val,
            "median_intensity": median_val,
            "contrast_ratio": contrast_ratio,
            "gradient_h_energy": grad_h_energy,
            "gradient_v_energy": grad_v_energy,
            "gradient_magnitude_mean": grad_mag_mean,
            "entropy": entropy,
            "circularity_estimate": circ_estimate,
        }

        feature_names = sorted(features.keys())

        return OtolithFeatureVector(
            features=features,
            feature_names=feature_names,
            dimension=len(features),
            summary={
                "aspect_ratio": round(aspect_ratio, 3),
                "mean_intensity": round(mean_val, 3),
                "contrast": round(contrast_ratio, 3),
                "extractor": "BaselineMorphologicalFeatureExtractor",
            },
        )
