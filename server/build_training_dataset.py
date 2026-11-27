# -*- coding: utf-8 -*-
"""
肝癌基线数据 → 训练数据集构建脚本

功能：
1. 合并多分片 CSV（可选 Excel），按 patient_sn 去重
2. 解析三行表头、消解重复英文字段名
3. 清洗二值/分类型/数值/日期，剔除 PII 与超高缺失字段
4. 构造二分类标签（death）与可选随访天数
5. 导出训练表 + QC 对比 JSON + 处理前后可视化图

用法（在项目根目录执行）：
  set PYTHONNOUSERSITE=1
  python server\\build_training_dataset.py
  python server\\build_training_dataset.py --include-xlsx
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# 中文字体（Windows 常见）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "原始数据"
OUT_DIR = BASE_DIR / "output"
FIG_DIR = OUT_DIR / "figures"

YES_NO_MAP = {
    "是": 1,
    "否": 0,
    "有": 1,
    "无": 0,
    "true": 1,
    "false": 0,
    "True": 1,
    "False": 0,
    "1": 1,
    "0": 0,
    "Y": 1,
    "N": 0,
    "y": 1,
    "n": 0,
}

GENDER_MAP = {"男": 1, "女": 0, "未知": -1, "不详": -1}

# 明确的 PII / 标识符（不当作模型特征）
PII_COLS = {
    "name",
    "inpatient_no_id",
    "基线_inpatient_no_id",
    "patient_id",
    "pathology_id",
    "pathology_exam_id",
    "exam_id",
}

# 自由文本 / 长文本：不进表格特征，可另存
TEXT_HINTS = (
    "history",
    "complain",
    "finding",
    "conclusion",
    "description",
    "diagnosis",
    "content",
    "comments",
    "result",
    "illness",
    "exam_finding",
    "exam_conclusion",
    "imaging",
    "immunohistochemistry",
    "chief_complain",
    "present_illness",
    "past_history",
    "personal_history",
    "family_history",
    "physical_exam",
    "specialist_exam",
    "auxiliary_exam",
    "positive_symptom",
    "pre_operative",
    "intra_operative",
    "post_operative",
    "menstrual",
    "allergen",
    "pre_disease_name",
    "infectious_disease_name",
    "main_diagnosis",
    "out_diagnosis",
    "last_diagnosis",
    "last_visit_history",
    "disease_name",
    "surgical_name",
    "order_item_name",
    "item_chinese_name",
    "normal_ref_value_text",
    "hybrid_result",
    "qualitative_result",
)

# vsn_* 仅为嵌套区块标记列
VSN_PREFIX = "vsn_"


def uniquify_names(names: list[str]) -> list[str]:
    """为重复英文字段名追加后缀 _2/_3..."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for name in names:
        name = (name or "").strip() or "unnamed"
        if name not in seen:
            seen[name] = 1
            out.append(name)
        else:
            seen[name] += 1
            out.append(f"{name}_{seen[name]}")
    return out


def list_source_files(include_xlsx: bool = False) -> list[Path]:
    src = RAW_DIR if RAW_DIR.is_dir() else BASE_DIR
    files = sorted(
        p
        for p in src.iterdir()
        if p.suffix.lower() == ".csv" and p.name.startswith("基线数据")
    )
    if include_xlsx:
        xlsx = src / "基线数据2.xlsx"
        if xlsx.exists():
            files.append(xlsx)
    return files


def read_one_table(path: Path) -> pd.DataFrame:
    """读取单个导出文件：跳过分组行，第1行中文、第2行英文，其后为数据。"""
    if path.suffix.lower() == ".xlsx":
        raw = pd.read_excel(path, sheet_name=0, header=None, dtype=str)
        cn = raw.iloc[1].tolist()
        en = uniquify_names([str(x) if pd.notna(x) else "" for x in raw.iloc[2].tolist()])
        df = raw.iloc[3:].copy()
        df.columns = en
        df = df.reset_index(drop=True)
    else:
        # 先读表头两行
        header = pd.read_csv(path, encoding="utf-8-sig", header=None, nrows=3, dtype=str)
        en = uniquify_names([str(x) if pd.notna(x) else "" for x in header.iloc[2].tolist()])
        df = pd.read_csv(
            path,
            encoding="utf-8-sig",
            header=None,
            skiprows=3,
            names=en,
            dtype=str,
            low_memory=False,
        )
        cn = header.iloc[1].tolist()

    df.attrs["cn_names"] = [str(c).split("\n")[0] if pd.notna(c) else "" for c in cn]
    df["__source_file"] = path.name
    return df


def nonempty_count(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in df.columns if not c.startswith("__")]
    arr = df[cols].to_numpy()
    # 字符串非空
    mask = np.vectorize(lambda x: False if x is None or (isinstance(x, float) and np.isnan(x)) else str(x).strip() != "")(arr)
    return pd.Series(mask.sum(axis=1), index=df.index)


def merge_and_dedup(frames: list[pd.DataFrame]) -> pd.DataFrame:
    all_df = pd.concat(frames, ignore_index=True, sort=False)
    all_df["patient_sn"] = all_df["patient_sn"].astype(str).str.strip()
    all_df = all_df[all_df["patient_sn"].notna() & (all_df["patient_sn"] != "") & (all_df["patient_sn"] != "nan")]
    all_df["__fill"] = nonempty_count(all_df)
    # 同患者保留填充最多的一行；并列时保留首次出现（通常靠前的分片）
    all_df = all_df.sort_values(["patient_sn", "__fill"], ascending=[True, False])
    dedup = all_df.drop_duplicates(subset=["patient_sn"], keep="first").reset_index(drop=True)
    return dedup


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
                    "null": np.nan,
                    "NA": np.nan,
                    "N/A": np.nan,
                    "-": np.nan,
                    "—": np.nan,
                    "不详": np.nan,
                    "未查": np.nan,
                    "未知": np.nan,
                }
            )
            out[c] = out[c].apply(lambda x: np.nan if isinstance(x, str) and x.strip() == "" else x)
    return out


def is_yes_no_series(s: pd.Series, min_known: float = 0.5) -> bool:
    vals = s.dropna().astype(str).str.strip()
    if len(vals) == 0:
        return False
    known = vals.isin(YES_NO_MAP.keys()).mean()
    return known >= min_known


def to_numeric_safe(s: pd.Series) -> pd.Series:
    if s.dtype != object:
        return pd.to_numeric(s, errors="coerce")
    cleaned = s.astype(str).str.strip().str.replace(",", "", regex=False)
    # 提取首个数值（处理 >10、<0.01 等）
    extracted = cleaned.str.extract(r"([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def parse_datetime(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def missing_rate(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in df.columns if not c.startswith("__")]
    return df[cols].isna().mean().sort_values(ascending=False)


def classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    cols = [c for c in df.columns if not c.startswith("__")]
    pii = [c for c in cols if c in PII_COLS or c.endswith("_id") and c not in {"patient_sn"}]
    vsn = [c for c in cols if c.startswith(VSN_PREFIX)]
    label_candidates = ["death"]
    id_cols = ["patient_sn", "group_name"]

    text_cols = []
    for c in cols:
        cl = c.lower()
        if c in pii or c in vsn or c in id_cols or c in label_candidates:
            continue
        if any(h in cl for h in TEXT_HINTS):
            # 短枚举字段例外
            if cl in {
                "abnormal_indicator",
                "score_grade",
                "visit_type",
                "visit_type_2",
                "order_status",
                "long_term_or_temporary",
                "diagnosis_type_name",
                "weight_change_property",
                "abo_blood_type",
                "rh_blood_type",
                "marriage_status",
                "ethnicity",
                "nationality",
                "last_visit_type",
            }:
                continue
            text_cols.append(c)

    force_numeric = {
        "times_of_inhospitalization",
        "quantity",
        "surgery_time_length",
        "icu_stay_length",
        "postoperative_inhospital_length",
        "surgery_blood_loss",
        "weight_change_value",
        "years_of_smoking",
        "daily_smoking_amount",
        "total_score",
        "item_value",
        "item_score",
        "high_value",
        "low_value",
        "age",
        "follow_up_days",
    }

    binary_cols = []
    for c in cols:
        if c in pii or c in vsn or c in text_cols or c in id_cols or c in force_numeric:
            continue
        if is_yes_no_series(df[c]):
            binary_cols.append(c)

    date_cols = []
    for c in cols:
        if c in pii + vsn + text_cols + binary_cols + id_cols or c in force_numeric:
            continue
        cl = c.lower()
        if cl.endswith("_length") or "time_length" in cl:
            continue
        if (
            cl.endswith("_date")
            or cl.endswith("_time")
            or cl.endswith("_datetime")
            or "datetime" in cl
            or cl.endswith("_birth_date")
        ):
            date_cols.append(c)

    cat_small = []
    num_cols = []
    reserved = set(
        pii
        + vsn
        + text_cols
        + binary_cols
        + date_cols
        + id_cols
        + label_candidates
        + ["gender", "基线_gender"]
    )
    for c in cols:
        if c in reserved:
            continue
        if c in force_numeric:
            num_cols.append(c)
            continue
        # ICD 编码不作连续数值
        if "icd10" in c.lower():
            if df[c].nunique(dropna=True) <= 50:
                cat_small.append(c)
            else:
                text_cols.append(c)
            continue
        nunique = df[c].nunique(dropna=True)
        num = to_numeric_safe(df[c])
        numeric_ratio = (
            num.notna().mean() / max(df[c].notna().mean(), 1e-9) if df[c].notna().any() else 0
        )
        if numeric_ratio >= 0.7 and nunique > 5:
            num_cols.append(c)
        elif nunique <= 30:
            cat_small.append(c)
        else:
            text_cols.append(c)

    return {
        "id": id_cols,
        "pii": sorted(set(pii)),
        "vsn": vsn,
        "binary": binary_cols,
        "categorical": cat_small + [c for c in ["gender", "基线_gender"] if c in df.columns],
        "numeric": num_cols,
        "datetime": date_cols,
        "text": sorted(set(text_cols)),
        "label": [c for c in label_candidates if c in df.columns],
    }


def build_features(df: pd.DataFrame, colmap: dict[str, list[str]], max_miss: float = 0.95) -> tuple[pd.DataFrame, dict]:
    """构建可训练的特征表。"""
    work = blank_to_na(df)
    meta: dict[str, Any] = {"transforms": {}, "dropped_high_missing": [], "label_stats": {}}

    # 标签
    if "death" not in work.columns:
        raise ValueError("缺少标签列 death")
    y = work["death"].map(YES_NO_MAP)
    meta["label_stats"]["death_raw"] = work["death"].value_counts(dropna=False).to_dict()
    meta["label_stats"]["death_mapped"] = y.value_counts(dropna=False).astype(int).to_dict()

    feat = pd.DataFrame({"patient_sn": work["patient_sn"]})
    feat["label_death"] = y

    # 性别
    if "gender" in work.columns:
        feat["gender"] = work["gender"].map(GENDER_MAP)
        meta["transforms"]["gender"] = "map 男=1,女=0,未知/不详=-1"
    elif "基线_gender" in work.columns:
        feat["gender"] = work["基线_gender"].map(GENDER_MAP)

    # 二值
    for c in colmap["binary"]:
        if c == "death":
            continue
        feat[c] = work[c].map(YES_NO_MAP)
        meta["transforms"][c] = "yes_no_map"

    # 数值
    for c in colmap["numeric"]:
        feat[c] = to_numeric_safe(work[c])
        meta["transforms"][c] = "to_numeric"

    # 小基数类别 → 整数编码（保留原值对照）
    cat_maps = {}
    for c in colmap["categorical"]:
        if c in {"gender", "基线_gender"}:
            continue
        cats = sorted(work[c].dropna().astype(str).unique().tolist())
        mapping = {v: i for i, v in enumerate(cats)}
        feat[c] = work[c].astype(str).map(mapping)
        # 原 NaN 映射到 nan
        feat.loc[work[c].isna(), c] = np.nan
        cat_maps[c] = mapping
        meta["transforms"][c] = f"label_encode n={len(mapping)}"
    meta["categorical_maps"] = cat_maps

    # 日期：转为时间戳（天）+ 衍生随访天数
    visit = parse_datetime(work["visit_date"]) if "visit_date" in work.columns else None
    adm = parse_datetime(work["admission_time"]) if "admission_time" in work.columns else None
    death_t = parse_datetime(work["death_time"]) if "death_time" in work.columns else None
    last_t = (
        parse_datetime(work["death_or_last_visit_date"])
        if "death_or_last_visit_date" in work.columns
        else None
    )
    birth = parse_datetime(work["birth_date"]) if "birth_date" in work.columns else None

    baseline = visit.copy() if visit is not None else None
    if baseline is not None and adm is not None:
        baseline = baseline.fillna(adm)
    elif adm is not None:
        baseline = adm

    if baseline is not None:
        feat["baseline_year"] = baseline.dt.year
        meta["transforms"]["baseline_year"] = "from visit_date/admission_time"

    if birth is not None and baseline is not None:
        age_from_birth = (baseline - birth).dt.days / 365.25
        if "age" in feat.columns:
            feat["age"] = feat["age"].fillna(age_from_birth)
        else:
            feat["age"] = age_from_birth
        meta["transforms"]["age"] = "prefer recorded age, else from birth_date"

    end_t = None
    if death_t is not None and last_t is not None:
        end_t = death_t.fillna(last_t)
    elif death_t is not None:
        end_t = death_t
    elif last_t is not None:
        end_t = last_t

    if baseline is not None and end_t is not None:
        fu = (end_t - baseline).dt.days
        fu = fu.where(fu >= 0)  # 负值视为异常缺失
        feat["follow_up_days"] = fu
        meta["transforms"]["follow_up_days"] = "end(death_or_last) - baseline"

    # 丢弃超高缺失特征（不含标签与 id）
    feature_cols = [c for c in feat.columns if c not in {"patient_sn", "label_death"}]
    miss = feat[feature_cols].isna().mean()
    keep = [c for c in feature_cols if miss[c] <= max_miss]
    drop = [c for c in feature_cols if miss[c] > max_miss]
    meta["dropped_high_missing"] = [{ "col": c, "missing_rate": round(float(miss[c]), 4)} for c in drop]
    feat = feat[["patient_sn", "label_death"] + keep]

    # 仅保留有标签的样本
    before_n = len(feat)
    feat = feat[feat["label_death"].isin([0, 1])].copy()
    feat["label_death"] = feat["label_death"].astype(int)
    meta["rows_before_label_filter"] = before_n
    meta["rows_after_label_filter"] = len(feat)
    meta["n_features"] = len(keep)
    meta["feature_columns"] = keep
    return feat, meta


def compute_qc(raw_dedup: pd.DataFrame, clean: pd.DataFrame, colmap: dict) -> dict:
    raw = blank_to_na(raw_dedup)
    raw_miss = missing_rate(raw)
    clean_miss = clean.drop(columns=["patient_sn"], errors="ignore").isna().mean().sort_values(ascending=False)

    module_patterns = {
        "人口学": ["gender", "birth_date", "ethnicity", "abo_blood_type", "marriage_status", "age"],
        "就诊": ["visit_type", "visit_date", "main_diagnosis", "icd10_code", "is_icu_transfer"],
        "入院/病史": ["admission_time", "is_hepatitis", "is_smoking", "is_drinking", "is_diabetes", "is_hypertension"],
        "检查": ["exam_type", "exam_name", "exam_date"],
        "病理": ["pathology_id", "imaging_conclusion"],
        "检验": ["test_time", "item_name", "test_result", "abnormal_indicator"],
        "手术": ["surgical_name", "surgery_time_length", "surgery_blood_loss"],
        "护理/评分": ["scoring_name", "total_score", "score_grade"],
        "结局": ["death", "death_time", "death_or_last_visit_date"],
    }
    module_before = {}
    for name, cols in module_patterns.items():
        present = [c for c in cols if c in raw.columns]
        if present:
            module_before[name] = round(float(1 - raw[present].isna().mean().mean()), 4)

    return {
        "raw": {
            "n_rows": int(len(raw)),
            "n_cols": int(raw.shape[1]),
            "overall_fill_rate": round(float(1 - raw_miss.mean()), 4),
            "death_counts": raw["death"].value_counts(dropna=False).astype(int).to_dict() if "death" in raw else {},
            "gender_counts": raw["gender"].value_counts(dropna=False).astype(int).to_dict() if "gender" in raw else {},
            "top_missing": [
                {"col": k, "missing_rate": round(float(v), 4)} for k, v in raw_miss.head(30).items()
            ],
            "module_fill": module_before,
            "column_roles": {k: v for k, v in colmap.items()},
        },
        "clean": {
            "n_rows": int(len(clean)),
            "n_cols": int(clean.shape[1]),
            "n_features": int(clean.shape[1] - 2),
            "overall_fill_rate": round(float(1 - clean_miss.mean()), 4),
            "label_counts": clean["label_death"].value_counts().astype(int).to_dict(),
            "positive_rate": round(float(clean["label_death"].mean()), 4),
            "top_missing": [
                {"col": k, "missing_rate": round(float(v), 4)} for k, v in clean_miss.head(30).items()
            ],
            "feature_fill": [
                {"col": c, "fill_rate": round(float(1 - clean[c].isna().mean()), 4)}
                for c in clean.columns
                if c not in {"patient_sn", "label_death"}
            ],
        },
    }


def plot_comparisons(qc: dict, clean: pd.DataFrame, raw_dedup: pd.DataFrame) -> list[Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    raw = blank_to_na(raw_dedup)

    # 1) 样本量与特征数
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["行数(患者)", "列数/特征数"]
    before = [qc["raw"]["n_rows"], qc["raw"]["n_cols"]]
    after = [qc["clean"]["n_rows"], qc["clean"]["n_features"]]
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w / 2, before, w, label="处理前(去重后原始)", color="#4C78A8")
    ax.bar(x + w / 2, after, w, label="处理后(训练表)", color="#F58518")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("数量")
    ax.set_title("处理前后：样本量与维度")
    ax.legend()
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(i - w / 2, b, str(b), ha="center", va="bottom", fontsize=8)
        ax.text(i + w / 2, a, str(a), ha="center", va="bottom", fontsize=8)
    p = FIG_DIR / "01_size_before_after.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p)

    # 2) 模块完整度（处理前）
    mod = qc["raw"]["module_fill"]
    if mod:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        names = list(mod.keys())
        vals = [mod[k] * 100 for k in names]
        ax.barh(names[::-1], vals[::-1], color="#4C78A8")
        ax.set_xlabel("字段平均非空率 (%)")
        ax.set_title("处理前：各业务模块字段完整度")
        ax.set_xlim(0, 100)
        p = FIG_DIR / "02_module_fill_before.png"
        fig.tight_layout()
        fig.savefig(p, dpi=140)
        plt.close(fig)
        paths.append(p)

    # 3) 标签分布
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    raw_death = qc["raw"]["death_counts"]
    axes[0].bar(list(map(str, raw_death.keys())), list(raw_death.values()), color="#4C78A8")
    axes[0].set_title("处理前 death 原始取值")
    axes[0].set_ylabel("人数")
    clean_y = qc["clean"]["label_counts"]
    axes[1].bar(["存活(0)", "死亡(1)"], [clean_y.get(0, clean_y.get("0", 0)), clean_y.get(1, clean_y.get("1", 0))], color="#F58518")
    axes[1].set_title(f"处理后标签 (阳性率 {qc['clean']['positive_rate']:.1%})")
    p = FIG_DIR / "03_label_before_after.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p)

    # 4) 缺失率分布对比
    raw_miss = raw.isna().mean()
    clean_miss = clean.drop(columns=["patient_sn", "label_death"], errors="ignore").isna().mean()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(raw_miss.values * 100, bins=20, alpha=0.65, label="处理前全部字段", color="#4C78A8")
    ax.hist(clean_miss.values * 100, bins=20, alpha=0.65, label="处理后特征", color="#F58518")
    ax.set_xlabel("缺失率 (%)")
    ax.set_ylabel("字段个数")
    ax.set_title("处理前后：字段缺失率分布")
    ax.legend()
    p = FIG_DIR / "04_missing_hist_before_after.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p)

    # 5) 关键特征填充率 Top
    fill = sorted(
        qc["clean"]["feature_fill"],
        key=lambda x: x["fill_rate"],
        reverse=True,
    )[:25]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([x["col"] for x in fill][::-1], [x["fill_rate"] * 100 for x in fill][::-1], color="#54A24B")
    ax.set_xlabel("非空率 (%)")
    ax.set_title("处理后：填充率最高的 25 个特征")
    ax.set_xlim(0, 100)
    p = FIG_DIR / "05_top_feature_fill.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p)

    # 6) 年龄分布（若有）
    if "age" in clean.columns and clean["age"].notna().any():
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(clean["age"].dropna(), bins=30, color="#4C78A8", edgecolor="white")
        ax.set_xlabel("年龄（岁）")
        ax.set_ylabel("人数")
        ax.set_title("处理后：年龄分布")
        p = FIG_DIR / "06_age_distribution.png"
        fig.tight_layout()
        fig.savefig(p, dpi=140)
        plt.close(fig)
        paths.append(p)

    # 7) 整体填充率对比
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.bar(
        ["处理前", "处理后"],
        [qc["raw"]["overall_fill_rate"] * 100, qc["clean"]["overall_fill_rate"] * 100],
        color=["#4C78A8", "#F58518"],
    )
    ax.set_ylabel("整体非空率 (%)")
    ax.set_title("整体字段完整度对比")
    ax.set_ylim(0, 100)
    for i, v in enumerate([qc["raw"]["overall_fill_rate"] * 100, qc["clean"]["overall_fill_rate"] * 100]):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center")
    p = FIG_DIR / "07_overall_fill_before_after.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p)

    return paths


def split_and_save(feat: pd.DataFrame, seed: int = 42) -> dict:
    y = feat["label_death"]
    train_df, temp_df = train_test_split(feat, test_size=0.3, random_state=seed, stratify=y)
    val_df, test_df = train_test_split(
        temp_df, test_size=0.5, random_state=seed, stratify=temp_df["label_death"]
    )
    train_df.to_csv(OUT_DIR / "train.csv", index=False, encoding="utf-8-sig")
    val_df.to_csv(OUT_DIR / "val.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(OUT_DIR / "test.csv", index=False, encoding="utf-8-sig")
    feat.to_csv(OUT_DIR / "dataset_full.csv", index=False, encoding="utf-8-sig")
    try:
        feat.to_parquet(OUT_DIR / "dataset_full.parquet", index=False)
    except Exception as e:
        print("parquet 导出跳过:", e)
    return {
        "train": len(train_df),
        "val": len(val_df),
        "test": len(test_df),
        "train_pos_rate": round(float(train_df["label_death"].mean()), 4),
        "val_pos_rate": round(float(val_df["label_death"].mean()), 4),
        "test_pos_rate": round(float(test_df["label_death"].mean()), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="构建肝癌基线训练数据集")
    parser.add_argument("--include-xlsx", action="store_true", help="额外合并 基线数据2.xlsx")
    parser.add_argument("--max-miss", type=float, default=0.95, help="特征最大缺失率阈值")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    sources = list_source_files(include_xlsx=args.include_xlsx)
    if not sources:
        raise SystemExit("未找到源数据文件")

    print("源文件:")
    frames = []
    source_row_counts = {}
    for p in sources:
        print("  读取", p.name, "...")
        df = read_one_table(p)
        source_row_counts[p.name] = len(df)
        print(f"    rows={len(df)} cols={df.shape[1]}")
        frames.append(df)

    print("合并去重...")
    raw_all_rows = sum(source_row_counts.values())
    dedup = merge_and_dedup(frames)
    print(f"  原始合计行={raw_all_rows} → 去重后患者={len(dedup)}")

    # 保存去重后的宽表（便于溯源，去掉内部列）
    export_raw = dedup.drop(columns=[c for c in dedup.columns if c.startswith("__")], errors="ignore")
    export_raw.to_csv(OUT_DIR / "dedup_raw.csv", index=False, encoding="utf-8-sig")

    print("字段角色识别...")
    colmap = classify_columns(blank_to_na(dedup))
    for k, v in colmap.items():
        print(f"  {k}: {len(v)}")

    print("构建训练特征...")
    feat, build_meta = build_features(dedup, colmap, max_miss=args.max_miss)
    print(f"  训练样本={len(feat)} 特征数={build_meta['n_features']} 阳性率={feat['label_death'].mean():.4f}")

    qc = compute_qc(dedup, feat, colmap)
    qc["pipeline"] = {
        "sources": source_row_counts,
        "raw_total_rows": raw_all_rows,
        "dedup_patients": len(dedup),
        "overlap_removed": raw_all_rows - len(dedup),
        "max_miss": args.max_miss,
        "seed": args.seed,
    }
    qc["build_meta"] = {
        k: v
        for k, v in build_meta.items()
        if k != "categorical_maps"
    }
    qc["build_meta"]["categorical_map_sizes"] = {k: len(v) for k, v in build_meta.get("categorical_maps", {}).items()}

    print("划分 train/val/test...")
    split_info = split_and_save(feat, seed=args.seed)
    qc["split"] = split_info

    print("绘制对比图...")
    fig_paths = plot_comparisons(qc, feat, dedup)
    qc["figures"] = [str(p.relative_to(BASE_DIR)) for p in fig_paths]

    # 类别映射另存
    with (OUT_DIR / "categorical_maps.json").open("w", encoding="utf-8") as fh:
        json.dump(build_meta.get("categorical_maps", {}), fh, ensure_ascii=False, indent=2)

    with (OUT_DIR / "qc_before_after.json").open("w", encoding="utf-8") as fh:
        json.dump(qc, fh, ensure_ascii=False, indent=2, default=str)

    # 文本字段旁路导出（可选 NLP）
    text_cols = [c for c in colmap["text"] if c in dedup.columns]
    if text_cols:
        text_df = blank_to_na(dedup)[["patient_sn", "death"] + text_cols]
        text_df.to_csv(OUT_DIR / "text_fields_sidecar.csv", index=False, encoding="utf-8-sig")

    summary = {
        "sources": source_row_counts,
        "dedup_patients": len(dedup),
        "train_rows": len(feat),
        "n_features": build_meta["n_features"],
        "positive_rate": round(float(feat["label_death"].mean()), 4),
        "split": split_info,
        "figures": qc["figures"],
        "outputs": [
            "output/dataset_full.csv",
            "output/train.csv",
            "output/val.csv",
            "output/test.csv",
            "output/dedup_raw.csv",
            "output/qc_before_after.json",
            "output/categorical_maps.json",
            "output/text_fields_sidecar.csv",
        ],
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("\n完成。摘要:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
