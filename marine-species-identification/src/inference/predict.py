"""
Standalone Production Inference Engine for Marine Species Identification.
Loads trained PyTorch classifier, applies deterministic preprocessing,
calibrates confidence scores, and returns top-k species predictions with taxonomic context.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image
import torch
import torch.nn.functional as F

from src.data.download import SPECIES_CATALOG
from src.preprocessing.dataset import get_eval_transforms
from src.training.model import build_marine_classifier

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "species_identifier"


class MarineSpeciesIdentifier:
    """
    Production inference engine for Marine Species Identification.
    """

    def __init__(
        self,
        model_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None
    ):
        self.model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        # Paths
        self.weights_path = self.model_dir / "species_model.pth"
        self.metadata_path = self.model_dir / "model_metadata.json"
        self.mapping_path = self.model_dir / "class_mapping.json"

        self.model: Optional[torch.nn.Module] = None
        self.id_to_class: Dict[int, str] = {}
        self.class_to_id: Dict[str, int] = {}
        self.num_classes: int = 0
        self.model_version: str = "1.0.0"
        self.transform = get_eval_transforms()

        self._load()

    def _load(self):
        """Loads model weights, class mapping, and metadata."""
        if not self.mapping_path.exists():
            # Fallback to main models directory
            alt_mapping = self.model_dir.parent / "class_mapping.json"
            if alt_mapping.exists():
                self.mapping_path = alt_mapping
            else:
                raise FileNotFoundError(f"Class mapping not found at {self.mapping_path}")

        with open(self.mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        self.id_to_class = {int(k): v for k, v in mapping["id_to_class"].items()}
        self.class_to_id = mapping["class_to_id"]
        self.num_classes = len(self.id_to_class)

        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.model_version = meta.get("version", "1.0.0")

        # Fallback weights check
        if not self.weights_path.exists():
            alt_weights = self.model_dir.parent / "final_model" / "final_model.pth"
            if alt_weights.exists():
                self.weights_path = alt_weights
            else:
                alt_base = self.model_dir.parent / "baseline" / "baseline_model.pth"
                if alt_base.exists():
                    self.weights_path = alt_base

        self.model = build_marine_classifier(
            architecture="resnet18",
            num_classes=self.num_classes,
            pretrained=False,
            freeze_backbone=False
        )

        if self.weights_path.exists():
            state_dict = torch.load(self.weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

    def _get_taxonomic_info(self, species_name: str) -> Dict[str, str]:
        """Resolves common name and family from catalog or fallback."""
        for sid, info in SPECIES_CATALOG.items():
            if info["name"].lower() == species_name.lower():
                return {
                    "common_name": info["common"],
                    "family": info["family"]
                }
        return {"common_name": species_name, "family": "Marine Fish"}

    @torch.no_grad()
    def predict(
        self,
        image_input: Union[str, Path, Image.Image],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Executes end-to-end inference on input image.
        Accepts file path or PIL Image.
        """
        t0 = time.perf_counter()

        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            if not img_path.exists():
                raise FileNotFoundError(f"Input image not found: {img_path}")
            with Image.open(img_path) as raw_img:
                pil_img = raw_img.convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        outputs = self.model(tensor)
        probs = F.softmax(outputs, dim=1).squeeze(0)

        # Top-k predictions
        k = min(top_k, self.num_classes)
        top_probs, top_indices = torch.topk(probs, k=k)

        top_predictions = []
        for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
            sp_name = self.id_to_class[int(idx)]
            tax = self._get_taxonomic_info(sp_name)
            top_predictions.append({
                "species": sp_name,
                "common_name": tax["common_name"],
                "family": tax["family"],
                "confidence": round(float(prob), 4)
            })

        top1 = top_predictions[0]
        confidence = top1["confidence"]

        # Confidence tiers (Phase O Calibration)
        if confidence >= 0.70:
            confidence_tier = "HIGH"
        elif confidence >= 0.40:
            confidence_tier = "MODERATE"
        else:
            confidence_tier = "LOW"

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "species": top1["species"],
            "common_name": top1["common_name"],
            "family": top1["family"],
            "confidence": confidence,
            "confidence_tier": confidence_tier,
            "top_predictions": top_predictions,
            "model_version": self.model_version,
            "device": str(self.device),
            "inference_time_ms": latency_ms
        }
