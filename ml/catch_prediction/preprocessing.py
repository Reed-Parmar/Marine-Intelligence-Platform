import pandas as pd
import joblib
from sklearn.preprocessing import OrdinalEncoder
from config import FEATURES, TARGET

def load_and_preprocess_data(file_path):
    # Load dataset
    df = pd.read_csv(file_path)
    
    # Filter as per requirements (if columns exist)
    if "CATCH_UNIT" in df.columns:
        df = df[df["CATCH_UNIT"] == "MT"]
    if "IS_SPECIES_AGGREGATE" in df.columns:
        df = df[df["IS_SPECIES_AGGREGATE"] == False]
        
    # Drop rows with missing values in required features or target
    df = df.dropna(subset=FEATURES + [TARGET, "YEAR"])
    
    # Sort chronologically for time-based split
    if "MONTH" in df.columns and "YEAR" in df.columns:
        df = df.sort_values(by=["YEAR", "MONTH"]).reset_index(drop=True)
        
    return df

def split_data_chronologically(df, test_size=0.2):
    # Chronological train/test split (DO NOT use random split)
    split_idx = int(len(df) * (1 - test_size))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    return train_df, test_df

def build_preprocessor(train_df):
    cat_cols = ["SPECIES", "FLEET", "FISHERY", "GEAR", "FISHING_GROUND_CODE"]
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    # Fit encoder on train data only
    encoder.fit(train_df[cat_cols])
    return encoder, cat_cols

def apply_preprocessing(df, encoder, cat_cols):
    df_processed = df.copy()
    df_processed[cat_cols] = encoder.transform(df_processed[cat_cols])
    return df_processed
