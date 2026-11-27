# -*- coding: utf-8 -*-
"""
Task A 基线模型：LogisticRegression + HistGradientBoosting
用法（在项目根目录执行）：
  set PYTHONNOUSERSITE=1
  python server\\train_baseline_a.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import task_a as cfg


def load_xy(split: str):
    x = pd.read_csv(cfg.OUT_DIR / f"X_{split}.csv")
    y = pd.read_csv(cfg.OUT_DIR / f"y_{split}.csv")[cfg.LABEL_COL].astype(int)
    return x, y


def eval_model(name: str, model, X_val, y_val, X_test, y_test) -> dict:
    out = {"model": name}
    for split, X, y in [("val", X_val, y_val), ("test", X_test, y_test)]:
        proba = model.predict_proba(X)[:, 1]
        pred = (proba >= 0.5).astype(int)
        out[f"{split}_auroc"] = round(float(roc_auc_score(y, proba)), 4)
        out[f"{split}_auprc"] = round(float(average_precision_score(y, proba)), 4)
        out[f"{split}_pos_rate_pred"] = round(float(pred.mean()), 4)
        print(f"\n=== {name} / {split} ===")
        print(f"AUROC={out[f'{split}_auroc']}  AUPRC={out[f'{split}_auprc']}")
        print(classification_report(y, pred, digits=4))
    return out


def main():
    if not (cfg.OUT_DIR / "X_train.csv").exists():
        raise SystemExit("请先运行 python server\\build_task_a.py")

    X_train, y_train = load_xy("train")
    X_val, y_val = load_xy("val")
    X_test, y_test = load_xy("test")
    print(
        f"shapes train={X_train.shape} val={X_val.shape} test={X_test.shape} "
        f"pos_rate={y_train.mean():.4f}"
    )

    results = []

    # 1) Logistic Regression + median impute + scale
    num_features = list(X_train.columns)
    logit = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=cfg.SEED,
                ),
            ),
        ]
    )
    logit.fit(X_train, y_train)
    results.append(eval_model("logistic_regression", logit, X_val, y_val, X_test, y_test))

    # 2) HistGradientBoosting (native missing support)
    hgb = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.05,
        max_iter=300,
        random_state=cfg.SEED,
        class_weight="balanced",
    )
    hgb.fit(X_train, y_train)
    results.append(eval_model("hist_gradient_boosting", hgb, X_val, y_val, X_test, y_test))

    # feature importance (HGB)
    # sklearn HGB has no feature_importances_ until recent; use permutation on val sample
    try:
        from sklearn.inspection import permutation_importance

        # subsample for speed
        rng = np.random.RandomState(cfg.SEED)
        idx = rng.choice(len(X_val), size=min(2000, len(X_val)), replace=False)
        imp = permutation_importance(
            hgb, X_val.iloc[idx], y_val.iloc[idx], n_repeats=5, random_state=cfg.SEED, scoring="average_precision"
        )
        order = np.argsort(imp.importances_mean)[::-1][:20]
        top = [
            {
                "feature": X_val.columns[i],
                "importance_mean": round(float(imp.importances_mean[i]), 6),
            }
            for i in order
        ]
    except Exception as e:
        top = [{"error": str(e)}]

    summary = {
        "task": "A_death_binary_baseline",
        "n_features": X_train.shape[1],
        "results": results,
        "hgb_top_features_perm_auprc": top,
    }
    out_path = cfg.OUT_DIR / "baseline_metrics.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("\n写入", out_path)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
