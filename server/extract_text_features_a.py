# -*- coding: utf-8 -*-
"""
Task A · 文本规则特征抽取（无需模型）

输入：output/text_fields_sidecar.csv（或 dedup_raw.csv 中同名列）
输出：dataset/task_a/text_features.csv

用法（在项目根目录执行）：
  set PYTHONNOUSERSITE=1
  python server\\extract_text_features_a.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from config import task_a as cfg

ROOT = cfg.ROOT
SIDECAR = ROOT / "output" / "text_fields_sidecar.csv"
DEDUP = cfg.RAW_DEDUP
OUT_PATH = cfg.OUT_DIR / "text_features.csv"

DIAG_COLS = [
    "last_diagnosis",
    "main_diagnosis",
    "disease_name",
    "out_diagnosis_name",
    "icd10_name",
    "icd10_name_2",
    "icd10_code",
    "icd10_code_2",
    "out_icd10_code",
    "pre_disease_name",
    "infectious_disease_name",
    "pre_operative_diagnosis",
    "post_operative_diagnosis",
    "intra_operative_diagnosis",
]

HISTORY_COLS = [
    "last_visit_history_of_present_illness",
    "present_illness_history",
    "chief_complain",
    "positive_symptom",
    "past_history",
    "personal_history",
    "family_history",
]

EXAM_COLS = [
    "physical_exam",
    "specialist_exam",
    "auxiliary_exam",
    "exam_conclusion",
    "exam_finding",
    "imaging_conclusion",
    "imaging_finding",
    "immunohistochemistry_result",
]

SURGERY_COLS = [
    "surgical_name",
    "description",
]

# 抽取规则：命中 → 1；文本包非空但未命中 → 0；文本包全空 → NaN
RULES: list[tuple[str, str, list[str]]] = [
    # (feature_name, regex, which_blob: diag/history/exam/surgery/all)
    (
        "has_portal_vein_thrombus",
        r"门静脉?癌栓|门脉癌栓|PVTT|门静脉癌栓形成|门脉主干.?癌栓|门脉右支.?癌栓",
        ["diag", "history", "exam"],
    ),
    (
        "has_metastasis",
        r"肝外转移|远处转移|肺转移|骨转移|脑转移|肾上腺转移|淋巴结转移|腹腔.?种植|多发转移|伴转移",
        ["diag", "history", "exam"],
    ),
    (
        "cirrhosis_decompensated",
        r"失代偿|失代偿期",
        ["diag", "history"],
    ),
    (
        "cirrhosis_compensated",
        r"(?<!失)代偿期",
        ["diag", "history"],
    ),
    (
        "has_cirrhosis",
        r"肝硬化|肝硬变",
        ["diag", "history"],
    ),
    (
        "has_ascites",
        r"腹水|腹腔积液|移动性浊音\s*[（(]?[+＋阳]",
        ["diag", "history", "exam"],
    ),
    (
        "has_variceal_bleed",
        r"静脉曲张破裂出血|食管.?胃底.?静脉曲张.?出血|呕血|黑便|上消化道出血",
        ["diag", "history"],
    ),
    (
        "tx_tace",
        r"TACE|tace|肝动脉化疗栓塞|经导管动脉化疗栓塞|碘油.?栓塞|动脉栓塞术",
        ["history", "surgery"],
    ),
    (
        "tx_resection",
        r"肝叶切除|肝癌切除|肝部分切除|肝段切除|手术切除|肝切除术",
        ["history", "surgery", "diag"],
    ),
    (
        "tx_ablation",
        r"射频消融|微波消融|酒精消融|消融术|RFA|MWA",
        ["history", "surgery", "diag"],
    ),
    (
        "tx_transplant",
        r"肝移植|原位肝移植|OLT",
        ["history", "surgery", "diag"],
    ),
    (
        "symptom_jaundice",
        r"黄疸|皮肤巩膜黄染|巩膜黄染|尿黄",
        ["history", "exam"],
    ),
    (
        "symptom_bleed",
        r"呕血|黑便|便血|出血",
        ["history", "exam"],
    ),
    (
        "has_hbv",
        r"乙肝|乙型肝炎|HBsAg|慢性乙型",
        ["diag", "history"],
    ),
]

CNLC_RE = re.compile(
    r"CNLC\s*([IVX]+[abcABC]?|\d[abcABC]?)",
    re.IGNORECASE,
)
TNM_STAGE_RE = re.compile(
    r"(?:TNM|分期)[：:\s]*([IVX]+[ABC]?b?)",
    re.IGNORECASE,
)
# 如 (CNLC IIIa期) / CNLC IV期
CNLC_MAP = {
    "i": 1,
    "ia": 1,
    "ib": 1,
    "ii": 2,
    "iia": 2,
    "iib": 2,
    "iii": 3,
    "iiia": 3,
    "iiib": 3,
    "iv": 4,
    "iva": 4,
    "ivb": 4,
    "1": 1,
    "1a": 1,
    "1b": 1,
    "2": 2,
    "2a": 2,
    "2b": 2,
    "3": 3,
    "3a": 3,
    "3b": 3,
    "4": 4,
    "4a": 4,
    "4b": 4,
}


def _join_cols(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    use = [c for c in cols if c in df.columns]
    if not use:
        return pd.Series([""] * len(df), index=df.index)
    return (
        df[use]
        .fillna("")
        .astype(str)
        .agg(lambda r: " || ".join(v for v in r if v and v.lower() not in {"nan", "none"}), axis=1)
    )


def _combine_blobs(parts: list[pd.Series]) -> tuple[pd.Series, pd.Series]:
    """拼接多个文本包；返回 (blob, nonempty_mask)。空包不拼进内容。"""
    mats = [p.fillna("").astype(str) for p in parts]
    rows = []
    for i in range(len(mats[0])):
        chunks = []
        for m in mats:
            v = m.iloc[i].strip()
            if v and v.lower() not in {"nan", "none"}:
                chunks.append(v)
        rows.append(" || ".join(chunks))
    blob = pd.Series(rows, index=parts[0].index)
    nonempty = blob.str.len().gt(0)
    return blob, nonempty


def _apply_rule(blob: pd.Series, pattern: str, nonempty: pd.Series | None = None) -> pd.Series:
    if nonempty is None:
        nonempty = blob.fillna("").astype(str).str.strip().ne("")
    # 简单否定：命中前 8 字内出现 无/否认/未见 则不算阳性
    hit = blob.str.contains(pattern, regex=True, na=False)
    neg = blob.str.contains(
        rf"(?:无|否认|未见|阴性).{{0,6}}(?:{pattern})",
        regex=True,
        na=False,
    )
    hit = hit & ~neg
    out = pd.Series(np.nan, index=blob.index, dtype="float")
    out.loc[nonempty & hit] = 1.0
    out.loc[nonempty & ~hit] = 0.0
    return out


def _extract_stage(diag_blob: pd.Series) -> tuple[pd.Series, pd.Series]:
    """返回 stage_cnlc (1-4) 与 has_stage (0/1/NaN)。"""
    stages = []
    has = []
    for text in diag_blob.tolist():
        t = (text or "").strip()
        if not t:
            stages.append(np.nan)
            has.append(np.nan)
            continue
        m = CNLC_RE.search(t)
        val = np.nan
        if m:
            key = m.group(1).lower().replace("期", "")
            val = CNLC_MAP.get(key, np.nan)
            if np.isnan(val) and key.startswith("iii"):
                val = 3
            elif np.isnan(val) and key.startswith("ii"):
                val = 2
            elif np.isnan(val) and key.startswith("iv"):
                val = 4
            elif np.isnan(val) and key.startswith("i"):
                val = 1
        if np.isnan(val):
            m2 = TNM_STAGE_RE.search(t)
            if m2:
                key = m2.group(1).lower()
                val = CNLC_MAP.get(key, np.nan)
        if np.isnan(val):
            stages.append(np.nan)
            has.append(0.0)
        else:
            stages.append(float(val))
            has.append(1.0)
    return pd.Series(stages, index=diag_blob.index), pd.Series(has, index=diag_blob.index)


def load_text_source() -> pd.DataFrame:
    if SIDECAR.exists():
        print("读取", SIDECAR)
        df = pd.read_csv(SIDECAR, dtype=str, low_memory=False)
    elif DEDUP.exists():
        print("sidecar 不存在，回退", DEDUP)
        df = pd.read_csv(DEDUP, dtype=str, low_memory=False)
    else:
        raise SystemExit("未找到 text_fields_sidecar.csv 或 dedup_raw.csv")
    if "patient_sn" not in df.columns:
        raise SystemExit("缺少 patient_sn")
    df["patient_sn"] = df["patient_sn"].astype(str)
    # 一人一行：若有重复，保留首行（sidecar 已是患者级）
    if df["patient_sn"].duplicated().any():
        print("警告: patient_sn 有重复，保留首行")
        df = df.drop_duplicates("patient_sn", keep="first")
    print(f"  rows={len(df)} cols={df.shape[1]}")
    return df


def extract(df: pd.DataFrame) -> pd.DataFrame:
    blobs = {
        "diag": _join_cols(df, DIAG_COLS),
        "history": _join_cols(df, HISTORY_COLS),
        "exam": _join_cols(df, EXAM_COLS),
        "surgery": _join_cols(df, SURGERY_COLS),
    }
    blobs["all"] = (
        blobs["diag"]
        + " || "
        + blobs["history"]
        + " || "
        + blobs["exam"]
        + " || "
        + blobs["surgery"]
    )

    out = pd.DataFrame({"patient_sn": df["patient_sn"].astype(str)})
    coverage = {}

    for name, pattern, sources in RULES:
        parts = [blobs[s] for s in sources if s in blobs]
        blob, nonempty = _combine_blobs(parts)
        out[name] = _apply_rule(blob, pattern, nonempty)
        coverage[name] = {
            "nonempty_rate": round(float(nonempty.mean()), 4),
            "positive_rate": round(float((out[name] == 1).mean()), 4),
            "missing_rate": round(float(out[name].isna().mean()), 4),
            "pattern": pattern,
            "sources": sources,
        }

    stage, has_stage = _extract_stage(blobs["diag"])
    # 诊断包为空 → has_stage/stage 均为 NaN
    empty_diag = blobs["diag"].str.strip().eq("")
    has_stage = has_stage.where(~empty_diag, np.nan)
    stage = stage.where(~empty_diag, np.nan)
    out["stage_cnlc"] = stage
    out["has_stage"] = has_stage
    coverage["stage_cnlc"] = {
        "nonempty_rate": round(float((~empty_diag).mean()), 4),
        "positive_rate": round(float((has_stage == 1).mean()), 4),
        "missing_rate": round(float(stage.isna().mean()), 4),
        "pattern": "CNLC/TNM",
        "sources": ["diag"],
    }
    coverage["has_stage"] = coverage["stage_cnlc"]

    # 文本包是否可用（元数据）
    out["text_diag_available"] = (~empty_diag).astype(int)
    out["text_history_available"] = blobs["history"].str.strip().ne("").astype(int)

    return out, coverage


def main():
    df = load_text_source()
    feat, coverage = extract(df)
    cfg.OUT_DIR.mkdir(parents=True, exist_ok=True)
    feat.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    cov_path = cfg.OUT_DIR / "text_feature_coverage.json"
    with cov_path.open("w", encoding="utf-8") as fh:
        json.dump(coverage, fh, ensure_ascii=False, indent=2)

    print("\n写入", OUT_PATH)
    print("覆盖率摘要:")
    for k, v in coverage.items():
        if k == "has_stage":
            continue
        print(
            f"  {k}: pos={v['positive_rate']:.1%} miss={v['missing_rate']:.1%} "
            f"text_nonempty={v['nonempty_rate']:.1%}"
        )
    print(f"特征列: {[c for c in feat.columns if c != 'patient_sn']}")


if __name__ == "__main__":
    main()
