"""
Comprehensive Evaluation Engine for Marine Species Identification.
Evaluates final model ONCE on the untouched test split and calculates
Macro/Weighted F1, Top-1/3/5 Accuracy, Per-Class Metrics, and Confusion Matrix.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader

from src.preprocessing.dataset import MarineSpeciesDataset, get_eval_transforms
from src.training.model import build_marine_classifier


@torch.no_grad()
def evaluate_model_on_test_set(
    model_weights_path: Path,
    test_csv_path: Path,
    class_mapping_path: Path,
    results_dir: Path,
    architecture: str = "resnet18",
    batch_size: int = 32,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Evaluates trained model on the untouched test split and exports all evaluation artifacts.
    """
    device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(class_mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    id_to_class = {int(k): v for k, v in mapping["id_to_class"].items()}
    class_to_id = mapping["class_to_id"]
    class_names = [id_to_class[i] for i in range(len(id_to_class))]
    num_classes = len(class_names)

    test_dataset = MarineSpeciesDataset(test_csv_path, class_to_id, transform=get_eval_transforms())
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Reconstruct model
    model = build_marine_classifier(
        architecture=architecture,
        num_classes=num_classes,
        pretrained=False,
        freeze_backbone=False
    )
    model.load_state_dict(torch.load(model_weights_path, map_location=device))
    model.to(device)
    model.eval()

    all_preds_top1 = []
    all_preds_top3 = []
    all_preds_top5 = []
    all_probs = []
    all_labels = []
    all_paths = []

    correct_top1 = 0
    correct_top3 = 0
    correct_top5 = 0
    total = 0

    criterion = nn.CrossEntropyLoss()
    running_loss = 0.0

    for i, (images, labels, _) in enumerate(test_loader):
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)
        running_loss += loss.item() * images.size(0)
        total += labels.size(0)

        probs = torch.softmax(outputs, dim=1)

        # Top-1
        _, top1 = torch.max(outputs, 1)
        correct_top1 += torch.sum(top1 == labels).item()

        # Top-3
        k3 = min(3, num_classes)
        _, top3 = torch.topk(outputs, k=k3, dim=1)
        correct_top3 += torch.sum(top3 == labels.unsqueeze(1)).item()

        # Top-5
        k5 = min(5, num_classes)
        _, top5 = torch.topk(outputs, k=k5, dim=1)
        correct_top5 += torch.sum(top5 == labels.unsqueeze(1)).item()

        all_preds_top1.extend(top1.cpu().numpy())
        all_preds_top3.extend(top3.cpu().numpy().tolist())
        all_preds_top5.extend(top5.cpu().numpy().tolist())
        all_probs.extend(probs.cpu().numpy().tolist())
        all_labels.extend(labels.cpu().numpy())

    test_loss = running_loss / total
    top1_acc = correct_top1 / total
    top3_acc = correct_top3 / total
    top5_acc = correct_top5 / total

    y_true = np.array(all_labels)
    y_pred = np.array(all_preds_top1)

    macro_precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_recall = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    weighted_precision = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_recall = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # Per-class metrics
    report_dict = classification_report(
        y_true, y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    per_class_rows = []
    for cls_name in class_names:
        stats = report_dict.get(cls_name, {})
        per_class_rows.append({
            "species_name": cls_name,
            "precision": round(stats.get("precision", 0.0), 4),
            "recall": round(stats.get("recall", 0.0), 4),
            "f1_score": round(stats.get("f1-score", 0.0), 4),
            "support": int(stats.get("support", 0))
        })

    per_class_df = pd.DataFrame(per_class_rows)
    per_class_csv_path = results_dir / "per_class_metrics.csv"
    per_class_df.to_csv(per_class_csv_path, index=False)

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.title("Untouched Test Set Confusion Matrix - Marine Species Identification", fontsize=12, weight="bold")
    plt.xlabel("Predicted Species", fontsize=10)
    plt.ylabel("Ground-Truth Species", fontsize=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    cm_plot_path = results_dir / "confusion_matrix.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()

    metrics = {
        "evaluation_dataset": "Untouched Test Set (data/splits/test.csv)",
        "total_test_samples": total,
        "test_loss": round(test_loss, 4),
        "top1_accuracy": round(top1_acc, 4),
        "top3_accuracy": round(top3_acc, 4),
        "top5_accuracy": round(top5_acc, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(weighted_precision, 4),
        "weighted_recall": round(weighted_recall, 4),
        "weighted_f1": round(weighted_f1, 4),
        "confusion_matrix_path": str(cm_plot_path.name),
        "per_class_metrics_path": str(per_class_csv_path.name),
        "per_class_summary": per_class_rows
    }

    test_metrics_path = results_dir / "test_metrics.json"
    with open(test_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("=" * 60)
    print("FINAL UNTOUCHED TEST EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Test Samples: {total}")
    print(f"Top-1 Accuracy:     {top1_acc * 100:.2f}%")
    print(f"Top-3 Accuracy:     {top3_acc * 100:.2f}%")
    print(f"Top-5 Accuracy:     {top5_acc * 100:.2f}%")
    print(f"Macro Precision:    {macro_precision:.4f}")
    print(f"Macro Recall:       {macro_recall:.4f}")
    print(f"Macro F1-Score:     {macro_f1:.4f}")
    print(f"Weighted F1-Score:  {weighted_f1:.4f}")

    return metrics, cm, all_probs, y_true, y_pred
