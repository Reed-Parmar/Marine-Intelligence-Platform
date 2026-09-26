"""
Data processing and quality audit module for Fisheries Catch Prediction.
Official IOTC (Indian Ocean Tuna Commission) Surface Fisheries Dataset.
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def decode_cwp_grid(grid_series: pd.Series):
    """
    Decode 7-digit CWP (Coordinating Working Party on Fishery Statistics) grid codes.
    Format: <res_code><quadrant><lat_2digits><lon_3digits>
    """
    def decode_single(val):
        try:
            s = str(int(val)).zfill(7)
            if len(s) != 7:
                return np.nan, np.nan, np.nan
            res_code = int(s[0])
            quad = int(s[1])
            lat_val = int(s[2:4])
            lon_val = int(s[4:7])
            
            res_map = {1: 10.0, 2: 20.0, 3: 30.0, 5: 1.0, 6: 5.0}
            res = res_map.get(res_code, np.nan)
            if np.isnan(res):
                return np.nan, np.nan, np.nan
                
            lat_sign = 1.0 if quad in [1, 4] else -1.0
            lon_sign = 1.0 if quad in [1, 2] else -1.0
            
            lat_center = lat_sign * (lat_val + res / 2.0)
            lon_center = lon_sign * (lon_val + res / 2.0)
            return lat_center, lon_center, res
        except Exception:
            return np.nan, np.nan, np.nan

    results = [decode_single(v) for v in grid_series]
    lats = [r[0] for r in results]
    lons = [r[1] for r in results]
    ress = [r[2] for r in results]
    return pd.Series(lats, index=grid_series.index), pd.Series(lons, index=grid_series.index), pd.Series(ress, index=grid_series.index)


def process_and_audit_dataset(base_dir: str = "fisheries_catch_prediction"):
    raw_path = os.path.join(base_dir, "data", "raw", "IOTC-2024-WPB22-DATA05-CESurface.csv")
    processed_dir = os.path.join(base_dir, "data", "processed")
    splits_dir = os.path.join(base_dir, "data", "splits")
    reports_dir = os.path.join(base_dir, "reports")
    figures_dir = os.path.join(reports_dir, "figures")
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(splits_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    print(f"Loading raw dataset from {raw_path}...")
    df_raw = pd.read_csv(raw_path, low_memory=False)
    initial_rows, initial_cols = df_raw.shape
    print(f"Raw shape: {initial_rows} rows x {initial_cols} columns")

    audit_log = {
        "initial_rows": initial_rows,
        "initial_cols": initial_cols,
        "raw_duplicates": int(df_raw.duplicated().sum()),
        "cleaning_rules": []
    }

    # Identify species catch columns
    catch_cols = [c for c in df_raw.columns if "-" in c]
    print(f"Found {len(catch_cols)} species catch columns.")

    # Target calculation
    # Total catch is sum of all landed species in MT for the stratum
    total_catch = df_raw[catch_cols].fillna(0.0).sum(axis=1)
    df_raw["TotalCatchMT"] = total_catch

    # Audit Rule 1: Whitespace cleanup
    df_raw["Fleet"] = df_raw["Fleet"].astype(str).str.strip()
    df_raw["Gear"] = df_raw["Gear"].astype(str).str.strip()
    df_raw["EffortUnits"] = df_raw["EffortUnits"].astype(str).str.strip()
    audit_log["cleaning_rules"].append({
        "rule": "Whitespace Normalization",
        "detected": "Trailing spaces in categorical strings (Fleet, Gear, EffortUnits)",
        "action": "Applied str.strip() across all categorical columns",
        "affected_records": initial_rows,
        "reason": "Ensure consistent categorical encoding without trailing space fragmentation"
    })

    # Audit Rule 2: Grid decoding
    lat, lon, res = decode_cwp_grid(df_raw["Grid"])
    df_raw["Latitude"] = lat
    df_raw["Longitude"] = lon
    df_raw["SpatialResolution"] = res
    audit_log["cleaning_rules"].append({
        "rule": "CWP Spatial Grid Decoding",
        "detected": "7-digit CWP grid codes",
        "action": "Decoded into standard decimal Latitude, Longitude, and SpatialResolution (degrees)",
        "affected_records": initial_rows,
        "reason": "Enable spatial feature modeling and GIS compatibility across the Indian Ocean and Arabian Sea"
    })

    # Audit Rule 3: Zero or negative Effort filtering
    zero_or_neg_effort = (df_raw["Effort"] <= 0)
    num_zero_effort = int(zero_or_neg_effort.sum())
    print(f"Detected {num_zero_effort} records with Effort <= 0.")
    df_clean = df_raw[~zero_or_neg_effort].copy()
    audit_log["cleaning_rules"].append({
        "rule": "Non-Positive Effort Removal",
        "detected": f"{num_zero_effort} records with Effort <= 0",
        "action": f"Removed {num_zero_effort} records ({num_zero_effort/initial_rows*100:.3f}% of dataset)",
        "affected_records": num_zero_effort,
        "reason": "Effort of 0 indicates missing or corrupt operational effort; catch cannot be physically generated with zero effort."
    })

    # Audit Rule 4: Data Leakage Removal
    # CatchUnits is directly collinear with zero catch (NaN if catch == 0, 'MT' if catch > 0)
    # Species catch columns sum to the target TotalCatchMT
    # Post-hoc reporting metadata: QualityCode, Source, iGrid
    leakage_cols = ["CatchUnits"] + catch_cols + ["QualityCode", "Source", "iGrid", "Grid", "MonthEnd"]
    df_clean = df_clean.drop(columns=[c for c in leakage_cols if c in df_clean.columns])
    df_clean = df_clean.rename(columns={"MonthStart": "Month"})
    audit_log["cleaning_rules"].append({
        "rule": "Target Leakage & Metadata Removal",
        "detected": f"Target leakage columns ({len(catch_cols)} species breakdowns, CatchUnits) and post-hoc reporting metadata",
        "action": f"Dropped {len(leakage_cols)} columns",
        "affected_records": len(df_clean),
        "reason": "Prevent target leakage: CatchUnits reveals zero catch; individual species columns sum to the target. QualityCode/Source are post-hoc admin flags."
    })

    # Add temporal & seasonal features
    df_clean["Month_Sin"] = np.sin(2 * np.pi * df_clean["Month"] / 12.0)
    df_clean["Month_Cos"] = np.cos(2 * np.pi * df_clean["Month"] / 12.0)
    df_clean["Quarter"] = (df_clean["Month"] - 1) // 3 + 1
    # Indian Ocean Monsoon seasons:
    # 1: NE Monsoon (Dec-Feb), 2: Spring Inter-monsoon (Mar-May), 3: SW Monsoon (Jun-Sep), 4: Autumn Inter-monsoon (Oct-Nov)
    def assign_monsoon(m):
        if m in [12, 1, 2]:
            return "NE_Monsoon"
        elif m in [3, 4, 5]:
            return "Intermonsoon_Spring"
        elif m in [6, 7, 8, 9]:
            return "SW_Monsoon"
        else:
            return "Intermonsoon_Autumn"
    df_clean["MonsoonSeason"] = df_clean["Month"].apply(assign_monsoon)
    df_clean["Log_Effort"] = np.log1p(df_clean["Effort"])

    # Target statistics
    y = df_clean["TotalCatchMT"]
    target_stats = {
        "count": int(len(y)),
        "mean": float(y.mean()),
        "std": float(y.std()),
        "min": float(y.min()),
        "q25": float(y.quantile(0.25)),
        "median": float(y.median()),
        "q75": float(y.quantile(0.75)),
        "q90": float(y.quantile(0.90)),
        "q95": float(y.quantile(0.95)),
        "q99": float(y.quantile(0.99)),
        "max": float(y.max()),
        "skewness": float(y.skew()),
        "zero_count": int((y == 0).sum()),
        "zero_percentage": float((y == 0).mean() * 100.0)
    }
    audit_log["target_stats"] = target_stats

    # Save cleaned full dataset
    clean_csv_path = os.path.join(processed_dir, "fisheries_catch_clean.csv")
    print(f"Saving cleaned dataset to {clean_csv_path}...")
    df_clean.to_csv(clean_csv_path, index=False)

    # Perform Chronological Train / Validation / Test Split
    # Train: 1970 - 2014 (45 years, historical period)
    # Validation: 2015 - 2018 (4 years, intermediate period)
    # Test: 2019 - 2022 (4 years, latest strictly held-out period)
    train_mask = (df_clean["Year"] <= 2014)
    val_mask = (df_clean["Year"] >= 2015) & (df_clean["Year"] <= 2018)
    test_mask = (df_clean["Year"] >= 2019)

    df_train = df_clean[train_mask].copy()
    df_val = df_clean[val_mask].copy()
    df_test = df_clean[test_mask].copy()

    split_info = {
        "train": {
            "period": "1970-2014",
            "rows": int(len(df_train)),
            "pct": float(len(df_train) / len(df_clean) * 100.0),
            "zero_pct": float((df_train["TotalCatchMT"] == 0).mean() * 100.0),
            "mean_catch": float(df_train["TotalCatchMT"].mean())
        },
        "validation": {
            "period": "2015-2018",
            "rows": int(len(df_val)),
            "pct": float(len(df_val) / len(df_clean) * 100.0),
            "zero_pct": float((df_val["TotalCatchMT"] == 0).mean() * 100.0),
            "mean_catch": float(df_val["TotalCatchMT"].mean())
        },
        "test": {
            "period": "2019-2022",
            "rows": int(len(df_test)),
            "pct": float(len(df_test) / len(df_clean) * 100.0),
            "zero_pct": float((df_test["TotalCatchMT"] == 0).mean() * 100.0),
            "mean_catch": float(df_test["TotalCatchMT"].mean())
        }
    }
    audit_log["split_info"] = split_info

    # Save splits
    train_path = os.path.join(splits_dir, "train.csv")
    val_path = os.path.join(splits_dir, "val.csv")
    test_path = os.path.join(splits_dir, "test.csv")

    df_train.to_csv(train_path, index=False)
    df_val.to_csv(val_path, index=False)
    df_test.to_csv(test_path, index=False)

    print(f"Saved splits: Train={len(df_train)}, Val={len(df_val)}, Test={len(df_test)}")

    # Generate Figures
    sns.set_theme(style="whitegrid")
    
    # 1. Target distribution (raw and log1p)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.histplot(df_clean["TotalCatchMT"], bins=60, kde=True, ax=axes[0], color="teal")
    axes[0].set_title("Target Distribution: Raw TotalCatchMT", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Catch (Metric Tons)")
    axes[0].set_ylabel("Count")

    sns.histplot(np.log1p(df_clean["TotalCatchMT"]), bins=60, kde=True, ax=axes[1], color="darkblue")
    axes[1].set_title("Target Distribution: log1p(TotalCatchMT)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("log1p(Catch MT)")
    axes[1].set_ylabel("Count")
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "target_distribution.png"), dpi=150)
    plt.close()

    # 2. Chronological catch and effort trend by year
    yearly = df_clean.groupby("Year").agg({
        "TotalCatchMT": ["sum", "mean"],
        "Effort": "sum"
    })
    yearly.columns = ["Total_Catch_Sum", "Catch_Mean", "Effort_Sum"]
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    color = "tab:blue"
    ax1.set_xlabel("Year", fontsize=11)
    ax1.set_ylabel("Annual Total Catch (Metric Tons)", color=color, fontsize=11)
    ax1.plot(yearly.index, yearly["Total_Catch_Sum"], color=color, lw=2, label="Annual Catch (MT)")
    ax1.tick_params(axis="y", labelcolor=color)

    ax2 = ax1.twinx()
    color = "tab:orange"
    ax2.set_ylabel("Annual Total Effort", color=color, fontsize=11)
    ax2.plot(yearly.index, yearly["Effort_Sum"], color=color, lw=2, linestyle="--", label="Annual Effort")
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title("IOTC Surface Fishery: Catch and Effort Historical Trajectory (1970-2022)", fontsize=13, fontweight="bold")
    # Annotate splits
    ax1.axvline(2014.5, color="red", linestyle=":", lw=2, label="Train/Val Cutoff (2014)")
    ax1.axvline(2018.5, color="purple", linestyle=":", lw=2, label="Val/Test Cutoff (2018)")
    fig.tight_layout()
    fig.savefig(os.path.join(figures_dir, "historical_trajectory.png"), dpi=150)
    plt.close()

    # 3. Monthly seasonality by Gear
    fig, ax = plt.subplots(figsize=(10, 5))
    top_gears = df_clean["Gear"].value_counts().head(3).index
    df_top_gears = df_clean[df_clean["Gear"].isin(top_gears)]
    sns.lineplot(data=df_top_gears, x="Month", y="TotalCatchMT", hue="Gear", marker="o", errorbar=None, ax=ax)
    ax.set_title("Mean Catch (MT) Seasonality Across Major Gears", fontsize=12, fontweight="bold")
    ax.set_xlabel("Month of Year")
    ax.set_ylabel("Mean Catch (Metric Tons)")
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "seasonality_by_gear.png"), dpi=150)
    plt.close()

    # Save audit log
    audit_json_path = os.path.join(processed_dir, "audit_summary.json")
    with open(audit_json_path, "w") as f:
        json.dump(audit_log, f, indent=2)
    print(f"Audit summary written to {audit_json_path}.")

    return audit_log


if __name__ == "__main__":
    process_and_audit_dataset()
