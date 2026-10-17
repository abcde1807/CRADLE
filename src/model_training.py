"""
CRADLE Machine Learning Model Training Module
Trains predictive models for Healthcare Gap Score and Priority Classification
using Leave-One-City-Out (LOCO) Spatial Cross-Validation across all supported cities.
Saves model binaries and preprocessor pipelines to the models/ directory.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    mean_squared_error, mean_absolute_error, r2_score, classification_report
)
import joblib

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

FEATURE_COLUMNS = [
    "Population",
    "Population_Density",
    "Elderly",
    "Children",
    "Households",
    "Vuln_Ratio",
    "Nearest_Facility_Distance",
    "Nearest_Hospital_Distance",
    "Healthcare_Facilities",
    "Beds_per_1000",
]

TARGET_CLASSIFICATION = "Priority_Category"
TARGET_REGRESSION = "Gap_Score"

PRIORITY_CLASSES = ["Low", "Moderate", "High", "Critical"]


def load_multi_city_training_data() -> pd.DataFrame:
    """
    Loads wards dataset across all cities, computes derived features,
    and returns a clean pandas DataFrame ready for feature extraction.
    """
    all_wards_path = config.PROCESSED_DATA_DIR / "all_cities_wards.geojson"
    if not all_wards_path.exists():
        raise FileNotFoundError(f"Missing combined processed wards: {all_wards_path}. Run preprocess_data.py first.")

    gdf = gpd.read_file(all_wards_path)

    # Calculate derived demographic and spatial ratios
    pop_safe = gdf["Population"].replace(0, 1)
    if "Elderly" in gdf.columns and "Children" in gdf.columns:
        gdf["Vuln_Ratio"] = ((gdf["Elderly"] + gdf["Children"]) / pop_safe).clip(0.0, 1.0)
    else:
        gdf["Vuln_Ratio"] = 0.25

    # Ensure all required features are present and numeric
    for col in FEATURE_COLUMNS:
        if col not in gdf.columns:
            gdf[col] = 0.0
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0.0)

    # Ensure City_Key exists
    if "City_Key" not in gdf.columns:
        gdf["City_Key"] = "chennai"

    return gdf


class SpatialLOCOCrossValidator:
    """
    Evaluates models using Leave-One-City-Out Spatial Cross Validation
    to prevent spatial autocorrelation leakage between geographic clusters.
    """

    def __init__(self, features: pd.DataFrame, groups: pd.Series):
        self.features = features
        self.groups = groups
        self.logo = LeaveOneGroupOut()

    def evaluate_classifier(self, clf, y: pd.Series) -> Dict[str, Any]:
        fold_results = []
        all_y_true = []
        all_y_pred = []

        for fold_idx, (train_idx, test_idx) in enumerate(self.logo.split(self.features, y, groups=self.groups)):
            test_city = self.groups.iloc[test_idx].iloc[0]
            X_train, X_test = self.features.iloc[train_idx], self.features.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Fit model on training cities
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            clf.fit(X_train_scaled, y_train)
            y_pred = clf.predict(X_test_scaled)

            acc = accuracy_score(y_test, y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)

            fold_results.append({
                "fold": fold_idx + 1,
                "test_city": test_city,
                "train_samples": len(train_idx),
                "test_samples": len(test_idx),
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
            })
            all_y_true.extend(y_test.tolist())
            all_y_pred.extend(y_pred.tolist())

        mean_acc = np.mean([r["accuracy"] for r in fold_results])
        mean_f1 = np.mean([r["f1_score"] for r in fold_results])

        return {
            "folds": fold_results,
            "mean_accuracy": round(float(mean_acc), 4),
            "mean_f1": round(float(mean_f1), 4),
            "overall_report": classification_report(all_y_true, all_y_pred, output_dict=True, zero_division=0),
            "all_y_true": all_y_true,
            "all_y_pred": all_y_pred,
        }

    def evaluate_regressor(self, reg, y: pd.Series) -> Dict[str, Any]:
        fold_results = []
        all_y_true = []
        all_y_pred = []

        for fold_idx, (train_idx, test_idx) in enumerate(self.logo.split(self.features, y, groups=self.groups)):
            test_city = self.groups.iloc[test_idx].iloc[0]
            X_train, X_test = self.features.iloc[train_idx], self.features.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            reg.fit(X_train_scaled, y_train)
            y_pred = reg.predict(X_test_scaled)

            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            mae = float(mean_absolute_error(y_test, y_pred))
            r2 = float(r2_score(y_test, y_pred))

            fold_results.append({
                "fold": fold_idx + 1,
                "test_city": test_city,
                "train_samples": len(train_idx),
                "test_samples": len(test_idx),
                "rmse": round(rmse, 3),
                "mae": round(mae, 3),
                "r2": round(r2, 3),
            })
            all_y_true.extend(y_test.tolist())
            all_y_pred.extend(y_pred.tolist())

        mean_rmse = np.mean([r["rmse"] for r in fold_results])
        mean_r2 = np.mean([r["r2"] for r in fold_results])

        return {
            "folds": fold_results,
            "mean_rmse": round(float(mean_rmse), 3),
            "mean_r2": round(float(mean_r2), 3),
        }


def train_and_export_models():
    """
    Full training pipeline:
    1. Loads dataset and extracts features
    2. Runs Leave-One-City-Out spatial cross-validation
    3. Trains final production models on full multi-city dataset
    4. Exports model binaries (.joblib) and performance metrics (.json)
    """
    print("=" * 65)
    print("CRADLE: MACHINE LEARNING MODEL TRAINING PIPELINE")
    print("=" * 65)

    df = load_multi_city_training_data()
    X = df[FEATURE_COLUMNS]
    y_clf = df[TARGET_CLASSIFICATION]
    y_reg = df[TARGET_REGRESSION]
    groups = df["City_Key"]

    print(f"[DATA] Ingested {len(df)} total wards across {groups.nunique()} cities.")
    print(f"       Features ({len(FEATURE_COLUMNS)}): {', '.join(FEATURE_COLUMNS)}")
    print(f"       Target 1 (Classification): {TARGET_CLASSIFICATION} ({y_clf.nunique()} classes)")
    print(f"       Target 2 (Regression): {TARGET_REGRESSION} (Mean: {y_reg.mean():.1f}, Std: {y_reg.std():.1f})")

    cv = SpatialLOCOCrossValidator(X, groups)

    # 1. Evaluate Priority Classifier with Spatial LOCO CV
    print("\n[EVAL] Running Leave-One-City-Out Spatial Cross-Validation for Classifier...")
    clf_model = RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_split=4, random_state=42)
    clf_cv_metrics = cv.evaluate_classifier(clf_model, y_clf)
    print(f"       Spatial LOCO Accuracy: {clf_cv_metrics['mean_accuracy'] * 100:.2f}%")
    print(f"       Spatial LOCO Weighted F1: {clf_cv_metrics['mean_f1']:.4f}")
    for fold in clf_cv_metrics["folds"]:
        print(f"         * Test City: {fold['test_city']:<12} Acc: {fold['accuracy']*100:.1f}%, F1: {fold['f1_score']:.3f}")

    # 2. Evaluate Gap Score Regressor with Spatial LOCO CV
    print("\n[EVAL] Running Leave-One-City-Out Spatial Cross-Validation for Regressor...")
    reg_model = GradientBoostingRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42)
    reg_cv_metrics = cv.evaluate_regressor(reg_model, y_reg)
    print(f"       Spatial LOCO Mean RMSE: {reg_cv_metrics['mean_rmse']:.2f}")
    print(f"       Spatial LOCO Mean R^2:  {reg_cv_metrics['mean_r2']:.3f}")
    for fold in reg_cv_metrics["folds"]:
        print(f"         * Test City: {fold['test_city']:<12} RMSE: {fold['rmse']:.2f}, R2: {fold['r2']:.3f}")

    # 3. Train Final Models on all cities
    print("\n[FIT] Training final production models on full multi-city corpus...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    final_clf = RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_split=4, random_state=42)
    final_clf.fit(X_scaled, y_clf)

    final_reg = GradientBoostingRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42)
    final_reg.fit(X_scaled, y_reg)

    # Extract Feature Importances
    clf_importances = dict(zip(FEATURE_COLUMNS, final_clf.feature_importances_.round(4).tolist()))
    reg_importances = dict(zip(FEATURE_COLUMNS, final_reg.feature_importances_.round(4).tolist()))

    print("[IMPORTANCE] Top 3 Classifier Features:")
    for k, v in sorted(clf_importances.items(), key=lambda item: item[1], reverse=True)[:3]:
        print(f"       - {k}: {v * 100:.1f}%")

    # 4. Save Artifacts to models/ and outputs/model_metrics/
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    config.MODEL_METRICS_DIR.mkdir(parents=True, exist_ok=True)

    clf_path = config.MODELS_DIR / "cradle_priority_classifier.joblib"
    reg_path = config.MODELS_DIR / "cradle_gap_regressor.joblib"
    scaler_path = config.MODELS_DIR / "cradle_ml_preprocessor.joblib"
    features_path = config.MODELS_DIR / "cradle_feature_names.json"

    joblib.dump(final_clf, clf_path)
    joblib.dump(final_reg, reg_path)
    joblib.dump(scaler, scaler_path)

    metadata = {
        "model_version": "1.0.0",
        "timestamp": pd.Timestamp.now().isoformat(),
        "training_samples": len(df),
        "cities": groups.unique().tolist(),
        "feature_names": FEATURE_COLUMNS,
        "target_classification": TARGET_CLASSIFICATION,
        "target_regression": TARGET_REGRESSION,
        "classifier_feature_importances": clf_importances,
        "regressor_feature_importances": reg_importances,
        "spatial_loco_classifier_metrics": {
            "mean_accuracy": clf_cv_metrics["mean_accuracy"],
            "mean_f1": clf_cv_metrics["mean_f1"],
            "folds": clf_cv_metrics["folds"],
        },
        "spatial_loco_regressor_metrics": {
            "mean_rmse": reg_cv_metrics["mean_rmse"],
            "mean_r2": reg_cv_metrics["mean_r2"],
            "folds": reg_cv_metrics["folds"],
        },
    }

    with open(features_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save metrics JSON to outputs/model_metrics/
    metrics_export_path = config.MODEL_METRICS_DIR / "spatial_loco_evaluation.json"
    with open(metrics_export_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[DONE] Production Model Artifacts Exported Successfully:")
    print(f"       -> Classifier:  {clf_path}")
    print(f"       -> Regressor:   {reg_path}")
    print(f"       -> Scaler:      {scaler_path}")
    print(f"       -> Metadata:    {features_path}")
    print(f"       -> Metrics:     {metrics_export_path}")
    print("=" * 65)

    return metadata


if __name__ == "__main__":
    train_and_export_models()
