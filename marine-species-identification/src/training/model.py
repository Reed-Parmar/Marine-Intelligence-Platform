"""
Transfer Learning Model Architecture for Marine Species Identification.
Supports MobileNetV3-Small, ResNet-18, and custom classifier heads.
"""

from typing import Tuple
import torch
import torch.nn as nn
import torchvision.models as models


def build_marine_classifier(
    architecture: str = "mobilenet_v3_small",
    num_classes: int = 10,
    pretrained: bool = True,
    freeze_backbone: bool = False,
    dropout_rate: float = 0.2
) -> nn.Module:
    """
    Constructs transfer learning model with custom classification head.
    """
    arch = architecture.lower()

    if arch == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)

        if freeze_backbone:
            for param in model.features.parameters():
                param.requires_grad = False

        # Replace classification head
        in_features = model.classifier[0].in_features
        model.classifier = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(256, num_classes)
        )

    elif arch == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)

        if freeze_backbone:
            for name, param in model.named_parameters():
                if "fc" not in name:
                    param.requires_grad = False

        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, num_classes)
        )

    else:
        raise ValueError(f"Unsupported architecture: {architecture}. Choose 'mobilenet_v3_small' or 'resnet18'.")

    return model


def count_parameters(model: nn.Module) -> Tuple[int, int]:
    """
    Returns (total_parameters, trainable_parameters).
    """
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable
