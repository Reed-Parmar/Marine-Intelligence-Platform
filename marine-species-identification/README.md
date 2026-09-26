# Phase 14.2 — Marine Species Identification
## Automated Deep Learning Classification for Marine Living Resources

Centre for Marine Living Resources & Ecology (CMLRE), Ministry of Earth Sciences, Government of India.

---

## 1. Project Overview & Problem Definition
Automated taxonomic identification of marine organisms from live underwater video surveillance and scientific surveys is essential for sustainable fisheries monitoring, biodiversity conservation, and ecosystem health assessment. Underwater visual classification faces severe environmental challenges including water turbidity, non-uniform ambient illumination, motion blur, and morphological similarities between related marine taxa.

This standalone production module establishes a rigorous, transfer-learning computer vision pipeline capable of identifying marine fish species from underwater imagery with calibrated uncertainty tiers and sub-20ms inference latency.

---

## 2. Dataset Discovery & Benchmark Selection
### Benchmark: University of Edinburgh Fish4Knowledge (F4K)
- **Official Source**: University of Edinburgh School of Informatics / EU FP7 Project
- **Scientific Labeling**: Verified ground-truth annotations by certified marine biologists from the National Museum of Marine Biology and Aquarium (NMMBA).
- **Environment**: Real-world open underwater camera arrays in Kenting National Park coral reef ecosystems, Taiwan.
- **License**: Open Academic Research & Scientific Evaluation Benchmark.
- **Acquired Dataset**: 3,551 verified real underwater fish images across 10 species and 7 taxonomic families:
  1. *Acanthurus nigrofuscus* (Brown surgeonfish, Family: Acanthuridae) — 218 images (71 trajectories)
  2. *Amphiprion clarkii* (Yellowtail clownfish, Family: Pomacentridae) — 600 images (33 trajectories)
  3. *Canthigaster valentini* (Valentin's sharpnose puffer, Family: Tetraodontidae) — 147 images (28 trajectories)
  4. *Chaetodon lunulatus* (Oval butterflyfish, Family: Chaetodontidae) — 600 images (130 trajectories)
  5. *Chaetodon trifascialis* (Chevron butterflyfish, Family: Chaetodontidae) — 190 images (79 trajectories)
  6. *Hemigymnus fasciatus* (Barred thicklip wrasse, Family: Labridae) — 241 images (58 trajectories)
  7. *Lutjanus fulvus* (Blacktail snapper, Family: Lutjanidae) — 206 images (15 trajectories)
  8. *Myripristis kuntee* (Shoulderspot soldierfish, Family: Holocentridae) — 450 images (71 trajectories)
  9. *Neoniphon sammara* (Sammara squirrelfish, Family: Holocentridae) — 299 images (53 trajectories)
  10. *Plectroglyphidodon dickii* (Blackbar damselfish, Family: Pomacentridae) — 600 images (150 trajectories)

---

## 3. Data Leakage Prevention (Trajectory-Grouped Splitting)
Underwater video datasets inherently contain successive frames from the same individual specimen. Random image-level splitting results in severe train-test contamination and artificially inflated evaluation metrics.

To ensure genuine generalization:
- Every image filename encodes its underwater tracking trajectory (`fish_<tracking_id>_<fish_id>.png`).
- All frames belonging to a given `tracking_id` are allocated **strictly to a single split** (Train, Validation, or Test).
- Split Ratio: **70% Train (2,494 images, 481 trajectories) / 15% Validation (539 images, 101 trajectories) / 15% Test (481 images, 106 trajectories)**.
- Trajectory overlap between any split pair: **0 (PASSED - ZERO LEAKAGE)**.
- The **TEST split remained completely untouched** until final evaluation.

---

## 4. Hardware & Environment Audit
- **Operating System**: Windows 10 (Build 10.0.26200)
- **Python**: 3.11.9 64-bit
- **CPU**: Intel 20 Logical Processors
- **RAM**: 15.69 GB Total Physical RAM
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB VRAM)
- **Deep Learning Framework**: PyTorch 2.14.0 + Torchvision 0.29.0

---

## 5. Image Preprocessing & Augmentation
- **Input Resolution**: $224 \times 224$ pixels, 3 RGB channels.
- **Normalization**: ImageNet standards ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
- **Training Augmentations**:
  - Random cropping with aspect preservation ($256 \rightarrow 224$)
  - Biologically valid random horizontal flip ($p=0.5$)
  - Slight orientation rotations ($\pm 15^\circ$)
  - Color jittering (brightness $\pm 15\%$, contrast $\pm 15\%$, saturation $\pm 10\%$) simulating variable turbidity.
- **Validation & Test Transforms**: Deterministic resize to $224 \times 224$ followed by channel normalization.

---

## 6. Model Architecture & Training Strategy
- **Backbone**: Deep Residual Network (ResNet-18) initialized with ImageNet-1K pretrained weights.
- **Baseline Model (Phase I)**:
  - All backbone layers frozen; only final linear classifier trained.
  - Standard unweighted Cross-Entropy loss.
  - Validation Accuracy: **90.0%**, Validation Macro-F1: **0.8712**.
- **Final Model (Phase J / K / L)**:
  - Early layers (`conv1`, `bn1`, `layer1`, `layer2`) frozen.
  - Residual blocks in `layer3` and `layer4` unfrozen for domain-specific underwater feature adaptation.
  - Classification head replaced with custom Dropout ($p=0.3$) + Linear classifier ($512 \rightarrow 10$).
  - **Class-Weighted Loss (Phase K)**: Inverse-frequency class weights ($0.572$ to $2.375$) to prevent majority class dominance.
  - **Optimizer & Scheduler**: AdamW with differential learning rates ($5 \times 10^{-5}$ for backbone, $5 \times 10^{-4}$ for head), ReduceLROnPlateau.
  - Best Validation Epoch: **10** (Validation Accuracy: **98.3%**, Validation Macro-F1: **0.9777**).

---

## 7. Final Untouched Test Set Evaluation (Phase M)
Evaluated ONCE on the completely untouched test set (481 real underwater images across 106 trajectories):

| Metric | Measured Result |
| :--- | :--- |
| **Total Test Samples** | 481 |
| **Top-1 Accuracy** | **98.34%** (473 / 481 correct) |
| **Top-3 Accuracy** | **100.00%** |
| **Top-5 Accuracy** | **100.00%** |
| **Macro Precision** | **0.9699** |
| **Macro Recall** | **0.9767** |
| **Macro F1-Score** | **0.9713** |
| **Weighted F1-Score** | **0.9838** |
| **Test Loss** | **0.0614** |

### Per-Class Performance
| Species (Scientific Name) | Precision | Recall | F1-Score | Test Samples |
| :--- | :---: | :---: | :---: | :---: |
| *Acanthurus nigrofuscus* | 0.9583 | 1.0000 | 0.9787 | 23 |
| *Amphiprion clarkii* | 1.0000 | 1.0000 | 1.0000 | 72 |
| *Canthigaster valentini* | 1.0000 | 0.8710 | 0.9310 | 31 |
| *Chaetodon lunulatus* | 1.0000 | 1.0000 | 1.0000 | 90 |
| *Chaetodon trifascialis* | 0.7778 | 1.0000 | 0.8750 | 21 |
| *Hemigymnus fasciatus* | 1.0000 | 0.9697 | 0.9846 | 33 |
| *Lutjanus fulvus* | 0.9630 | 1.0000 | 0.9811 | 26 |
| *Myripristis kuntee* | 1.0000 | 1.0000 | 1.0000 | 64 |
| *Neoniphon sammara* | 1.0000 | 0.9268 | 0.9620 | 41 |
| *Plectroglyphidodon dickii* | 1.0000 | 1.0000 | 1.0000 | 80 |

---

## 8. Error Analysis & Confidence Calibration (Phase N & O)
- **Total Test Errors**: 8 / 481 images (1.7% error rate).
- **Confusion Analysis**:
  - *Canthigaster valentini* $\rightarrow$ *Chaetodon trifascialis* (4 instances): Occurred in high-turbidity frames where fine body shape outline was obscured by sediment backscatter.
  - *Neoniphon sammara* $\rightarrow$ *Chaetodon trifascialis* (2 instances): Both exhibit horizontal longitudinal striping that resembles chevron patterns at extreme camera angles.
- **Empirical Calibration Tiers**:
  - **HIGH CONFIDENCE ($\ge 0.70$)**: 472 samples (98.1% of test set) $\rightarrow$ **99.79% empirical accuracy** (mean confidence: 0.9933).
  - **MODERATE CONFIDENCE ($0.40 - 0.70$)**: 8 samples (1.7% of test set) $\rightarrow$ **25.00% accuracy**.
  - **LOW CONFIDENCE ($< 0.40$)**: 1 sample (0.2% of test set) $\rightarrow$ **0.00% accuracy**.
  - Confirms strong calibration: predictions tagged "HIGH" are almost certain ($\sim 99.8\%$), while uncertain predictions are appropriately flagged.

---

## 9. Inference Benchmarking (Phase U)
- **Model File Size**: 42.73 MB
- **Total Parameters**: 11,181,642
- **Device**: CPU (OpenMP multi-threaded)
- **Mean Latency**: **13.85 ms** per image
- **Median (P50) Latency**: **13.22 ms** per image
- **P95 Latency**: **15.83 ms** per image
- **P99 Latency**: **19.63 ms** per image
- **Throughput**: **72.2 images/second (FPS)**

---

## 10. Automated Testing (Phase T)
- Pytest Suite: `tests/test_inference.py`
- Tests Executed: 6 passed in 3.56s (Health check, Direct Python inference, API predict success, Invalid format rejection, Empty file rejection, Corrupt binary handling).

---

## 11. Standalone Integration Package (Phase W)
Located at: `marine-species-identification/integration_package/`
- `model/species_model.pth`: Trained model weights (42.73 MB)
- `model/class_mapping.json`: Integer to species mapping
- `model/model_metadata.json`: Architectural specifications
- `inference/predict.py`: Standalone inference class
- `inference/preprocessing.py`: Image transforms
- `api/species_routes.py`: FastAPI router ready for backend mount
- `requirements.txt`: Minimal deployment dependencies
- `INTEGRATION_GUIDE.md`: Step-by-step instructions for copying into the main repository.
