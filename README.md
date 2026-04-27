# WaveletAI — Op-Amp Signal Intelligence Platform

A desktop GUI application for **Op-Amp signal analysis** using wavelet decomposition.  
Supports both **Manual** (known gain/shift) and **AI/ML** (XGBoost, Linear, Random Forest, GPR) prediction modes.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Application Tabs](#application-tabs)
  - [1. Preprocessing](#1-preprocessing)
  - [2. Manual Analysis](#2-manual-analysis)
  - [3. AI / ML Mode](#3-ai--ml-mode)
- [File Descriptions](#file-descriptions)
- [How the ML Works](#how-the-ml-works)
- [Output Files](#output-files)
- [Dependencies](#dependencies)

---

## Overview

WaveletAI takes raw Op-Amp signal CSV files, decomposes them using **Daubechies-4 (db4) wavelet** at Level 11/12, applies gain and shift corrections at each wavelet level, and reconstructs the predicted output signal.

The app measures prediction quality using:
- **SNR** — Signal-to-Noise Ratio (dB)
- **MSE** — Mean Squared Error
- **RMSE** — Root Mean Squared Error
- **MAE** — Mean Absolute Error

---

## Project Structure

```
mlmodel2/
│
├── uii.py                  # Main entry point — launches the app
├── theme.py                # Design tokens, colors, fonts, helper UI functions
├── widgets.py              # Reusable custom widget classes
├── preprocessing.py        # Tab 1 — Preprocessing logic (mixin)
├── manual_analysis.py      # Tab 2 — Manual analysis logic (mixin)
├── ml_analysis.py          # Tab 3 — ML prediction + result display (mixin)
│
├── tool/
│   ├── src/
│   │   ├── core_ml.py      # Wavelet decomposition & reconstruction functions
│   │   └── trainer.py      # Feature extraction & ML model training functions
│   ├── models/             # Trained .pkl model files (generated after training)
│   └── output/             # Runtime output — plots (.png) and Excel (.xlsx)
│       └── intermediate/   # Wavelet coefficient Excel files per run
│
├── requirements.txt        # All Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## Installation

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd mlmodel2
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

**3. Install all dependencies**
```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python uii.py
```

The app opens a **1340×920** desktop window with a sidebar and 3 tabs.

---

## Application Tabs

### 1. Preprocessing

**Purpose:** Convert a raw hardware CSV file into a training-ready Excel file.

**Steps:**
1. Click `Browse` → select your raw hardware `.csv` file
2. Click `⚡ GENERATE PROCESSED DATA`
3. The app computes and adds these columns:

| Column | Description |
|---|---|
| `gain` | dB → linear conversion: `10^(dB/20)` |
| `del_t` | Time delay from phase: `(Phase/360) × (1/freq)` |
| `delay` | `del_t` in nanoseconds |
| `shift_courage` | Rounded delay (integer ns) |
| `Phase_2` | Half phase value |
| `avg_shift` | Rounded half-phase delay |
| `avg_gain` | Block-averaged gain (powers of 2 block sizes) |

4. Output saved as `<input_filename>_processed.xlsx` next to the input file
5. Last 20 rows preview shown in the app

---

### 2. Manual Analysis

**Purpose:** Apply known gains and shifts (from a processed Excel) to decompose and reconstruct the signal manually.

**Steps:**
1. Browse → select **Test Signal CSV** (must have `vinp` and `vinn` columns)
2. Browse → select **Processed Excel** (output from Preprocessing tab)
3. Enter the **Sheet Name** (default: `Sheet1`)
4. Click `▶ EXECUTE MANUAL ANALYSIS`

**What happens internally:**
```
Input Signal (vinp)
       ↓
Wavelet Decomposition (db4, Level 12)  →  13 coefficient arrays
       ↓
Multiply each level by avg_gain[i]
       ↓
Reconstruct with avg_shift[i] applied as circular shift per level
       ↓
Predicted Output Signal
```

**Output:**
- Excel saved to `tool/output/intermediate/wavelet_analysis_manual_<timestamp>.xlsx`
  - Sheet `decomposition` — raw wavelet coefficients
  - Sheet `stage 1` — coefficients × gain, shift values, prediction per sample
- Result card shown in app with SNR, MSE, RMSE, MAE and plot

---

### 3. AI / ML Mode

**Purpose:** Use pre-trained ML models to automatically predict gain and shift values for each wavelet level, then reconstruct the signal.

**Steps:**
1. Browse → select **Test Signal CSV**
2. Click `⚡ RUN ALL AI MODELS`
3. All 4 models run automatically: **XGBoost**, **Linear**, **Random Forest**, **GPR**

**What happens internally:**
```
Input Signal (vinp)
       ↓
extract_wavelet_features_l11()  →  13 features (mean abs energy per level)
       ↓
gain_<model>.pkl  →  predict 13 gain values
shift_<model>.pkl →  predict 13 shift values
       ↓
Wavelet Decomposition (db4, Level 11)
       ↓
Apply predicted gains + shifts per level
       ↓
Reconstruct → Predicted Output Signal
```

**Output per model:**
- Excel saved to `tool/output/intermediate/wavelet_analysis_ML_<model>_<timestamp>.xlsx`
- Plot saved to `tool/output/plot_ML_<model>_<timestamp>.png`
- Result card shown in app with metrics and plot image

> **Note:** Models must exist in `tool/models/` as `gain_<model>.pkl` and `shift_<model>.pkl`.  
> If a model file is missing, that model is silently skipped.

---

## File Descriptions

### `uii.py`
Main application entry point. Defines `WaveletApp` which inherits from all 3 mixins and `ctk.CTk`. Builds the sidebar, navigation, and main scrollable content area.

### `theme.py`
Centralised design system:
- `C` — color palette dictionary (bg, surface, accent, danger, etc.)
- `FONT_*` — font tuples for titles, labels, buttons, metrics
- Helper functions: `make_card`, `accent_label`, `dim_label`, `primary_btn`, `ghost_btn`, `separator`, `_darken`, `_lighten`

### `widgets.py`
Reusable custom UI components:

| Class | Description |
|---|---|
| `PulsingDot` | Animated green dot that pulses when processing is active |
| `TagBadge` | Colored pill label for model/feature tags |
| `MetricTile` | KPI card showing a label + large metric value |
| `FilePickRow` | File browser row with label, filename display, and Browse button |
| `AnimatedProgressBar` | Indeterminate progress bar for background tasks |
| `NavButton` | Sidebar navigation button with step number, icon, and label |

### `preprocessing.py`
`PreprocessingMixin` — all methods for Tab 1:
- `setup_pre()` — builds the UI
- `execute_preprocessing()` — runs in background thread, computes all columns
- `_pre_done()` — updates UI with preview table after processing

### `manual_analysis.py`
`ManualAnalysisMixin` — all methods for Tab 2:
- `setup_manual()` — builds the UI
- `execute_manual(sheet)` — runs wavelet decomposition + gain/shift application
- `_manual_done()` — triggers result display

### `ml_analysis.py`
`MLAnalysisMixin` — all methods for Tab 3 + shared result display:
- `setup_ml()` — builds the UI
- `execute_ml()` — loads models, extracts features, runs all 4 models
- `display_result()` — saves plot, renders result card with metrics and image

### `tool/src/core_ml.py`
Core signal processing functions:

| Function | Description |
|---|---|
| `get_wavelet_levels(signal, wavelet, level)` | Decomposes signal using `pywt.wavedec`, returns list of coefficient arrays |
| `reconstruct_optimized(coeffs_list, shifts, wavelet)` | Reconstructs signal level-by-level, applying circular shift per level before summing |

### `tool/src/trainer.py`
ML training and feature extraction:

| Function | Description |
|---|---|
| `extract_features(signal, vdda)` | Returns 3 basic features: RMS, ZCR, normalized peak |
| `extract_wavelet_features_l11(signal, wavelet, level)` | Returns 13 features — mean absolute energy of each wavelet level |
| `train_engine(X, target_gains, target_shifts, model_type)` | Trains gain and shift models, saves as `.pkl` to `tool/models/` |

**Supported model types:** `xgboost`, `linear`, `rf`, `gpr`

---

## How the ML Works

```
Training Phase (offline):
  Raw CSV data → extract_wavelet_features_l11() → 13 features per sample
  Known gains  → MultiOutputRegressor(model).fit() → gain_<model>.pkl
  Known shifts → MultiOutputRegressor(model).fit() → shift_<model>.pkl

Inference Phase (in app):
  New signal → extract_wavelet_features_l11() → 13 features
  gain_<model>.pkl.predict()  → 13 predicted gains
  shift_<model>.pkl.predict() → 13 predicted shifts
  get_wavelet_levels()        → decompose signal
  reconstruct_optimized()     → apply gains + shifts → output signal
```

---

## Output Files

| File | Location | Generated By |
|---|---|---|
| `<name>_processed.xlsx` | Same folder as input CSV | Preprocessing tab |
| `wavelet_analysis_manual_<ts>.xlsx` | `tool/output/intermediate/` | Manual Analysis tab |
| `wavelet_analysis_ML_<model>_<ts>.xlsx` | `tool/output/intermediate/` | ML tab |
| `plot_Manual_<sheet>_<ts>.png` | `tool/output/` | Manual Analysis tab |
| `plot_ML_<model>_<model>_<ts>.png` | `tool/output/` | ML tab |
| `gain_<model>.pkl` | `tool/models/` | `train_engine()` in trainer.py |
| `shift_<model>.pkl` | `tool/models/` | `train_engine()` in trainer.py |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `customtkinter` | ≥ 5.2.0 | Modern desktop GUI framework |
| `Pillow` | ≥ 10.0.0 | Loading plot images into the UI |
| `numpy` | ≥ 1.24.0 | Numerical operations |
| `pandas` | ≥ 2.0.0 | CSV / Excel read & write |
| `openpyxl` | ≥ 3.1.0 | Excel file engine for pandas |
| `scikit-learn` | ≥ 1.3.0 | Linear, RF, GPR models |
| `xgboost` | ≥ 2.0.0 | XGBoost model |
| `joblib` | ≥ 1.3.0 | Model serialization (.pkl) |
| `PyWavelets` | ≥ 1.4.0 | Wavelet decomposition & reconstruction |
| `matplotlib` | ≥ 3.7.0 | Signal plots |
| `scipy` | ≥ 1.11.0 | Statistical features (kurtosis, skew) |

Install all with:
```bash
pip install -r requirements.txt
```
