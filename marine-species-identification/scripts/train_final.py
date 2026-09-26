"""
Script to Train Phase J / K / L Final Tuned Marine Species Classifier.
Architecture: ResNet-18 Transfer Learning with Fine-Tuned Deeper Layers (Layer4 + Head).
Class-Weighted CrossEntropyLoss for Imbalance Mitigation (Phase K).
Biological Training Augmentation & Learning Rate Scheduling (Phase L).
"""

import json
import sys
from pathlib import Path
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.dataset import (
    MarineSpeciesDataset,
    get_eval_transforms,
    get_train_transforms,
)
from src.training.model import build_marine_classifier
from src.training.trainer import MarineTrainer, log_experiment, plot_training_curves


def main():
    print("=" * 60)
    print("PHASE J/K/L: FINAL MODEL DEVELOPMENT & TUNING")
    print("=" * 60)

    mapping_path = PROJECT_ROOT / "models" / "class_mapping.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)
    class_to_id = mapping_data["class_to_id"]
    num_classes = len(class_to_id)

    train_csv = PROJECT_ROOT / "data" / "splits" / "train.csv"
    val_csv = PROJECT_ROOT / "data" / "splits" / "val.csv"

    # Full biological training transforms
    train_dataset = MarineSpeciesDataset(train_csv, class_to_id, transform=get_train_transforms())
    val_dataset = MarineSpeciesDataset(val_csv, class_to_id, transform=get_eval_transforms())

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

    # Phase K: Class-Weighted Loss Calculation
    class_weights = train_dataset.get_class_weights()
    print("Class weights for imbalance mitigation:")
    for cls_name, cls_id in class_to_id.items():
        print(f"  [{cls_id}] {cls_name:30s}: weight = {class_weights[cls_id]:.3f}")

    # Build model: ResNet-18 with unfrozen Layer4 for domain adaptation
    model = build_marine_classifier(
        architecture="resnet18",
        num_classes=num_classes,
        pretrained=True,
        freeze_backbone=False,
        dropout_rate=0.3
    )

    # Freeze early layers (conv1, bn1, layer1, layer2) to prevent catastrophic forgetting
    # Fine-tune layer3, layer4 and the fc head
    for name, param in model.named_parameters():
        if "layer4" not in name and "layer3" not in name and "fc" not in name:
            param.requires_grad = False

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

    # AdamW optimizer with differential learning rates
    optimizer = AdamW([
        {"params": [p for n, p in model.named_parameters() if ("layer3" in n or "layer4" in n) and p.requires_grad], "lr": 5e-5, "weight_decay": 1e-4},
        {"params": model.fc.parameters(), "lr": 5e-4, "weight_decay": 1e-4}
    ])

    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    best_model_dir = PROJECT_ROOT / "models" / "best_model"
    final_model_dir = PROJECT_ROOT / "models" / "final_model"
    species_identifier_dir = PROJECT_ROOT / "models" / "species_identifier"

    best_model_dir.mkdir(parents=True, exist_ok=True)
    final_model_dir.mkdir(parents=True, exist_ok=True)
    species_identifier_dir.mkdir(parents=True, exist_ok=True)

    trainer = MarineTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        output_dir=best_model_dir,
        experiment_id="exp_02_finetuned_resnet18_weighted"
    )

    res = trainer.train(epochs=10, early_stopping_patience=4)

    # Save training history
    history_path = PROJECT_ROOT / "results" / "training_history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    # Plot training curves
    plot_training_curves(res["history"], PROJECT_ROOT / "results" / "training_curves.png")

    # Load best model weights and save to final_model and species_identifier
    best_weights_path = best_model_dir / "best_model.pth"
    if best_weights_path.exists():
        model.load_state_dict(torch.load(best_weights_path, map_location=device))

    torch.save(model.state_dict(), final_model_dir / "final_model.pth")
    torch.save(model.state_dict(), species_identifier_dir / "species_model.pth")

    # Save metadata
    best_val_idx = res["best_epoch"] - 1 if res["best_epoch"] > 0 else -1
    model_metadata = {
        "model_name": "MarineSpeciesClassifier",
        "architecture": "resnet18_transfer_learning",
        "pretrained_weights": "ImageNet1K_V1",
        "num_classes": num_classes,
        "input_shape": [3, 224, 224],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "class_mapping": mapping_data["id_to_class"],
        "best_epoch": res["best_epoch"],
        "val_top1_accuracy": res["history"]["val_acc"][best_val_idx],
        "val_macro_f1": res["best_val_macro_f1"],
        "val_loss": res["history"]["val_loss"][best_val_idx],
        "training_time_sec": res["total_training_time_sec"],
        "version": "1.0.0"
    }

    with open(species_identifier_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2)

    with open(species_identifier_dir / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, indent=2)

    # Log to experiment log
    log_experiment(
        PROJECT_ROOT / "results" / "experiment_log.csv",
        {
            "experiment_id": "exp_02_finetuned_resnet18_weighted",
            "architecture": "resnet18_finetuned_layer3_layer4",
            "learning_rate": "5e-5 (backbone) / 5e-4 (fc)",
            "batch_size": 32,
            "epochs": res["total_epochs"],
            "augmentation": "Crop, Flips, Rotations, ColorJitter",
            "frozen_layers": "conv1, bn1, layer1, layer2 frozen; layer3, layer4 fine-tuned",
            "class_weighting": "Inverse-frequency weights",
            "validation_accuracy": res["history"]["val_acc"][best_val_idx],
            "validation_macro_f1": res["best_val_macro_f1"],
            "validation_loss": res["history"]["val_loss"][best_val_idx],
            "training_time_sec": res["total_training_time_sec"],
            "notes": "Final fine-tuned production candidate with class weighting"
        }
    )

    print("\nFinal model training complete! Exported to models/final_model/ and models/species_identifier/")


if __name__ == "__main__":
    main()
