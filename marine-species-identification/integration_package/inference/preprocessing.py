"""
Image Preprocessing and PyTorch Dataset Pipeline for Marine Species Identification.
Supports training augmentation (biologically valid transforms for fish orientation & lighting)
and deterministic validation/testing transforms.
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union
from PIL import Image
import pandas as pd
import torch
from torch.utils.data import Dataset
from torchvision import transforms

# Standard ImageNet normalization parameters
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
DEFAULT_IMAGE_SIZE = (224, 224)


def get_train_transforms(image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    """
    Biologically sound training transforms for marine fish imagery.
    Avoids extreme distortion that would destroy fin/striping taxonomy.
    """
    return transforms.Compose([
        transforms.Resize((int(image_size[0] * 1.14), int(image_size[1] * 1.14))),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])


def get_eval_transforms(image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    """
    Deterministic evaluation transforms for validation, testing, and production inference.
    """
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])


class MarineSpeciesDataset(Dataset):
    """
    PyTorch Dataset loading images from split CSV manifests.
    """

    def __init__(
        self,
        csv_path: Union[str, Path],
        class_to_id: Dict[str, int],
        transform: Optional[Callable] = None,
        base_dir: Optional[Path] = None
    ):
        self.df = pd.read_csv(csv_path)
        self.class_to_id = class_to_id
        self.transform = transform
        self.base_dir = base_dir

        # Validate that all rows have valid classes
        valid_mask = self.df["species_name"].isin(self.class_to_id)
        if not valid_mask.all():
            self.df = self.df[valid_mask].reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        row = self.df.iloc[idx]
        img_path = Path(row["image_path"])

        # If absolute path doesn't exist, try relative to base_dir
        if not img_path.exists() and self.base_dir:
            img_path = self.base_dir / row["relative_path"]

        # Open and ensure RGB
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            if self.transform:
                tensor = self.transform(img)
            else:
                tensor = transforms.ToTensor()(img)

        label = self.class_to_id[row["species_name"]]
        return tensor, label, row["species_name"]

    def get_class_counts(self) -> Dict[int, int]:
        """Returns image counts per integer class index."""
        counts = {}
        for sp_name, cnt in self.df["species_name"].value_counts().items():
            if sp_name in self.class_to_id:
                counts[self.class_to_id[sp_name]] = int(cnt)
        return counts

    def get_class_weights(self) -> torch.Tensor:
        """
        Calculates inverse-frequency class weights for cross-entropy loss
        to counteract natural class imbalance.
        """
        counts = self.get_class_counts()
        num_classes = len(self.class_to_id)
        weights = torch.ones(num_classes, dtype=torch.float32)
        total_samples = len(self.df)

        for cls_id in range(num_classes):
            cnt = counts.get(cls_id, 1)
            # Standard inverse-frequency weighting normalized to mean=1.0
            weights[cls_id] = total_samples / (num_classes * cnt)

        return weights
