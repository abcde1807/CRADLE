"""
CRADLE Machine Learning Model Evaluation Module
Evaluates trained models, generates classification confusion matrices,
precision/recall/F1 metrics, regression residuals, and exports tabular reports
to the outputs/model_metrics/ directory.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix, classification_report, accuracy_score,
    precision_recall_fscore_support, mean_squared_error, mean_absolute_error, r2_score
)
import joblib

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.model_training import FEATURE_COLUMNS, TARGET_CLASSIFICATION, TARGET_REGRESSION, load_multi_city_training_data


class ModelEvaluator:
    """Evaluates CRADLE's trained spatial machine learning models."""

    def __init__(self):
        self.clf_path = config.MODELS_DIR / "cradle_priority_classifier.joblib"
        self.reg_path = config.MODELS_DIR / "cradle_gap_regressor.joblib"
        self.scaler_path = config.MODELS_DIR / "cradle_ml_preprocessor.joblib"
        self.meta_path = config.MODELS_DIR / "cradle_feature_names.json"

        self._check_models_exist()
        self.clf = joblib.load(self.clf_path)
        self.reg = joblib.load(self.reg_path)
        self.scaler = joblib.load(self.scaler_path)
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def _check_models_exist(self):
        for p in [self.clf_path, self.reg_path, self.scaler_path, self.meta_path]:
            if not p.exists():
                raise FileNotFoundError(f"Model artifact {p} not found. Run model_training.py first.")

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Runs full evaluation and saves reports to outputs/model_metrics/."""
        df = load_multi_city_training_data()
        X = df[FEATURE_COLUMNS]
        y_clf = df[TARGET_CLASSIFICATION]
        y_reg = df[TARGET_REGRESSION]

        X_scaled = self.scaler.transform(X)

        # 1. Classification Predictions & Metrics
        y_clf_pred = self.clf.predict(X_scaled)
        classes = ["Low", "Moderate", "High", "Critical"]

        # Confusion Matrix
        cm = confusion_matrix(y_clf, y_clf_pred, labels=classes)
        cm_df = pd.DataFrame(cm, index=[f"Actual_{c}" for c in classes], columns=[f"Pred_{c}" for c in classes])
        cm_path = config.MODEL_METRICS_DIR / "confusion_matrix.csv"
        cm_df.to_csv(cm_path)

        acc = accuracy_score(y_clf, y_clf_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_clf, y_clf_pred, average="weighted", zero_division=0)
        report_dict = classification_report(y_clf, y_clf_pred, labels=classes, output_dict=True, zero_division=0)

        # Per-class metrics table
        class_metrics_list = []
        for c in classes:
            c_metrics = report_dict.get(c, {})
            class_metrics_list.append({
                "Class": c,
                "Precision": round(c_metrics.get("precision", 0.0), 3),
                "Recall": round(c_metrics.get("recall", 0.0), 3),
                "F1-Score": round(c_metrics.get("f1-score", 0.0), 3),
                "Support": c_metrics.get("support", 0),
            })
        class_metrics_df = pd.DataFrame(class_metrics_list)
        class_metrics_path = config.MODEL_METRICS_DIR / "classification_metrics.csv"
        class_metrics_df.to_csv(class_metrics_path, index=False)

        # 2. Regression Predictions & Metrics
        y_reg_pred = self.reg.predict(X_scaled)
        rmse = float(np.sqrt(mean_squared_error(y_reg, y_reg_pred)))
        mae = float(mean_absolute_error(y_reg, y_reg_pred))
        r2 = float(r2_score(y_reg, y_reg_pred))

        # 3. Feature Importance Table
        feat_df = pd.DataFrame({
            "Feature": FEATURE_COLUMNS,
            "Classifier_Importance": [self.clf.feature_importances_[i] for i in range(len(FEATURE_COLUMNS))],
            "Regressor_Importance": [self.reg.feature_importances_[i] for i in range(len(FEATURE_COLUMNS))],
        }).sort_values(by="Classifier_Importance", ascending=False)
        feat_path = config.MODEL_METRICS_DIR / "feature_importances.csv"
        feat_df.to_csv(feat_path, index=False)

        # 4. Summary JSON
        summary = {
            "model_family": "RandomForestClassifier & GradientBoostingRegressor",
            "evaluated_samples": len(df),
            "classification": {
                "accuracy": round(float(acc), 4),
                "weighted_precision": round(float(prec), 4),
                "weighted_recall": round(float(rec), 4),
                "weighted_f1": round(float(f1), 4),
                "classes": classes,
                "confusion_matrix": cm.tolist(),
                "per_class": class_metrics_list,
            },
            "regression": {
                "rmse": round(rmse, 3),
                "mae": round(mae, 3),
                "r2_score": round(r2, 3),
            },
            "spatial_loco_cross_validation": self.metadata.get("spatial_loco_classifier_metrics", {}),
            "feature_importances": feat_df.to_dict(orient="records"),
        }

        summary_path = config.MODEL_METRICS_DIR / "model_evaluation_report.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("=" * 65)
        print("CRADLE MODEL EVALUATION SUMMARY")
        print("=" * 65)
        print(f"Overall Accuracy:  {acc * 100:.2f}%")
        print(f"Weighted F1-Score: {f1:.4f}")
        print(f"Regression RMSE:   {rmse:.2f} (R2: {r2:.3f})")
        print(f"\nConfusion Matrix:")
        print(cm_df)
        print(f"\nSaved Reports to {config.MODEL_METRICS_DIR}:")
        print(f"  -> {cm_path.name}")
        print(f"  -> {class_metrics_path.name}")
        print(f"  -> {feat_path.name}")
        print(f"  -> {summary_path.name}")
        print("=" * 65)

        return summary


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.run_full_evaluation()
