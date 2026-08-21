"""
Phase 7 — Otolith / Marine Image Preprocessing.
Validates input images, converts color spaces, resizes, and normalizes pixel arrays using PIL & NumPy.
"""

from dataclasses import dataclass, field
import io
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image


SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "JPG", "TIFF", "TIF", "BMP", "WEBP"}


@dataclass
class ImageValidationResult:
    """Validation report for image input."""
    is_valid: bool
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mode: Optional[str] = None
    channels: Optional[int] = None
    file_size_bytes: Optional[int] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "format": self.format,
            "dimensions": f"{self.width}x{self.height}" if self.width and self.height else None,
            "mode": self.mode,
            "file_size_bytes": self.file_size_bytes,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class PreprocessedImage:
    """Container for preprocessed image data and normalized array representations."""
    image: Image.Image
    array: np.ndarray                # 2D or 3D NumPy array [0.0, 1.0] or [0, 255]
    normalized_array: np.ndarray     # Standardized float array in [0.0, 1.0]
    width: int
    height: int
    original_dimensions: Tuple[int, int]
    is_grayscale: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


def _load_pil_image(image_input: Union[str, Path, bytes, BinaryIO, Image.Image]) -> Tuple[Optional[Image.Image], Optional[int], List[str]]:
    """Helper to safely open PIL Image from various input types."""
    errors: List[str] = []
    file_size: Optional[int] = None

    if isinstance(image_input, Image.Image):
        return image_input.copy(), None, []

    try:
        if isinstance(image_input, (str, Path)):
            path_obj = Path(image_input)
            if not path_obj.exists():
                return None, None, [f"Image file does not exist: {image_input}"]
            file_size = path_obj.stat().st_size
            if file_size == 0:
                return None, 0, ["Image file is empty (0 bytes)."]
            img = Image.open(path_obj)
            img.load()
            return img, file_size, []

        elif isinstance(image_input, bytes):
            file_size = len(image_input)
            if file_size == 0:
                return None, 0, ["Image byte stream is empty (0 bytes)."]
            bio = io.BytesIO(image_input)
            img = Image.open(bio)
            img.load()
            return img, file_size, []

        elif hasattr(image_input, "read"):
            img = Image.open(image_input)
            img.load()
            return img, None, []

        else:
            return None, None, [f"Unsupported image input type: {type(image_input)}"]

    except Exception as e:
        return None, file_size, [f"Corrupt or unreadable image: {str(e)}"]


def validate_image_input(
    image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
    min_dimension: int = 32,
) -> ImageValidationResult:
    """
    Validates image file readability, dimensions, and supported format.
    """
    img, file_size, errors = _load_pil_image(image_input)
    if errors or img is None:
        return ImageValidationResult(
            is_valid=False,
            file_size_bytes=file_size,
            errors=errors,
        )

    img_format = (img.format or "PNG").upper()
    width, height = img.size
    mode = img.mode
    channels = len(mode) if mode in ("RGB", "RGBA", "CMYK") else 1
    warnings: List[str] = []

    if img_format not in SUPPORTED_IMAGE_FORMATS:
        warnings.append(f"Image format '{img_format}' is not in standard list {sorted(SUPPORTED_IMAGE_FORMATS)}.")

    if width < min_dimension or height < min_dimension:
        return ImageValidationResult(
            is_valid=False,
            format=img_format,
            width=width,
            height=height,
            mode=mode,
            channels=channels,
            file_size_bytes=file_size,
            errors=[f"Image dimensions ({width}x{height}) are smaller than minimum allowed ({min_dimension}x{min_dimension})."],
        )

    return ImageValidationResult(
        is_valid=True,
        format=img_format,
        width=width,
        height=height,
        mode=mode,
        channels=channels,
        file_size_bytes=file_size,
        warnings=warnings,
    )


def preprocess_image(
    image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
    target_size: Tuple[int, int] = (224, 224),
    to_grayscale: bool = True,
    normalize: bool = True,
) -> PreprocessedImage:
    """
    Standardizes image input for scientific feature extraction and classification.

    Args:
        image_input: Path, bytes, or PIL Image.
        target_size: (width, height) output resolution.
        to_grayscale: Convert to 1-channel luminance ('L').
        normalize: Scale pixel float values to [0.0, 1.0].
    """
    img, _, errors = _load_pil_image(image_input)
    if errors or img is None:
        raise ValueError(f"Cannot preprocess invalid image: {'; '.join(errors)}")

    orig_dims = img.size

    # Convert color space
    if to_grayscale:
        proc_img = img.convert("L")
    else:
        proc_img = img.convert("RGB")

    # Resize using bilinear resampling
    resample_filter = getattr(Image, "Resampling", Image).BILINEAR
    proc_img = proc_img.resize(target_size, resample=resample_filter)

    # Convert to NumPy array
    raw_array = np.array(proc_img)
    if normalize:
        norm_array = raw_array.astype(np.float32) / 255.0
    else:
        norm_array = raw_array.astype(np.float32)

    return PreprocessedImage(
        image=proc_img,
        array=raw_array,
        normalized_array=norm_array,
        width=target_size[0],
        height=target_size[1],
        original_dimensions=orig_dims,
        is_grayscale=to_grayscale,
        metadata={"target_size": target_size, "to_grayscale": to_grayscale},
    )
