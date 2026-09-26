"""
Script to Train Phase I Baseline Marine Species Classifier.
Architecture: ResNet-18 with Frozen Backbone (Linear Classification Head Only).
Standard CrossEntropyLoss, No Class Weighting.
"""

import json
import sys
from pathlib import Path
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.dataset import (
    MarineSpeciesDataset,
    get_eval_transforms,
    get_train_transforms,
)
from src.training.model import build_marine_classifier
from src.training.trainer import MarineTrainer, log_experiment


def main():
    print("=" * 60)
    print("PHASE I: BASELINE MODEL TRAINING (FROZEN BACKBONE)")
    print("=" * 60)

    mapping_path = PROJECT_ROOT / "models" / "class_mapping.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)
    class_to_id = mapping_data["class_to_id"]
    num_classes = len(class_to_id)

    train_csv = PROJECT_ROOT / "data" / "splits" / "train.csv"
    val_csv = PROJECT_ROOT / "data" / "splits" / "val.csv"

    # Minimal baseline transforms (no heavy augmentation)
    train_dataset = MarineSpeciesDataset(train_csv, class_to_id, transform=get_eval_transforms())
    val_dataset = MarineSpeciesDataset(val_csv, class_to_id, transform=get_eval_transforms())

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

    # ResNet-18 with frozen feature backbone
    model = build_marine_classifier(
        architecture="resnet18",
        num_classes=num_classes,
        pretrained=True,
        freeze_backbone=True,
        dropout_rate=0.2
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3)

    baseline_dir = PROJECT_ROOT / "models" / "baseline"
    trainer = MarineTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        output_dir=baseline_dir,
        experiment_id="exp_01_baseline_frozen_resnet18"
    )

    res = trainer.train(epochs=6, early_stopping_patience=3)

    # Save baseline weights
    torch.save(model.state_dict(), baseline_dir / "baseline_model.pth")
    with open(baseline_dir / "baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    # Log to experiment CSV
    best_val_idx = res["best_epoch"] - 1 if res["best_epoch"] > 0 else -1
    log_experiment(
        PROJECT_ROOT / "results" / "experiment_log.csv",
        {
            "experiment_id": "exp_01_baseline_frozen_resnet18",
            "architecture": "resnet18_frozen",
            "learning_rate": 1e-3,
            "batch_size": 32,
            "epochs": res["total_epochs"],
            "augmentation": "None (Eval transforms)",
            "frozen_layers": "All backbone layers frozen",
            "class_weighting": "None",
            "validation_accuracy": res["history"]["val_acc"][best_val_idx],
            "validation_macro_f1": res["best_val_macro_f1"],
            "validation_loss": res["history"]["val_loss"][best_val_idx],
            "training_time_sec": res["total_training_time_sec"],
            "notes": "Baseline model for Phase I comparison"
        }
    )

    print("\nBaseline training complete! Saved to models/baseline/")


if __name__ == "__main__":
    main()
