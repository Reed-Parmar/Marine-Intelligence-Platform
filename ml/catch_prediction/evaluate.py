import numpy as np
import json
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    metrics = {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2)
    }
    return metrics

def save_metrics(metrics, file_path):
    with open(file_path, 'w') as f:
        json.dump(metrics, f, indent=4)

if __name__ == "__main__":
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from config import PREDICTIONS_PATH, ARTIFACTS_DIR
    import os
    
    print("Loading predictions...")
    # Load existing predictions from artifacts
    df = pd.read_csv(PREDICTIONS_PATH)
    
    y_true = df["Actual_CATCH"]
    # Clamp negative predictions just as we did for inference
    y_pred = df["Predicted_CATCH"].clip(lower=0.0)
    
    print("Computing metrics...")
    metrics = evaluate_model(y_true, y_pred)
    print("Full Test-Set Metrics:")
    print(f"MAE:  {metrics['MAE']:.4f}")
    print(f"RMSE: {metrics['RMSE']:.4f}")
    print(f"R2:   {metrics['R2']:.4f}")
    
    print("Generating Actual vs Predicted scatter plot...")
    plt.figure(figsize=(8, 6))
    plt.scatter(y_true, y_pred, alpha=0.5, color='blue')
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
    plt.xlabel('Actual CATCH (MT)')
    plt.ylabel('Predicted CATCH (MT)')
    plt.title('Actual vs Predicted CATCH')
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "actual_vs_predicted.png"))
    plt.close()
    
    print("Generating Residual/Error distribution plot...")
    residuals = y_true - y_pred
    plt.figure(figsize=(8, 6))
    sns.histplot(residuals, bins=50, kde=True, color='purple')
    plt.xlabel('Residual Error (Actual - Predicted)')
    plt.ylabel('Frequency')
    plt.title('Residual Error Distribution')
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "residual_distribution.png"))
    plt.close()
    
    print("Plots saved successfully in ml/catch_prediction/")
