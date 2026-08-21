# Model 3: Fisheries / Catch Prediction

This directory contains the isolated machine learning pipeline for **Model 3: Fisheries Catch Prediction**, trained on the IOTC Geo-Referenced Catch and Effort dataset (2023–2024).

## Structure
- `data/`: Contains the `iotc_2023_2024.csv` dataset (note: stored in `ml/data` for this run, referenced in config)
- `config.py`: Configuration and hyperparameters.
- `preprocessing.py`: Data loading, filtering, and categorical encoding.
- `train.py`: Main script to train the XGBoost Regressor model.
- `evaluate.py`: Evaluation metrics (MAE, RMSE, R²).
- `predict.py`: Contains the `predict_catch(input_data)` function for inference.

## Artifacts Generated
Upon running `train.py`, the following artifacts are generated:
- `xgboost_model.json`: The trained XGBoost model.
- `preprocessing.joblib`: Fitted OrdinalEncoder for categorical variables.
- `metrics.json`: MAE, RMSE, and R² scores on the test set.
- `feature_importance.csv`: Ranked feature importance.
- `predictions.csv`: Actual vs predicted values for the test set.

## Run Training
```bash
python train.py
```
