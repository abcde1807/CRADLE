"""
CRADLE Machine Learning Model Inference Module
Exposes clean, robust prediction APIs for priority classification and gap score regression,
supporting single-ward predictions, batch evaluations, and feature contribution explainability.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Union, List, Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import joblib

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.model_training import FEATURE_COLUMNS, PRIORITY_CLASSES


class CradlePredictor:
    """
    High-performance inference engine for CRADLE spatial machine learning models.
    Supports single-ward interactive prediction and batch GeoDataFrame enrichment.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CradlePredictor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.clf_path = config.MODELS_DIR / "cradle_priority_classifier.joblib"
        self.reg_path = config.MODELS_DIR / "cradle_gap_regressor.joblib"
        self.scaler_path = config.MODELS_DIR / "cradle_ml_preprocessor.joblib"
        self.meta_path = config.MODELS_DIR / "cradle_feature_names.json"

        if not self.clf_path.exists() or not self.reg_path.exists():
            raise FileNotFoundError("Trained models not found. Please run model_training.py first.")

        self.clf = joblib.load(self.clf_path)
        self.reg = joblib.load(self.reg_path)
        self.scaler = joblib.load(self.scaler_path)

        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.feature_names = self.metadata.get("feature_names", FEATURE_COLUMNS)
        self.classes = list(self.clf.classes_)
        self._initialized = True

    def get_model_info(self) -> Dict[str, Any]:
        """Returns model metadata and LOCO spatial validation performance."""
        return {
            "version": self.metadata.get("model_version", "1.0.0"),
            "training_samples": self.metadata.get("training_samples", 0),
            "cities": self.metadata.get("cities", []),
            "feature_names": self.feature_names,
            "classes": self.classes,
            "loco_classifier_accuracy": self.metadata.get("spatial_loco_classifier_metrics", {}).get("mean_accuracy", 0.0),
            "loco_regressor_rmse": self.metadata.get("spatial_loco_regressor_metrics", {}).get("mean_rmse", 0.0),
            "classifier_feature_importances": self.metadata.get("classifier_feature_importances", {}),
            "regressor_feature_importances": self.metadata.get("regressor_feature_importances", {}),
        }

    def _prepare_features(self, input_data: Union[Dict[str, Any], pd.DataFrame]) -> pd.DataFrame:
        """Standardizes input dictionaries or dataframes into expected feature dataframe."""
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        else:
            df = input_data.copy()

        # Compute Vuln_Ratio if Elderly and Children present
        if "Vuln_Ratio" not in df.columns:
            if "Elderly" in df.columns and "Children" in df.columns and "Population" in df.columns:
                pop = df["Population"].replace(0, 1)
                df["Vuln_Ratio"] = ((df["Elderly"] + df["Children"]) / pop).clip(0.0, 1.0)
            else:
                df["Vuln_Ratio"] = 0.25

        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df[self.feature_names]

    def predict_ward(self, ward_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts Priority Category and Gap Score for a single ward dictionary.
        Returns predicted category, probabilities, gap score, and top feature drivers.
        """
        X = self._prepare_features(ward_data)
        X_scaled = self.scaler.transform(X)

        pred_class = self.clf.predict(X_scaled)[0]
        pred_probs = self.clf.predict_proba(X_scaled)[0]
        prob_dict = {cls_name: round(float(p), 4) for cls_name, p in zip(self.classes, pred_probs)}
        confidence = float(np.max(pred_probs))

        pred_gap = float(np.clip(self.reg.predict(X_scaled)[0], 0.0, 100.0))

        # Explainability: compute relative feature deviation * feature importance
        importances = self.metadata.get("classifier_feature_importances", {})
        feat_vals = X.iloc[0].to_dict()
        driver_scores = {}
        for feat, val in feat_vals.items():
            weight = importances.get(feat, 0.1)
            driver_scores[feat] = round(float(val * weight), 3)

        top_drivers = sorted(driver_scores.items(), key=lambda item: item[1], reverse=True)[:4]

        return {
            "predicted_priority": pred_class,
            "confidence": round(confidence, 4),
            "priority_probabilities": prob_dict,
            "predicted_gap_score": round(pred_gap, 1),
            "top_drivers": [{"feature": k, "impact_score": v} for k, v in top_drivers],
        }

    def predict_batch(self, df_or_gdf: Union[pd.DataFrame, gpd.GeoDataFrame]) -> Union[pd.DataFrame, gpd.GeoDataFrame]:
        """
        Enriches a DataFrame or GeoDataFrame with ML predictions:
        Adds ML_Predicted_Priority, ML_Confidence, and ML_Predicted_Gap_Score.
        """
        res = df_or_gdf.copy()
        X = self._prepare_features(res)
        X_scaled = self.scaler.transform(X)

        preds = self.clf.predict(X_scaled)
        probs = self.clf.predict_proba(X_scaled)
        confs = np.max(probs, axis=1)
        gaps = np.clip(self.reg.predict(X_scaled), 0.0, 100.0)

        res["ML_Predicted_Priority"] = preds
        res["ML_Confidence"] = np.round(confs, 3)
        res["ML_Predicted_Gap_Score"] = np.round(gaps, 1)

        return res
