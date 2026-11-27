# -*- coding: utf-8 -*-
"""Task A：死亡二分类训练集配置。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DEDUP = ROOT / "output" / "dedup_raw.csv"
OUT_DIR = ROOT / "dataset" / "task_a"

SEED = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.15  # 相对全量；先切 30% 再对半分 → 约 70/15/15

# 标签
LABEL_COL = "label_death"
ID_COL = "patient_sn"

# 肝癌强关键词（队列可证实）
HCC_STRONG_KEYWORDS = [
    "肝癌",
    "肝细胞癌",
    "原发性肝癌",
    "肝恶性肿瘤",
    "肝细胞性癌",
    "HCC",
    "hcc",
    "肝Ca",
    "肝CA",
]

# 用于队列打标的诊断相关列（存在则拼接）
DIAG_TEXT_COLS = [
    "main_diagnosis",
    "icd10_name",
    "icd10_code",
    "disease_name",
    "icd10_name_2",
    "icd10_code_2",
    "last_diagnosis",
    "out_diagnosis_name",
    "pre_operative_diagnosis",
    "post_operative_diagnosis",
]

# 明确泄漏 / 不宜作预测特征的列
LEAKAGE_COLS = {
    "death",
    "death_time",
    "death_reason",
    "death_or_last_visit_date",
    "label_death",
}

# PII
PII_COLS = {
    "name",
    "inpatient_no_id",
    "基线_inpatient_no_id",
    "patient_id",
    "pathology_id",
    "pathology_exam_id",
    "exam_id",
}

# 核心表型特征（Task A 主特征集）
CORE_FEATURES = [
    "gender",
    "age",
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
    "times_of_inhospitalization",
    "years_of_smoking",
    "daily_smoking_amount",
    "abo_blood_type",
    "marriage_status",
    "visit_type",
    "baseline_year",
    "follow_up_days",  # 训练时可选用；基线模型默认排除防泄漏争议时见 EXCLUDE_FROM_MODEL
    "cohort_hcc_strong",
]

# 建模时默认不用的列（标签/ID/QC/可选泄漏争议）
EXCLUDE_FROM_MODEL = {
    ID_COL,
    LABEL_COL,
    "cohort_hcc_strong",  # 可用作筛选，默认不当特征；也可打开
    "qc_age_oob",
    "qc_death_no_followup",
    "qc_smoke_conflict",
    "label_uncertain",
    "split",
}

# follow_up_days 是否入模：分类任务中它含结局时间信息，默认不入模
MODEL_EXCLUDE_EXTRA = {
    "follow_up_days",
    # 文本可用性标记：元数据，默认不入模
    "text_diag_available",
    "text_history_available",
}

# 文本规则特征（由 extract_text_features_a.py 生成后并入）
TEXT_FEATURES_PATH = OUT_DIR / "text_features.csv"
USE_TEXT_FEATURES = True
TEXT_FEATURE_COLS = [
    "has_portal_vein_thrombus",
    "has_metastasis",
    "cirrhosis_decompensated",
    "cirrhosis_compensated",
    "has_cirrhosis",
    "has_ascites",
    "has_variceal_bleed",
    "tx_tace",
    "tx_resection",
    "tx_ablation",
    "tx_transplant",
    "symptom_jaundice",
    "symptom_bleed",
    "has_hbv",
    "stage_cnlc",
    "has_stage",
]
TEXT_META_COLS = [
    "text_diag_available",
    "text_history_available",
]

# 缺失率超过该阈值的核心特征仍保留，但会生成缺失指示
MAX_MISS_DROP = 0.98

# 是否为每个核心数值/二值特征生成 *_isna
ADD_MISSING_INDICATORS = True
