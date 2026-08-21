import time
import joblib
import xgboost as xgb
import pandas as pd
from config import (
    DATA_FILE,
    MODEL_PATH,
    PREPROCESSING_PATH,
    METRICS_PATH,
    FEATURE_IMPORTANCE_PATH,
    PREDICTIONS_PATH,
    XGB_PARAMS,
    FEATURES,
    TARGET
)
from preprocessing import load_and_preprocess_data, split_data_chronologically, build_preprocessor, apply_preprocessing
from evaluate import evaluate_model, save_metrics

def main():
    start_time = time.time()
    
    # 1. Load and prepare data
    print("Loading data...")
    df = load_and_preprocess_data(DATA_FILE)
    dataset_size = len(df)
    print(f"Dataset size after filtering: {dataset_size}")
    
    # 2. Chronological split
    train_df, test_df = split_data_chronologically(df, test_size=0.2)
    
    # 3. Preprocessing (fit on train, transform both)
    encoder, cat_cols = build_preprocessor(train_df)
    train_processed = apply_preprocessing(train_df, encoder, cat_cols)
    test_processed = apply_preprocessing(test_df, encoder, cat_cols)
    
    X_train = train_processed[FEATURES]
    y_train = train_processed[TARGET]
    X_test = test_processed[FEATURES]
    y_test = test_processed[TARGET]
    
    # 4. Train Model
    print("Training XGBoost Regressor...")
    model = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(X_train, y_train)
    
    training_time = time.time() - start_time
    print(f"Training completed in {training_time:.2f} seconds.")
    
    # 5. Evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    metrics = evaluate_model(y_test, y_pred)
    
    # Include dataset size and training time in metrics for reporting
    metrics["dataset_size"] = dataset_size
    metrics["training_time_seconds"] = training_time
    
    print(f"Metrics: {metrics}")
    
    # 6. Save Artifacts
    print("Saving artifacts...")
    # Save model
    model.save_model(MODEL_PATH)
    # Save preprocessor
    joblib.dump({"encoder": encoder, "cat_cols": cat_cols}, PREPROCESSING_PATH)
    # Save metrics
    save_metrics(metrics, METRICS_PATH)
    # Save feature importance
    importance = model.feature_importances_
    feat_imp_df = pd.DataFrame({"Feature": FEATURES, "Importance": importance})
    feat_imp_df = feat_imp_df.sort_values(by="Importance", ascending=False)
    feat_imp_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    # Save predictions
    predictions_df = pd.DataFrame({
        "Actual_CATCH": y_test,
        "Predicted_CATCH": y_pred
    })
    predictions_df.to_csv(PREDICTIONS_PATH, index=False)
    
    print("All artifacts saved successfully.")

if __name__ == "__main__":
    main()
