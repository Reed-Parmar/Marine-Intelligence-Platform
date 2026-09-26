"""
Training Engine for Marine Species Identification.
Supports Baseline training, Full Fine-Tuning, Class Imbalance Weighting,
Learning Rate Scheduling, and Experiment Logging.
"""

import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.optim import Adam, AdamW, Optimizer
from torch.optim.lr_scheduler import ReduceLROnPlateau, _LRScheduler
from torch.utils.data import DataLoader

from src.preprocessing.dataset import (
    MarineSpeciesDataset,
    get_eval_transforms,
    get_train_transforms,
)
from src.training.model import build_marine_classifier, count_parameters


class MarineTrainer:
    """
    Modular Trainer for Marine Species Classification.
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: nn.Module,
        optimizer: Optimizer,
        scheduler: Optional[Any] = None,
        device: Optional[torch.device] = None,
        output_dir: Optional[Path] = None,
        experiment_id: str = "exp_01"
    ):
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.output_dir = Path(output_dir or "models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_id = experiment_id

        self.history: Dict[str, List[float]] = {
            "epoch": [],
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "val_macro_f1": [],
            "val_top3_acc": [],
            "lr": []
        }

    def train_epoch(self) -> Tuple[float, float]:
        """Runs one full training epoch."""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels, _ in self.train_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc = correct / total
        return epoch_loss, epoch_acc

    @torch.no_grad()
    def evaluate(self, loader: Optional[DataLoader] = None) -> Dict[str, float]:
        """Evaluates model on validation or test loader."""
        eval_loader = loader or self.val_loader
        self.model.eval()
        running_loss = 0.0
        correct_top1 = 0
        correct_top3 = 0
        total = 0

        all_preds = []
        all_labels = []

        for images, labels, _ in eval_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            total += labels.size(0)

            # Top-1
            _, top1_preds = torch.max(outputs, 1)
            correct_top1 += torch.sum(top1_preds == labels).item()

            # Top-3
            _, top3_preds = torch.topk(outputs, k=min(3, outputs.size(1)), dim=1)
            correct_top3 += torch.sum(top3_preds == labels.unsqueeze(1)).item()

            all_preds.extend(top1_preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

        eval_loss = running_loss / total
        top1_acc = correct_top1 / total
        top3_acc = correct_top3 / total
        macro_f1 = float(f1_score(all_labels, all_preds, average="macro", zero_division=0))

        return {
            "loss": float(round(eval_loss, 4)),
            "top1_acc": float(round(top1_acc, 4)),
            "top3_acc": float(round(top3_acc, 4)),
            "macro_f1": float(round(macro_f1, 4))
        }

    def train(
        self,
        epochs: int = 10,
        early_stopping_patience: int = 4,
        save_best: bool = True
    ) -> Dict[str, Any]:
        """Full training loop with early stopping."""
        best_val_macro_f1 = -1.0
        best_epoch = 0
        patience_counter = 0

        total_p, trainable_p = count_parameters(self.model)
        print(f"[{self.experiment_id}] Starting training: {epochs} epochs | Device: {self.device}")
        print(f"Parameters: Total={total_p:,}, Trainable={trainable_p:,}")

        start_time = time.time()

        for epoch in range(1, epochs + 1):
            ep_start = time.time()
            train_loss, train_acc = self.train_epoch()
            val_metrics = self.evaluate(self.val_loader)

            current_lr = self.optimizer.param_groups[0]["lr"]
            if self.scheduler:
                if isinstance(self.scheduler, ReduceLROnPlateau):
                    self.scheduler.step(val_metrics["loss"])
                else:
                    self.scheduler.step()

            self.history["epoch"].append(epoch)
            self.history["train_loss"].append(round(train_loss, 4))
            self.history["train_acc"].append(round(train_acc, 4))
            self.history["val_loss"].append(val_metrics["loss"])
            self.history["val_acc"].append(val_metrics["top1_acc"])
            self.history["val_macro_f1"].append(val_metrics["macro_f1"])
            self.history["val_top3_acc"].append(val_metrics["top3_acc"])
            self.history["lr"].append(current_lr)

            elapsed = time.time() - ep_start
            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) | "
                f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.1f}% | "
                f"Val Loss: {val_metrics['loss']:.4f} Acc: {val_metrics['top1_acc']*100:.1f}% "
                f"Macro-F1: {val_metrics['macro_f1']:.4f} Top-3: {val_metrics['top3_acc']*100:.1f}%"
            )

            # Checkpoint best model on validation macro-f1
            if val_metrics["macro_f1"] > best_val_macro_f1:
                best_val_macro_f1 = val_metrics["macro_f1"]
                best_epoch = epoch
                patience_counter = 0
                if save_best:
                    best_model_path = self.output_dir / "best_model.pth"
                    torch.save(self.model.state_dict(), best_model_path)
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print(f"Early stopping triggered at epoch {epoch} (No improvement for {early_stopping_patience} epochs).")
                    break

        total_time = time.time() - start_time
        print(f"Training completed in {total_time:.1f}s. Best Epoch: {best_epoch} (Val Macro-F1: {best_val_macro_f1:.4f})")

        return {
            "experiment_id": self.experiment_id,
            "total_epochs": epoch,
            "best_epoch": best_epoch,
            "best_val_macro_f1": best_val_macro_f1,
            "total_training_time_sec": round(total_time, 1),
            "history": self.history
        }


def plot_training_curves(history: Dict[str, List[float]], output_path: Path):
    """Generates and saves dual-panel loss and accuracy curves."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epochs = history["epoch"]

    plt.figure(figsize=(14, 5))

    # Loss Curve
    plt.subplot(1, 2, 1)
    plt.plot(epochs, history["train_loss"], "o-", label="Train Loss", color="#1f77b4", linewidth=2)
    plt.plot(epochs, history["val_loss"], "s--", label="Val Loss", color="#d62728", linewidth=2)
    plt.title("Cross-Entropy Loss Across Epochs", fontsize=12, weight="bold")
    plt.xlabel("Epoch", fontsize=10)
    plt.ylabel("Loss", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    # Accuracy / Macro-F1 Curve
    plt.subplot(1, 2, 2)
    plt.plot(epochs, [a * 100 for a in history["train_acc"]], "o-", label="Train Top-1 Acc (%)", color="#2ca02c", linewidth=2)
    plt.plot(epochs, [a * 100 for a in history["val_acc"]], "s--", label="Val Top-1 Acc (%)", color="#ff7f0e", linewidth=2)
    plt.plot(epochs, [f * 100 for f in history["val_macro_f1"]], "^:", label="Val Macro-F1 (%)", color="#9467bd", linewidth=2)
    plt.title("Classification Performance Metrics (%)", fontsize=12, weight="bold")
    plt.xlabel("Epoch", fontsize=10)
    plt.ylabel("Percentage (%)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Training curves saved to {output_path}")


def log_experiment(log_csv_path: Path, experiment_data: Dict[str, Any]):
    """Appends experiment result to experiment_log.csv."""
    log_csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_csv_path.exists()

    fieldnames = [
        "experiment_id",
        "architecture",
        "learning_rate",
        "batch_size",
        "epochs",
        "augmentation",
        "frozen_layers",
        "class_weighting",
        "validation_accuracy",
        "validation_macro_f1",
        "validation_loss",
        "training_time_sec",
        "notes"
    ]

    with open(log_csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(experiment_data)
    print(f"Experiment logged to {log_csv_path}")
