import joblib
import xgboost as xgb
import pandas as pd
from config import MODEL_PATH, PREPROCESSING_PATH, FEATURES
from preprocessing import apply_preprocessing

# Global references for lazy loading
_model = None
_preprocessor = None

def load_resources():
    global _model, _preprocessor
    if _model is None:
        _model = xgb.XGBRegressor()
        _model.load_model(MODEL_PATH)
    if _preprocessor is None:
        _preprocessor = joblib.load(PREPROCESSING_PATH)

def predict_catch(input_data: pd.DataFrame) -> pd.Series:
    """
    Predicts catch using the trained Model 3 XGBoost Regressor.
    
    Args:
        input_data (pd.DataFrame): DataFrame containing at least the FEATURES columns.
        
    Returns:
        pd.Series: Predicted catch values.
    """
    load_resources()
    
    # Extract only required features to ensure column order and presence
    df_features = input_data[FEATURES].copy()
    
    encoder = _preprocessor["encoder"]
    cat_cols = _preprocessor["cat_cols"]
    
    # Apply preprocessing
    df_processed = apply_preprocessing(df_features, encoder, cat_cols)
    
    # Predict
    predictions = _model.predict(df_processed)
    
    # Clamp negative predictions to 0
    predictions = predictions.clip(min=0.0)
    
    return pd.Series(predictions, name="Predicted_CATCH")

if __name__ == "__main__":
    from config import DATA_FILE, TARGET
    from preprocessing import load_and_preprocess_data, split_data_chronologically
    
    # 1. Load the dataset and get the test split to ensure we are testing on unseen data
    df = load_and_preprocess_data(DATA_FILE)
    _, test_df = split_data_chronologically(df, test_size=0.2)
    
    # 2. Take 5 records from the test portion
    sample_data = test_df.head(5).copy()
    
    # 3. Predict
    predictions = predict_catch(sample_data)
    
    # 4. Print Actual vs Predicted
    print("Actual CATCH | Predicted CATCH")
    print("-" * 35)
    for i in range(len(sample_data)):
        actual = sample_data.iloc[i][TARGET]
        pred = predictions.iloc[i]
        print(f"{actual:12.6f} | {pred:15.6f}")
