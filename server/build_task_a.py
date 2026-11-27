# -*- coding: utf-8 -*-
"""
Task A：构建死亡二分类正式训练集

依赖：优先读取 output/dedup_raw.csv（需先跑 build_training_dataset.py）
输出：dataset/task_a/

用法（在项目根目录执行）：
  set PYTHONNOUSERSITE=1
  python server\\build_task_a.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from config import task_a as cfg

YES_NO_MAP = {
    "是": 1,
    "否": 0,
    "有": 1,
    "无": 0,
    "1": 1,
    "0": 0,
    "Y": 1,
    "N": 0,
    "y": 1,
    "n": 0,
    "true": 1,
    "false": 0,
}
GENDER_MAP = {"男": 1, "女": 0, "未知": np.nan, "不详": np.nan}


def blank_to_na(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].replace(
                {
                    "": np.nan,
                    "nan": np.nan,
                    "None": np.nan,
                    "NULL": np.nan,
                    "NA": np.nan,
                    "N/A": np.nan,
                    "-": np.nan,
                    "—": np.nan,
                    "不详": np.nan,
                    "未查": np.nan,
                    "未知": np.nan,
                }
            )
    return out


def to_num(s: pd.Series) -> pd.Series:
    if s.dtype != object:
        return pd.to_numeric(s, errors="coerce")
    extracted = s.astype(str).str.strip().str.replace(",", "", regex=False)
    extracted = extracted.str.extract(r"([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def map_yes_no(s: pd.Series) -> pd.Series:
    return s.map(YES_NO_MAP)


def parse_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def load_raw() -> pd.DataFrame:
    if not cfg.RAW_DEDUP.exists():
        raise SystemExit(
            f"未找到 {cfg.RAW_DEDUP}，请先运行：python server\\build_training_dataset.py"
        )
    print("读取", cfg.RAW_DEDUP)
    df = pd.read_csv(cfg.RAW_DEDUP, dtype=str, low_memory=False)
    df = blank_to_na(df)
    print(f"  rows={len(df)} cols={df.shape[1]}")
    return df


def add_cohort_flag(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in cfg.DIAG_TEXT_COLS if c in df.columns]
    if not cols:
        df["cohort_hcc_strong"] = 0
        return df
    blob = df[cols].fillna("").astype(str).agg(" ".join, axis=1)
    pattern = "|".join(re.escape(k) for k in cfg.HCC_STRONG_KEYWORDS)
    df["cohort_hcc_strong"] = blob.str.contains(pattern, regex=True, na=False).astype(int)
    print(
        "队列可证实 cohort_hcc_strong=1:",
        int(df["cohort_hcc_strong"].sum()),
        f"({df['cohort_hcc_strong'].mean():.1%})",
    )
    return df


def add_baseline_and_label(df: pd.DataFrame) -> pd.DataFrame:
    # label
    if "death" not in df.columns:
        raise SystemExit("缺少 death 列")
    df[cfg.LABEL_COL] = map_yes_no(df["death"])

    visit = parse_dt(df["visit_date"]) if "visit_date" in df.columns else None
    adm = parse_dt(df["admission_time"]) if "admission_time" in df.columns else None
    birth = parse_dt(df["birth_date"]) if "birth_date" in df.columns else None
    death_t = parse_dt(df["death_time"]) if "death_time" in df.columns else None
    last_t = (
        parse_dt(df["death_or_last_visit_date"])
        if "death_or_last_visit_date" in df.columns
        else None
    )

    baseline = visit.copy() if visit is not None else None
    if baseline is not None and adm is not None:
        baseline = baseline.fillna(adm)
    elif adm is not None:
        baseline = adm
    df["baseline_time"] = baseline
    df["baseline_year"] = baseline.dt.year if baseline is not None else np.nan

    # age
    age = to_num(df["age"]) if "age" in df.columns else pd.Series(np.nan, index=df.index)
    if birth is not None and baseline is not None:
        age_from_birth = (baseline - birth).dt.days / 365.25
        age = age.fillna(age_from_birth)
    df["age"] = age

    # follow-up
    end_t = None
    if death_t is not None and last_t is not None:
        end_t = death_t.fillna(last_t)
    elif death_t is not None:
        end_t = death_t
    elif last_t is not None:
        end_t = last_t
    if baseline is not None and end_t is not None:
        fu = (end_t - baseline).dt.days
        fu = fu.where(fu >= 0)
        df["follow_up_days"] = fu
    else:
        df["follow_up_days"] = np.nan

    return df


def encode_core_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {"categorical_maps": {}, "transforms": {}}
    out = pd.DataFrame({cfg.ID_COL: df[cfg.ID_COL].astype(str)})
    out[cfg.LABEL_COL] = df[cfg.LABEL_COL]
    out["cohort_hcc_strong"] = df["cohort_hcc_strong"]

    # gender
    if "gender" in df.columns:
        out["gender"] = df["gender"].map(GENDER_MAP)
        meta["transforms"]["gender"] = "男=1,女=0"
    else:
        out["gender"] = np.nan

    binary_like = [
        "is_hepatitis",
        "is_hypertension",
        "is_diabetes",
        "is_coronary",
        "is_smoking",
        "is_drinking",
        "is_past_surgery",
        "is_past_disease",
        "is_infectious_disease",
        "is_tuberculosis",
        "is_icu_transfer",
        "is_quit_smoking",
        "is_tox_contact",
        "is_radioactive_contact",
    ]
    for c in binary_like:
        if c in df.columns:
            out[c] = map_yes_no(df[c])
            meta["transforms"][c] = "yes_no_map"

    numeric_like = [
        "age",
        "times_of_inhospitalization",
        "years_of_smoking",
        "daily_smoking_amount",
        "baseline_year",
        "follow_up_days",
        "weight_change_value",
        "surgery_time_length",
        "total_score",
    ]
    for c in numeric_like:
        if c not in df.columns:
            continue
        if c in ("age", "baseline_year", "follow_up_days"):
            out[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            out[c] = to_num(df[c])
        meta["transforms"][c] = "numeric"

    cat_like = ["abo_blood_type", "marriage_status", "visit_type", "ethnicity"]
    for c in cat_like:
        if c not in df.columns:
            continue
        vals = df[c].astype(str)
        cats = sorted(v for v in vals.dropna().unique() if v not in ("nan", "None"))
        mapping = {v: i for i, v in enumerate(cats)}
        out[c] = vals.map(mapping)
        out.loc[df[c].isna(), c] = np.nan
        meta["categorical_maps"][c] = mapping
        meta["transforms"][c] = f"label_encode n={len(mapping)}"

    return out, meta


def merge_text_features(feat: pd.DataFrame) -> pd.DataFrame:
    """并入规则抽取的文本特征；缺失文件时跳过。"""
    if not getattr(cfg, "USE_TEXT_FEATURES", True):
        print("跳过文本特征（USE_TEXT_FEATURES=False）")
        return feat
    path = getattr(cfg, "TEXT_FEATURES_PATH", cfg.OUT_DIR / "text_features.csv")
    if not path.exists():
        print(f"未找到 {path}，请先运行 python server\\extract_text_features_a.py；本次仅表型特征")
        return feat
    tex = pd.read_csv(path, dtype={cfg.ID_COL: str})
    keep = [cfg.ID_COL] + [
        c
        for c in list(getattr(cfg, "TEXT_FEATURE_COLS", []))
        + list(getattr(cfg, "TEXT_META_COLS", []))
        if c in tex.columns
    ]
    tex = tex[keep].drop_duplicates(cfg.ID_COL, keep="first")
    before = feat.shape[1]
    out = feat.merge(tex, on=cfg.ID_COL, how="left")
    print(f"并入文本特征: +{out.shape[1] - before} 列（来自 {path.name}，匹配 {tex[cfg.ID_COL].isin(feat[cfg.ID_COL]).sum()} 人）")
    return out


def add_qc_flags(raw: pd.DataFrame, feat: pd.DataFrame) -> pd.DataFrame:
    out = feat.copy()
    out["qc_age_oob"] = ((out["age"] < 0) | (out["age"] > 110)).fillna(False).astype(int)
    smoke_conflict = (
        (out.get("is_smoking") == 0)
        & (out.get("years_of_smoking").fillna(0) > 0)
    )
    out["qc_smoke_conflict"] = smoke_conflict.fillna(False).astype(int)
    death_no_fu = (out[cfg.LABEL_COL] == 1) & out["follow_up_days"].isna()
    out["qc_death_no_followup"] = death_no_fu.fillna(False).astype(int)
    out["label_uncertain"] = out["qc_death_no_followup"]
    # 越界年龄置空
    out.loc[out["qc_age_oob"] == 1, "age"] = np.nan
    print(
        "QC flags:",
        f"age_oob={int(out['qc_age_oob'].sum())}",
        f"smoke_conflict={int(out['qc_smoke_conflict'].sum())}",
        f"death_no_fu={int(out['qc_death_no_followup'].sum())}",
    )
    return out


def add_missing_indicators(feat: pd.DataFrame) -> pd.DataFrame:
    if not cfg.ADD_MISSING_INDICATORS:
        return feat
    out = feat.copy()
    skip = {
        cfg.ID_COL,
        cfg.LABEL_COL,
        "cohort_hcc_strong",
        "qc_age_oob",
        "qc_smoke_conflict",
        "qc_death_no_followup",
        "label_uncertain",
    }
    for c in list(out.columns):
        if c in skip or c.endswith("_isna"):
            continue
        miss = out[c].isna()
        if miss.any() and miss.mean() < 1.0:
            out[f"{c}_isna"] = miss.astype(int)
    return out


def select_model_matrix(feat: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    exclude = set(cfg.EXCLUDE_FROM_MODEL) | set(cfg.MODEL_EXCLUDE_EXTRA)
    # keep cohort as optional metadata only
    feature_cols = [
        c
        for c in feat.columns
        if c not in exclude and not c.startswith("qc_") and c != "label_uncertain"
    ]
    # drop ultra-high missing non-indicator cols
    keep = []
    for c in feature_cols:
        if c.endswith("_isna"):
            keep.append(c)
            continue
        miss = feat[c].isna().mean()
        if miss <= cfg.MAX_MISS_DROP:
            keep.append(c)

    meta_cols = [
        cfg.ID_COL,
        cfg.LABEL_COL,
        "cohort_hcc_strong",
        "label_uncertain",
        "follow_up_days",
        "qc_age_oob",
        "qc_smoke_conflict",
        "qc_death_no_followup",
    ]
    meta_cols = [c for c in meta_cols if c in feat.columns]
    # 避免 keep 与 meta 重复
    keep = [c for c in keep if c not in meta_cols]
    return feat[meta_cols + keep].copy(), keep


def build_feature_dictionary(feat: pd.DataFrame, feature_cols: list[str], meta: dict) -> pd.DataFrame:
    rows = []
    descriptions = {
        "gender": "性别 男=1 女=0",
        "age": "基线年龄（岁），记录优先，否则出生日期推算",
        "is_hepatitis": "是否有肝炎",
        "is_hypertension": "是否高血压",
        "is_diabetes": "是否糖尿病",
        "is_coronary": "是否冠心病",
        "is_smoking": "是否吸烟",
        "is_drinking": "是否饮酒",
        "is_past_surgery": "是否有手术史",
        "is_past_disease": "是否有既往疾病史",
        "is_infectious_disease": "是否有传染病史",
        "is_tuberculosis": "是否有结核",
        "is_icu_transfer": "是否转入ICU",
        "times_of_inhospitalization": "住院总次数",
        "years_of_smoking": "烟龄(年)",
        "daily_smoking_amount": "日吸烟量",
        "abo_blood_type": "ABO血型(编码)",
        "marriage_status": "婚姻状况(编码)",
        "visit_type": "就诊类型(编码)",
        "ethnicity": "民族(编码)",
        "baseline_year": "基线年份",
        "cohort_hcc_strong": "肝癌强关键词可证实标记（元数据）",
        "follow_up_days": "随访天数（默认不入模）",
        "has_portal_vein_thrombus": "文本抽取:门脉癌栓",
        "has_metastasis": "文本抽取:转移",
        "cirrhosis_decompensated": "文本抽取:肝硬化失代偿",
        "cirrhosis_compensated": "文本抽取:肝硬化代偿期",
        "has_cirrhosis": "文本抽取:肝硬化",
        "has_ascites": "文本抽取:腹水/腹腔积液",
        "has_variceal_bleed": "文本抽取:静脉曲张出血/消化道出血",
        "tx_tace": "文本抽取:TACE/栓塞治疗史",
        "tx_resection": "文本抽取:肝切除史",
        "tx_ablation": "文本抽取:消融治疗史",
        "tx_transplant": "文本抽取:肝移植史",
        "symptom_jaundice": "文本抽取:黄疸",
        "symptom_bleed": "文本抽取:出血相关症状",
        "has_hbv": "文本抽取:乙肝相关",
        "stage_cnlc": "文本抽取:CNLC分期(1-4)",
        "has_stage": "文本抽取:是否写出分期",
        "text_diag_available": "元数据:诊断文本是否非空",
        "text_history_available": "元数据:病史文本是否非空",
    }
    for c in feature_cols:
        base = c[:-5] if c.endswith("_isna") else c
        rows.append(
            {
                "feature": c,
                "dtype": str(feat[c].dtype),
                "missing_rate": round(float(feat[c].isna().mean()), 4),
                "nunique": int(feat[c].nunique(dropna=True)),
                "is_missing_indicator": c.endswith("_isna"),
                "description": (
                    f"{descriptions.get(base, base)} 缺失指示"
                    if c.endswith("_isna")
                    else descriptions.get(c, meta.get("transforms", {}).get(c, ""))
                ),
                "in_model": True,
            }
        )
    return pd.DataFrame(rows)


def split_and_save(feat: pd.DataFrame, feature_cols: list[str]) -> dict:
    y = feat[cfg.LABEL_COL].astype(int)
    train_df, temp = train_test_split(
        feat, test_size=cfg.TEST_SIZE + cfg.VAL_SIZE, random_state=cfg.SEED, stratify=y
    )
    rel = cfg.TEST_SIZE / (cfg.TEST_SIZE + cfg.VAL_SIZE)
    val_df, test_df = train_test_split(
        temp, test_size=rel, random_state=cfg.SEED, stratify=temp[cfg.LABEL_COL]
    )
    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()
    train_df["split"] = "train"
    val_df["split"] = "val"
    test_df["split"] = "test"

    cfg.OUT_DIR.mkdir(parents=True, exist_ok=True)
    patients = pd.concat([train_df, val_df, test_df], ignore_index=True)
    patients.to_csv(cfg.OUT_DIR / "patients.csv", index=False, encoding="utf-8-sig")
    try:
        patients.to_parquet(cfg.OUT_DIR / "patients.parquet", index=False)
    except Exception as e:
        print("parquet skip:", e)

    meta_cols = [cfg.ID_COL, cfg.LABEL_COL, "cohort_hcc_strong", "label_uncertain", "split"]
    use_cols = meta_cols + feature_cols

    def dump_split(name: str, part: pd.DataFrame):
        part[use_cols].to_csv(cfg.OUT_DIR / f"features_{name}.csv", index=False, encoding="utf-8-sig")
        try:
            part[use_cols].to_parquet(cfg.OUT_DIR / f"features_{name}.parquet", index=False)
        except Exception:
            pass

    dump_split("train", train_df)
    dump_split("val", val_df)
    dump_split("test", test_df)

    # X-only matrices for modeling convenience
    for name, part in [("train", train_df), ("val", val_df), ("test", test_df)]:
        part[feature_cols].to_csv(cfg.OUT_DIR / f"X_{name}.csv", index=False, encoding="utf-8-sig")
        part[[cfg.LABEL_COL]].to_csv(cfg.OUT_DIR / f"y_{name}.csv", index=False, encoding="utf-8-sig")

    info = {
        "train": len(train_df),
        "val": len(val_df),
        "test": len(test_df),
        "train_pos_rate": round(float(train_df[cfg.LABEL_COL].mean()), 4),
        "val_pos_rate": round(float(val_df[cfg.LABEL_COL].mean()), 4),
        "test_pos_rate": round(float(test_df[cfg.LABEL_COL].mean()), 4),
        "n_features": len(feature_cols),
        "cohort_strong_n": int(patients["cohort_hcc_strong"].sum()),
        "label_uncertain_n": int(patients["label_uncertain"].sum()),
    }
    return info


def gate_report(feat: pd.DataFrame, feature_cols: list[str]) -> dict:
    core = [c for c in ["gender", "age", "is_hepatitis", "is_smoking"] if c in feature_cols]
    core_miss = {c: round(float(feat[c].isna().mean()), 4) for c in core}
    gates = {
        "label_mappable_rate": round(float(feat[cfg.LABEL_COL].isin([0, 1]).mean()), 4),
        "patient_unique": bool(~feat[cfg.ID_COL].duplicated().any()),
        "death_with_followup_rate": round(
            float(
                (
                    (feat[cfg.LABEL_COL] == 1) & feat["follow_up_days"].notna()
                ).sum()
                / max((feat[cfg.LABEL_COL] == 1).sum(), 1)
            ),
            4,
        ),
        "core_feature_missing": core_miss,
        "n_features": len(feature_cols),
        "pass_label_coverage": True,
        "pass_unique": bool(~feat[cfg.ID_COL].duplicated().any()),
        "pass_min_features": len(feature_cols) >= 10,
    }
    gates["overall_pass"] = (
        gates["pass_label_coverage"] and gates["pass_unique"] and gates["pass_min_features"]
    )
    return gates


def main():
    raw = load_raw()
    raw = add_cohort_flag(raw)
    raw = add_baseline_and_label(raw)

    # keep labeled only
    before = len(raw)
    raw = raw[raw[cfg.LABEL_COL].isin([0, 1])].copy()
    raw[cfg.LABEL_COL] = raw[cfg.LABEL_COL].astype(int)
    print(f"标签过滤: {before} → {len(raw)}")

    feat, meta = encode_core_columns(raw)
    # ensure numeric cols from baseline present
    for c in ["age", "baseline_year", "follow_up_days", "cohort_hcc_strong"]:
        if c in raw.columns and c not in feat.columns:
            feat[c] = raw[c].values
        elif c in raw.columns:
            feat[c] = pd.to_numeric(raw[c], errors="coerce")

    feat = add_qc_flags(raw, feat)
    feat = merge_text_features(feat)
    feat = add_missing_indicators(feat)
    model_df, feature_cols = select_model_matrix(feat)
    print(f"建模特征数: {len(feature_cols)}")

    cfg.OUT_DIR.mkdir(parents=True, exist_ok=True)
    split_info = split_and_save(model_df, feature_cols)

    # dictionary
    # merge feat for miss rates on full labeled set
    fdict = build_feature_dictionary(model_df, feature_cols, meta)
    fdict.to_csv(cfg.OUT_DIR / "feature_dictionary.csv", index=False, encoding="utf-8-sig")

    with (cfg.OUT_DIR / "categorical_maps.json").open("w", encoding="utf-8") as fh:
        json.dump(meta.get("categorical_maps", {}), fh, ensure_ascii=False, indent=2)

    with (cfg.OUT_DIR / "feature_list.json").open("w", encoding="utf-8") as fh:
        json.dump({"features": feature_cols, "exclude_from_model": sorted(cfg.MODEL_EXCLUDE_EXTRA)}, fh, ensure_ascii=False, indent=2)

    gates = gate_report(model_df, feature_cols)
    summary = {
        "task": "A_death_binary",
        "n_patients": len(model_df),
        "positive_rate": round(float(model_df[cfg.LABEL_COL].mean()), 4),
        "split": split_info,
        "gates": gates,
        "label_spec": "docs/label_spec_a.md",
        "outputs": [
            "dataset/task_a/patients.csv",
            "dataset/task_a/features_{train,val,test}.csv",
            "dataset/task_a/X_{train,val,test}.csv",
            "dataset/task_a/y_{train,val,test}.csv",
            "dataset/task_a/text_features.csv",
            "dataset/task_a/text_feature_coverage.json",
            "dataset/task_a/feature_dictionary.csv",
            "dataset/task_a/feature_list.json",
            "dataset/task_a/categorical_maps.json",
            "dataset/task_a/summary.json",
        ],
        "text_features_merged": bool(
            getattr(cfg, "USE_TEXT_FEATURES", True)
            and getattr(cfg, "TEXT_FEATURES_PATH", cfg.OUT_DIR / "text_features.csv").exists()
        ),
    }
    with (cfg.OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    # copy label spec pointer
    print("\n完成 Task A 构建")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not gates["overall_pass"]:
        raise SystemExit("门禁未通过，请检查 gates")


if __name__ == "__main__":
    main()
